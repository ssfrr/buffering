from simplecoremidi import MIDISource
from stepseq import Seq
from manta import (Manta,
                   PadVelocityEvent,
                   ButtonVelocityEvent,
                   PadValueEvent,
                   SliderValueEvent,
                   note_from_pad,
                   pad_from_note,
                   row_from_pad,
                   OFF, AMBER, RED,
                   PAD_AND_BUTTON)
import time
from mantaseqstates import *

class MantaSeqPadLED(object):
    led_color_threshold = 75
    def __init__(self, pad_num, manta):
        self.pad_num = pad_num
        self.manta = manta
        self.led_state = OFF
        self._intensity = 0
        self._active = False
        self._highlight = False
        self.highlight_color = RED
        self.active_color = AMBER

    def highlight(self, highlight):
        self._highlight = highlight
        self._update_led()

    def active(self, active):
        self._active = active
        self._update_led()

    def intensity(self, intensity):
        self._intensity = intensity
        self._update_led()

    def _update_led(self):
        if self._intensity > MantaSeqPadLED.led_color_threshold:
            new_led_state = RED
        elif self._highlight:
            new_led_state = self.highlight_color
        elif self._active:
            new_led_state = self.active_color
        elif self._intensity > 0:
            new_led_state = AMBER
        else:
            new_led_state = OFF

        if self.led_state != new_led_state:
            self.manta.set_led_pad(new_led_state, self.pad_num)
            self.led_state = new_led_state

class MantaSeq(object):
    def __init__(self):
        #TODO: get rid of current_step attribute in favor of querying seq
        self._manta = Manta()
        self._midi_source = MIDISource('MantaSeq')
        self._seq = Seq()
        self._manta.set_led_enable(PAD_AND_BUTTON, True)
        self.step_duration = 0.125
        # the first step should get executed on the first process() call
        self.next_step_timestamp = time.time()
        self.current_step = 0
        self.note_offs = {}
        self.running = False
        self.start_stop_button = 0
        self.shift_button = 1
        self._state = MantaSeqIdleState(self)
        self.pad_leds = [MantaSeqPadLED(i, self._manta) for i in range(48)]

    def cleanup(self):
        self._manta.set_led_enable(PAD_AND_BUTTON, False)

    def start(self):
        self.running = True
        self.next_step_timestamp = time.time()

    def stop(self):
        self.running = False

    def _get_step_color(self, step_num):
        if step_num == self.current_step:
            return RED
        elif self._seq.steps[step_num].velocity > 0:
            return AMBER
        else:
            return OFF

    def _send_midi_cc(self, cc_num, value):
        self._midi_source.send(make_cc(cc_num, value))

    def _send_midi_note(self, note_num, velocity):
        # remove from note_offs dict if present
        self.note_offs.pop(note_num, None)
        midi_note = make_note(note_num, velocity)
        self._midi_source.send(midi_note)

    def _schedule_note_off(self, note_num, timestamp):
        self.note_offs[note_num] = timestamp

    def set_pad_highlight(self, pad_num, highlight):
        self.pad_leds[pad_num].highlight(highlight)

    def set_pad_active(self, pad_num, active):
        self.pad_leds[pad_num].active(active)

    def set_pad_intensity(self, pad_num, intensity):
        self.pad_leds[pad_num].intensity(intensity)

    def process(self):
        now = time.time()
        events = self._manta.process()
        for event in events:
            if isinstance(event, PadVelocityEvent):
                self._process_pad_velocity_event(event)
            if isinstance(event, ButtonVelocityEvent):
                self._process_button_velocity_event(event)
            elif isinstance(event, PadValueEvent):
                self._process_pad_value_event(event)
            elif isinstance(event, SliderValueEvent):
                self._process_slider_value_event(event)

        # send any pending note_offs
        for note_num, timestamp in self.note_offs.items():
            if now >= timestamp:
                # send_midi_note will take care of removing the note
                # from the list
                self._send_midi_note(note_num, 0)
                self.set_pad_intensity(pad_from_note(note_num), 0)

        # if it's time for another step, do it
        if self.running and now >= self.next_step_timestamp:
            last_step = self.current_step
            self.current_step = self._seq.current_step_index
            step_obj = self._seq.step()
            if step_obj.velocity > 0:
                self._send_midi_note(step_obj.note, step_obj.velocity)
                note_off_timestamp = self.next_step_timestamp + (step_obj.duration *
                            self.step_duration)
                self._schedule_note_off(step_obj.note, note_off_timestamp)
                self.set_pad_intensity(pad_from_note(step_obj.note),
                        step_obj.velocity)
            self._send_midi_cc(0, step_obj.cc0)
            self._send_midi_cc(1, step_obj.cc1)

            # update the step LEDs (previous and current)
            self.set_pad_highlight(last_step, False)
            self.set_pad_highlight(self.current_step, True)

            # remember which step we turned on so we can turn it off next time
            # around
            self.next_step_timestamp += self.step_duration

    # most of the events get deferred to the state, as they're state-dependent
    def _process_pad_velocity_event(self, event):
        if row_from_pad(event.pad_num) < 2:
            if event.velocity > 0:
                self._state.process_step_press(event.pad_num)
            else:
                self._state.process_step_release(event.pad_num)
        else:
            self._state.process_note_velocity(event.pad_num,
                                              event.velocity)

    def _process_button_velocity_event(self, event):
        if event.button_num == self.start_stop_button:
            if event.velocity > 0:
                self.stop() if self.running else self.start()
        elif event.button_num == self.shift_button:
            if event.velocity > 0:
                self._state.process_shift_press()
            else:
                self._state.process_shift_release()

    def _process_pad_value_event(self, event):
        # pad value messages are ignored for step selection pads
        if event.pad_num > 15:
            self._state.process_note_value(event.pad_num, event.value)

    def _process_slider_value_event(self, event):
        if event.touched:
            self._state.process_slider_value(event.slider_num, event.value)
        else:
            self._state.process_slider_release(event.slider_num)

def make_note(note, velocity, channel = 0):
    return (0x90 | channel, note, velocity)

def make_cc(cc_num, value, channel = 0):
    return (0xB0 | channel, cc_num, value)

def main():
    seq = MantaSeq()
    try:
        while True:
            seq.process()
            time.sleep(0.0001)
    except KeyboardInterrupt:
        seq.cleanup()

if __name__ == '__main__':
    main()
