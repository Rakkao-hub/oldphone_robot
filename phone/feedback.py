# feedback.py : ระบบคำชมและตำหนิของแซน (Python ล้วน ไม่ต้องติดตั้งอะไรเพิ่ม)
#
#   ชม      "เก่งมาก" "น่ารักจัง" "ขอบคุณ"        -> แซนดีใจ อารมณ์ดีขึ้น
#   ตำหนิ    "ไม่ดี" "ดื้อ" "ไม่เอา"                -> แซนขอโทษ อารมณ์แย่ลง
#   แก้คำสั่ง "ไม่เอา เลี้ยวซ้าย" "ไม่ใช่ ถอยหลัง"   -> ทำคำสั่งใหม่ และนับเป็นตำหนิเบา ๆ
#   ถามผล   "ได้คำชมกี่ครั้ง" "คะแนนเท่าไหร่"       -> แซนเล่าว่าถูกชม/ถูกดุกี่ครั้ง
#
# อารมณ์ (mood) เป็นตัวเลข -1 (งอน) ถึง 1 (อารมณ์ดี) ขยับตามคำชม/ตำหนิ แล้วค่อย ๆ จางกลับมาที่ 0 เอง
# หน้าแซน (face.html) เอาค่านี้ไปปรับสัญชาตญาณ: อารมณ์ดี = สนใจสิ่งที่ขยับ, งอน = เมินหนี
# ทุกครั้งที่ถูกชม/ถูกดุจะจดลงไฟล์ .feedback.json ว่าตอนนั้นเพิ่งทำท่าอะไร จึงจำได้ข้ามวัน
# (บันทึกนี้คือ "สัญญาณรางวัล" ที่ขั้นความจำของสมองแมลงวันจะเอาไปใช้ต่อ)
import json
import os
import random
import re
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, ".feedback.json")

# ---------------------------------------------------------------- คำที่ถือเป็นคำชม / ตำหนิ
# ข้อความที่ส่งมาถูกตัดช่องว่างและแปลงเป็นตัวพิมพ์เล็กแล้ว (commands.parse ทำให้)
# เช็กคำตำหนิก่อนเสมอ เพราะ "ไม่เก่ง" "ไม่น่ารัก" มีคำชมซ่อนอยู่ข้างใน
SCOLD = re.compile(r"ไม่(ค่อย)?(ดี|เก่ง|น่ารัก|ฉลาด|ได้เรื่อง|สวย)|นิสัยไม่ดี|นิสัยแย่|ดื้อ|แย่มาก|ทำแย่|ห่วย"
                   r"|ทำผิด|ผิดแล้ว|ผิดนะ|^อย่า(ทำ|ดื้อ|นะ)|badboy|badrobot")
CORRECT = re.compile(r"^(ไม่เอา|ไม่ใช่)(แบบนี้|อย่างนี้|แบบนั้น|นะ|สิ|แล้ว)?")   # ตามด้วยคำสั่งใหม่ได้
PRAISE = re.compile(r"เก่ง|^(ทำ(ได้)?)?ดี(มาก|จัง|เลย)|เยี่ยม|สุดยอด|น่ารัก|ฉลาด|เด็กดี|เจ๋ง|ถูกต้อง|ใช่เลย"
                    r"|goodboy|goodjob|verygood|goodrobot")
THANKS = re.compile(r"ขอบคุณ|ขอบใจ|แต๊งกิ้ว|thankyou|thanks")
REPORT = re.compile(r"(ได้|โดน|ถูก)?(คำ)?ชม(ไป)?กี่|(โดน|ถูก)(ดุ|ว่า|ตำหนิ)(ไป)?กี่|คะแนน(เท่า|กี่|ของ|แซน|$)|สมุดพก")
MAX_LEN = 24   # ยาวกว่านี้ส่วนใหญ่เป็นประโยคคุยกัน ไม่ใช่ชมหรือดุแซน

SAY = {
    "praise": ["ขอบคุณนะ แซนดีใจจัง", "เย้ แซนเก่งใช่ไหมล่ะ", "แซนจะตั้งใจกว่าเดิมอีก", "ชมอีกได้นะ แซนชอบ"],
    "thanks": ["ยินดีเลย", "ด้วยความยินดี", "ไม่เป็นไร แซนเต็มใจ"],
    "scold":  ["ขอโทษนะ", "โธ่ แซนขอโทษ", "แซนจะไม่ทำแล้ว", "งื้อ แซนเสียใจ"],
    "correct": ["ขอโทษนะ เอาใหม่ก็ได้", "อ้าว ไม่ใช่เหรอ ขอโทษนะ"],
}
EMOTION = {"praise": ["love", "shy", "excited", "happy"], "thanks": ["happy", "shy"], "scold": ["sad"], "correct": ["sad"]}
VALUE = {"praise": 1.0, "thanks": 0.5, "scold": -1.0, "correct": -0.5}


def parse(t):
    """t = ข้อความที่ตัดช่องว่างแล้ว คืน dict หรือ None ถ้าไม่ใช่คำชม/ตำหนิ
    กรณีแก้คำสั่ง คืน rest = ข้อความส่วนที่เหลือ ให้ commands.parse ลองอ่านเป็นคำสั่งใหม่"""
    if REPORT.search(t):
        return {"report": True}
    m = CORRECT.match(t)
    if m:   # ประโยคยาวที่ไม่มีคำสั่งตามมา (long) commands.parse จะมองข้าม เพราะน่าจะเป็นคนคุยกัน
        return _reply("correct", rest=t[m.end():], long=len(t) > MAX_LEN)
    if len(t) > MAX_LEN:
        return None
    for kind, pattern in (("scold", SCOLD), ("praise", PRAISE), ("thanks", THANKS)):
        if pattern.search(t):
            return _reply(kind)
    return None


def _reply(kind, **extra):
    return {"feedback": VALUE[kind], "kind": kind, "say": random.choice(SAY[kind]),
            "emotion": random.choice(EMOTION[kind]), **extra}


# ---------------------------------------------------------------- อารมณ์สะสม + สมุดจด
HALF_LIFE = 180.0   # วินาที: ไม่มีใครชมหรือดุ อารมณ์จะจางเหลือครึ่งหนึ่งทุก 3 นาที
STEP = 0.5          # ชมหรือดุเต็ม ๆ หนึ่งครั้ง ขยับอารมณ์เท่านี้
RECENT = 30.0       # ท่าที่ทำภายในกี่วินาที ถือว่าเป็นสิ่งที่กำลังถูกชม/ดุ
MAX_EVENTS = 300

# ---------------------------------------------------------------- ความจำดี/ไม่ดี
# ท่าที่ถูกชมบ่อย แซนจำได้ว่าถนัด ท่าที่โดนดุบ่อย แซนจำได้ว่าต้องระวัง (ความจำเก่าค่อย ๆ จาง)
MEMORY_HALF_LIFE = 7 * 86400   # วินาที: ความรู้สึกต่อท่าหนึ่ง ๆ จางเหลือครึ่งทุก 7 วัน
LIKE = 0.4                     # ความรู้สึกเกินนี้ = ชอบ / ต่ำกว่าค่าติดลบนี้ = ไม่ชอบ (ชมหรือดุ 2 ครั้งขึ้นไป)
REMIND_GAP = 600               # ท่าเดิมพูดถึงความจำซ้ำได้ทุกกี่วินาที (ไม่พูดทุกครั้งให้น่ารำคาญ)
RECALL_SAY = {
    "good": ["ท่านี้แซนถนัด", "เย้ ท่าโปรดของแซน", "ท่านี้เคยได้คำชมด้วยนะ"],
    "bad":  ["ครั้งก่อนโดนดุเรื่องนี้ แซนจะระวังนะ", "รอบนี้แซนจะตั้งใจกว่าเดิม", "ขอแก้ตัวนะ"],
}


class Mood:
    lock = threading.Lock()
    value = 0.0
    at = time.time()
    last_action = None      # ท่าล่าสุดที่แซนทำ เช่น "เต้น"
    last_action_at = 0.0
    book = None             # {"praise": n, "scold": n, "by_action": {ท่า: [ชม, ดุ]}, "events": [[เวลา, ค่า, ท่า], ...]}
    reminded = {}           # ท่า -> เวลาที่พูดถึงความจำครั้งล่าสุด

    @classmethod
    def _load(cls):
        if cls.book is None:
            try:
                with open(STORE, encoding="utf-8") as f:
                    cls.book = json.load(f)
            except (OSError, ValueError):
                cls.book = {}
            cls.book.setdefault("praise", 0)
            cls.book.setdefault("scold", 0)
            cls.book.setdefault("by_action", {})
            cls.book.setdefault("events", [])
        return cls.book

    @classmethod
    def _save(cls):
        try:
            tmp = STORE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(cls.book, f, ensure_ascii=False)
            os.replace(tmp, STORE)
        except OSError:
            pass   # จดไม่ได้ก็ไม่เป็นไร แซนยังทำงานต่อได้

    @classmethod
    def now(cls):
        """อารมณ์ตอนนี้ (-1 ถึง 1) หลังหักส่วนที่จางไปตามเวลา"""
        with cls.lock:
            return round(cls._decayed(), 2)

    @classmethod
    def _decayed(cls):
        t = time.time()
        cls.value *= 0.5 ** ((t - cls.at) / HALF_LIFE)
        cls.at = t
        return cls.value

    @classmethod
    def did(cls, action):
        """จดว่าแซนเพิ่งทำท่าอะไร (brain.py เรียกทุกครั้งที่สั่งรถ)"""
        with cls.lock:
            cls.last_action, cls.last_action_at = action, time.time()

    @classmethod
    def give(cls, value):
        """รับคำชม (ค่าบวก) หรือตำหนิ (ค่าลบ) คืนชื่อท่าที่ถูกชม/ดุ (None = ไม่ได้เพิ่งทำท่าอะไร)"""
        with cls.lock:
            cls.value = max(-1.0, min(1.0, cls._decayed() + STEP * value))
            action = cls.last_action if time.time() - cls.last_action_at < RECENT else None
            book = cls._load()
            key = "praise" if value > 0 else "scold"
            book[key] += 1
            if action:
                pair = book["by_action"].setdefault(action, [0, 0])
                pair[0 if value > 0 else 1] += 1
            book["events"] = book["events"][-(MAX_EVENTS - 1):] + [[round(time.time()), value, action]]
            cls._save()
            return action

    @classmethod
    def opinion(cls, action):
        """แซนรู้สึกยังไงกับท่านี้: -1 (โดนดุบ่อย) ถึง 1 (ถูกชมบ่อย) ชมหรือดุครั้งเดียวได้แค่ราว ±0.33"""
        with cls.lock:
            t, total = time.time(), 0.0
            for at, value, act in cls._load()["events"]:
                if act == action:
                    total += value * 0.5 ** ((t - at) / MEMORY_HALF_LIFE)
            return round(total / (abs(total) + 2), 2)

    @classmethod
    def recall(cls, action):
        """แซนนึกอะไรออกตอนกำลังจะทำท่านี้: คืน (คำพูด, สีหน้า) หรือ None ถ้าไม่มีอะไรน่าพูด"""
        o = cls.opinion(action)
        kind = "good" if o >= LIKE else "bad" if o <= -LIKE else None
        if not kind or time.time() - cls.reminded.get(action, 0) < REMIND_GAP:
            return None
        cls.reminded[action] = time.time()
        return random.choice(RECALL_SAY[kind]), "excited" if kind == "good" else "focus"

    @classmethod
    def report(cls):
        """ประโยคที่แซนเล่าว่าถูกชม/ถูกดุมาเท่าไร"""
        with cls.lock:
            book = cls._load()
            praise, scold = book["praise"], book["scold"]
            if not praise and not scold:
                return "ยังไม่มีใครชมหรือดุแซนเลย"
            text = f"แซนได้คำชม {praise} ครั้ง โดนดุ {scold} ครั้ง"
            best = max(book["by_action"].items(), key=lambda kv: kv[1][0], default=None)
            if best and best[1][0] > 0:
                text += f" ถูกชมตอน{best[0]}บ่อยที่สุด"
            worst = max(book["by_action"].items(), key=lambda kv: kv[1][1], default=None)
            if worst and worst[1][1] > 0:
                text += f" โดนดุตอน{worst[0]}บ่อยที่สุด"
            return text


if __name__ == "__main__":
    for s in ["เก่งมาก", "ดีมากเลย", "น่ารักจัง", "ขอบคุณนะ", "ไม่ดีเลย", "ดื้อจัง", "ไม่เก่งเลย", "ไม่เอาเลี้ยวซ้าย",
              "ไม่ใช่", "ได้คำชมกี่ครั้ง", "วันนี้อากาศดีไหม", "เดินหน้า50เซนติเมตร"]:
        print(f"{s!r:24} -> {parse(s)}")
