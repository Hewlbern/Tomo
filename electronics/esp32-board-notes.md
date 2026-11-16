# Tomo by DreamMachina (formerly evoKin V.01) — electronics: ESP32-S3 notes

**Nothing on this page has been purchased, fabricated or brought up.** These are
planning notes for a first prototype and for a later custom board. Prices in
AUD are November 2026 supplier quotes and may have changed. The mechanical CAD
still has a Raspberry Pi Zero–sized tray envelope and Adafruit breakout
pockets from earlier revisions; the current plan is an ESP32-S3.

A condensed source for the custom-board section is a Gemini (Code and analysis
— 4 Argon) design discussion, captured in November 2026.

## What the robot needs

| Function | Role |
|---|---|
| Brain | ESP32-S3 with enough flash and Octal PSRAM for a camera frame buffer plus audio |
| Camera | OV3660 or OV5640 (Seeed now ships these on the XIAO Sense; OV2640 is discontinued), on a long 24-pin 0.5 mm FPC through the hollow neck journal to the 'nose' pod behind a Ø3.5 window. Optional: Tomo works without it |
| Voice in | I2S or PDM MEMS microphone |
| Voice out | I2S amplifier (MAX98357A) into an Adafruit 3923 mini oval speaker (8 Ω 1 W, 30 × 20 × 5 mm, 3 g) on the inside of torso_back; keep the amp gain low |
| Motion | **Two** Feetech FS90 servos, 9 g plastic gear (lighter Tomo; was FS90MG): head pan and head tilt/nod — two PWM channels. The arms are passive (torsion spring per shoulder, opened by hand) and need no electronics |
| Power | USB-C in, 1S 400 mAh LiPo (Core CE04375, 11 g, PCM, 2C), charged by the XIAO's onboard charger, a clean 3.3 V rail that holds up as the pack sags, and a **separate 5 V servo rail** with bulk capacitance |
| Fail-safe | Sense current on the 5 V rail and cut servo power so the head goes limp if a child forces it. The arms are no longer motorised, so there is no grip current and no clasp interlock; the only driven parts are the pan and tilt servos (firmware clamps ±42° pan, ±10° tilt). |

Budget about 700 mA stall per FS90 at 4.8 V (800 mA at 6 V, Feetech) — **≈1.4 A** if both
stall at once — and keep the first bench bring-up on a current-limited supply.
Holding a hug costs no power at all.
The planned portable rail is a **Pololu U3V16F5** 5 V boost (0.4 g, ≈1.6 A typical
input, so roughly 1 A out at 5 V from 3.7 V) on the **400 mAh** cell (2C = 0.8 A,
leads rated 1 A). Neither covers two stalled servos, so the firmware moves one joint
at a time (`ONE_JOINT_AT_A_TIME`) and goes limp between behaviours, and the INA219
trip must sit below ≈0.6 A on the servo rail. Runtime ≈2 h at ≈170 mA average with
Wi-Fi on (ASSUMED), longer with light-sleep.

## Two prototype options (planned, not purchased)

### Option A — about A$93–98 electronics, or about A$114.90–119.40 with the two priced servos, speaker and battery

A project buy, not a single-robot kit: one first-article board plus spare
modules for a later custom PCB.

| Item | Qty | AUD | Supplier (Nov 2026) |
|---|---:|---:|---|
| Seeed XIAO ESP32S3 Sense | 1 | 22.58 | DigiKey Australia |
| ESP32-S3-WROOM-1U-N16R8 | 4 | 10.98 each | DigiKey Australia |
| DigiKey line, free shipping | | 66.50 | |
| MAX98357A breakout (clone) | 1 | 7.95 | AuscomTech |
| INA219 breakout (clone) | 1 | 7.00 | AuscomTech |
| Pololu U3V16F5 5 V boost | 1 | 11.70 | Core Electronics |
| **Subtotal** | | **93.15** | |
| Optional MakerStore TP4056 | 1 | 4.50 | optional |

The XIAO Sense is 21 × 17.5 mm and already has 8 MB PSRAM, a detachable
OV3660/OV5640 camera, a digital MEMS mic and a small battery charger. Unplug the stock
camera if you want to try a longer 24-pin FPC through the printed collar.

Cautions: many bare TP4056 boards have no protection IC — only use a pack that
already has a PCM, or prefer a BQ24074. The U3V16F5 has thermal shutdown and an
input current limit but no short-circuit or reverse protection; put 33 µF on its
input and 470 µF on the 5 V servo header. The Pololu S13V20F5 (about A$29.55) is the
heavier, protected alternative. Clone INMP441 modules
are often fake; the Sense already has a mic, so you may not need one yet.

### Option B — about A$56 electronics, or about A$77.68 with the two priced servos, speaker and battery, plus a PCA9685 (not yet sourced)

| Item | Qty | AUD | Supplier (Nov 2026) |
|---|---:|---:|---|
| DFRobot ESP32-S3 AI Camera DFR1154 (OV3660, PDM mic, MAX98357, 5–12 V VIN, no charger) | 1 | 37.23 | Core Electronics |
| INA219 breakout (clone) | 1 | 7.00 | AuscomTech |
| Pololu U3V16F5 5 V boost | 1 | 11.70 | Core Electronics |
| **Subtotal** | | **55.93** | |
| PCA9685 16-ch I2C servo driver (needed for the 2 servos + INA219 on one bus) | 1 | not yet sourced | — |

There is no charger on this board. Confirm the board outline against the tray
before ordering.

## Servo channels — do the boards have spare PWM GPIOs? (checked Nov 2026)

V.01 (passive hug) needs two servo PWM outputs (head pan, head tilt) plus I2C for the INA219. On the ESP32-S3 any
free GPIO can output servo PWM through the LEDC peripheral, so the question is
only whether pins are free.

**DFRobot DFR1154 — not enough for direct drive. Confirmed from the DFRobot
wiki pin table:** only **GPIO43 and GPIO44** (the Gravity / UART port) are
free. The rest are used by the OV3660 camera (DVP bus), the PDM mic (GPIO38/39),
the MAX98357 amp (GPIO45/46/42), the SD slot (GPIO10–13), the IR LED (GPIO47),
the status LED (GPIO3) and BOOT (GPIO0). GPIO43/44 could drive the two head
servos directly, but then there is no I2C left for the INA219. Plan: run GPIO43/44 as I2C to a **PCA9685** 16-channel servo
driver (also gives spare channels), shared with the INA219. Losing the UART
port means logging over native USB. The PCA9685 is not yet sourced or priced.

**Seeed XIAO ESP32S3 Sense — yes, spare pins confirmed** (Seeed wiki): the
header has 11 GPIOs (D0–D10), all LEDC-PWM capable. The Sense board's camera
and PDM mic (GPIO41/42) use the B2B connector, not the header; its SD card uses
D8–D10. A workable map:

| Use | Pins |
|---|---|
| Servo PWM: head pan, head tilt (D2 now spare) | D0, D1 |
| I2S to MAX98357A (BCLK, LRCLK, DIN) | D3, D6, D7 |
| I2C to INA219 (SDA, SCL) | D4, D5 |
| Spare (or SD card) | D8, D9, D10 |

That is 7 of 11 header pins, leaving D2 and D8–D10 spare if the SD card is unused.
`firmware/evokin_v01/evokin_v01.ino` uses D0 = pan and D1 = tilt.
Pin choice is a plan, not bring-up tested.

### Name-brand alternatives (Core Electronics, Nov 2026)

MAX98357A A$10.65 · INMP441 A$12.30 · BQ24074 breakout A$28.25 · Pololu
S13V20F5 A$29.55 · INA219 A$17.30.

## Custom board target (not designed yet)

Aim for a 65 × 55 mm, 4-layer, single-sided SMT board that sits in the torso
tray. The 65 mm length matches the current tray envelope; **55 mm depth is
larger than the present 30 × 8.5 mm Pi-shaped dummy** and will need a tray
check before the board is laid out.

Suggested block:

```
USB-C 5 V ──► BQ24074 power-path & LiPo charger ◄── 1S LiPo (400–600 mAh, with PCM)
                 │ V_SYS (about 3.5–4.4 V)
     ┌───────────┼────────────────────────────┐
     ▼           ▼                            ▼
 TPS63020     TPS61088 (not MT3608)        MAX98357A
 3.3 V MCU    5.0 V servo rail + 470–1000 µF   ► Adafruit 3923
 & camera        │
                 ▼
           INA219 + TPS259241 eFuse  ► 2× FS90
     ESP32-S3-WROOM-1-N16R8 ── I2S mic (INMP441 / ICS-43434)
                             ── OV3660 / OV5640 on 24-pin FPC
                             ── native USB D+/D− to USB-C
```

Notes worth keeping:

- Use the pre-certified WROOM module (LCSC C2913202 PCB antenna, or C3013946
  U.FL), not a bare ESP32-S3.
- On N16R8 modules, **do not use GPIO 33–37** — they are taken by Octal PSRAM.
- Trip the eFuse when INA219 sees current above a threshold for about 200 ms,
  and also when the head is parked. The “about 450 mA” figure in the design
  discussion is a starting guess only: **measure the real FS90 moving and
  stall current on the bench before you freeze a threshold.**
- When the 5 V rail is cut, the plastic-gear FS90 back-drives easily, which is
  what makes an electronic limp mode possible. That is not a substitute for a
  rated mechanical breakaway.
- Route the camera FPC as a loose vertical U-bend through the hollow journal.
  Do not twist the flat cable around the yaw axis. The tilt servo rides on the
  neck turret, so its 3-wire lead also crosses the pan joint: give it a ≥40 mm
  service loop down the Ø34 collar bore and tie it to the FPC.
- Keep a 15 × 7 mm copper keep-out under a PCB antenna, and keep servo wires,
  the speaker magnet and the battery at least 20 mm away.
- Rough cost from the design discussion: about A$120 at JLCPCB for five 4-layer
  boards and two assembled, plus about A$60 of local parts (camera, mic,
  speaker, servos, battery) per robot. Lighter Tomo uses two FS90s and a 400 mAh pack.

A first bring-up checklist, before anyone spins a board: smoke-test the rails
with peripherals unplugged; enumerate native USB (GPIO19/20); confirm
`esp_psram_get_size()` returns 8 MB; loop I2S audio through PSRAM; stream the
camera over Wi-Fi while moving the head by hand; then sweep the servos and log
INA219 current.

## Fit against the V.01 CAD (electronics pockets unchanged from v4)

- Speaker frame and grille: Adafruit 3923 mini oval on the inside of torso_back (centre x 0, y 38, z 64), 5 × 3 grid of Ø2.2 holes. The 3351 pocket is gone.
- Amp pocket: sized for Adafruit 3006 (19.4 × 17.8 × 3.0 mm + 8 mm headroom).
  Clone boards should be measured.
- Mic pocket: sized for Adafruit 3421 (SPH0645). An INMP441 on a short lead,
  or the onboard mic of the Sense / DFR1154, may not use this pocket.
- Tray envelope: 65 × 8.5 × 30 mm was a Pi Zero with a header. A XIAO Sense
  fits easily. A 65 × 55 mm custom board, or the DFR1154, needs a tray
  overlay before you commit.
- Neck ribbon path: loop bay r = 14 mm, 17 × 2.5 mm slot for a 15 × 1 mm FPC,
  now in the neck_turret deck, then the +x side of the Ø34 yaw bore. Still the
  right idea for an OV3660 / OV5640 ribbon. The loop bay sits close to the tilt
  axis, so ±10° of nod moves the FPC only about ±3 mm.
