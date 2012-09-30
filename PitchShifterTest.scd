"/Users/srussell/SuperCollider/buffering/PitchShifter.scd".load;

~pitchShifterInit.value;

~pitch1 = ~pitchShifterNew.value(0, 0, 12);
~pitch1.setShiftSemitones(12);
~pitch1.setAmplitude(0);
~pitch1.setAmplitude(0.5);
~pitch1.setAmplitude(1);
~pitch1.freePitchShifter;
