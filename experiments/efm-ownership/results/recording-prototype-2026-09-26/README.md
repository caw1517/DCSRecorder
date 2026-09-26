# Actual-flight capture preparation

The recorder hook and `EFM-Probe-Hornet-record.miz` were installed with DCS
closed on 2026-09-26. `installed-files.json` records installed hashes and verifies
that the prior synthetic roll DLL and mission retain their documented hashes.
No recorded-flight DLL has been installed: a real completed take is needed first.

All seven CTests passed after the new DLL contract check was corrected to
recognize both Hornet target names. The final recorded-path extension was then
checked with the two relevant CTests (`native-checks.txt`). Capture integration
output (`capture-checks.txt`) covers the actual serialized mission and hook,
fake-host takes, malformed recording rejection, conversion, native evaluation
and installed DCS mission validators. Temporary fake-host recordings in that
output were deleted with their test directories and are not user recordings.

Live capture, frame sampling performance and real recorded-flight playback
remain unverified. Follow the [recording protocol](../../../../docs/research/dcs-recorded-flight-prototype.md)
for the first flight and subsequent import/install workflow.
