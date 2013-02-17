from simplecoremidi import MIDISource
from stepseq import Seq
from manta import (Manta,
                   PadVelocityEvent,
                   PadValueEvent,
                   note_from_pad,
                   row_from_pad)
from time import sleep

class MantaSeq(object):
    def __init__(self):
        self._manta = Manta()
        self._midi_source = MIDISource('MantaSeq')
        self._seq = Seq()

    def process(self):
        events = self._manta.process()
        for event in events:
            if isinstance(event, PadVelocityEvent):
                self._process_pad_velocity_event(event)
            elif isinstance(event, PadValueEvent):
                self._process_pad_value_event(event)

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
                midi_note = make_note(note_num, event.velocity)
                self._midi_source.send(midi_note)

    def _process_pad_value_event(self, event):
        note_num = note_from_pad(event.pad_num)
        self._seq.set_note(note_num)
        self._seq.set_velocity(event.value)

def make_note(note, velocity, channel = 0):
    return (0x90 | channel, note, velocity)

def main():
    seq = MantaSeq()
    try:
        while True:
            seq.process()
            sleep(0.003)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
