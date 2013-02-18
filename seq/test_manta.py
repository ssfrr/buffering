import unittest
from manta import note_from_pad, pad_from_note

BASE_MIDI_NOTE = 48

class TestNoteConversion(unittest.TestCase):
    def test_base_midi_note(self):
        self.assertEquals(note_from_pad(0), BASE_MIDI_NOTE)

    def test_up_two_rows_is_one_octave(self):
        self.assertEquals(note_from_pad(16), BASE_MIDI_NOTE + 12)

    def test_over_6_columns_is_one_octave(self):
        self.assertEquals(note_from_pad(6), BASE_MIDI_NOTE + 12)

    def test_base_midi_note_gives_first_pad(self):
        self.assertEquals(pad_from_note(BASE_MIDI_NOTE), 0)

    def test_octave_above_base_midi_note_gives_16th_pad(self):
        self.assertEquals(pad_from_note(BASE_MIDI_NOTE+12), 16)
