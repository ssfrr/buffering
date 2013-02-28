from manta import note_from_pad, OFF, AMBER, RED
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

class MantaSeqIdleState(MantaSeqState):
    def process_step_press(self, step_num):
        self.manta_seq._seq.select_step(step_num)
        self.manta_seq._light_note_for_step(step_num)
        self.manta_seq._state = MantaSeqStepsSelectedState(self.manta_seq)

    def process_shift_press(self):
        self.manta_seq._state = MantaSeqShiftedState(self.manta_seq)

    def process_note_velocity(self, pad_num, velocity):
        note_num = note_from_pad(pad_num)
        self.manta_seq._send_midi_note(note_num, velocity)

class MantaSeqStepsSelectedState(MantaSeqState):
    def process_step_press(self, step_num):
        self.manta_seq._seq.select_step(step_num)
        self.manta_seq._light_note_for_step(step_num)

    def process_step_release(self, step_num):
        self.manta_seq._seq.deselect_step(step_num)
        self.manta_seq._light_note_for_step(step_num)
        if len(self.manta_seq._seq.selected_steps) == 0:
            self.manta_seq._state = MantaSeqIdleState(self.manta_seq)

    def process_note_value(self, pad_num, value):
        note_num = note_from_pad(pad_num)
        self.manta_seq._seq.set_note(note_num)
        self.manta_seq._seq.set_velocity(value)
        # first set the pad color of the note pad
        if value == 0:
            self.manta_seq._set_led_pad(OFF, pad_num)
        elif value < self.manta_seq.led_color_threshold:
            self.manta_seq._set_led_pad(AMBER, pad_num)
        else:
            self.manta_seq._set_led_pad(RED, pad_num)

        # then update the pad colors of any selected pads
        for i, step in enumerate(self.manta_seq._seq.steps):
            if step in self.manta_seq._seq.selected_steps:
                self.manta_seq._set_led_pad(self.manta_seq._get_step_color(i), i)

class MantaSeqShiftedState(MantaSeqState):
    def process_shift_release(self):
        self.manta_seq._state = MantaSeqIdleState(self.manta_seq)

    def process_slider_value(self, slider_num, value):
        if slider_num == 0:
            self.manta_seq._state = MantaSeqTempoAdjustState(
                    self.manta_seq, value,
                    self.manta_seq.step_duration)

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
