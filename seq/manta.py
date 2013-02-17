from OSC import OSCClient, OSCServer, OSCMessage
import sys


wickihayden = [0,  2,  4,  6,  8,  10, 12, 14,
               7,  9,  11, 13, 15, 17, 19, 21,
               12, 14, 16, 18, 20, 22, 24, 26,
               19, 21, 23, 25, 27, 29, 31, 33,
               24, 26, 28, 30, 32, 34, 36, 38,
               31, 33, 35, 37, 39, 41, 43, 45]

def note_from_pad(pad_number):
    return wickihayden[pad_number] + 30

# define constants
PAD_AND_BUTTON = 'padandbutton'
SLIDER = 'slider'
BUTTON = 'button'
RED = 'red'
AMBER = 'amber'
OFF = 'off'

class Manta(object):

    def __init__(self, receive_port=31416, send_port=31417, send_address='127.0.0.1'):
        self.osc_client = OSCClient()
        self.osc_server = OSCServer(('127.0.0.1', receive_port))
        self.osc_client.connect(('127.0.0.1', send_port))
        # set the osc server to time out after 100ms
        self.osc_server.timeout = 0.1

    def process(self):
        self.osc_server.handle_request()

    def set_pad_value_callback(self, callback):
        self.osc_server.addMsgHandler('/manta/continuous/pad', callback)

    def set_slider_value_callback(self, callback):
        self.osc_server.addMsgHandler('/manta/continuous/slider', callback)

    def set_button_value_callback(self, callback):
        self.osc_server.addMsgHandler('/manta/continuous/button', callback)

    def set_pad_velocity_callback(self, callback):
        self.osc_server.addMsgHandler('/manta/valocity/pad', callback)

    def set_button_velocity_callback(self, callback):
        self.osc_server.addMsgHandler('/manta/velocity/button', callback)

    def send_osc(self, path, *args):
        msg = OSCMessage(path)
        msg.append(args)
        self.osc_client.send(msg)

    def set_led_enable(self, led_type, enabled):
        self.send_osc('/manta/ledcontrol', led_type, 1 if enabled else 0)

    def set_led_pad(self, led_state, pad_index):
        self.send_osc('/manta/led/pad', led_state, pad_index)


#"/manta/led/pad/row", "sii", LEDRowHandler, this);
#"/manta/led/pad/column", "sii", LEDColumnHandler, this);
#"/manta/led/pad/frame", "ss", LEDFrameHandler, this);
#"/manta/led/slider", "sii", LEDSliderHandler, this);
#"/manta/led/button", "si", LEDButtonHandler, this);

def main():
    manta = Manta()
    manta.set_led_enable(PAD_AND_BUTTON, 1)
    def print_pad_value(path, tags, args, source):
        print args

    def default_handler(path, tags, args, source):
        print "Default Handler Called"
        print "path: " + path
        print "args: " + str(args)

    count = 10
    led_on = False
    manta.osc_server.addMsgHandler('default', default_handler)
    manta.set_pad_value_callback(print_pad_value)
    print manta.osc_server
    while True:
        manta.process()
        count -= 1
        if not count:
            manta.set_led_pad(OFF if led_on else RED, 10)
            led_on = not led_on
            count = 10

if __name__ == '__main__':
    main()
