~looperInit = {
    SynthDef(
        \looper,
        { | inBus, outBus, bufNum, t_rec=0, t_play=0, t_stop=0 |
            var out, length=0;
            var isRecording = SetResetFF.kr(t_rec, t_stop);
            var isPlaying = SetResetFF.kr(t_play, t_stop);
            var recPos = Sweep.ar(t_rec, SampleRate.ir() * isRecording);
            var playPos = Phasor.ar(t_play, isPlaying, 0, recPos);

            BufWr.ar(In.ar(inBus), bufNum, recPos);
            out = BufRd.ar(1, bufNum, playPos) * isPlaying;
            Out.ar(outBus, out);
        }
    ).add;
};

~looperNew = { | inBus, outBus, group=1 |
    var loopBuffer = Buffer.alloc(s, s.sampleRate * 30);
    var loopSynth = Synth(\looper,
            [inBus: inBus, outBus: outBus, bufNum: loopBuffer], group);
    (
        loopBuffer: loopBuffer,
        loopSynth: loopSynth,
        recordLoop: { | l |
            l.loopSynth.set(\t_stop, 1);
            l.loopSynth.set(\t_rec, 1);
        },
        playLoop: { | l |
            l.loopSynth.set(\t_stop, 1);
            l.loopSynth.set(\t_play, 1);
        },
        stopLoop: { | l |
            l.loopSynth.set(\t_stop, 1);
        },
        freeLoop: { | l |
            l.loopBuffer.free;
            l.loopSynth.free;
        },
    )
};
