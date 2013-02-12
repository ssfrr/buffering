import simplecoremidi
from time import sleep

def note_tuple(note, velocity, channel = 0):
    return (0x90 | channel, note, velocity)

def main():
    midi_source = simplecoremidi.MIDISource("MidiTest")
    while True:
        midi_source.send(note_tuple(75, 100))
        sleep(0.03)
        midi_source.send(note_tuple(75, 0))
        sleep(0.03)

if __name__ == '__main__':
    main()
