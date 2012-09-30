"/Users/srussell/SuperCollider/buffering/Looper.scd".load;
"/Users/srussell/SuperCollider/buffering/PitchShifter.scd".load;

~passThroughInit = {
    SynthDef(
        \passThrough,
        { | inBus, outBus, amplitude=1 |
            Out.ar(outBus, In.ar(inBus) * amplitude);
        }
    ).add;
};


~createPitchShifters = { | inBus, outBus, shifterList, group |
    [-24,-12,-7,0,4,7,12,24].do
        { |shift|
            // TODO: make this less hacky
            if (shift != 0)
                { shifterList.add(~pitchShifterNew.value(inBus, outBus, shift, group)) }
                { shifterList.add(Synth(\passThrough,
                    [inBus: inBus, outBus: outBus], group)) }
        };
};

~createLoopers = { | inBus, outBus, looperList, group |
    8.do { | x | looperList.add(~looperNew.value(inBus, outBus, group)); };
};

~currentLooperChannel = 0;

/*
Takes input from Channel 1 and uses the fader values to set the amplitude
of the bank of pitch shifters. Assumes that the 4th pitch shifter is a
pass-through.
TODO: make the pass-through handling less hacky
*/
~initMIDIControl = { | looperList, looperStates, shifterList |
    MIDIFunc.cc(
        { | val, num, chan, src |
            if ((num >= 81) && (num <= 88))
                {
                    var faderNum = num - 81;
                    if (faderNum != 3)
                        { shifterList[faderNum].setAmplitude(val / 127); }
                        { shifterList[faderNum].set(\amplitude, val / 127) };
                };
        },
        chan: 0
    );

    MIDIFunc.cc(
        { | val, num, chan, source |
            "num: %, val %\n".postf(num, val);
            if ((val == 127) && (num >= 65) && (num <= 72))
                {~currentLooperChannel = num - 65};
            if ((num >= 73) && (num <= 80))
                {};
        },
        chan:0;
    );

    MIDIFunc.cc(
        { | val, num, chan, source |
            if (val == 127)
                {
                    switch(looperStates[~currentLooperChannel])
                        {\stopped}
                        {
                            looperList[~currentLooperChannel].recordLoop;
                            looperStates[~currentLooperChannel] = \recording;
                            "Starting to Record Looper %\n".postf;
                        }
                        {\recording}
                        {
                            looperList[~currentLooperChannel].playLoop;
                            looperStates[~currentLooperChannel] = \playing;
                            "Starting to Play Looper %\n".postf;
                        }
                        {\playing}
                        {
                            looperList[~currentLooperChannel].stopLoop;
                            looperStates[~currentLooperChannel] = \stopped;
                            "Stopping Looper %\n".postf;
                        };
                }
        },
        chan:0, ccNum:93;
    );
};


// HW Inputs -> Looper Input -> Looper -> PitchShifter -> HW Outputs
s.options.hardwareBufferSize = 64;
s.waitForBoot {
    var shifterList = List(8);
    var looperList = List(8);
    var microphoneBus = s.options.numOutputBusChannels;
    var bassBus = microphoneBus + 1;
    var outBus = 0;
    var looperInputBus = Bus.audio;
    var fxBus = Bus.audio;
    var looperStates = \stopped.dup(8);
    var inputGroup = Group.new;
    var looperGroup = Group.after(inputGroup);
    var shifterGroup = Group.after(looperGroup);

    ~looperInit.value;
    ~pitchShifterInit.value;
    ~passThroughInit.value;
    MIDIIn.connectAll;
    s.sync;

    // Create pass-throughs to mix down hardware inputs to the looper input
    Synth(\passThrough, [inBus: microphoneBus, outBus: looperInputBus], inputGroup);
    Synth(\passThrough, [inBus: bassBus, outBus: looperInputBus], inputGroup);

    // Also create passthrough to bypass the loopers, so that we can hear the input,
    // not just the loops. Volume will be controlled in the pitchShift mixer
    Synth(\passThrough, [inBus: looperInputBus, outBus: fxBus], looperGroup);

    ~createPitchShifters.value(fxBus, outBus, shifterList, shifterGroup);
    ~createLoopers.value(looperInputBus, fxBus, looperList, looperGroup);
    ~initMIDIControl.value(looperList, looperStates, shifterList);
    s.queryAllNodes;
};
