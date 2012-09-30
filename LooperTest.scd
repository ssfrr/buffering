"/Users/srussell/SuperCollider/buffering/Looper.scd".load;

s.boot;

~looperInit.value;

~loop1 = ~looperNew.value(0,0);
~loop1.recordLoop;
~loop1.stopLoop;
~loop1.playLoop;

~loop2 = ~looperNew.value(0,0);
~loop2.recordLoop;
~loop2.stopLoop;
~loop2.playLoop;
