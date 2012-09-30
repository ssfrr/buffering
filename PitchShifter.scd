~pitchShifterInit = {
    SynthDef(
        \pitchshifter,
        { | inBus, outBus, shiftSemitones=0, amplitude=1 |
            var ratio = shiftSemitones.midiratio();
            var out = PitchShift.ar(In.ar(inBus), 0.1 / ratio,
                ratio, 0, 0.02, amplitude);
            Out.ar(outBus, out)
        }
    ).add();
};

~pitchShifterNew = { | inBus, outBus, shiftSemitones=0, group=1 |
    var pitchSynth = Synth(\pitchshifter,
        [inBus: inBus, outBus: outBus, shiftSemitones: shiftSemitones], group);
    (
        pitchSynth: pitchSynth,
        setShiftSemitones: { | l, shift |
            l.pitchSynth.set(\shiftSemitones, shift);
        },
        setAmplitude: { | l, amplitude |
            l.pitchSynth.set(\amplitude, amplitude);
        },
        freePitchShifter: { | l | l.pitchSynth.free },
    )
};
