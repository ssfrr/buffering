def note_tuple(note, velocity, channel = 0):
    return (0x90 | channel, note, velocity)
