from OSC import OSCClient, OSCServer, OSCMessage
import sys


wickihayden = [0,  2,  4,  6,  8,  10, 12, 14,
               7,  9,  11, 13, 15, 17, 19, 21,
               12, 14, 16, 18, 20, 22, 24, 26,
               19, 21, 23, 25, 27, 29, 31, 33,
               24, 26, 28, 30, 32, 34, 36, 38,
               31, 33, 35, 37, 39, 41, 43, 45]

wickihayden_rev = dict([(wickihayden[i], i) for i in range(len(wickihayden))])

def note_from_pad(pad_number):
    '''
    Returns a MIDI note number based on the pad index. The first
    pad is set to be C3 (48).
    '''
    return wickihayden[pad_number] + 48

def pad_from_note(note_number):
    '''
    Returns a pad index matching the given note number. Note that
    this isn't uniquely defined, so converting from a pad to a note
    and back is a lossy operation.
    '''
    return wickihayden_rev[note_number - 48]

def row_from_pad(pad_number):
    return int(pad_number / 8)

def column_from_pad(pad_number):
    return pad_number % 8

# define constants
PAD_AND_BUTTON = 'padandbutton'
SLIDER = 'slider'
BUTTON = 'button'
RED = 'red'
AMBER = 'amber'
OFF = 'off'

class PadVelocityEvent(object):
    def __init__(self, pad_num, velocity):
        self.pad_num = pad_num
        self.velocity = velocity

    def __str__(self):
        return "Pad Velocity Event: idx %d, velocity %d" % (
                self.pad_num, self.velocity)

class ButtonVelocityEvent(object):
    def __init__(self, button_num, velocity):
        self.button_num = button_num
        self.velocity = velocity

    def __str__(self):
        return "Button Velocity Event: idx %d, velocity %d" % (
                self.button_num, self.velocity)

class PadValueEvent(object):
    def __init__(self, pad_num, value):
        self.pad_num = pad_num
        self.value = value

    def __str__(self):
        return "Pad Value Event: idx %d, value %d" % (self.pad_num, self.value)

class SliderValueEvent(object):
    '''A touch, release, or movement on one of the two sliders.
    If touched is false then the value is invalid'''
    def __init__(self, slider_num, touched, value):
        self.touched = touched
        self.slider_num = slider_num
        self.value = value

    def __str__(self):
        return "Slider Value Event: idx %d, %s, value %d" % (
                self.slider_num,
                'touched' if self.touched else 'not touched',
                self.value)

class Manta(object):

    def __init__(self, receive_port=31416, send_port=31417, send_address='127.0.0.1'):
        self.osc_client = OSCClient()
        self.osc_server = OSCServer(('127.0.0.1', receive_port))
        self.osc_client.connect(('127.0.0.1', send_port))
        # set the osc server to time out after 1ms
        self.osc_server.timeout = 0.001
        self.event_queue = []
        self.osc_server.addMsgHandler('/manta/continuous/pad',
                self._pad_value_callback)
        self.osc_server.addMsgHandler('/manta/continuous/slider',
                self._slider_value_callback)
        self.osc_server.addMsgHandler('/manta/continuous/button',
                self._button_value_callback)
        self.osc_server.addMsgHandler('/manta/velocity/pad',
                self._pad_velocity_callback)
        self.osc_server.addMsgHandler('/manta/velocity/button',
                self._button_velocity_callback)

    def process(self):
        self.osc_server.handle_request()
        ret_list = self.event_queue
        self.event_queue = []
        return ret_list

    def _pad_value_callback(self, path, tags, args, source):
        self.event_queue.append(PadValueEvent(args[0], args[1]))

    def _slider_value_callback(self, path, tags, args, source):
        touched = False if args[1] == 0xffff else True
        scaled_value = args[1] / 4096.0
        self.event_queue.append(SliderValueEvent(args[0], touched, scaled_value))

    def _button_value_callback(self, path, tags, args, source):
        pass

    def _pad_velocity_callback(self, path, tags, args, source):
        self.event_queue.append(PadVelocityEvent(args[0], args[1]))

    def _button_velocity_callback(self, path, tags, args, source):
        self.event_queue.append(ButtonVelocityEvent(args[0], args[1]))

    def _send_osc(self, path, *args):
        msg = OSCMessage(path)
        msg.append(args)
        self.osc_client.send(msg)

    def set_led_enable(self, led_type, enabled):
        self._send_osc('/manta/ledcontrol', led_type, 1 if enabled else 0)

    def set_led_pad(self, led_state, pad_index):
        self._send_osc('/manta/led/pad', led_state, pad_index)


#"/manta/led/pad/row", "sii", LEDRowHandler, this);
#"/manta/led/pad/column", "sii", LEDColumnHandler, this);
#"/manta/led/pad/frame", "ss", LEDFrameHandler, this);
#"/manta/led/slider", "sii", LEDSliderHandler, this);
#"/manta/led/button", "si", LEDButtonHandler, this);

def main():
    manta = Manta()
    manta.set_led_enable(PAD_AND_BUTTON, 1)

    count = 10
    led_on = False
    while True:
        events = manta.process()
        for event in events:
            print event
        count -= 1
        if not count:
            manta.set_led_pad(OFF if led_on else RED, 10)
            led_on = not led_on
            count = 1000

if __name__ == '__main__':
    main()
