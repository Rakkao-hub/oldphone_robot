/*
  ==========================================================================
   Robot AI : ESP8266 (NodeMCU) + L298N + มอเตอร์ TT 2 ตัว + ถ่าน 18650 x2
  ==========================================================================
   บอร์ดรู้แค่ "คำสั่งพื้นฐาน" 5 แบบ
     F<ซม.>          เดินหน้า            เช่น F30
     B<ซม.>          ถอยหลัง            เช่น B10
     L<องศา>         หมุนซ้ายอยู่กับที่     เช่น L90
     R<องศา>         หมุนขวาอยู่กับที่     เช่น R45
     W<มิลลิวินาที>    หยุดรอ             เช่น W500

   ส่วนที่ "คิด" อยู่ในหน้าเว็บที่บอร์ดเสิร์ฟ (เปิดด้วยมือถือหรือคอม)
     พิมพ์ "วิ่งเป็นรูปหัวใจ" -> หน้าเว็บถาม Claude -> ได้แผนเป็นเส้นตรง+เส้นโค้ง
     -> หน้าเว็บแตกเป็นคำสั่งพื้นฐาน + จำลองรูปให้ดูก่อน -> ส่งมาที่ POST /api/run

   ทดสอบจากแถบที่อยู่เบราว์เซอร์ได้เลย เช่น
     http://robot.local/api/run?p=F20 L90 F20     สั่งวิ่ง
     http://robot.local/api/stop                  หยุด
     http://robot.local/api/config?msPerCm=25     ปรับค่า

   ต่อ WiFi บ้านไม่ได้ -> บอร์ดเปิด WiFi "Robot-AI" ให้ต่อแล้วเปิด http://192.168.4.1
     หน้าเว็บจะบอกสาเหตุ (ไม่พบชื่อ / รหัสผิด / สัญญาณอ่อน) และมีปุ่มลองต่อใหม่
     ถ้าไม่มีใครต่อ Robot-AI อยู่ บอร์ดจะลองต่อ WiFi บ้านใหม่เองทุกประมาณ 2 นาที

   ไลบรารี : ใช้ของที่มากับ ESP8266 core ทั้งหมด ไม่ต้องติดตั้งเพิ่ม
   บอร์ด   : NodeMCU 1.0 (ESP-12E Module)
   ไฟล์    : robot_ai.ino + index_html.h ต้องอยู่ในโฟลเดอร์ชื่อ robot_ai ด้วยกัน
  ==========================================================================
*/

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266mDNS.h>
#include <EEPROM.h>
#include "index_html.h"

// ============ 1) WiFi : ชื่อและรหัสอยู่ในไฟล์ secrets.h (ไม่อัปขึ้น GitHub) ============
// ครั้งแรก: คัดลอก secrets.example.h เป็น secrets.h แล้วใส่ชื่อ/รหัสจริง
#if __has_include("secrets.h")
#include "secrets.h"
#else
#error "ยังไม่มี secrets.h : คัดลอก secrets.example.h เป็น secrets.h แล้วใส่ชื่อ/รหัส WiFi จริง"
#endif

const uint16_t BRAIN_PORT = 8080;   // brain.py ในมือถือ
const char* HOSTNAME = "robot";     // เปิดเว็บผ่าน http://robot.local ได้ (iPhone / Mac)
const char* AP_SSID  = "Robot-AI";  // ถ้าต่อ WiFi ไม่ติด บอร์ดจะปล่อย WiFi ชื่อนี้ให้บังคับเองได้
                                    // (โหมดนี้ไม่มีอินเทอร์เน็ต จึงใช้ AI ไม่ได้)

// ============ 2) ขาที่ต่อกับ L298N (เลข GPIO / ชื่อที่พิมพ์บนบอร์ด) ============
// ** ถอดจัมเปอร์ที่ขา ENA และ ENB ของ L298N ออกก่อนต่อสาย **
const uint8_t PIN_ENA = 5;    // D1  แรงล้อซ้าย (PWM)
const uint8_t PIN_IN1 = 4;    // D2
const uint8_t PIN_IN2 = 14;   // D5
const uint8_t PIN_IN3 = 12;   // D6
const uint8_t PIN_IN4 = 13;   // D7
const uint8_t PIN_ENB = 15;   // D8  แรงล้อขวา (PWM)
const uint8_t PIN_LED = 2;    // D4  ไฟ LED บนบอร์ด ติด = กำลังวิ่ง

// ============ 3) ค่าคงที่อื่น ๆ ============
const int      PWM_MAX        = 1023;
const int      PWM_FREQ       = 1000;  // Hz
const uint32_t KICK_MS        = 30;    // ช่วงออกตัวจ่ายไฟเต็ม ให้ท่าสั้น ๆ ขยับได้จริง
const uint32_t MANUAL_TIMEOUT = 600;   // บังคับเองแล้วสัญญาณขาด รถจะหยุดเองภายในเวลานี้ (ms)
const int      MAX_CMDS       = 300;

// ------------------------------------------------------------------------
// ค่าปรับเทียบ (เก็บใน EEPROM ปรับได้จากหน้าเว็บ ไม่ต้องอัปโหลดโค้ดใหม่)
// ------------------------------------------------------------------------
struct Config {
  uint32_t magic;
  uint16_t driveSpeed;  // แรงตอนเดินหน้า/ถอย 0-1023
  uint16_t turnSpeed;   // แรงตอนหมุน 0-1023
  float    msPerCm;     // วิ่ง 1 ซม. ใช้กี่มิลลิวินาที
  float    msPerDeg;    // หมุน 1 องศา ใช้กี่มิลลิวินาที
  int16_t  trim;        // + ลดแรงล้อซ้าย, - ลดแรงล้อขวา (เปอร์เซ็นต์) ใช้แก้รถวิ่งเบี้ยว
  uint16_t pauseMs;     // หยุดนิ่งระหว่างแต่ละท่า
  uint8_t  invL;        // กลับทิศล้อซ้าย
  uint8_t  invR;        // กลับทิศล้อขวา
  uint8_t  swapLR;      // สลับล้อซ้าย/ขวา
};
const uint32_t CFG_MAGIC = 0x524F4231UL;  // "ROB1"
Config cfg;

void setDefaults() {
  cfg.magic      = CFG_MAGIC;
  cfg.driveSpeed = 650;
  cfg.turnSpeed  = 620;
  cfg.msPerCm    = 22.0f;
  cfg.msPerDeg   = 4.0f;
  cfg.trim       = 0;
  cfg.pauseMs    = 150;
  cfg.invL       = 0;
  cfg.invR       = 0;
  cfg.swapLR     = 0;
}

void saveConfig() {
  EEPROM.put(0, cfg);
  EEPROM.commit();
}

void loadConfig() {
  EEPROM.begin(64);
  EEPROM.get(0, cfg);
  bool ok = cfg.magic == CFG_MAGIC &&
            cfg.msPerCm > 0.5f && cfg.msPerCm < 1000.0f &&
            cfg.msPerDeg > 0.1f && cfg.msPerDeg < 1000.0f &&
            cfg.driveSpeed <= PWM_MAX && cfg.turnSpeed <= PWM_MAX;
  if (!ok) {
    setDefaults();
    saveConfig();
  }
}

long clampL(long v, long lo, long hi) { return v < lo ? lo : (v > hi ? hi : v); }
float clampF(float v, float lo, float hi) {
  if (!(v >= lo)) return lo;  // จับ NaN ด้วย
  return v > hi ? hi : v;
}

// ------------------------------------------------------------------------
// มอเตอร์
// ------------------------------------------------------------------------
// dir: +1 เดินหน้า, -1 ถอยหลัง, 0 ปล่อยฟรี
void motorChannel(uint8_t en, uint8_t inA, uint8_t inB, int dir, int pwm) {
  if (dir == 0 || pwm <= 0) {
    digitalWrite(inA, LOW);
    digitalWrite(inB, LOW);
    analogWrite(en, 0);
    return;
  }
  digitalWrite(inA, dir > 0 ? HIGH : LOW);
  digitalWrite(inB, dir > 0 ? LOW : HIGH);
  analogWrite(en, clampL(pwm, 0, PWM_MAX));
}

int lastL = 99, lastR = 99, lastPwm = -1;  // กันสั่ง PWM ค่าเดิมซ้ำ ๆ

void setWheels(int dirL, int dirR, int pwm) {
  if (dirL == lastL && dirR == lastR && pwm == lastPwm) return;
  lastL = dirL;
  lastR = dirR;
  lastPwm = pwm;

  int pwmL = pwm, pwmR = pwm;
  if (cfg.trim > 0) pwmL = pwm * (100 - cfg.trim) / 100;
  if (cfg.trim < 0) pwmR = pwm * (100 + cfg.trim) / 100;
  if (cfg.invL) dirL = -dirL;
  if (cfg.invR) dirR = -dirR;

  if (!cfg.swapLR) {
    motorChannel(PIN_ENA, PIN_IN1, PIN_IN2, dirL, pwmL);
    motorChannel(PIN_ENB, PIN_IN3, PIN_IN4, dirR, pwmR);
  } else {
    motorChannel(PIN_ENA, PIN_IN1, PIN_IN2, dirR, pwmR);
    motorChannel(PIN_ENB, PIN_IN3, PIN_IN4, dirL, pwmL);
  }
}

// เบรก: ขั้วมอเตอร์ทั้งสองลงกราวด์ผ่าน L298N รถหยุดทันที ไม่ไถล
void brakeMotors() {
  lastL = lastR = 99;
  lastPwm = -1;
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, LOW);
  analogWrite(PIN_ENA, PWM_MAX);
  analogWrite(PIN_ENB, PWM_MAX);
}

// ปล่อยฟรี: ตัดไฟมอเตอร์ เข็นรถด้วยมือได้
void coastMotors() {
  lastL = lastR = 99;
  lastPwm = -1;
  digitalWrite(PIN_IN1, LOW);
  digitalWrite(PIN_IN2, LOW);
  digitalWrite(PIN_IN3, LOW);
  digitalWrite(PIN_IN4, LOW);
  analogWrite(PIN_ENA, 0);
  analogWrite(PIN_ENB, 0);
}

// ------------------------------------------------------------------------
// ตัวรันโปรแกรม (ไม่ใช้ delay เว็บจึงตอบได้ตลอดเวลาที่รถวิ่ง)
// ------------------------------------------------------------------------
struct Cmd {
  char  op;
  float val;
};
Cmd prog[MAX_CMDS];
int progLen = 0;
int progIdx = -1;

enum Phase : uint8_t { PH_IDLE, PH_MOVE, PH_PAUSE };
Phase    phase      = PH_IDLE;
uint32_t phaseStart = 0;
uint32_t phaseDur   = 0;
int      curL = 0, curR = 0, curPwm = 0;
bool     kicking    = false;

bool     manualOn   = false;
uint32_t manualLast = 0;
uint32_t coastAt    = 0;   // เวลาที่จะปล่อยเบรกหลังหยุด
uint32_t runId      = 0;   // นับรอบการวิ่ง หน้าเว็บใช้แยกว่าเป็นรอบของใคร
bool     apMode     = false;
int      wifiErr    = 0;   // สถานะตอนต่อ WiFi บ้านไม่สำเร็จ (1 ไม่พบชื่อ, 6 รหัสผิด, อื่น ๆ หมดเวลา)
int      wifiSeen   = 0;   // สัญญาณ WiFi บ้านที่สแกนเจอ (dBm) 0 = สแกนไม่เจอ

void beginCmd(int i) {
  const Cmd& c = prog[i];
  float ms = 0;
  curL = curR = 0;
  curPwm = 0;
  switch (c.op) {
    case 'F': curL = 1;  curR = 1;  curPwm = cfg.driveSpeed; ms = c.val * cfg.msPerCm;  break;
    case 'B': curL = -1; curR = -1; curPwm = cfg.driveSpeed; ms = c.val * cfg.msPerCm;  break;
    case 'L': curL = -1; curR = 1;  curPwm = cfg.turnSpeed;  ms = c.val * cfg.msPerDeg; break;
    case 'R': curL = 1;  curR = -1; curPwm = cfg.turnSpeed;  ms = c.val * cfg.msPerDeg; break;
    default:  ms = c.val; break;  // 'W'
  }
  progIdx    = i;
  phase      = PH_MOVE;
  phaseStart = millis();
  phaseDur   = (uint32_t)(ms + 0.5f);
  coastAt    = 0;
  if (curPwm > 0) {
    kicking = KICK_MS > 0;
    setWheels(curL, curR, kicking ? PWM_MAX : curPwm);
  } else {
    kicking = false;
    brakeMotors();
  }
}

void finishProgram() {
  brakeMotors();
  coastAt = millis() + 300;
  phase   = PH_IDLE;
  progIdx = progLen;  // บอกหน้าเว็บว่าวิ่งครบแล้ว
}

void updateProgram() {
  if (phase == PH_IDLE) return;
  uint32_t el = millis() - phaseStart;
  if (phase == PH_MOVE) {
    if (kicking && el >= KICK_MS) {
      kicking = false;
      setWheels(curL, curR, curPwm);
    }
    if (el >= phaseDur) {
      brakeMotors();
      phase      = PH_PAUSE;
      phaseStart = millis();
      phaseDur   = cfg.pauseMs;
    }
  } else if (el >= phaseDur) {  // พักจบแล้ว ไปท่าถัดไป
    if (progIdx + 1 < progLen) beginCmd(progIdx + 1);
    else finishProgram();
  }
}

void stopAll() {
  phase    = PH_IDLE;
  manualOn = false;
  progLen  = 0;
  progIdx  = -1;
  brakeMotors();
  coastAt = millis() + 300;
}

char flipOp(char op) {
  switch (op) {
    case 'F': return 'B';
    case 'B': return 'F';
    case 'L': return 'R';
    case 'R': return 'L';
  }
  return op;
}

// แปลงข้อความ "L45 F30.5 R90 ..." เป็นคำสั่งใน prog[]  คืนค่าจำนวนคำสั่ง
int parseProgram(const char* p) {
  int n = 0;
  while (*p && n < MAX_CMDS) {
    char op = toupper((unsigned char)*p);
    if (op == 'F' || op == 'B' || op == 'L' || op == 'R' || op == 'W') {
      char* end;
      double v = strtod(p + 1, &end);
      if (end == p + 1) {  // เป็นตัวอักษรเฉย ๆ ไม่มีตัวเลขตามหลัง
        p++;
        continue;
      }
      if (v < 0) {
        v  = -v;
        op = flipOp(op);
      }
      double lim = (op == 'F' || op == 'B') ? 500.0 : (op == 'W' ? 30000.0 : 3600.0);
      if (v > lim) v = lim;
      if (v > 0) {  // NaN ไม่ผ่านเงื่อนไขนี้
        prog[n].op  = op;
        prog[n].val = (float)v;
        n++;
      }
      p = end;
    } else {
      p++;
    }
  }
  return n;
}

// ------------------------------------------------------------------------
// เว็บเซิร์ฟเวอร์
// ------------------------------------------------------------------------
ESP8266WebServer server(80);

void sendJson(const String& body, int code = 200) {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Cache-Control", "no-store");
  server.send(code, "application/json", body);
}

String configJson() {
  String j;
  j.reserve(220);
  j += F("{\"driveSpeed\":"); j += (int)cfg.driveSpeed;
  j += F(",\"turnSpeed\":");  j += (int)cfg.turnSpeed;
  j += F(",\"msPerCm\":");    j += String(cfg.msPerCm, 3);
  j += F(",\"msPerDeg\":");   j += String(cfg.msPerDeg, 3);
  j += F(",\"trim\":");       j += (int)cfg.trim;
  j += F(",\"pauseMs\":");    j += (int)cfg.pauseMs;
  j += F(",\"invL\":");       j += (int)cfg.invL;
  j += F(",\"invR\":");       j += (int)cfg.invR;
  j += F(",\"swapLR\":");     j += (int)cfg.swapLR;
  j += '}';
  return j;
}

void handleRoot() {
  server.sendHeader("Cache-Control", "no-cache");
  server.send_P(200, PSTR("text/html; charset=utf-8"), INDEX_HTML);
}

void handleStatus() {
  String j;
  j.reserve(500);
  j += F("{\"running\":"); j += (phase != PH_IDLE) ? F("true") : F("false");
  j += F(",\"manual\":");  j += manualOn ? F("true") : F("false");
  j += F(",\"idx\":");     j += progIdx;
  j += F(",\"total\":");   j += progLen;
  j += F(",\"run\":");     j += (unsigned long)runId;
  j += F(",\"rssi\":");    j += (int)WiFi.RSSI();
  j += F(",\"ap\":");      j += apMode ? F("true") : F("false");
  j += F(",\"ip\":\"");    j += (apMode ? WiFi.softAPIP() : WiFi.localIP()).toString();
  j += F("\",\"host\":\""); j += HOSTNAME;
  j += F("\",\"ssid\":\""); j += WIFI_SSID;
  j += F("\",\"wifiErr\":"); j += wifiErr;
  j += F(",\"wifiSeen\":");  j += wifiSeen;
  j += F(",\"config\":");    j += configJson();
  j += '}';
  sendJson(j);
}

void handleRun() {
  String body = server.arg("plain");
  if (body.length() == 0) body = server.arg("p");  // เผื่อสั่งทดสอบแบบ /api/run?p=F20L90
  int n = parseProgram(body.c_str());
  if (n == 0) {
    sendJson(F("{\"ok\":false,\"error\":\"no commands\"}"), 400);
    return;
  }
  manualOn = false;
  progLen  = n;
  runId++;
  beginCmd(0);
  String j = F("{\"ok\":true,\"count\":");
  j += n;
  j += F(",\"run\":");
  j += (unsigned long)runId;
  j += '}';
  sendJson(j);
}

void handleDrive() {
  String d = server.arg("d");
  int l = 0, r = 0, pwm = cfg.driveSpeed;
  if (d == "F")      { l = 1;  r = 1; }
  else if (d == "B") { l = -1; r = -1; }
  else if (d == "L") { l = -1; r = 1;  pwm = cfg.turnSpeed; }
  else if (d == "R") { l = 1;  r = -1; pwm = cfg.turnSpeed; }
  if (server.hasArg("s")) pwm = clampL(server.arg("s").toInt(), 0, PWM_MAX);

  if (l == 0) {
    stopAll();
    sendJson(F("{\"ok\":true}"));
    return;
  }
  if (phase != PH_IDLE) {  // บังคับเองแทรกโปรแกรมที่กำลังวิ่ง
    phase   = PH_IDLE;
    progLen = 0;
    progIdx = -1;
  }
  coastAt = 0;
  setWheels(l, r, pwm);
  manualOn   = true;
  manualLast = millis();
  sendJson(F("{\"ok\":true}"));
}

void handleRestart() {  // ปุ่ม "ลองต่อ WiFi บ้านอีกครั้ง" บนหน้าเว็บ
  stopAll();
  sendJson(F("{\"ok\":true}"));
  delay(300);
  ESP.restart();
}

void handleStop() {
  stopAll();
  sendJson(F("{\"ok\":true}"));
}

void handleConfig() {
  bool changed = false;
  if (server.hasArg("reset"))      { setDefaults(); changed = true; }
  if (server.hasArg("driveSpeed")) { cfg.driveSpeed = clampL(server.arg("driveSpeed").toInt(), 0, PWM_MAX); changed = true; }
  if (server.hasArg("turnSpeed"))  { cfg.turnSpeed  = clampL(server.arg("turnSpeed").toInt(), 0, PWM_MAX);  changed = true; }
  if (server.hasArg("msPerCm"))    { cfg.msPerCm    = clampF(server.arg("msPerCm").toFloat(), 1.0f, 500.0f); changed = true; }
  if (server.hasArg("msPerDeg"))   { cfg.msPerDeg   = clampF(server.arg("msPerDeg").toFloat(), 0.2f, 200.0f); changed = true; }
  if (server.hasArg("trim"))       { cfg.trim       = clampL(server.arg("trim").toInt(), -40, 40);          changed = true; }
  if (server.hasArg("pauseMs"))    { cfg.pauseMs    = clampL(server.arg("pauseMs").toInt(), 0, 3000);       changed = true; }
  if (server.hasArg("invL"))       { cfg.invL   = server.arg("invL").toInt() ? 1 : 0;   changed = true; }
  if (server.hasArg("invR"))       { cfg.invR   = server.arg("invR").toInt() ? 1 : 0;   changed = true; }
  if (server.hasArg("swapLR"))     { cfg.swapLR = server.arg("swapLR").toInt() ? 1 : 0; changed = true; }
  if (changed) {
    saveConfig();
    lastPwm = -1;  // ให้ค่าใหม่มีผลทันทีกับคำสั่งถัดไป
  }
  sendJson(configJson());
}

void handleNotFound() {
  server.send(404, "text/plain", "not found");
}

// ------------------------------------------------------------------------
// WiFi
// ------------------------------------------------------------------------
// ------------------------------------------------------------------------
// ต่อ Hotspot มือถืออยู่: บอกที่อยู่ตัวเองให้ brain.py รู้ (มือถือคือ gateway)
// ทำเฉพาะตอนรถจอดนิ่ง เพราะระหว่างรอคำตอบบอร์ดจะค้างสั้น ๆ
// (ต่อ WiFi บ้าน brain.py หาบอร์ดเองผ่าน robot.local)
// ------------------------------------------------------------------------
bool     onPhone    = false;
bool     brainFound = false;
uint32_t lastHello  = 0;

void helloBrain() {
  WiFiClient client;
  HTTPClient http;
  http.setTimeout(400);
  String url = "http://" + WiFi.gatewayIP().toString() + ":" + BRAIN_PORT + "/api/hello";
  if (!http.begin(client, url)) return;
  bool ok = http.GET() == 200 && http.getString() == "brain-ok";
  http.end();
  if (ok && !brainFound) Serial.println(F("[Robot AI] เจอสมองในมือถือแล้ว"));
  brainFound = ok;
}

void printAddress() {
  if (apMode) {
    Serial.printf("[Robot AI] ต่อ WiFi \"%s\" (รหัส %s) แล้วเปิด http://%s\n",
                  AP_SSID, AP_PASS, WiFi.softAPIP().toString().c_str());
  } else if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("[Robot AI] เปิดเว็บ: http://%s  หรือ http://%s.local\n",
                  WiFi.localIP().toString().c_str(), HOSTNAME);
  } else {
    Serial.println(F("[Robot AI] WiFi หลุด กำลังต่อใหม่..."));
  }
}

void setupWiFi() {
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.hostname(HOSTNAME);
  WiFi.setSleepMode(WIFI_NONE_SLEEP);  // ตอบสนองไวขึ้นตอนบังคับเอง
  // สแกนก่อน: เห็น WiFi บ้าน -> ต่อบ้าน (สั่งผ่านเว็บได้เหมือนเดิม)
  //           ไม่เห็นบ้านแต่เห็น Hotspot มือถือ -> ต่อมือถือ
  const char* ssid = WIFI_SSID;
  const char* pass = WIFI_PASS;
  bool seenHome = false, seenPhone = false;
  int found = WiFi.scanNetworks();
  for (int i = 0; i < found; i++) {
    if (WiFi.SSID(i) == WIFI_SSID) seenHome = true;
    if (WiFi.SSID(i) == PHONE_SSID) seenPhone = true;
  }
  WiFi.scanDelete();
  if (!seenHome && seenPhone) {
    ssid = PHONE_SSID;
    pass = PHONE_PASS;
    onPhone = true;
  }
  WiFi.begin(ssid, pass);

  Serial.printf("\nกำลังต่อ WiFi \"%s\" ", ssid);
  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 30000) {
    digitalWrite(PIN_LED, !digitalRead(PIN_LED));  // ไฟกะพริบระหว่างต่อ
    delay(250);
    Serial.print('.');
  }
  digitalWrite(PIN_LED, HIGH);  // LED บนบอร์ดติดเมื่อเป็น LOW
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    WiFi.setAutoReconnect(true);
    if (MDNS.begin(HOSTNAME)) MDNS.addService("http", "tcp", 80);
  } else {
    // จำสาเหตุไว้ แล้วสแกนดูว่ามองเห็น WiFi บ้านไหม เพื่อบอกบนหน้าเว็บ
    wifiErr = WiFi.status();
    WiFi.disconnect();
    delay(100);
    int n = WiFi.scanNetworks();
    for (int i = 0; i < n; i++) {
      if (WiFi.SSID(i) == WIFI_SSID && (wifiSeen == 0 || WiFi.RSSI(i) > wifiSeen)) wifiSeen = WiFi.RSSI(i);
    }
    WiFi.scanDelete();
    Serial.printf("ต่อ WiFi ไม่ได้ (สถานะ %d, สแกน%s) -> เปิดโหมด Robot-AI แทน\n",
                  wifiErr, wifiSeen ? (String(" เจอ สัญญาณ ") + wifiSeen + " dBm").c_str() : "ไม่เจอชื่อนี้");
    if (wifiErr == WL_WRONG_PASSWORD) Serial.println(F("  -> รหัส WiFi ไม่ถูกต้อง"));
    else if (!wifiSeen) Serial.println(F("  -> ไม่เห็น WiFi ชื่อนี้: เช็กชื่อ (ตัวพิมพ์เล็กใหญ่), ต้องเป็น 2.4 GHz, วางใกล้เราเตอร์"));
    apMode = true;
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_PASS);
  }
  printAddress();
}

// ------------------------------------------------------------------------
void setup() {
  // ตั้งขามอเตอร์เป็น LOW ก่อนอย่างอื่น กันล้อกระตุกตอนเปิดเครื่อง
  const uint8_t pins[] = { PIN_ENA, PIN_IN1, PIN_IN2, PIN_IN3, PIN_IN4, PIN_ENB };
  for (uint8_t p : pins) {
    pinMode(p, OUTPUT);
    digitalWrite(p, LOW);
  }
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, HIGH);

  Serial.begin(115200);
  analogWriteRange(PWM_MAX);
  analogWriteFreq(PWM_FREQ);
  coastMotors();
  loadConfig();
  setupWiFi();

  server.on("/", HTTP_GET, handleRoot);
  server.on("/api/status", HTTP_GET, handleStatus);
  server.on("/api/run", HTTP_ANY, handleRun);     // POST จากหน้าเว็บ หรือ GET ?p=... จากแถบที่อยู่
  server.on("/api/drive", HTTP_GET, handleDrive);
  server.on("/api/stop", handleStop);
  server.on("/api/restart", handleRestart);
  server.on("/api/config", HTTP_GET, handleConfig);
  server.onNotFound(handleNotFound);
  server.begin();
}

uint32_t lastPrint = 0;

void loop() {
  server.handleClient();
  if (!apMode) MDNS.update();
  updateProgram();

  uint32_t now = millis();
  if (manualOn && now - manualLast > MANUAL_TIMEOUT) stopAll();  // สัญญาณจากมือถือขาด
  if (coastAt && (int32_t)(now - coastAt) >= 0) {
    coastAt = 0;
    if (phase == PH_IDLE && !manualOn) coastMotors();
  }
  digitalWrite(PIN_LED, (phase != PH_IDLE || manualOn) ? LOW : HIGH);

  // ยังไม่เจอสมอง: ถามทุก 5 วิ, เจอแล้ว: ทุก 20 วิ (เผื่อ brain.py ถูกปิดแล้วเปิดใหม่)
  if (onPhone && phase == PH_IDLE && !manualOn && WiFi.status() == WL_CONNECTED &&
      now - lastHello > (brainFound ? 20000UL : 5000UL)) {
    lastHello = now;
    helloBrain();
  }

  // โหมด Robot-AI: ถ้าไม่มีใครต่ออยู่ ลองต่อ WiFi บ้านใหม่ทุก ~2 นาที (รีสตาร์ตบอร์ด)
  if (apMode && now > 120000 && phase == PH_IDLE && !manualOn && WiFi.softAPgetStationNum() == 0) {
    Serial.println(F("ไม่มีใครต่อ Robot-AI -> รีสตาร์ตเพื่อลองต่อ WiFi บ้านอีกครั้ง"));
    delay(100);
    ESP.restart();
  }

  if (now - lastPrint > 15000) {  // พิมพ์ที่อยู่เว็บซ้ำ เผื่อเปิด Serial Monitor ทีหลัง
    lastPrint = now;
    printAddress();
  }
}
