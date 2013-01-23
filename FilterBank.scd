/*
 * FilterBank creates an processing instrument intended to be used with
 * a Manta and an 8-channel faderbox, such as the Behringer BCF2000.
 *
 * in is the audio bus the filterbank should read from
 * out is the audio bus the result should be written to
 * freq is the base frequency of the filterbank
 * decayTimes is an 8-channel bus
*/
~filterBankInit = {
    SynthDef(
        \filterbank,
        { | in, out, freq, amp, decayTimes |
            var inSig = In.ar(in) * amp;
            // I know, there's an elegant way to build this array. I'll do it later
            var freqs = [freq, freq*2, freq*3, freq*4, freq*5, freq*6, freq*7, freq*8];
            var decays = In.kr(decayTimes, 8);
            var outSig = DynKlank.ar(`[freqs, nil, decays], inSig);
            // the Linen is just to free the synth after the decay. we need to figure out
            // how to make the decay time dynamic
            var env = Linen.kr(amp, 0.001, 1, 10, doneAction:2);
            Out.ar(out, outSig);
        }
    ).add;
};
