# First app-managed replay - 26 September 2026

The user reported "It worked!" after selecting the automatically saved take in
the companion, generating its playback mission and flying it in DCS.

The 39.48-second / 1,975-sample recording was previously saved automatically and
validated. Package d7a5d25a98d04c06acad1d350c7d62df contains an exact copy of that source. The app
created DCSRecorder-Playback-d7a5d25a.miz and activated its matching tape; the
mission accepted the native fingerprint/status handshake.

Native playback began at 10.801 seconds and reached 47.461 seconds: 36.66 seconds
observed, with 1,834 successful motion writes. The first commanded position
matches the selected recording's initial position. The object was destroyed at
mission restart, followed by a new INITIALIZED event. No COMPLETE event exists
for this new take, so full playback completion is not claimed for this run.
The earlier 38.78-second baseline already demonstrated full completion/removal.

This establishes the app-managed record, Stop, automatic save, library selection,
mission generation, activation and playback-start path in the tested local setup.
It does not close the workflow issue: repeated/longer takes, real pause/resume,
frame-rate coverage and the remaining acceptance criteria still require evidence.
All new integration/app source remains local; no new publication is implied.

Raw logs and native traces stay local and ignored. summary.json records exact
source hashes and bounded results.
