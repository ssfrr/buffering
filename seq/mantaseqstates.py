from manta import note_from_pad, OFF, AMBER, RED, pad_from_note
class MantaSeqState(object):
    def __init__(self, manta_seq):
        self.manta_seq = manta_seq

    def process_step_press(self, step_num):
        pass

    def process_step_release(self, step_num):
        pass

    def process_shift_press(self):
        pass

    def process_shift_release(self):
        pass

    def process_note_value(self, note_pad, value):
        pass

    def process_note_velocity(self, note_pad, velocity):
        pass

    def process_slider_value(self, slider_num, value):
        pass

    def process_slider_release(self, slider_num):
        pass

    def set_note_intensity_from_step_num(self, step_num, on):
        '''if on is True, the intensity is set from the steps velocity.
        if on is False, the intensity is set to zero'''
        step = self.manta_seq._seq.steps[step_num]
        if step.velocity > 0:
            if on:
                intensity = step.velocity
            else:
                intensity = 0
            pad_num = pad_from_note(step.note)
            self.manta_seq.set_pad_intensity(pad_num, intensity)

    def prefill_steps(self):
        '''
        If the mantaseq has any notes or sliders already selected,
        assign them to the notes.
        '''
        selected_note = self.manta_seq._selected_note
        if selected_note is not None:
            self.manta_seq._seq.set_note(selected_note[0])
            self.manta_seq._seq.set_velocity(selected_note[1])
        selected_cc1 = self.manta_seq._selected_cc1
        if selected_cc1 is not None:
            self.manta_seq._seq.set_cc1(selected_cc1)
        selected_cc2 = self.manta_seq._selected_cc2
        if selected_cc2 is not None:
            self.manta_seq._seq.set_cc2(selected_cc2)

class MantaSeqIdleState(MantaSeqState):
    def process_step_press(self, step_num):
        self.manta_seq._seq.select_step(step_num)
        self.set_note_intensity_from_step_num(step_num, True)
        self.prefill_steps()
        if self.manta_seq._selected_note is not None:
            self.manta_seq.set_pad_active(step_num, True)

        self.manta_seq._state = MantaSeqStepsSelectedState(self.manta_seq)

    def process_shift_press(self):
        self.manta_seq._state = MantaSeqShiftedState(self.manta_seq)

    def process_note_velocity(self, pad_num, velocity):
        note_num = note_from_pad(pad_num)
        self.manta_seq._send_midi_note(note_num, velocity)

    def process_note_value(self, pad_num, value):
        note_num = note_from_pad(pad_num)
        if value > 0:
            self.manta_seq._selected_note = (note_num, value)
        else:
            self.manta_seq._selected_note = None

    def process_slider_value(self, slider_num, value):
        cc_value = int(value * 127)
        if slider_num == 0:
            self.manta_seq._global_cc1 = cc_value
            self.manta_seq._selected_cc1 = cc_value
        else:
            self.manta_seq._global_cc2 = cc_value
            self.manta_seq._selected_cc2 = cc_value
        self.manta_seq._send_midi_cc(slider_num + 1, cc_value)

    def process_slider_release(self, slider_num):
        if slider_num == 0:
            self.manta_seq._selected_cc1 = None
        else:
            self.manta_seq._selected_cc2 = None

class MantaSeqStepsSelectedState(MantaSeqState):
    def process_step_press(self, step_num):
        self.manta_seq._seq.select_step(step_num)
        self.set_note_intensity_from_step_num(step_num, True)
        self.prefill_steps()
        if self.manta_seq._selected_note is not None:
            self.manta_seq.set_pad_active(step_num, True)

    def process_step_release(self, step_num):
        self.manta_seq._seq.deselect_step(step_num)
        self.set_note_intensity_from_step_num(step_num, False)
        if len(self.manta_seq._seq.selected_steps) == 0:
            self.manta_seq._state = MantaSeqIdleState(self.manta_seq)
        # TODO: make sure all pads have intensity of 0, otherwise they
        # could get stuck on, as the intensity doesn't get updated unless
        # there are steps selected

    def process_note_value(self, pad_num, value):
        note_num = note_from_pad(pad_num)
        self.manta_seq._seq.set_note(note_num)
        self.manta_seq._seq.set_velocity(value)
        # note - this isn't very efficient. if necessary we should
        # use the set_row_led API call
        for i in range(48):
            if i != pad_num:
                self.manta_seq.set_pad_intensity(i, 0)
        self.manta_seq.set_pad_intensity(pad_num, value)
        if value > 0:
            self.manta_seq._selected_note = (note_num, value)
        else:
            self.manta_seq._selected_note = None

        # then update the pad colors of any selected pads
        for i, step in enumerate(self.manta_seq._seq.steps):
            if step in self.manta_seq._seq.selected_steps:
                active = (value > 0)
                self.manta_seq.set_pad_active(i, active)

    def process_slider_value(self, slider_num, value):
        if slider_num == 0:
            self.manta_seq._seq.set_cc1(int(value * 127))
        else:
            self.manta_seq._seq.set_cc2(int(value * 127))

class MantaSeqShiftedState(MantaSeqState):
    def process_shift_release(self):
        self.manta_seq._state = MantaSeqIdleState(self.manta_seq)

    def process_slider_value(self, slider_num, value):
        if slider_num == 0:
            self.manta_seq._state = MantaSeqTempoAdjustState(
                    self.manta_seq, value,
                    self.manta_seq.step_duration)

    def process_step_press(self, step_num):
        '''Shifted step select erases that note'''
        self.manta_seq.set_pad_active(step_num, False)
        self.manta_seq._seq.select_step(step_num)
        self.manta_seq._seq.set_velocity(0)
        self.manta_seq._seq.set_cc1(0)
        self.manta_seq._seq.set_cc2(0)
        self.manta_seq._seq.deselect_step(step_num)

class MantaSeqTempoAdjustState(MantaSeqState):
    def __init__(self, manta_seq, slide_begin, initial_duration):
        'Takes the initial value of the slider so we can reference against it'
        super(MantaSeqTempoAdjustState, self).__init__(manta_seq)
        self.slide_begin = slide_begin
        self.initial_duration = initial_duration

    def process_shift_release(self):
        self.manta_seq._state = MantaSeqIdleState(self.manta_seq)

    def process_slider_value(self, slider_num, value):
        if slider_num == 0:
            # the exponent should be between -1 and 1. Note that we're working
            # with duration instead of tempo so the exponiation is backwards
            exponent = (self.slide_begin - value)
            self.manta_seq.step_duration = self.initial_duration * 2 ** exponent

    def process_slider_release(self, slider_num):
        self.manta_seq._state = MantaSeqShiftedState(self.manta_seq)
