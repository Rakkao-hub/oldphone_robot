#!/usr/bin/env python3
# brain.py : สมองหุ่นยนต์ รันใน Termux บนมือถือ Android (ใช้แต่ไลบรารีที่มากับ Python ยกเว้น edge-tts ที่มีหรือไม่มีก็ได้)
#
#   python brain.py            แล้วเปิด Chrome ไปที่ http://localhost:8080
#
# หน้าที่
#   - เสิร์ฟหน้าตาหุ่น (face.html) ให้ Chrome เปิดเต็มจอ  Chrome ฟังเสียง/พูด/แสดงหน้า
#   - รับข้อความที่ได้ยินจาก Chrome -> แปลงเป็นคำสั่งขยับรถ (ไม่มีคุยเล่น เพื่อให้มือถือทำงานเบา)
#   - สั่งบอร์ด ESP8266 ผ่าน WiFi (บอร์ดเรียก /api/hello มาบอกที่อยู่ตัวเองเป็นระยะ)
import hmac
import json
import os
import random
import re
import secrets
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import commands
import feedback  # fly-instinct: คำชม/ตำหนิ และอารมณ์สะสม
import mission   # เดินสำรวจ และภารกิจหาของ
import people    # จำหน้าและชื่อคน

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
        self.user_at = 0.0  # คนสั่งรถครั้งล่าสุดเมื่อไร (สัญชาตญาณจะไม่หันตัวแทรก)
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
            self.user_at = time.time()
            try:
                return self._get("/api/run?p=" + urllib.parse.quote(prog))
            except OSError:  # คำสั่งแรกหลังจอดนิ่งนาน ๆ บางทีหมดเวลา ลองอีกรอบ
                return self._get("/api/run?p=" + urllib.parse.quote(prog), timeout=4)

    def stop(self):
        with self.lock:
            self.user_at = time.time()
            return self._get("/api/stop")

    def run_if_idle(self, prog, quiet):
        """fly-instinct: ทำท่าเฉพาะตอนรถว่าง และไม่มีคนสั่งอะไรมาภายใน quiet วินาที คืน True ถ้าได้ทำ"""
        with self.lock:
            if time.time() - self.user_at < quiet or self._get("/api/status", timeout=1.0).get("running"):
                return False
            self._get("/api/run?p=" + urllib.parse.quote(prog))
            return True

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
FOLLOW_STEP = re.compile(r"^FOLLOW(\d+(?:\.\d+)?)$")  # ท่อนหันตามในสคริปต์แนะนำตัว (commands.follow)


class Follow:
    on = False
    found = False
    x = 0.0
    w = 0.0
    at = 0.0


# fly-instinct: สัญชาตญาณ = สมองแมลงวันจิ๋วที่รันในหน้าแซน (phone/fly/) คุมการเหลือบตาตอนว่าง
# เปิด/ปิดด้วยเสียง "เปิดสัญชาตญาณ" / "ปิดสัญชาตญาณ" หรือเริ่มแบบปิดด้วย INSTINCT=0
# หันตัวตามสิ่งที่ขยับ (สั่งล้อ) ปิดอย่างเดียวด้วย INSTINCT_TURN=0 (ตายังเหลือบตามเหมือนเดิม)
# สะดุ้งถอยเมื่อมีของพุ่งเข้าหา ปิดอย่างเดียวด้วย INSTINCT_STARTLE=0 (ยังทำหน้าตกใจ แต่ไม่ถอย)
class Instinct:
    on = os.environ.get("INSTINCT", "1") != "0"
    turn = os.environ.get("INSTINCT_TURN", "1") != "0"
    startle = os.environ.get("INSTINCT_STARTLE", "1") != "0"
    explore = os.environ.get("INSTINCT_EXPLORE", "1") != "0"   # เบื่อแล้วออกเดินสำรวจเอง
    moved_at = {}   # ท่า -> เวลาที่ทำเองครั้งล่าสุด
    lock = threading.Lock()


INSTINCT_GAP = 6.0     # หันตัวเองได้อย่างมากทุกกี่วินาที (ถูกชมเรื่องหันบ่อย = ถี่ขึ้น, โดนดุ = ห่างขึ้น)
INSTINCT_QUIET = 5.0   # คนเพิ่งสั่งรถภายในกี่วินาที ไม่หันแทรก
INSTINCT_MAX_DEG = 60
INSTINCT_ACTION = "หันตามสิ่งที่ขยับ"  # ชื่อท่าในสมุดคำชม/ตำหนิ
STARTLE_ACTION = "สะดุ้งถอย"
STARTLE_PROG = "B10"   # ถอยหลัง 10 ซม.
STARTLE_GAP = 8.0


def instinct_move(action, prog, gap):
    """สัญชาตญาณขอขยับล้อเอง คืน True ถ้าทำจริง
    ความจำ: โดนดุเรื่องนี้บ่อย ๆ แซนเลิกทำเอง จนความจำจางหรือถูกชมใหม่ ส่วนถูกชมบ่อยจะทำถี่ขึ้น"""
    if not Instinct.on or Follow.on or Echo.on:
        return False
    liked = feedback.Mood.opinion(action)
    if liked <= -feedback.LIKE:
        return False
    with Instinct.lock:
        if time.time() - Instinct.moved_at.get(action, 0) < gap * (1 - liked):
            return False
        try:
            if not robot.run_if_idle(prog, INSTINCT_QUIET):
                return False
        except Exception:
            return False
        Instinct.moved_at[action] = time.time()
    log(f"สัญชาตญาณ: {action} {prog} (ความรู้สึกต่อเรื่องนี้ {liked})")
    feedback.Mood.did(action)  # ถูกชม/ถูกดุหลังจากนี้ จะจดว่าเป็นเรื่องนี้
    return True


def instinct_turn(d, deg):
    """หน้าแซนขอหันตัวไปทางสิ่งที่ขยับ (d = L/R ตามภาพกล้อง)"""
    if d not in ("L", "R") or not Instinct.turn:
        return False
    try:
        deg = max(10, min(INSTINCT_MAX_DEG, int(deg)))
    except (TypeError, ValueError):
        return False
    if FOLLOW_FLIP:  # ใช้ค่าเดียวกับโหมดตามหน้า: ถ้ารถหันหนีคน ก็จะหันหนีของที่ขยับด้วย
        d = "R" if d == "L" else "L"
    return instinct_move(INSTINCT_ACTION, f"{d}{deg}", INSTINCT_GAP)


def auto_move(kind, prog):
    """สำรวจ/ภารกิจขอขยับหนึ่งท่า คืน {ok, why} (why = cancelled: ภารกิจจบแล้ว ให้หน้าแซนเลิก)"""
    ok, why = mission.allow_move(kind, prog)
    if not ok:
        return {"ok": False, "why": why}
    if Follow.on or Echo.on:
        mission.Auto.cancel()
        return {"ok": False, "why": "cancelled"}
    if FOLLOW_FLIP:
        prog = mission.flip(prog)
    try:
        if not robot.run_if_idle(prog, INSTINCT_QUIET):
            return {"ok": False, "why": "busy"}
    except Exception:
        return {"ok": False, "why": "offline"}
    log(f"{'สำรวจ' if kind == 'explore' else 'ภารกิจ'}: {prog}")
    if kind == "explore":
        feedback.Mood.did(mission.EXPLORE_ACTION)
    return {"ok": True, "why": ""}


def auto_start(kind):
    """สัญชาตญาณขอเริ่มเอง: explore = เบื่อแล้วออกสำรวจ, wonder = สงสัยของใหม่ ขอไปดูแล้วจดจำ
    ต้องเปิดสัญชาตญาณ ไม่มีภารกิจอื่น ไม่มีคนเพิ่งสั่งรถ และไม่ได้ถูกดุเรื่องนั้นบ่อย"""
    if kind not in ("explore", "wonder") or not Instinct.on or mission.Auto.kind or Follow.on or Echo.on:
        return False
    if kind == "explore" and (not Instinct.explore or feedback.Mood.opinion(mission.EXPLORE_ACTION) <= -feedback.LIKE):
        return False
    if kind == "wonder" and mission.Wonders.pending() >= mission.MAX_WONDERS:
        return False
    if time.time() - robot.user_at < 20:
        return False
    mission.Auto.start(kind)
    log("เบื่อแล้ว ออกสำรวจเอง" if kind == "explore" else "สงสัยของใหม่ ไปดูหน่อย")
    return True


def instinct_startle():
    """หน้าแซนเห็นของพุ่งเข้าหา ขอถอยหลังนิดหนึ่ง"""
    return Instinct.startle and instinct_move(STARTLE_ACTION, STARTLE_PROG, STARTLE_GAP)


ACTION_NAMES = {"F": "เดินหน้า", "B": "ถอยหลัง", "L": "เลี้ยวซ้าย", "R": "เลี้ยวขวา", "W": "อยู่นิ่ง"}


def action_name(cmd):
    """ชื่อท่าที่เพิ่งทำ ใช้จดว่าแซนถูกชม/ถูกดุเรื่องอะไร"""
    if cmd.get("follow"):
        return "หันตาม"
    if cmd.get("music") == "dance":
        return "เต้น"
    prog = cmd.get("prog", "").strip()
    return "วาดรูป" if " " in prog else ACTION_NAMES.get(prog[:1], "ขยับ")


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
    if called and res["emotion"] != "sad" and "feedback" not in res:  # คำชม/ตำหนิมีสีหน้าของตัวเอง
        res["emotion"] = "happy"
    return res


last_cmd = {"op": None, "at": 0.0}
NUMBER_ONLY = re.compile(r"^\s*[\d๐-๙.]+\s*(เซน(ติเมตร)?|ซม\.?|องศา|เมตร)?\s*$")


HELP = "แซนยังทำได้แค่ขยับนะ ลองบอกให้เดินหน้า เลี้ยวซ้าย เต้น วาดรูปหัวใจ ตามมา ไปสำรวจ หรือสอนแซนจำของแล้วสั่งให้หาดูสิ"


MAX_CMD_LEN = 40  # ประโยคยาวกว่านี้ (ไม่นับช่องว่าง) ส่วนใหญ่เป็นเสียงคนคุยกันรอบ ๆ ไม่ใช่สั่งแซน


def do_text(text, called=False):
    # เสียงคนคุยกันยาว ๆ ไม่เอามาสั่งรถ (ยกเว้น "หยุด" ใช้ได้เสมอ และถ้าเรียกชื่อแซนนำหน้าก็ยังสั่งได้)
    if not called and len(re.sub(r"\s", "", text)) > MAX_CMD_LEN and not re.search("หยุด|เบรก", text):
        return {"say": "", "emotion": "confused"}
    # พูดตัวเลขตามหลังคำสั่ง เช่น "เลี้ยวซ้าย" ... "90" -> เลี้ยวซ้าย 90 องศา
    if NUMBER_ONLY.match(text) and last_cmd["op"] and time.time() - last_cmd["at"] < 15:
        text = {"F": "เดินหน้า", "B": "ถอยหลัง", "L": "เลี้ยวซ้าย", "R": "เลี้ยวขวา"}[last_cmd["op"]] + " " + text
    # แซนเพิ่งถาม "ชื่ออะไรเหรอ" / "อันนี้คืออะไร" คำที่ได้ยินต่อมา (ที่ไม่ใช่คำสั่ง) คือคำตอบ
    if not commands.parse(text):
        res = people.Ask.answer(text)
        if res:
            log("รู้จักคนใหม่:", res.get("met") or "ไม่ได้ชื่อ")
            return res
        res = mission.Wonders.answer(text)
        if res:
            log("ตอบข้อสงสัย:", res.get("learned") or "ไม่จำ")
            return res
    res = people.parse(text)   # "ผมชื่อ...", "รู้จักใครบ้าง", "ลืมหน้า..."
    if res:
        return res
    # ภารกิจ/สำรวจ: "จำของ...", "หา...", "ลืม...", "ไปสำรวจ" (อยู่ก่อนคำสั่งรถ เพราะ "หา" ไม่ใช่คำสั่งขยับ)
    res = mission.parse(text)
    if res:
        if res.get("teach") or res.get("mission") or res.get("explore"):
            Follow.on = False
            log("เริ่ม", mission.Auto.kind, mission.Auto.name or "")
        return res
    cmd = commands.parse(text)
    if cmd and cmd.get("prog", " ")[0] in "FBLR" and " " not in cmd.get("prog", " "):
        last_cmd.update(op=cmd["prog"][0], at=time.time())
    # ---- fly-instinct: สวิตช์สัญชาตญาณ / ถามผลคำชม / คำชม-ตำหนิ
    if cmd and "instinct" in cmd:
        Instinct.on = bool(cmd["instinct"])
        if not Instinct.on and mission.Auto.kind == "explore":
            mission.Auto.cancel()
        log("สัญชาตญาณ:", "เปิด" if Instinct.on else "ปิด")
        return {"say": cmd["say"], "emotion": cmd["emotion"]}
    if cmd and cmd.get("report"):
        return {"say": feedback.Mood.report(), "emotion": "happy"}
    if cmd and "feedback" in cmd:
        value = cmd.pop("feedback")
        about = feedback.Mood.give(value)
        log("คำชม" if value > 0 else "ตำหนิ", value, "เรื่อง:", about or "-", "อารมณ์:", feedback.Mood.now())
        if "kind" in cmd:  # ชมหรือดุล้วน ๆ (ถ้าเป็นการแก้คำสั่ง จะไม่มี kind และไหลลงไปทำคำสั่งใหม่ข้างล่าง)
            return {"say": cmd["say"], "emotion": cmd["emotion"], "feedback": value}
    # ---- จบส่วน fly-instinct
    if cmd and cmd.get("exclaim"):
        log("อุทาน:", cmd["exclaim"])
        return exclaim_reply(cmd)
    if cmd and cmd.get("sound"):  # เสียงพิเศษ (ผิวปาก / อุทาน)
        log("เสียงพิเศษ:", cmd["sound"])
        return {"say": "", "emotion": cmd["emotion"], "sound": cmd["sound"]}
    if cmd and (cmd.get("script") or cmd.get("faces") or "prog" in cmd or cmd.get("stop") or cmd.get("follow")):
        mission.Auto.cancel()  # คำสั่งอื่นเลิกภารกิจ/สำรวจที่ทำอยู่
    if cmd and cmd.get("script"):  # แนะนำตัว: ส่งทั้งสคริปต์ให้ Chrome เล่นทีละท่อน (พูด + สั่งท่าผ่าน /api/move)
        Follow.on = False
        steps = []
        for item in cmd["script"]:
            if not (isinstance(item, tuple) and len(item) == 3 and all(isinstance(x, str) for x in item)):
                log("ข้ามท่อนแนะนำตัวที่เขียนผิดรูป (ต้องเป็น (คำพูด, สีหน้า, ท่าขยับ)):", item)
                continue
            line, emo, prog = item
            fol = FOLLOW_STEP.match(prog.strip())  # follow(8) -> "FOLLOW8": หันตามคนแทนการสั่งท่า
            extra = {"prog": "", "follow": min(float(fol.group(1)), commands.MAX_FOLLOW)} if fol else {"prog": prog}
            if line.startswith("!"):  # ท่อนอุทาน เช่น "!wow"
                r = exclaim_reply(commands.exclaim(line[1:].strip()))
                steps.append({"say": r["say"], "emotion": emo, "sound": r.get("sound"), **extra})
            else:
                steps.append({"say": polite(line), "emotion": emo, **extra})
        log("แนะนำตัว", len(steps), "ท่อน")
        feedback.Mood.did("แนะนำตัว")  # fly-instinct
        threading.Thread(target=lambda: [tts_safe(st["say"]) for st in steps if st["say"]], daemon=True).start()
        return {"say": "", "emotion": cmd["emotion"], "script": steps}
    if cmd and cmd.get("faces"):  # โชว์สีหน้าทั้งหมด: Chrome เล่นเอง ไม่ต้องสั่งรถ
        Follow.on = False
        log("โชว์สีหน้าทั้งหมด")
        return {"say": "", "emotion": cmd["emotion"], "faces": True}
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
            if not cmd.get("stop"):
                feedback.Mood.did(action_name(cmd))  # fly-instinct: จดไว้ว่าเพิ่งทำท่าอะไร เผื่อถูกชม/ถูกดุ
                memo = feedback.Mood.recall(action_name(cmd))  # ความจำ: ท่าที่เคยถูกชม/โดนดุบ่อย
                if memo:
                    log("นึกออก:", action_name(cmd), memo[0])
                    res["say"], res["emotion"] = f"{memo[0]} {res['say']}".strip(), memo[1]
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


# ---------------------------------------------------------------- ควบคุมทางไกล (/remote)
# คนดูเปิด /remote จากเครื่องอื่น (ผ่าน Tailscale) -> เห็นภาพกล้องหน้าแซน, กดค้างพูดให้ออกลำโพงแซน, ขับรถ
# ทุกคำขอต้องมีรหัส (หัว X-Key) ตั้งเองได้ด้วย REMOTE_KEY ไม่งั้นสุ่มให้ครั้งแรกแล้วเก็บใน .remote_key
# Chrome ในมือถือส่งภาพเฉพาะตอนมีคนดูอยู่ (ประหยัดแบต) และดึงเสียงที่คนดูพูดมาเล่นเอง
KEY_FILE = os.path.join(HERE, ".remote_key")
MAX_VOICE = 2_000_000   # ไบต์ต่อคลิปเสียง (~1-2 นาที)
MAX_FRAME = 300_000     # ไบต์ต่อภาพ
MAX_JSON = 2_000_000    # ไบต์ต่อคำขอ JSON (ลายนิ้วมือของที่สอนแซนใหญ่สุด)
REMOTE_PROG = re.compile(r"^(?:[FBLR]\d{1,3}\s*){1,4}$")  # คนดูสั่งได้แค่ท่าพื้นฐานสั้น ๆ


def load_remote_key():
    key = os.environ.get("REMOTE_KEY", "").strip()
    if key:
        return key
    try:
        with open(KEY_FILE) as f:
            key = f.read().strip()
    except OSError:
        key = ""
    if not key:
        key = secrets.token_urlsafe(9)
        with open(KEY_FILE, "w") as f:
            f.write(key)
    return key


class Remote:
    key = load_remote_key()
    frame = b""
    frame_at = 0.0
    viewer_at = 0.0
    voices = []      # [(id, bytes, content-type)] เก็บแค่ไม่กี่คลิปล่าสุด
    voice_id = 0
    lock = threading.Lock()

    @classmethod
    def viewing(cls):
        return time.time() - cls.viewer_at < 5

    @classmethod
    def add_voice(cls, audio, ctype):
        with cls.lock:
            cls.voice_id += 1
            cls.voices = cls.voices[-4:] + [(cls.voice_id, audio, ctype)]
            return cls.voice_id

    @classmethod
    def next_voice(cls, after):
        with cls.lock:
            return next((v for v in cls.voices if v[0] > after), None)


# ---------------------------------------------------------------- เว็บเซิร์ฟเวอร์
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json; charset=utf-8", headers=None):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode() if ctype.startswith("application/json") else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
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

    def remote_ok(self):
        if hmac.compare_digest(self.headers.get("X-Key", "").encode(), Remote.key.encode()):
            return True
        time.sleep(0.5)  # กันเดารหัสรัว ๆ
        self.send(401, {"error": "bad key"})
        return False

    def body(self, limit):
        n = int(self.headers.get("Content-Length") or 0)
        if n > limit:
            raise ValueError("too big")
        return self.rfile.read(n)

    def do_GET(self):
        path, _, qs = self.path.partition("?")
        if path in ("/", "/face.html", "/remote"):
            name = "remote.html" if path == "/remote" else "face.html"
            with open(os.path.join(HERE, name), "rb") as f:
                self.send(200, f.read(), "text/html; charset=utf-8")
        elif path == "/api/remote/frame":  # ภาพล่าสุดจากกล้องหน้าแซน
            if not self.remote_ok():
                return
            Remote.viewer_at = time.time()
            if not Remote.frame or time.time() - Remote.frame_at > 5:
                return self.send(204, b"", "image/jpeg")
            self.send(200, Remote.frame, "image/jpeg")
        elif path == "/api/remote/state":
            if not self.remote_ok():
                return
            self.send(200, {"name": ROBOT_NAME, "online": robot.online()})
        elif path == "/api/voice":  # Chrome ในมือถือดึงเสียงที่คนดูพูดมาเล่น
            if not self.local_only():
                return
            try:
                after = int(urllib.parse.parse_qs(qs).get("after", ["0"])[0])
            except ValueError:
                after = 0
            v = Remote.next_voice(after)
            if not v:
                return self.send(204, b"", "text/plain")
            self.send(200, v[1], v[2], {"X-Voice-Id": str(v[0])})
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
                            "echo": Echo.on and time.time() - Echo.at < ECHO_IDLE,
                            "viewer": Remote.viewing(), "voice": Remote.voice_id,
                            "mood": feedback.Mood.now(), "instinct": Instinct.on,  # fly-instinct
                            "auto": mission.Auto.kind, "explore": Instinct.on and Instinct.explore,
                            "wonders": mission.Wonders.pending() if Instinct.on else 0})
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
            ctype = {".mjs": "text/javascript", ".js": "text/javascript", ".json": "application/json",
                     ".wasm": "application/wasm"}.get(os.path.splitext(fp)[1], "application/octet-stream")
            with open(fp, "rb") as f:
                self.send(200, f.read(), ctype)
        elif path.startswith("/fly/") and ".." not in path:  # fly-instinct: สมองแมลงวันจิ๋ว (โค้ด + ผังสายไฟ)
            fp = os.path.join(HERE, "fly", os.path.basename(urllib.parse.unquote(path)))
            ctype = {".js": "text/javascript", ".json": "application/json"}.get(os.path.splitext(fp)[1])
            if not (ctype and os.path.isfile(fp)):
                return self.send(404, {"error": "not found"})
            with open(fp, "rb") as f:
                self.send(200, f.read(), ctype)
        else:
            self.send(404, {"error": "not found"})

    def do_POST(self):
        if self.path.startswith("/api/remote/"):
            return self.do_remote_post()
        if not (self.local_only() and self.same_origin()):  # เครื่องอื่นใน WiFi / เว็บอื่น สั่งรถแทนไม่ได้
            return
        if self.path == "/api/frame":  # Chrome ส่งภาพกล้องมา (เฉพาะตอนมีคนดู)
            try:
                Remote.frame, Remote.frame_at = self.body(MAX_FRAME), time.time()
            except ValueError:
                return self.send(413, {"error": "too big"})
            return self.send(200, {"viewer": Remote.viewing()})
        try:
            data = json.loads(self.body(MAX_JSON) or b"{}")
            if not isinstance(data, dict):
                raise ValueError
        except ValueError:
            return self.send(400, {"error": "bad json or too big"})
        if self.path == "/api/hear":
            text = str(data.get("text", "")).strip()
            log("ได้ยิน:", text)
            res = hear(text) if text else {"say": "", "emotion": "neutral"}
            log("ตอบ:", res["say"])
            res["follow"] = Follow.on
            res["auto"] = mission.Auto.kind
            res["echo"] = Echo.on
            res["mood"], res["instinct"] = feedback.Mood.now(), Instinct.on  # fly-instinct
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
        elif self.path == "/api/follow":  # สคริปต์แนะนำตัวเปิด/ปิดโหมดหันตาม
            Follow.on = bool(data.get("on"))
            log("โหมดหันตาม (สคริปต์):", "เปิด" if Follow.on else "ปิด")
            if not Follow.on:
                try:
                    robot.stop()
                except Exception:
                    pass
            self.send(200, {"follow": Follow.on})
        elif self.path == "/api/instinct/turn":  # fly-instinct: สมองแมลงวันขอหันตัว
            self.send(200, {"ok": instinct_turn(data.get("dir"), data.get("deg"))})
        elif self.path == "/api/instinct/startle":  # fly-instinct: ของพุ่งเข้าหา ขอถอยหนี
            self.send(200, {"ok": instinct_startle()})
        elif self.path == "/api/log":
            log("[Chrome]", data.get("msg", ""))
            self.send(200, {"ok": True})
        elif self.path == "/api/track":
            Follow.found = bool(data.get("found"))
            Follow.x = float(data.get("x") or 0)
            Follow.w = float(data.get("w") or 0)
            Follow.at = time.time()
            self.send(200, {"follow": Follow.on})
        elif self.path == "/api/auto/move":  # สำรวจ/ภารกิจ: หน้าแซนขอขยับทีละท่า
            self.send(200, auto_move(data.get("kind"), data.get("prog")))
        elif self.path == "/api/auto/start":  # เบื่อแล้วขอออกสำรวจเอง / สงสัยของแล้วขอไปดู
            self.send(200, {"ok": auto_start(data.get("kind"))})
        elif self.path == "/api/wonder":  # ข้อสงสัยใหม่: ลายนิ้วมือ + รูปของที่แซนเจอเอง
            n = mission.Wonders.add(data.get("vectors"), data.get("th"), data.get("photo"))
            if mission.Auto.kind == "wonder":
                mission.Auto.cancel()
            log("สงสัย: เก็บของใหม่ไว้ถาม" if n else "สงสัย: ข้อมูลผิดรูป", f"(ค้าง {mission.Wonders.pending()})")
            self.send(200, {"ok": bool(n), "pending": mission.Wonders.pending()})
        elif self.path == "/api/people":  # จำหน้าคนตรงหน้าคู่กับชื่อ ("ผมชื่อ...")
            name = people.People.put(data.get("name"), data.get("vectors"))
            log("จำหน้า:", name or "ไม่สำเร็จ")
            self.send(200, {"ok": bool(name), "name": name})
        elif self.path == "/api/people/list":  # หน้าที่จำไว้ทั้งหมด ให้หน้าแซนเทียบเอง
            self.send(200, {"people": people.People.all()})
        elif self.path == "/api/people/ask":  # หน้าแซนเจอคนแปลกหน้า ถามชื่อ รอคำตอบ
            ok = people.Ask.start(data.get("vectors"))
            log("เจอคนแปลกหน้า ถามชื่อ" if ok else "ถามชื่อไม่ได้ (ข้อมูลหน้าผิดรูป)")
            self.send(200, {"ok": ok})
        elif self.path == "/api/wonder/next":  # เห็นคนแล้ว ขอรูปข้อสงสัยไปถาม
            w = mission.Wonders.next()
            if w:
                log("ถามข้อสงสัย", w["id"])
            self.send(200, w or {})
        elif self.path == "/api/auto/end":
            kind = data.get("kind")
            if mission.Auto.kind == kind:
                name = mission.Auto.name
                mission.Auto.cancel()
                log("จบ", kind, name or "", "เจอแล้ว" if data.get("found") else "")
                if kind == "mission" and data.get("found"):
                    feedback.Mood.did(mission.FIND_ACTION)  # ชมหลังเจอของ จะจดว่าเป็นเรื่องนี้
            self.send(200, {"ok": True})
        elif self.path == "/api/items":  # ลายนิ้วมือของที่เพิ่งสอน
            name = mission.Items.put(data.get("name"), data.get("vectors"), data.get("th"))
            if mission.Auto.kind == "teach":
                mission.Auto.cancel()
            log("จำของ:", name or "ไม่สำเร็จ (ข้อมูลผิดรูปหรือของเต็ม)")
            self.send(200, {"ok": bool(name), "name": name})
        elif self.path == "/api/stop":
            Follow.on = False
            Echo.on = False
            mission.Auto.cancel()
            try:
                robot.stop()
                self.send(200, {"ok": True})
            except Exception as e:
                self.send(502, {"ok": False, "error": str(e)})
        else:
            self.send(404, {"error": "not found"})

    def do_remote_post(self):
        if not self.remote_ok():
            return
        try:
            data = self.body(MAX_VOICE)
        except ValueError:
            return self.send(413, {"error": "too big"})
        if self.path == "/api/remote/voice":  # เสียงที่คนดูพูด -> ออกลำโพงแซน
            ctype = self.headers.get("Content-Type", "audio/webm").split(";")[0]
            if not ctype.startswith("audio/") or not data:
                return self.send(400, {"error": "not audio"})
            log(f"คนดูพูดผ่านไมค์ ({len(data) // 1024} KB)")
            return self.send(200, {"id": Remote.add_voice(data, ctype)})
        try:
            prog = str(json.loads(data or b"{}").get("prog", "")).strip().upper()
        except (ValueError, AttributeError):
            return self.send(400, {"error": "bad json"})
        try:
            if self.path == "/api/remote/stop":
                Follow.on = False
                mission.Auto.cancel()
                robot.stop()
            elif self.path == "/api/remote/move" and REMOTE_PROG.match(prog):
                Follow.on = False
                mission.Auto.cancel()
                log("คนดูสั่งรถ:", prog)
                robot.run(prog)
            else:
                return self.send(400, {"error": "bad command"})
            self.send(200, {"ok": True})
        except Exception as e:
            self.send(502, {"ok": False, "error": str(e)})


def main():
    threading.Thread(target=probe_robot_local, daemon=True).start()
    threading.Thread(target=follow_loop, daemon=True).start()
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    log(f"สมอง{ROBOT_NAME}พร้อมแล้ว เปิด Chrome ไปที่ http://localhost:{PORT}")
    log("รอบอร์ด ESP8266 เรียกเข้ามา..." if not robot.url else f"บอร์ดล่าสุด: {robot.url}")
    log(f"ควบคุมทางไกล: เปิด /remote แล้วใส่รหัส {Remote.key}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
