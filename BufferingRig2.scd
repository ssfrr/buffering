"BCF.scd".load;
"Looper.scd".load;
"Manta.scd".load;
"FilterBank.scd".load;

// HW Inputs -> FilterBank -> HW Outputs
//s.options.hardwareBufferSize = 64;
s.options.device = "JackRouter";
s.waitForBoot {
    var microphoneBus = s.options.numOutputBusChannels;
    var bassBus = microphoneBus + 1;
    var outBus = 0;
    var filterBus = Bus.audio;
    var looperGroup = Group.new;
    var filterGroup = Group.after(looperGroup);
    // we need to allocate each bus separately so we can send them values
    var decayBusses = {Bus.control}.dup(8);
    var filterBanks = nil.dup(48);
    var maxDecayTime = 7;
    var looper;
    var looperState = \stopped;
    var freqRand = 0.5;

    "Booting...".postln;
    ~filterBankInit.value;
    ~looperInit.value;
    SynthDef(
        \passThrough,
        { | inBus, outBus, amplitude=1 |
            Out.ar(outBus, In.ar(inBus) * amplitude);
        }
    ).add;

    MIDIIn.connectAll;
    s.sync;

    looper = ~looperNew.value(microphoneBus, filterBus, looperGroup);
    Synth(\passThrough, [inBus: microphoneBus, outBus: filterBus,
                         group: looperGroup]);
    ~registerPedalCallback.value({ | value |
        if (value == 1)
        {
            switch (looperState)
            {\stopped}
            {
                looperState = \recording;
                looper.recordLoop;
                "recording".postln;
            }
            {\recording}
            {
                looperState = \playing;
                looper.playLoop;
                "playing".postln;
            }
            {\playing}
            {
                looperState = \stopped;
                looper.stopLoop;
                "stopping".postln;
            };
        }
    });

    ~registerMantaPadCallback.value({ | padNum, amp |
        if (filterBanks[padNum] == nil)
        {
            if (amp != 0)
            {
                "creating synth %\n".postf(padNum);
                filterBanks[padNum] = Synth(\filterbank,
                    [in: filterBus,
                        out: outBus,
                        freq: ~freqFromPad.value(padNum),
                        amp: amp.linexp(0,1,0.001,1),
                        decayTimes: decayBusses[0]],
                    filterGroup);
            }
        }
        {
            filterBanks[padNum].set(\amp, amp);
            if (amp == 0)
            {
                "killing synth %\n".postf(padNum);
                filterBanks[padNum] = nil;
            }
        }
    });

    ~registerFaderCallback.value({ | faderNum, value |
        var decayTime = value.linexp(0, 127, 0.05, maxDecayTime);
        decayBusses[faderNum].value = decayTime;
        "setting reson % to %s\n".postf(faderNum, decayTime);
        decayBusses[faderNum].get;
    });

    //OSCFunc.trace(true);
};
