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
            var inSig = In.ar(in) * amp * 0.2;
            var decays = In.kr(decayTimes, 8);
            var freqRand = 0.05;
            var freqs = {| n | freq * (n+1) * rrand(1-freqRand, 1+freqRand)}.dup(8);
            //var freqs = {| n | freq * (n+1)}.dup(8);
            var outSig = DynKlank.ar(`[freqs, nil, decays], inSig);
            // the Linen is just to free the synth after the decay. we need to figure out
            // how to make the decay time dynamic
            var env = Linen.kr(amp, 0.001, 1, 4, doneAction:2);

            Out.ar(out, outSig);
        }
    ).add;
};
