import unittest
from stepseq import Seq

class SeqTest(unittest.TestCase):
    def setUp(self):
        self.seq = Seq()

class TestInit(SeqTest):
    def test_there_are_16_steps(self):
        self.assertEqual(len(self.seq.steps), 16)

    def test_steps_have_zero_velocity(self):
        for step in self.seq.steps:
            self.assertEqual(step.velocity, 0)

    # just reassuring myself of basic python
    def test_different_steps_are_not_equal(self):
        self.assertNotEqual(self.seq.steps[0], self.seq.steps[1])

class TestStepSelection(SeqTest):
    def test_select_one_makes_one_selected(self):
        self.seq.select_step(4)
        self.assertEqual(len(self.seq.selected_steps), 1)

    def test_select_one_selects_correct_step(self):
        self.seq.select_step(4)
        self.assertEqual(self.seq.selected_steps[0],
                         self.seq.steps[4])

    def test_selecting_same_step_twice_doesnt_duplicate(self):
        self.seq.select_step(4)
        self.seq.select_step(4)
        self.assertEqual(len(self.seq.selected_steps), 1)

    def test_deselect_removes_step(self):
        self.seq.select_step(4)
        self.seq.deselect_step(4)
        self.assertEqual(len(self.seq.selected_steps), 0)

    def test_deselect_removes_correct_step(self):
        self.seq.select_step(4)
        self.seq.select_step(5)
        self.seq.deselect_step(4)
        self.assertIn(self.seq.steps[5], self.seq.selected_steps)
        self.assertNotIn(self.seq.steps[4], self.seq.selected_steps)

class TestStepValueSetting(SeqTest):
    def test_params_on_single_step_can_be_set(self):
        self.seq.select_step(4)
        self.seq.set_velocity(42)
        self.seq.set_note(43)
        self.seq.set_cc1(44)
        self.seq.set_cc2(45)
        self.seq.set_duration(0.5)
        self.assertEqual(self.seq.steps[4].velocity, 42)
        self.assertEqual(self.seq.steps[4].note, 43)
        self.assertEqual(self.seq.steps[4].cc1, 44)
        self.assertEqual(self.seq.steps[4].cc2, 45)
        self.assertEqual(self.seq.steps[4].duration, 0.5)

    def test_params_on_multiple_steps_can_be_set(self):
        self.seq.select_step(4)
        self.seq.select_step(5)
        self.seq.set_velocity(42)
        self.seq.set_note(43)
        self.seq.set_cc1(44)
        self.seq.set_cc2(45)
        self.seq.set_duration(0.5)
        for i in [4,5]:
            self.assertEqual(self.seq.steps[i].velocity, 42)
            self.assertEqual(self.seq.steps[i].note, 43)
            self.assertEqual(self.seq.steps[i].cc1, 44)
            self.assertEqual(self.seq.steps[i].cc2, 45)
            self.assertEqual(self.seq.steps[i].duration, 0.5)

class TestStepping(unittest.TestCase):
    def setUp(self):
        self.seq = Seq()
        self.seq.register_step_callback(self.step_callback)
        # set the velocity of all steps to 100
        for i in range(16):
            self.seq.select_step(i)
        self.seq.set_velocity(100)
        for i in range(16):
            self.seq.deselect_step(i)
        # now go through and give each a different note
        for i in range(16):
            self.seq.select_step(i)
            self.seq.set_note(60 + i)
            self.seq.deselect_step(i)
        self.step_calls = []

    def step_callback(self, step):
        self.step_calls.append(step)

    def test_each_step_calls_callback(self):
        for i in range(23):
            self.seq.step()
        self.assertEqual(len(self.step_calls), 23)

    def test_each_step_calls_next_step(self):
        for i in range(16):
            self.seq.step()
        for i, step in enumerate(self.step_calls):
            self.assertEqual(step.note, 60 + i)

    def test_steps_wrap(self):
        for i in range(50):
            self.seq.step()
        for i, step in enumerate(self.step_calls):
            self.assertEqual(step.note, 60 + i % 16)
