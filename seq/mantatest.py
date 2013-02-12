import liblo, sys

class Manta(object):

    def __init__(self, receive_port=8000, send_port=8001, send_address='127.0.0.1'):
        self.osc_server = liblo.Server(receive_port)
        self.osc_target = liblo.Address(send_port)

    def send_osc(self, path, *args):
        #liblo.send(self.osc_target, *args)
        liblo.send(self.osc_target, "/foo/message1", 123)

def main():
    manta = Manta()
    manta.send_osc('/testing/testing')

if __name__ == '__main__':
    main()
