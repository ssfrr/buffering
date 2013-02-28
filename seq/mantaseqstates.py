from manta import note_from_pad, OFF, AMBER, RED
class MantaSeqState(object):
    def process_step_press(self, manta, step_num):
        pass

    def process_step_release(self, manta, step_num):
        pass

    def process_shift_press(self, manta):
        pass

    def process_shift_release(self, manta):
        pass

    def process_note_value(self, manta, note_pad, value):
        pass

    def process_note_velocity(self, manta, note_pad, velocity):
        pass

    def process_slider_value(self, manta, slider_num, value):
        pass

    def process_slider_release(self, manta, slider_num):
        pass

class MantaSeqIdleState(MantaSeqState):
    def process_step_press(self, manta, step_num):
        manta._seq.select_step(step_num)
        manta._light_note_for_step(step_num)
        manta._state = MantaSeqStepsSelectedState()

    def process_shift_press(self, manta):
        manta._state = MantaSeqShiftedState()

    def process_note_velocity(self, manta, pad_num, velocity):
        note_num = note_from_pad(pad_num)
        manta._send_midi_note(note_num, velocity)

class MantaSeqStepsSelectedState(MantaSeqState):
    def process_step_press(self, manta, step_num):
        manta._seq.select_step(step_num)
        manta._light_note_for_step(step_num)

    def process_step_release(self, manta, step_num):
        manta._seq.deselect_step(step_num)
        manta._light_note_for_step(step_num)
        if len(manta._seq.selected_steps) == 0:
            manta._state = MantaSeqIdleState()

    def process_note_value(self, manta, pad_num, value):
        note_num = note_from_pad(pad_num)
        manta._seq.set_note(note_num)
        manta._seq.set_velocity(value)
        # first set the pad color of the note pad
        if value == 0:
            manta._set_led_pad(OFF, pad_num)
        elif value < manta.led_color_threshold:
            manta._set_led_pad(AMBER, pad_num)
        else:
            manta._set_led_pad(RED, pad_num)

        # then update the pad colors of any selected pads
        for i, step in enumerate(manta._seq.steps):
            if step in manta._seq.selected_steps:
                manta._set_led_pad(manta._get_step_color(i), i)

class MantaSeqShiftedState(MantaSeqState):
    def process_shift_release(self, manta):
        manta._state = MantaSeqIdleState()

    def process_slider_value(self, manta, slider_num, value):
        if slider_num == 0:
            manta._state = MantaSeqTempoAdjustState(value, manta.step_duration)

class MantaSeqTempoAdjustState(MantaSeqState):
    def __init__(self, slide_begin, initial_duration):
        'Takes the initial value of the slider so we can reference against it'
        self.slide_begin = slide_begin
        self.initial_duration = initial_duration

    def process_shift_release(self, manta):
        manta._state = MantaSeqIdleState()

    def process_slider_value(self, manta, slider_num, value):
        if slider_num == 0:
            # the exponent should be between -1 and 1. Note that we're working
            # with duration instead of tempo so the exponiation is backwards
            exponent = (self.slide_begin - value)
            manta.step_duration = self.initial_duration * 2 ** exponent

    def process_slider_release(self, manta, slider_num):
        manta._state = MantaSeqShiftedState()
