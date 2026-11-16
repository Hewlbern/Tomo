# Tomo by DreamMachina (formerly evoKin V.01) — firmware

`evokin_v01/evokin_v01.ino` is a small Arduino sketch for a Seeed XIAO ESP32S3 that drives the two
head servos only (pan on D0, tilt on D1) with the ESP32Servo library. The arms are passive spring
hug arms and have no firmware.

Behaviours: look-around, nod, and a shy turn-away. Send `l`, `n`, `s`, `c` (centre) or `o` (servos
off / limp) over serial at 115200 baud; otherwise it picks one at random every 8–20 s and then
goes limp.

Limits are clamped in software inside the CAD hard stops: pan ±42° (stop ≈ ±47°), tilt ±10°
(+ = nod down; first contact +16.5° / −23.5°). Set `PAN_CENTRE_US`, `TILT_CENTRE_US` and the
direction signs on the bench before the head is fitted.

Untested: nothing has been built or brought up. Bench power only, on a current-limited supply.
