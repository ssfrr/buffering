class Step(object):
    def __init__(self, note=0, velocity=0, cc1=0, cc2=0, duration=0):
        self.note = note
        self.velocity = velocity
        self.cc1 = cc1
        self.cc2 = cc2
        self.duration = duration

class Seq(object):
    def __init__(self):
        self.step_count = 16
        self.steps = [Step() for i in range(self.step_count)]
        # pitches, velocities, etc. can be assigned to multiple steps at once
        self.selected_steps = []
        self.callback = None
        self.current_step_index = 0

    def register_step_callback(self, callback):
        self.callback = callback

    def step(self):
        # catch the case where the step count was changed and
        # we're now past the end of the sequence
        if self.current_step_index >= self.step_count:
            self.current_step_index = 0
        current_step = self.steps[self.current_step_index]
        self.current_step_index += 1
        self.current_step_index %= self.step_count
        return current_step

    def select_step(self, step_index):
        step = self.steps[step_index]
        if step not in self.selected_steps:
            self.selected_steps.append(step)

    def deselect_step(self, step_index):
        self.selected_steps.remove(self.steps[step_index])

    def set_selected_step_property(self, property_name, value):
        for step in self.selected_steps:
            setattr(step, property_name, value)

    # implement methods to set step attributes
    def __getattr__(self, attr):
        if not attr.startswith('set_'):
            raise AttributeError()
        attr = attr[4:]
        # define a function that sets the given value on all selected steps
        def set_step_value(value):
            for step in self.selected_steps:
                setattr(step, attr, value)
        return set_step_value
