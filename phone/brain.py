#!/usr/bin/env python3
# brain.py : สมองหุ่นยนต์ รันใน Termux บนมือถือ Android (ใช้แต่ไลบรารีที่มากับ Python ยกเว้น edge-tts ที่มีหรือไม่มีก็ได้)
#
#   python brain.py            แล้วเปิด Chrome ไปที่ http://localhost:8080
#
# หน้าที่
#   - เสิร์ฟหน้าตาหุ่น (face.html) ให้ Chrome เปิดเต็มจอ  Chrome ฟังเสียง/พูด/แสดงหน้า
#   - รับข้อความที่ได้ยินจาก Chrome -> แปลงเป็นคำสั่งขยับรถ (ไม่มีคุยเล่น เพื่อให้มือถือทำงานเบา)
#   - สั่งบอร์ด ESP8266 ผ่าน WiFi (บอร์ดเรียก /api/hello มาบอกที่อยู่ตัวเองเป็นระยะ)
import json
import os
import random
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import commands

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("BRAIN_PORT", "8080"))
ROBOT_NAME = os.environ.get("ROBOT_NAME", "แซน")
# คำที่ระบบฟังเสียงอาจสะกดชื่อออกมา (เรียกชื่อแล้วหุ่นจะหน้ายิ้ม)
NAME_RE = re.compile(os.environ.get("ROBOT_NAME_RE", r"แซ[่้]?น+(?:ด์)?|^แสน$|sand|san\b|zan\b"), re.I)
GREETINGS = ["ว่าไง แซนอยู่นี่", "จ้า เรียกแซนเหรอ", "แซนมาแล้ว มีอะไรให้ช่วยไหม", "แซนพร้อมลุยแล้ว"]
CALL_WORDS = re.compile(r"สวัสดี|หวัดดี|ฮัลโหล|เฮ้|ไง|จ๋า|จ้า|ครับ|ค่ะ|คะ|นะ|หน่อย|อยู่ไหม|อยู่ไหน|ๆ|\s")
STATE_FILE = os.path.join(HERE, ".robot_url")

def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ---------------------------------------------------------------- บอร์ด ESP8266
class Robot:
    def __init__(self):
        self.url = os.environ.get("ROBOT_URL") or self._load()
        self.last_seen = 0.0
        self.lock = threading.Lock()

    def _load(self):
        try:
            with open(STATE_FILE) as f:
                return f.read().strip() or None
        except OSError:
            return None

    def hello(self, ip):
        url = f"http://{ip}"
        if url != self.url:  # อย่าเชื่อทันที เช็กก่อนว่าเป็นบอร์ดหุ่นจริง (กันเครื่องอื่นใน WiFi มาหลอก)
            try:
                with urllib.request.urlopen(url + "/api/status", timeout=2) as r:
                    if "running" not in json.loads(r.read()):
                        return
            except Exception:
                return
        if url != self.url:
            log(f"เจอบอร์ดที่ {url}")
            try:
                with open(STATE_FILE, "w") as f:
                    f.write(url)
            except OSError:
                pass
        self.url = url
        self.last_seen = time.time()

    def _get(self, path, timeout=2.0):
        if not self.url:
            raise ConnectionError("ยังไม่เจอบอร์ด")
        with urllib.request.urlopen(self.url + path, timeout=timeout) as r:
            return json.loads(r.read() or b"{}")

    def online(self):
        if time.time() - self.last_seen < 45:
            return True
        try:
            self._get("/api/status", timeout=1.0)
            self.last_seen = time.time()
            return True
        except Exception:
            return False

    def run(self, prog):
        with self.lock:
            try:
                return self._get("/api/run?p=" + urllib.parse.quote(prog))
            except OSError:  # คำสั่งแรกหลังจอดนิ่งนาน ๆ บางทีหมดเวลา ลองอีกรอบ
                return self._get("/api/run?p=" + urllib.parse.quote(prog), timeout=4)

    def stop(self):
        with self.lock:
            return self._get("/api/stop")

    def drive(self, d, speed=None):
        """ใช้เฉพาะโหมดตาม: เช็ก Follow.on ภายใต้ lock กันส่งแทรกหลังผู้ใช้สั่งท่าอื่นไปแล้ว"""
        q = f"/api/drive?d={d}" + (f"&s={int(speed)}" if speed else "")
        with self.lock:
            if Follow.on:
                return self._get(q, timeout=0.5)


robot = Robot()


# ---------------------------------------------------------------- โหมดหันหน้าตามคน ("ตามมา")
# Chrome จับหน้าด้วยกล้องหน้า แล้วส่งตำแหน่งมาที่ /api/track ราว 8 ครั้งต่อวินาที
#   x : -1 (ซ้ายของภาพ) .. 1 (ขวาของภาพ)   w : ความกว้างหน้าเทียบกับภาพ (ใกล้ = ใหญ่)
# หมุนอยู่กับที่ให้หน้าคนอยู่กลางภาพเท่านั้น ไม่เดินหน้า/ถอยหลัง
FOLLOW_FLIP = os.environ.get("FOLLOW_FLIP") == "1"   # ถ้ารถหันหนีคน ให้ตั้งเป็น 1
TURN_MIN = int(os.environ.get("TURN_MIN", "470"))      # แรงหมุนตอนหน้าเยื้องนิดเดียว
TURN_MAX = int(os.environ.get("TURN_MAX", "620"))      # แรงหมุนตอนหน้าอยู่ขอบภาพ
DEADBAND = 0.2


class Follow:
    on = False
    found = False
    x = 0.0
    w = 0.0
    at = 0.0


def follow_step():
    """ตัดสินใจ 1 ครั้ง คืน (ทิศ, แรง) หรือ None = หยุด"""
    if not (Follow.found and time.time() - Follow.at < 0.5):
        return None
    x = -Follow.x if FOLLOW_FLIP else Follow.x
    if abs(x) > DEADBAND:
        k = min(1.0, (abs(x) - DEADBAND) / (1 - DEADBAND))
        return ("L" if x < 0 else "R", TURN_MIN + (TURN_MAX - TURN_MIN) * k)
    return None  # หน้าอยู่กลางภาพแล้ว หยุดนิ่ง


def follow_loop():
    stopped = True
    while True:
        time.sleep(0.12)
        if not Follow.on:
            stopped = True
            continue
        step = follow_step()
        try:
            if step:
                robot.drive(*step)
                stopped = False
            elif not stopped:
                robot.stop()
                stopped = True
        except Exception:
            pass


def probe_robot_local():
    """ถ้ายังไม่เจอบอร์ด ลอง http://robot.local ทุก 10 วิ (ใช้ได้เมื่ออยู่ WiFi บ้านเดียวกัน
    ส่วนตอนมือถือเปิด Hotspot บอร์ดจะเรียก /api/hello มาเอง)"""
    while True:
        if not robot.online():
            try:
                with urllib.request.urlopen("http://robot.local/api/status", timeout=3) as r:
                    robot.hello(json.loads(r.read())["ip"])
            except Exception:
                pass
        time.sleep(10)


# ---------------------------------------------------------------- โหมดพูดตาม
# "พูดตาม" -> แซนตอบ "พร้อมฟัง" แล้วจดทุกประโยคที่ได้ยินขึ้นจอ (ไม่ขยับรถ)
# "พูดตามได้" -> แซนพูดข้อความทั้งหมดที่จดไว้ แล้วออกจากโหมด
# "ยกเลิก" (คำเดียว) หรือแตะจอ -> ออกจากโหมดโดยไม่พูด
ECHO_START = re.compile(r"พูด\s*ตาม(?!\s*ได้)")
ECHO_SAY = re.compile(r"พูด\s*ตาม\s*ได้(\s*แล้ว)?")
ECHO_CANCEL = re.compile(r"^\s*(ยกเลิก|เลิก|หยุด|พอ)(พูดตาม)?\s*$")
ECHO_IDLE = 120  # ไม่ได้ยินอะไรเลยนานเท่านี้ (วิ) ออกจากโหมดเอง


class Echo:
    on = False
    words = []
    at = 0.0


def echo_text():
    return " ".join(Echo.words)


def echo_mode(text):
    """อยู่ในโหมดพูดตาม: คืนคำตอบ หรือ None ถ้าไม่ได้อยู่ในโหมด"""
    if Echo.on and time.time() - Echo.at > ECHO_IDLE:
        Echo.on = False
    if not Echo.on:
        return None
    Echo.at = time.time()
    if ECHO_CANCEL.match(text):
        Echo.on = False
        return {"say": "เลิกพูดตามแล้ว", "emotion": "neutral", "board": None}
    m = ECHO_SAY.search(text)
    if m:
        before = text[:m.start()].strip()  # เผื่อพูดต่อท้ายประโยคสุดท้ายในลมหายใจเดียว
        if before:
            Echo.words.append(before)
        Echo.on = False
        said = echo_text()
        log("พูดตาม:", said)
        if not said:
            return {"say": "ยังไม่ได้พูดอะไรให้แซนฟังเลยนะ", "emotion": "happy", "board": None}
        return {"say": said, "emotion": "happy", "board": said, "raw": True}
    Echo.words.append(text)
    return {"say": "", "emotion": "listening", "board": echo_text()}


def polite(text):
    """เติมคำลงท้ายให้ฟังเป็นคนพูด: ครับ (เสียงผู้ชาย) / ค่ะ, คะ (เสียงผู้หญิง)"""
    text = text.strip()
    if not text or re.search(r"(ครับ|ค่ะ|คะ|จ้า|จ๊ะ|จ้ะ)$", text):
        return text
    female = "Premwadee" in TTS_VOICE
    # เขียนติดกันไม่เว้นวรรค ไม่งั้นเสียง AI จะเว้นจังหวะก่อน "ครับ" จนฟังขาด ๆ
    if re.search(r"(นะ|ไหม|หรือยัง|อะไร|ไหน|สิ)$", text):  # ท้ายแบบนี้ผู้หญิงใช้ "คะ"
        return text + ("คะ" if female else "ครับ")
    return text + ("ค่ะ" if female else "ครับ")


def hear(text):
    """ได้ยินข้อความ -> คืน {say, emotion} (+ board = ข้อความบนจอโหมดพูดตาม, None = ซ่อน)"""
    res = echo_mode(text)  # เช็กก่อน เพราะในโหมดนี้ทุกคำ (แม้แต่ "แซน" หรือ "เดินหน้า") คือข้อความที่ต้องจด
    if res:
        if not res.pop("raw", False):  # ข้อความที่ผู้ใช้ให้พูดตาม ห้ามเติมคำลงท้าย
            res["say"] = polite(res["say"])
        return res
    res = understand(text)
    if not res.pop("raw", False):  # คำอุทานไม่เติม ครับ/ค่ะ
        res["say"] = polite(res["say"])
    return res


# ---------------------------------------------------------------- อุทาน
SOUNDS_DIR = os.path.join(HERE, "sounds")
SOUND_TYPES = {".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg", ".m4a": "audio/mp4"}


def sound_file(key):
    for ext in SOUND_TYPES:
        if os.path.isfile(os.path.join(SOUNDS_DIR, key + ext)):
            return key + ext
    return None


def exclaim_reply(cmd):
    """มีไฟล์เสียง -> ให้ Chrome เล่นไฟล์ / ไม่มี -> แซนพูดคำอุทานเอง"""
    f = sound_file(cmd["exclaim"])
    if f:
        return {"say": "", "emotion": cmd["emotion"], "sound": {"type": "file", "url": "/sounds/" + urllib.parse.quote(f)}, "raw": True}
    return {"say": cmd["say"], "emotion": cmd["emotion"], "raw": True}


def understand(text):
    if ECHO_START.search(text):
        Echo.on, Echo.words, Echo.at = True, [], time.time()
        log("เข้าโหมดพูดตาม")
        return {"say": "พร้อมฟัง", "emotion": "happy", "board": ""}
    called = bool(NAME_RE.search(text))
    if called:
        text = NAME_RE.sub(" ", text).strip()
        if not CALL_WORDS.sub("", text):  # เรียกชื่อเฉย ๆ เช่น "แซน" "สวัสดีแซน"
            return {"say": random.choice(GREETINGS), "emotion": "happy"}
    res = do_text(text, called)
    if called and res["emotion"] != "sad":
        res["emotion"] = "happy"
    return res


last_cmd = {"op": None, "at": 0.0}
NUMBER_ONLY = re.compile(r"^\s*[\d๐-๙.]+\s*(เซน(ติเมตร)?|ซม\.?|องศา|เมตร)?\s*$")


HELP = "แซนยังทำได้แค่ขยับนะ ลองบอกให้เดินหน้า ถอยหลัง เลี้ยวซ้าย เต้น วาดรูปหัวใจ หรือตามมาดูสิ"


MAX_CMD_LEN = 40  # ประโยคยาวกว่านี้ (ไม่นับช่องว่าง) ส่วนใหญ่เป็นเสียงคนคุยกันรอบ ๆ ไม่ใช่สั่งแซน


def do_text(text, called=False):
    # เสียงคนคุยกันยาว ๆ ไม่เอามาสั่งรถ (ยกเว้น "หยุด" ใช้ได้เสมอ และถ้าเรียกชื่อแซนนำหน้าก็ยังสั่งได้)
    if not called and len(re.sub(r"\s", "", text)) > MAX_CMD_LEN and not re.search("หยุด|เบรก", text):
        return {"say": "", "emotion": "confused"}
    # พูดตัวเลขตามหลังคำสั่ง เช่น "เลี้ยวซ้าย" ... "90" -> เลี้ยวซ้าย 90 องศา
    if NUMBER_ONLY.match(text) and last_cmd["op"] and time.time() - last_cmd["at"] < 15:
        text = {"F": "เดินหน้า", "B": "ถอยหลัง", "L": "เลี้ยวซ้าย", "R": "เลี้ยวขวา"}[last_cmd["op"]] + " " + text
    cmd = commands.parse(text)
    if cmd and cmd.get("prog", " ")[0] in "FBLR" and " " not in cmd.get("prog", " "):
        last_cmd.update(op=cmd["prog"][0], at=time.time())
    if cmd and cmd.get("exclaim"):
        log("อุทาน:", cmd["exclaim"])
        return exclaim_reply(cmd)
    if cmd and cmd.get("sound"):  # เสียงพิเศษ (ผิวปาก / อุทาน)
        log("เสียงพิเศษ:", cmd["sound"])
        return {"say": "", "emotion": cmd["emotion"], "sound": cmd["sound"]}
    if cmd and cmd.get("script"):  # แนะนำตัว: ส่งทั้งสคริปต์ให้ Chrome เล่นทีละท่อน (พูด + สั่งท่าผ่าน /api/move)
        Follow.on = False
        steps = []
        for line, emo, prog in cmd["script"]:
            if line.startswith("!"):  # ท่อนอุทาน เช่น "!wow"
                r = exclaim_reply(commands.exclaim(line[1:].strip()))
                steps.append({"say": r["say"], "emotion": emo, "prog": prog, "sound": r.get("sound")})
            else:
                steps.append({"say": polite(line), "emotion": emo, "prog": prog})
        log("แนะนำตัว", len(steps), "ท่อน")
        threading.Thread(target=lambda: [tts_safe(st["say"]) for st in steps if st["say"]], daemon=True).start()
        return {"say": "", "emotion": cmd["emotion"], "script": steps}
    if cmd:
        Follow.on = bool(cmd.get("follow"))  # คำสั่งอื่นทุกอันเลิกโหมดตาม
        try:
            if cmd.get("stop"):
                robot.stop()
            elif Follow.on:
                log("เริ่มโหมดตามหน้า")
            else:
                log("สั่งรถ:", cmd["prog"])
                robot.run(cmd["prog"])
            res = {"say": cmd["say"], "emotion": cmd["emotion"]}
            f = cmd.get("music") and sound_file(cmd["music"])
            if f:  # เพลงประกอบ (เช่น เต้น + sounds/dance.mp3) เล่นจนรถทำท่าจบ
                res["music"] = "/sounds/" + urllib.parse.quote(f)
            return res
        except Exception as e:
            log("สั่งรถไม่ได้:", e)
            return {"say": "แย่จัง ติดต่อล้อไม่ได้ ช่วยเช็กหน่อยว่ารถเปิดอยู่ไหม", "emotion": "sad"}
    # ไม่ใช่คำสั่ง: ถ้าเรียกชื่อแซนมาด้วย บอกว่าทำอะไรได้บ้าง
    # ถ้าไม่ได้เรียก (อาจเป็นเสียงคนคุยกันหรือทีวี) ทำหน้างงเงียบ ๆ ไม่พูดแทรก
    if called:
        return {"say": HELP, "emotion": "neutral"}
    return {"say": "", "emotion": "confused"}


# ---------------------------------------------------------------- เสียงพูด
# มือถือเครื่องนี้ไม่มีเสียงอ่านภาษาไทยในเครื่อง จึงขอไฟล์เสียงจากเน็ต แล้วให้ Chrome เล่นเป็นไฟล์เสียงธรรมดา
#   1) เสียง AI ของ Microsoft Edge (ชัดและเป็นธรรมชาติที่สุด) ต้องติดตั้งก่อน: pip install edge-tts
#   2) ถ้าไม่ได้ติดตั้งหรือใช้ไม่ได้ ใช้เสียง Google แปลภาษาแทน
# เปลี่ยนเสียงได้ด้วย TTS_VOICE: th-TH-NiwatNeural (ผู้ชาย) / th-TH-PremwadeeNeural (ผู้หญิง)
# TTS_RATE ปรับความเร็ว เช่น +10% หรือ -10%, TTS_PITCH ปรับเสียงสูงต่ำ เช่น +20Hz ให้ฟังเป็นหุ่นตัวเล็ก
TTS_VOICE = os.environ.get("TTS_VOICE", "th-TH-NiwatNeural")
TTS_RATE = os.environ.get("TTS_RATE", "+5%")
TTS_PITCH = os.environ.get("TTS_PITCH", "+8Hz")
try:
    import asyncio
    import edge_tts
except ImportError:
    edge_tts = None
    log("ไม่มี edge-tts ใช้เสียง Google แทน (ติดตั้ง: pip install edge-tts)")


def tts_edge(text, rate=None):
    async def run():
        audio = b""
        async for part in edge_tts.Communicate(text, TTS_VOICE, rate=rate or TTS_RATE, pitch=TTS_PITCH).stream():
            if part["type"] == "audio":
                audio += part["data"]
        return audio
    audio = asyncio.run(asyncio.wait_for(run(), timeout=10))
    if not audio:
        raise RuntimeError("edge-tts ไม่ส่งเสียงกลับมา")
    return audio


TTS_URL = "https://translate.google.com/translate_tts?ie=UTF-8&tl=th&client=tw-ob&q="
tts_cache = {}


def tts_chunks(text, limit=180):
    """Google รับได้ครั้งละไม่เกินราว 200 ตัวอักษร ตัดตามช่องว่าง"""
    chunks, cur = [], ""
    for word in text.split():
        if cur and len(cur) + len(word) + 1 > limit:
            chunks.append(cur)
            cur = ""
        cur = f"{cur} {word}".strip()
    return chunks + ([cur] if cur else [])


def tts_google(text):
    audio = b""
    for chunk in tts_chunks(text):
        req = urllib.request.Request(TTS_URL + urllib.parse.quote(chunk), headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            audio += r.read()  # ไฟล์ mp3 ต่อท้ายกันเล่นต่อเนื่องได้เลย
    return audio


def tts_safe(text):
    """ทำเสียงเก็บไว้ล่วงหน้า (ท่อนถัดไปจะได้พูดต่อได้ทันที) error ก็ไม่เป็นไร"""
    try:
        tts(text)
    except Exception:
        pass


def tts(text, rate=None):
    key = (text, rate)
    if key in tts_cache:
        return tts_cache[key]
    audio = None
    if edge_tts:
        try:
            audio = tts_edge(text, rate)
        except Exception as e:
            log("เสียง Edge ใช้ไม่ได้ ใช้เสียง Google แทน:", e)
    if audio is None:
        audio = tts_google(text)
    if len(tts_cache) > 50:
        tts_cache.clear()
    tts_cache[key] = audio
    return audio


# ---------------------------------------------------------------- เว็บเซิร์ฟเวอร์
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json; charset=utf-8"):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode() if ctype.startswith("application/json") else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass  # Chrome ยกเลิกเอง (เช่นแตะหยุดตอนกำลังโหลดเสียง) ไม่ต้องทำอะไร

    def local_only(self):
        if self.client_address[0] in ("127.0.0.1", "::1"):
            return True
        self.send(403, {"error": "local only"})
        return False

    def same_origin(self):
        """เว็บไซต์อื่นที่เปิดใน Chrome มือถือก็ส่งมาจาก localhost ได้ จึงเช็กว่ามาจากหน้าแซนเองจริง"""
        origin = self.headers.get("Origin")
        if origin in (None, f"http://localhost:{PORT}", f"http://127.0.0.1:{PORT}"):
            return True
        self.send(403, {"error": "bad origin"})
        return False

    def do_GET(self):
        path, _, qs = self.path.partition("?")
        if path in ("/", "/face.html"):
            with open(os.path.join(HERE, "face.html"), "rb") as f:
                self.send(200, f.read(), "text/html; charset=utf-8")
        elif path == "/api/hello":  # บอร์ดเรียกมาเอง
            robot.hello(self.client_address[0])
            self.send(200, "brain-ok", "text/plain")
        elif path == "/api/tts":
            if not self.local_only():  # ให้เฉพาะ Chrome ในมือถือเอง ไม่เปิดเป็นทางผ่านให้เครื่องอื่น
                return
            q = urllib.parse.parse_qs(qs)
            text = q.get("q", [""])[0].strip()
            try:
                self.send(200, tts(text), "audio/mpeg")
            except Exception as e:
                log("ทำเสียงพูดไม่ได้:", e)
                self.send(502, {"error": str(e)})
        elif path == "/api/robot":  # รถกำลังทำท่าอยู่ไหม (สคริปต์แนะนำตัวใช้รอท่าจบ)
            try:
                self.send(200, {"running": bool(robot._get("/api/status", timeout=1.5).get("running"))})
            except Exception:
                self.send(200, {"running": False, "offline": True})
        elif path == "/api/state":
            self.send(200, {"robot": robot.url, "online": robot.online(), "name": ROBOT_NAME, "follow": Follow.on,
                            "echo": Echo.on and time.time() - Echo.at < ECHO_IDLE})
        elif path.startswith("/sounds/") and ".." not in path:  # ไฟล์เสียงอุทาน
            fp = os.path.join(SOUNDS_DIR, os.path.basename(urllib.parse.unquote(path)))
            ctype = SOUND_TYPES.get(os.path.splitext(fp)[1].lower())
            if not (ctype and os.path.isfile(fp)):
                return self.send(404, {"error": "not found"})
            with open(fp, "rb") as f:
                self.send(200, f.read(), ctype)
        elif path.startswith("/vendor/") and ".." not in path:  # MediaPipe เก็บในเครื่อง ใช้ได้แม้ไม่มีเน็ต
            fp = os.path.join(HERE, path.lstrip("/"))
            if not os.path.isfile(fp):
                return self.send(404, {"error": "not found"})
            ctype = {".mjs": "text/javascript", ".js": "text/javascript",
                     ".wasm": "application/wasm"}.get(os.path.splitext(fp)[1], "application/octet-stream")
            with open(fp, "rb") as f:
                self.send(200, f.read(), ctype)
        else:
            self.send(404, {"error": "not found"})

    def do_POST(self):
        if not (self.local_only() and self.same_origin()):  # เครื่องอื่นใน WiFi / เว็บอื่น สั่งรถแทนไม่ได้
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(data, dict):
                raise ValueError
        except ValueError:
            return self.send(400, {"error": "bad json"})
        if self.path == "/api/hear":
            text = str(data.get("text", "")).strip()
            log("ได้ยิน:", text)
            res = hear(text) if text else {"say": "", "emotion": "neutral"}
            log("ตอบ:", res["say"])
            res["follow"] = Follow.on
            res["echo"] = Echo.on
            self.send(200, res)
        elif self.path == "/api/move":  # สคริปต์แนะนำตัวสั่งท่า
            prog = str(data.get("prog", "")).strip()
            try:
                if prog:
                    log("สั่งรถ:", prog)
                    robot.run(prog)
                self.send(200, {"ok": True})
            except Exception as e:
                log("สั่งรถไม่ได้:", e)
                self.send(502, {"ok": False, "error": str(e)})
        elif self.path == "/api/log":
            log("[Chrome]", data.get("msg", ""))
            self.send(200, {"ok": True})
        elif self.path == "/api/track":
            Follow.found = bool(data.get("found"))
            Follow.x = float(data.get("x") or 0)
            Follow.w = float(data.get("w") or 0)
            Follow.at = time.time()
            self.send(200, {"follow": Follow.on})
        elif self.path == "/api/stop":
            Follow.on = False
            Echo.on = False
            try:
                robot.stop()
                self.send(200, {"ok": True})
            except Exception as e:
                self.send(502, {"ok": False, "error": str(e)})
        else:
            self.send(404, {"error": "not found"})


def main():
    threading.Thread(target=probe_robot_local, daemon=True).start()
    threading.Thread(target=follow_loop, daemon=True).start()
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    log(f"สมอง{ROBOT_NAME}พร้อมแล้ว เปิด Chrome ไปที่ http://localhost:{PORT}")
    log("รอบอร์ด ESP8266 เรียกเข้ามา..." if not robot.url else f"บอร์ดล่าสุด: {robot.url}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
