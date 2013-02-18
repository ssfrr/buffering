import unittest
from mock import Mock, patch
from mantaseq import MantaSeq
from mantaseq import make_note
from manta import (PadVelocityEvent,
                   PadValueEvent,
                   ButtonVelocityEvent,
                   SliderValueEvent,
                   AMBER, RED, OFF,
                   PAD_AND_BUTTON)

# base MIDI note (for the first pad used for note selection)
# is C3
MIDI_BASE_NOTE = 60

class MockedBoundaryTest(unittest.TestCase):
    def setUp(self):
        # note that because Manta and MIDISource are imported with from...
        # then we have to patch them in the mantaseq namespace
        self.manta_patch = patch('mantaseq.Manta')
        self.manta_patch.start()
        self.midi_patch = patch('mantaseq.MIDISource')
        self.midi_patch.start()
        self.time_patch = patch('time.time',
                side_effect = lambda: self.logical_time)
        self.time_patch.start()
        # allow the logical time of a test to be set
        self.logical_time = 1000

        self.seq = MantaSeq()
        self.event_queue = []
        self.seq._manta.process.side_effect = self.get_next_event
        self.seq._manta.set_led_pad.side_effect = self.set_led_state
        self.led_states = [OFF] * 48
        self.seq.start()

    def step_time(self, amount):
        self.logical_time += amount

    def tearDown(self):
        self.manta_patch.stop()
        self.midi_patch.stop()
        self.time_patch.stop()

    def add_sequenced_note(self, step, pad_offset, velocity):
        self.enqueue_step_select(step)
        self.enqueue_note_value_event(pad_offset, velocity)
        self.enqueue_step_deselect(step)
        self.enqueue_note_value_event(pad_offset, 0)

    def set_led_state(self, led_state, pad_num):
        self.led_states[pad_num] = led_state

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

    def assert_led_state(self, pad_num, state):
        self.assertEqual(self.led_states[pad_num], state)

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

class TestLEDBehavior(MockedBoundaryTest):
    def test_initializes_leds(self):
        self.seq._manta.set_led_enable.assert_called_with(PAD_AND_BUTTON, True)

    def test_low_pad_value_causes_amber_led(self):
        self.enqueue_note_value_event(0, 35)
        self.process_queued_manta_events()
        self.assert_led_state(16, AMBER)

    def test_high_pad_value_causes_red_led(self):
        self.enqueue_note_value_event(0, 100)
        self.process_queued_manta_events()
        self.assert_led_state(16, RED)

    def test_zero_pad_value_turns_led_off(self):
        self.enqueue_note_value_event(0, 100)
        self.enqueue_note_value_event(0, 0)
        self.process_queued_manta_events()
        self.assert_led_state(16, OFF)

    def test_pad_values_dont_effect_step_pads(self):
        self.event_queue.append(PadValueEvent(15, 50))
        self.process_queued_manta_events()
        self.assert_led_state(15, OFF)

    def test_red_led_should_track_step(self):
        self.seq.process()
        self.assert_led_state(0, RED)
        self.step_time(self.seq.step_duration)
        self.seq.process()
        self.assert_led_state(0, OFF)
        self.assert_led_state(1, RED)

    def test_active_steps_should_be_colored_amber(self):
        self.enqueue_step_select(4)
        self.enqueue_note_value_event(10, 45)
        self.process_queued_manta_events()
        self.assert_led_state(4, AMBER)

    def test_active_steps_should_be_colored_amber_after_release(self):
        self.enqueue_step_select(4)
        self.enqueue_note_value_event(10, 45)
        self.enqueue_step_deselect(4)
        self.enqueue_note_value_event(10, 0)
        self.process_queued_manta_events()
        self.assert_led_state(4, AMBER)

    def test_note_leds_should_light_amber_on_sequence_playback(self):
        self.add_sequenced_note(1, 0, 45)
        self.process_queued_manta_events()
        self.step_time(self.seq.step_duration + 0.001)
        self.seq.process()
        self.assertTrue(self.led_states[16] == AMBER or
                self.led_states[6] == AMBER)

    def test_note_leds_go_off_on_sequence_note_off(self):
        self.add_sequenced_note(1, 0, 45)
        self.process_queued_manta_events()
        self.step_time(self.seq.step_duration + 0.001)
        self.seq.process()
        self.step_time(self.seq.step_duration)
        self.seq.process()
        self.assert_led_state(16, OFF)
        self.assert_led_state(6, OFF)

class TestStepping(MockedBoundaryTest):
    def test_next_step_timestamp_should_be_incremented_on_first_process(self):
        self.assertEqual(self.seq.next_step_timestamp, self.logical_time)
        self.seq.process()
        self.assertEqual(self.seq.next_step_timestamp,
                self.logical_time + self.seq.step_duration)

    def test_step_should_send_midi_note_if_velocity_nonzero(self):
        # the first process() call kicks off the first step, so we have to
        # start with the second step
        self.add_sequenced_note(1, 0, 45)
        self.process_queued_manta_events()
        # make sure we're a little behind of the step times to account for
        # possible floating point issues.
        self.step_time(self.seq.step_duration + 0.001)
        self.seq.process()
        self.assert_midi_note_sent(MIDI_BASE_NOTE, 45)

    def test_step_should_schedule_note_off(self):
        self.add_sequenced_note(1, 0, 45)
        self.process_queued_manta_events()
        # make sure we're a little behind of the step times to account for
        # possible floating point issues.
        self.step_time(self.seq.step_duration + 0.001)
        self.seq.process()
        self.step_time(self.seq.step_duration)
        self.seq.process()
        self.assert_midi_note_sent(MIDI_BASE_NOTE, 0)

class TestTempoAdjust(MockedBoundaryTest):
    def test_swiping_full_right_to_left_should_cut_tempo_in_half(self):
        initial_step_duration = self.seq.step_duration
        self.event_queue.append(SliderValueEvent(0, True, 1))
        self.event_queue.append(SliderValueEvent(0, True, 0))
        self.event_queue.append(SliderValueEvent(0, False, 0))
        self.process_queued_manta_events()
        self.assertEqual(self.seq.step_duration, initial_step_duration * 2)

    def test_swiping_full_left_to_right_should_double_tempo(self):
        initial_step_duration = self.seq.step_duration
        self.event_queue.append(SliderValueEvent(0, True, 0))
        self.event_queue.append(SliderValueEvent(0, True, 1))
        self.event_queue.append(SliderValueEvent(0, False, 0))
        self.process_queued_manta_events()
        self.assertEqual(self.seq.step_duration, initial_step_duration / 2)

class TestStartStop(MockedBoundaryTest):
    def test_should_not_execute_steps_if_stopped(self):
        self.event_queue.append(ButtonVelocityEvent(2, 100))
        self.event_queue.append(ButtonVelocityEvent(2, 0))
        self.add_sequenced_note(1, 0, 45)
        self.process_queued_manta_events()
        self.step_time(self.seq.step_duration + 0.001)
        self.seq.process()
        self.assert_no_midi_note_sent()

    def test_restarting_should_only_execute_next_step(self):
        self.add_sequenced_note(1, 0, 100)
        self.add_sequenced_note(2, 1, 100)
        self.process_queued_manta_events()
        self.event_queue.append(ButtonVelocityEvent(2, 100))
        self.event_queue.append(ButtonVelocityEvent(2, 0))
        self.step_time(10 * self.seq.step_duration)
        self.seq.process()
        self.event_queue.append(ButtonVelocityEvent(2, 100))
        self.event_queue.append(ButtonVelocityEvent(2, 0))
        self.seq.process()
        self.seq.process()
        self.assert_midi_note_sent(MIDI_BASE_NOTE, 100)
