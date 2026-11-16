// SPDX-License-Identifier: MIT
// Tomo by DreamMachina (formerly evoKin V.01) — head motion sketch, passive-hug build.
//
// The arms are passive: a torsion spring in each shoulder holds the hug with zero power and you open
// them by hand. There is no clasp logic, no grip current and no arm interlock any more.
// This sketch only drives the head: pan (FS90MG in the yaw collar) and tilt/nod (FS90MG on the
// neck turret), with three simple behaviours: look-around, nod and a shy turn-away.
//
// Untested planning code — nothing has been built or brought up. Bench power only, on a
// current-limited 5 V supply, servos unplugged from the head until the centre trim is set.
//
// Board: Seeed XIAO ESP32S3 (Sense). Library: ESP32Servo (Kevin Harrington / madhephaestus).
// Pins: D0 = pan, D1 = tilt (see electronics/esp32-board-notes.md).
// Serial (115200): 'l' look-around, 'n' nod, 's' shy, 'c' centre, 'o' servos off.

#include <ESP32Servo.h>

// ---------- pins and limits ----------
static const int PIN_PAN  = D0;
static const int PIN_TILT = D1;

// CAD: pan hard stop ≈ ±47°, so the software clamp stays inside it.
static const float PAN_MIN  = -42.0f, PAN_MAX  = 42.0f;
// CAD: first rigid contact at +16.5° nose down / −23.5° looking up; clamp ±10°.
static const float TILT_MIN = -10.0f, TILT_MAX = 10.0f;   // + = nod down

// Servo centre trims (µs) and direction. Set these on the bench before fitting the head.
static const int   PAN_CENTRE_US  = 1500, TILT_CENTRE_US = 1500;
static const float US_PER_DEG     = 1000.0f / 90.0f;     // FS90MG: ~500–2500 µs over ~180°
static const int   PAN_DIR = +1, TILT_DIR = +1;           // flip if a joint runs backwards

// Motion smoothing: max speed (deg/s) per joint.
static const float PAN_SPEED  = 90.0f;
static const float TILT_SPEED = 60.0f;

Servo pan, tilt;
float panNow = 0, tiltNow = 0;
bool attached = false;

static float clampf(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }

static void writeRaw(float panDeg, float tiltDeg) {
  panDeg  = clampf(panDeg,  PAN_MIN,  PAN_MAX);
  tiltDeg = clampf(tiltDeg, TILT_MIN, TILT_MAX);
  pan.writeMicroseconds(PAN_CENTRE_US  + (int)(PAN_DIR  * panDeg  * US_PER_DEG));
  tilt.writeMicroseconds(TILT_CENTRE_US + (int)(TILT_DIR * tiltDeg * US_PER_DEG));
  panNow = panDeg; tiltNow = tiltDeg;
}

static void attachServos() {
  if (attached) return;
  pan.setPeriodHertz(50);  tilt.setPeriodHertz(50);
  pan.attach(PIN_PAN, 500, 2500);
  tilt.attach(PIN_TILT, 500, 2500);
  attached = true;
  writeRaw(panNow, tiltNow);
}

static void detachServos() {   // limp head: lets a child push it without fighting the servo
  if (!attached) return;
  pan.detach(); tilt.detach();
  attached = false;
}

// Move both joints together with an ease-in/ease-out, respecting the speed limits.
static void moveTo(float panDeg, float tiltDeg, float speedScale = 1.0f) {
  attachServos();
  panDeg  = clampf(panDeg,  PAN_MIN,  PAN_MAX);
  tiltDeg = clampf(tiltDeg, TILT_MIN, TILT_MAX);
  float p0 = panNow, t0 = tiltNow;
  float tp = fabsf(panDeg - p0) / (PAN_SPEED * speedScale);
  float tt = fabsf(tiltDeg - t0) / (TILT_SPEED * speedScale);
  float dur = max(max(tp, tt), 0.05f) * 1.5f;              // eased profile peaks at 1.5x mean speed
  uint32_t start = millis(), ms = (uint32_t)(dur * 1000.0f);
  while (true) {
    float u = (millis() - start) / (float)ms;
    if (u >= 1.0f) break;
    float e = 0.5f - 0.5f * cosf(u * PI);                   // cosine ease
    writeRaw(p0 + (panDeg - p0) * e, t0 + (tiltDeg - t0) * e);
    delay(15);
  }
  writeRaw(panDeg, tiltDeg);
}

static void hold(uint32_t ms) { delay(ms); }

// ---------- behaviours ----------
// Look-around: a slow curious scan, a little head-up at each side, back to centre.
void lookAround() {
  moveTo(-35, -4, 0.6f);  hold(500);
  moveTo(-15,  2, 0.8f);  hold(200);
  moveTo( 35, -6, 0.6f);  hold(600);
  moveTo( 20,  0, 0.8f);  hold(250);
  moveTo(  0, -3, 0.7f);  hold(300);
  moveTo(  0,  0, 0.7f);
}

// Nod: two small "yes" nods (+ = nose down), then settle.
void nod() {
  float p = panNow;
  for (int i = 0; i < 2; i++) {
    moveTo(p,  9, 1.0f);
    moveTo(p, -3, 1.0f);
  }
  moveTo(p, 0, 0.8f);
}

// Shy turn-away: glance down, turn away quickly, hold, then peek back slowly.
void shy() {
  int side = (random(2) == 0) ? -1 : 1;
  moveTo(panNow, 8, 1.2f);                     // look down
  moveTo(side * 40, 10, 1.4f);                 // turn away, head down
  hold(1200);
  moveTo(side * 28, 6, 0.4f);                  // slow peek back
  hold(600);
  moveTo(side * 38, 9, 1.0f);                  // ...and away again
  hold(800);
  moveTo(0, 0, 0.5f);                          // shyly come back to centre
}

void centre() { moveTo(0, 0, 0.6f); }

void setup() {
  Serial.begin(115200);
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  randomSeed(esp_random());
  attachServos();
  writeRaw(0, 0);
  delay(500);
  Serial.println("Tomo (evoKin V.01) head: l=look-around n=nod s=shy c=centre o=off");
}

uint32_t nextIdle = 8000;

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    switch (c) {
      case 'l': lookAround(); break;
      case 'n': nod(); break;
      case 's': shy(); break;
      case 'c': centre(); break;
      case 'o': detachServos(); Serial.println("servos off (limp)"); break;
      default: break;
    }
    nextIdle = millis() + 8000;
  }
  // Idle life: every 8–20 s pick a behaviour, then go limp to save power and heat.
  if (millis() > nextIdle) {
    int r = random(10);
    if (r < 6) lookAround(); else if (r < 9) nod(); else shy();
    delay(300);
    detachServos();
    nextIdle = millis() + 8000 + random(12000);
  }
}
