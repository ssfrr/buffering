import liblo, sys


wickihayden = [0,  2,  4,  6,  8,  10, 12, 14,
               7,  9,  11, 13, 15, 17, 19, 21,
               12, 14, 16, 18, 20, 22, 24, 26,
               19, 21, 23, 25, 27, 29, 31, 33,
               24, 26, 28, 30, 32, 34, 36, 38,
               31, 33, 35, 37, 39, 41, 43, 45]

def note_from_pad(pad_number):
    return wickihayden[pad_number] + 30

class Manta(object):
    pad_and_button = 'padandbutton'
    slider = 'slider'
    button = 'button'
    red = 'red'
    amber = 'amber'
    off = 'off'

    def __init__(self, receive_port=8000, send_port=8001, send_address='127.0.0.1'):
        self.osc_server = liblo.Server(receive_port)
        self.osc_target = liblo.Address(send_port)

    def process(self):
        self.osc_server.recv(100)

    def set_pad_value_callback(self, callback, user_data):
        self.osc_server.add_method('/manta/continuous/pad', None, callback, user_data)

    def set_slider_value_callback(self, callback, user_data):
        self.osc_server.add_method('/manta/continuous/slider', None, callback, user_data)

    def set_button_value_callback(self, callback, user_data):
        self.osc_server.add_method('/manta/continuous/button', None, callback, user_data)

    def set_pad_velocity_callback(self, callback, user_data):
        self.osc_server.add_method('/manta/valocity/pad', None, callback, user_data)

    def set_button_velocity_callback(self, callback, user_data):
        self.osc_server.add_method('/manta/velocity/button', None, callback, user_data)

    def send_osc(self, path, *args):
        #liblo.send(self.osc_target, *args)
        liblo.send(self.osc_target, "/foo/message1", 123)

    def set_led_enable(self, led_type, enabled):
        self.send_osc('/manta/ledcontrol', "padandbutton", 1)

    def set_led_pad(self, led_type, state):
        self.send_osc('/manta/led/pad', led_state, led_index)


#"/manta/led/pad/row", "sii", LEDRowHandler, this);
#"/manta/led/pad/column", "sii", LEDColumnHandler, this);
#"/manta/led/pad/frame", "ss", LEDFrameHandler, this);
#"/manta/led/slider", "sii", LEDSliderHandler, this);
#"/manta/led/button", "si", LEDButtonHandler, this);

def main():
    manta = Manta()
    manta.set_led_enable(Manta.pad_and_button, 1)

    count = 10
    led_on = False
    while True:
        manta.process()
        count -= 1
        print count
        if not count:
            set_led_pad(Manta.off if led_on else Manta.red, 10)
            led_on = not led_on
            count = 10

if __name__ == '__main__':
    main()
