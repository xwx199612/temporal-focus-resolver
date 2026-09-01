# v0.4.2b8 executable snapshot

This release is an explicit development-only residual rank characterization on
the `.20 / 640 / .70` candidate profile. It evaluates global deterministic
parallel rank projections while preserving the frozen resolver and production
default `.25 / 640 / .70`. Historical data is in-sample only; production
integration remains disabled.

This release adds the explicit `dev_candidate_recall_020` development profile.
The production reference remains `production_reference_025` (0.25 / 640 / 0.70).
The CLI requires `--profile`; 0.20 is never an implicit runtime default. This
historical 29-frame replay is in-sample characterization only and production
integration remains disabled.

Encoded image bytes are routed through the official live Microsoft OmniParser
icon_detect_v3 boundary and the frozen g6 Temporal Focus resolver. Release
integrity uses CONTENT_MANIFEST.json, RELEASE_SEAL.json, and
RELEASE_SEAL.sha256 without self-reference or circular hashing.

Canonical repository infrastructure release; frozen b1/b2/b3/b4 behavior is
unchanged. b6 separates canonical semantic replay projections from container
hashes and reports IoU>=0.75 only as a parallel diagnostic metric.
