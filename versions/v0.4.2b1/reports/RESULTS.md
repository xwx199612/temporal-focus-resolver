# v0.4.2b1 Results

The version-local CLI now executes official `icon_detect_v3` from encoded image bytes. Three historical regression frames passed through live Omni, anonymous normalization, frozen g6, and prediction sealing. Existing raw JSON was not used.

No new data was supplied; the three frames remain historical regression-only. GT was not loaded before sealing.

Decisions are recorded in `decision.json`.
