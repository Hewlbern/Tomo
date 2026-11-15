# Evokin electronics — ESP32-S3 notes

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
| Camera | OV2640 or OV3660, on a 24-pin 0.5 mm FPC through the hollow neck journal |
| Voice in | I2S or PDM MEMS microphone |
| Voice out | I2S amplifier (MAX98357A) into the Adafruit 3351 3 W 4 Ω enclosed speaker already seated in the torso |
| Motion | Two Feetech FS90MG servos: head yaw, and a cord-drum that clasps the arms |
| Power | USB-C in, 1S LiPo, a clean 3.3 V rail that holds up as the pack sags, and a **separate 5 V servo rail** with bulk capacitance |
| Fail-open | Sense current on the 5 V rail and cut servo power so the paws go limp if a child pulls the arms apart. A mechanical weak link in the cord is still a requirement only — it has not been designed or rated. |

Budget about 800 mA stall per FS90MG, conservatively, and keep the first bench
bring-up on a current-limited supply. Portable power is unresolved.

## Two prototype options (planned, not purchased)

### Option A — about A$88–93 electronics, or about A$112–117 with the priced servos and speaker

A project buy, not a single-robot kit: one first-article board plus spare
modules for a later custom PCB.

| Item | Qty | AUD | Supplier (Nov 2026) |
|---|---:|---:|---|
| Seeed XIAO ESP32S3 Sense | 1 | 22.58 | DigiKey Australia |
| ESP32-S3-WROOM-1U-N16R8 | 4 | 10.98 each | DigiKey Australia |
| DigiKey line, free shipping | | 66.50 | |
| MAX98357A breakout (clone) | 1 | 7.95 | AuscomTech |
| INA219 breakout (clone) | 1 | 7.00 | AuscomTech |
| XL6009 boost, set to 5 V | 1 | 6.95 | AuscomTech |
| **Subtotal** | | **88.40** | |
| Optional MakerStore TP4056 | 1 | 4.50 | optional |

The XIAO Sense is 21 × 17.5 mm and already has 8 MB PSRAM, a detachable
OV2640, a digital MEMS mic and a small battery charger. Unplug the stock
camera if you want to try a longer 24-pin FPC through the printed collar.

Cautions: many bare TP4056 boards have no protection IC — only use a pack that
already has a PCM, or prefer a BQ24074. The XL6009 has no input/output
protection; put 470–1000 µF on the 5 V servo header, and prefer a protected
regulator (Pololu S13V20F5, about A$29.55) when you can. Clone INMP441 modules
are often fake; the Sense already has a mic, so you may not need one yet.

### Option B — about A$51 electronics, or about A$75 with the priced servos and speaker

| Item | Qty | AUD | Supplier (Nov 2026) |
|---|---:|---:|---|
| DFRobot ESP32-S3 AI Camera DFR1154 (OV3660, PDM mic, MAX98357, 5–12 V VIN, no charger) | 1 | 37.23 | Core Electronics |
| INA219 breakout (clone) | 1 | 7.00 | AuscomTech |
| XL6009 boost, set to 5 V | 1 | 6.95 | AuscomTech |
| **Subtotal** | | **51.18** | |

This is the cheaper, quicker first-build path **if** the DFR1154 still has two
free GPIOs that can drive the two FS90MG servos at the same time as the
camera, mic and amplifier. Those GPIOs have **not** been verified. Confirm the
pinout and the board outline against the v3 tray before ordering. There is no
charger on this board.

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
USB-C 5 V ──► BQ24074 power-path & LiPo charger ◄── 1S LiPo (2000–3000 mAh, with PCM)
                 │ V_SYS (about 3.5–4.4 V)
     ┌───────────┼────────────────────────────┐
     ▼           ▼                            ▼
 TPS63020     TPS61088 (not MT3608)        MAX98357A
 3.3 V MCU    5.0 V servo rail + 470–1000 µF   ► Adafruit 3351
 & camera        │
                 ▼
           INA219 + TPS259241 eFuse  ► 2× FS90MG
     ESP32-S3-WROOM-1-N16R8 ── I2S mic (INMP441 / ICS-43434)
                             ── OV2640 / OV3660 on 24-pin FPC
                             ── native USB D+/D− to USB-C
```

Notes worth keeping:

- Use the pre-certified WROOM module (LCSC C2913202 PCB antenna, or C3013946
  U.FL), not a bare ESP32-S3.
- On N16R8 modules, **do not use GPIO 33–37** — they are taken by Octal PSRAM.
- Trip the eFuse when INA219 sees current above a threshold for about 200 ms,
  and also after a completed clasp. The “about 450 mA” figure in the design
  discussion is a starting guess only: **measure the real FS90MG moving and
  stall current on the bench before you freeze a threshold.**
- When the 5 V rail is cut, the FS90MG back-drives reasonably easily, which is
  what makes an electronic limp mode possible. That is not a substitute for a
  rated mechanical breakaway.
- Route the camera FPC as a loose vertical U-bend through the hollow journal.
  Do not twist the flat cable around the yaw axis.
- Keep a 15 × 7 mm copper keep-out under a PCB antenna, and keep servo wires,
  the speaker magnet and the battery at least 20 mm away.
- Rough cost from the design discussion: about A$120 at JLCPCB for five 4-layer
  boards and two assembled, plus about A$60 of local parts (camera, mic,
  speaker, two FS90MG, 2000 mAh pack) per robot.

A first bring-up checklist, before anyone spins a board: smoke-test the rails
with peripherals unplugged; enumerate native USB (GPIO19/20); confirm
`esp_psram_get_size()` returns 8 MB; loop I2S audio through PSRAM; stream the
camera over Wi-Fi while moving the head by hand; then sweep the servos and log
INA219 current.

## Fit against the v3 CAD

- Speaker pocket and grille: Adafruit 3351 — keep this part.
- Amp pocket: sized for Adafruit 3006 (19.4 × 17.8 × 3.0 mm + 8 mm headroom).
  Clone boards should be measured.
- Mic pocket: sized for Adafruit 3421 (SPH0645). An INMP441 on a short lead,
  or the onboard mic of the Sense / DFR1154, may not use this pocket.
- Tray envelope: 65 × 8.5 × 30 mm was a Pi Zero with a header. A XIAO Sense
  fits easily. A 65 × 55 mm custom board, or the DFR1154, needs a tray
  overlay before you commit.
- Neck ribbon path: loop bay r = 14 mm, 17 × 2.5 mm slot for a 15 × 1 mm FPC,
  then the +x side of the Ø34 yaw bore. Still the right idea for an OV2640 /
  OV3660 ribbon.
