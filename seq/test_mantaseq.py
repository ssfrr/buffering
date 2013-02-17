import unittest
from mock import Mock, patch
from mantaseq import MantaSeq
from mantaseq import make_note
from manta import PadVelocityEvent, PadValueEvent

# base MIDI note (for the first pad used for note selection)
# is C3
MIDI_BASE_NOTE = 48

class MockedBoundaryTest(unittest.TestCase):
    def setUp(self):
        # note that because Manta and MIDISource are imported with from...
        # then we have to patch them in the mantaseq namespace
        self.manta_patch = patch('mantaseq.Manta')
        self.manta_patch.start()
        self.midi_patch = patch('mantaseq.MIDISource')
        self.midi_patch.start()
        self.seq = MantaSeq()
        self.event_queue = []
        self.seq._manta.process.side_effect = self.get_next_event

    def tearDown(self):
        self.manta_patch.stop()
        self.midi_patch.stop()

    def get_next_event(self):
        # each element in event_queue should be a list of events to be
        # returned by a manta.process() call, or a single event in which
        # case it gets wrapped in a list before being returned
        if self.event_queue:
            event = self.event_queue.pop(0)
            try:
                # just to check whether it's iterable
                iter(event)
                return event
            except TypeError:
                return [event]
        else:
            return []

    def process_queued_manta_events(self):
        '''Calls the MantaSeq.process() call for each queued manta message'''
        for i in range(len(self.event_queue)):
            self.seq.process()

    def enqueue_step_deselect(self, step_num):
        self.event_queue.append(PadVelocityEvent(step_num, 0))

    def enqueue_step_select(self, step_num):
        self.event_queue.append(PadVelocityEvent(step_num, 100))

    def enqueue_note_velocity_event(self, pad_offset, velocity):
        self.event_queue.append(PadVelocityEvent(pad_offset + 16, velocity))

    def enqueue_note_value_event(self, pad_offset, value):
        self.event_queue.append(PadValueEvent(pad_offset + 16, value))

    def assert_midi_note_sent(self, note, velocity):
        self.seq._midi_source.send.assert_called_with(make_note(note, velocity))

    def assert_no_midi_note_sent(self):
        self.assertEqual(len(self.seq._midi_source.send.mock_calls), 0)


class TestPassThrough(MockedBoundaryTest):
    def test_process_generates_base_midi_note(self):
        self.enqueue_note_velocity_event(0, 100)
        self.process_queued_manta_events()
        self.assert_midi_note_sent(MIDI_BASE_NOTE, 100)

    def test_process_generates_releases(self):
        self.enqueue_note_velocity_event(0, 0)
        self.process_queued_manta_events()
        self.assert_midi_note_sent(MIDI_BASE_NOTE, 0)

    def test_process_generates_octave_above_base_midi_notes(self):
        self.enqueue_note_velocity_event(16, 100)
        self.process_queued_manta_events()
        self.assert_midi_note_sent(MIDI_BASE_NOTE + 12, 100)

class TestSelection(MockedBoundaryTest):
    def test_selected_seq_notes_prevent_pass_through(self):
        # first hit a step-selection pad, then a note pad
        self.enqueue_step_select(3)
        self.enqueue_note_velocity_event(16, 100)
        self.process_queued_manta_events()
        # assert that we didn't send out any MIDI notes
        self.assert_no_midi_note_sent()

    def test_deselecting_notes_reenables_pass_through(self):
        self.enqueue_step_select(3)
        self.enqueue_step_deselect(3)
        self.enqueue_note_velocity_event(0, 100)
        self.process_queued_manta_events()
        self.assert_midi_note_sent(MIDI_BASE_NOTE, 100)

class TestStepSetting(MockedBoundaryTest):
    def setUp(self):
        super(TestStepSetting, self).setUp()
        self.enqueue_step_select(3)
        self.enqueue_note_value_event(0, 100)
        self.process_queued_manta_events()

    def test_pad_values_set_step_note(self):
        self.assertEqual(self.seq._seq.steps[3].note, MIDI_BASE_NOTE)

    def test_pad_values_set_step_velocity(self):
        self.assertEqual(self.seq._seq.steps[3].velocity, 100)

