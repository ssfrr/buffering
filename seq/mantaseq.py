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

class MantaSeq(object):
    def __init__(self):
        self._manta = Manta()
        self._midi_source = MIDISource('MantaSeq')
        self._seq = Seq()
        self._manta.set_led_enable(PAD_AND_BUTTON, True)
        self.led_color_threshold = 75
        self.step_duration = 0.125
        # the first step should get executed on the first process() call
        self.next_step_timestamp = time.time()
        self.current_step = 0
        self.note_offs = {}
        self.tempo_adjustment_in_progress = False
        self.running = False

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

    def _send_midi_note(self, note_num, velocity):
        # remove from note_offs dict if present
        self.note_offs.pop(note_num, None)
        midi_note = make_note(note_num, velocity)
        self._midi_source.send(midi_note)

    def _schedule_note_off(self, note_num, timestamp):
        self.note_offs[note_num] = timestamp

    def _set_led_pad(self, *args):
        self._manta.set_led_pad(*args)

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
                self._set_led_pad(OFF, pad_from_note(note_num))

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
                self._set_led_pad(AMBER, pad_from_note(step_obj.note))

            # update the step LEDs (previous and current)
            self._set_led_pad(self._get_step_color(last_step), last_step)
            self._set_led_pad(self._get_step_color(self.current_step),
                                    self.current_step)
            # remember which step we turned on so we can turn it off next time
            # around
            self.next_step_timestamp += self.step_duration

    def _process_pad_velocity_event(self, event):
        if row_from_pad(event.pad_num) < 2:
            if event.velocity > 0:
                self._seq.select_step(event.pad_num)
            else:
                self._seq.deselect_step(event.pad_num)
        else:
            # only pass-through if no steps are selected
            if self._seq.selected_steps == []:
                note_num = note_from_pad(event.pad_num)
                self._send_midi_note(note_num, event.velocity)

    def _process_button_velocity_event(self, event):
        if event.velocity > 0:
            if self.running:
                self.stop()
            else:
                self.start()

    def _process_pad_value_event(self, event):
        # pad value messages are ignored for step selection pads
        if event.pad_num > 15:
            note_num = note_from_pad(event.pad_num)
            self._seq.set_note(note_num)
            self._seq.set_velocity(event.value)
            # first set the pad color of the note pad
            if event.value == 0:
                self._set_led_pad(OFF, event.pad_num)
            elif event.value < self.led_color_threshold:
                self._set_led_pad(AMBER, event.pad_num)
            else:
                self._set_led_pad(RED, event.pad_num)

            # then update the pad colors of any selected pads
            for i, step in enumerate(self._seq.steps):
                if step in self._seq.selected_steps:
                    self._set_led_pad(self._get_step_color(i), i)

    def _process_slider_value_event(self, event):
        if not event.touched:
            self.tempo_adjustment_in_progress = False
        elif self.tempo_adjustment_in_progress:
            # the exponent should be between -1 and 1. Note that we're working
            # with duration instead of tempo so the exponiation is backwards
            exponent = (self.reference_slider_value - event.value)
            self.step_duration = self.reference_step_duration * 2 ** exponent
        else:
            self.tempo_adjustment_in_progress = True
            self.reference_step_duration = self.step_duration
            self.reference_slider_value = event.value

def make_note(note, velocity, channel = 0):
    return (0x90 | channel, note, velocity)

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
