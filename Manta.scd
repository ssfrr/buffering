~wickihayden =
        [0, 2, 4, 6, 8, 10, 12, 14,
        7, 9, 11, 13, 15, 17, 19, 21,
        12, 14, 16, 18, 20, 22, 24, 26,
        19, 21, 23, 25, 27, 29, 31, 33,
        24, 26, 28, 30, 32, 34, 36, 38,
        31, 33, 35, 37, 39, 41, 43, 45];

~registerMantaCallback = { | callback |
    // callback should take a pad number and amplitude as arguments
    "Registering Manta Callback".postln;
    OSCFunc(
        { | msg, time, addr, port |
            var padNum = msg[1] - 1;
            var voiceAmp = msg[3] / 128;
            callback.value(padNum, voiceAmp);
        },
        'manta/value'
    );
};

~freqFromPad = { | padNum |
    (~wickihayden[padNum] + 30).midicps;
};
