# mission.py : เดินสำรวจ และภารกิจหาของ (Python ล้วน)
#
#   "จำของ หมี" / "นี่คือหมี" / "จำหมีไว้"  -> สอนแซน: ถือของให้กล้องดูราว 8 วิ แซนจดลายนิ้วมือภาพไว้ใน .items.json
#   "หาหมี" / "ไปหาหมี" / "ภารกิจหาหมี"    -> ภารกิจ: แซนหมุนมองรอบตัว เดินสำรวจ เจอแล้วเข้าไปใกล้ ประกาศว่าเจอ
#   "ลืมหมี" / "รู้จักของอะไรบ้าง"          -> ลบของที่จำไว้ / บอกรายชื่อของที่รู้จัก
#   "ไปสำรวจ" / "เลิกสำรวจ"                 -> เดินสำรวจเอง (ปกติแซนออกสำรวจเองตอนเบื่อ ถ้าสัญชาตญาณเปิดอยู่)
#   โหมดสงสัย: แซนเจอของใหม่เอง จดจำ ถ่ายรูปเก็บเป็น "ข้อสงสัย" แล้วเอามาถามคน ("อันนี้คืออะไรเหรอ")
#              คนตอบ "หมี" / "มันคือหมี" -> จำเป็นของชิ้นหนึ่งใน .items.json, ตอบ "ไม่รู้" -> ทิ้งไป
#
# หน้าแซน (face.html + fly/mission.js, fly/explore.js) เป็นคนดูภาพและเลือกท่า แล้วขอให้ brain.py ขยับล้อทีละท่า
# ผ่าน /api/auto/move ส่วนไฟล์นี้ตัดสินว่ายอมให้ขยับไหม (ยังอยู่ในภารกิจ ไม่มีคนสั่งแทรก ท่าไม่ใหญ่เกิน)
# ภารกิจและการสำรวจจบทันทีเมื่อมีคำสั่งอื่น พูด "หยุด" หรือแตะจอ
import json
import os
import re
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, ".items.json")
MAX_ITEMS = 30
MAX_VECTORS = 40          # ลายนิ้วมือต่อของหนึ่งชิ้น
MAX_DIM = 2048
EXPLORE_ACTION = "เดินสำรวจ"   # ชื่อในสมุดคำชม/ตำหนิ
FIND_ACTION = "หาของ"

# ท่าที่ยอมให้ขยับเองได้: ไม่เกิน 4 ท่าต่อครั้ง เดินหน้า/ถอยไม่เกิน 40 ซม. หมุนไม่เกิน 180 องศา
AUTO_PROG = re.compile(r"^[FBLR]\d{1,3}( [FBLR]\d{1,3}){0,3}$")
LIMIT = {"F": 40, "B": 40, "L": 180, "R": 180}

POLITE = re.compile(r"(ให้หน่อย|หน่อย|ให้ที|ด้วย|ไว้|นะ|ครับ|ค่ะ|คะ|จ้ะ|จ้า|สิ|ที)+$")
TEACH = re.compile(r"^(?:ช่วย)?(?:จำของ|จำสิ่งของ|จดจำ|นี่คือ|นี่คือของ|นี่ชื่อ|รู้จักกับ)(?:ชื่อ)?(.+)$|^(?:ช่วย)?จำ(.+?)ไว้")
FIND = re.compile(r"^(?:ภารกิจ)?(?:ไป)?(?:ช่วย)?(?:ตามหา|ค้นหา|หา)(?!ย)(?:ของ)?(.+)$")
FORGET = re.compile(r"^ลืม(?:ของ)?(.+)$")
LIST = re.compile(r"รู้จัก(?:ของ)?อะไรบ้าง|จำ(?:ของ)?อะไร(?:ได้)?บ้าง|ของที่(?:รู้จัก|จำได้)")
EXPLORE = re.compile(r"^(?:ไป|ออก|เดิน)+สำรวจ|^สำรวจ")
STOP_EXPLORE = re.compile(r"(?:เลิก|ไม่ต้อง|พอ)สำรวจ")


def clean_name(s):
    s = POLITE.sub("", s.strip())
    return s if 0 < len(s) <= 20 else None


def check_vectors(vectors, th):
    """ลายนิ้วมือที่หน้าแซนส่งมา: คืน (vectors, th) ที่ตรวจแล้ว หรือ None ถ้าผิดรูป"""
    if not isinstance(vectors, list) or not 3 <= len(vectors) <= MAX_VECTORS:
        return None
    try:
        dim = len(vectors[0])
        vecs = [[round(float(x), 4) for x in v] for v in vectors]
        th = float(th)
    except (TypeError, ValueError):
        return None
    if not 0 < dim <= MAX_DIM or any(len(v) != dim for v in vecs) or not 0 < th < 1:
        return None
    return vecs, th


# ---------------------------------------------------------------- สมุดจำของ
class Items:
    lock = threading.Lock()
    data = None   # {ชื่อ: {"vectors": [[...], ...], "th": เกณฑ์, "at": เวลาสอน}}

    @classmethod
    def _load(cls):
        if cls.data is None:
            try:
                with open(STORE, encoding="utf-8") as f:
                    cls.data = json.load(f)
            except (OSError, ValueError):
                cls.data = {}
        return cls.data

    @classmethod
    def _save(cls):
        try:
            tmp = STORE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(cls.data, f, ensure_ascii=False)
            os.replace(tmp, STORE)
        except OSError:
            pass

    @classmethod
    def names(cls):
        with cls.lock:
            return list(cls._load())

    @classmethod
    def find(cls, spoken):
        """ชื่อที่ได้ยินอาจไม่ตรงเป๊ะ ("ตุ๊กตาหมี" กับ "หมี") เลือกชื่อที่ตรงที่สุด"""
        with cls.lock:
            names = list(cls._load())
        if spoken in names:
            return spoken
        close = [n for n in names if n in spoken or spoken in n]
        return max(close, key=len) if close else None

    @classmethod
    def get(cls, name):
        with cls.lock:
            return cls._load().get(name)

    @classmethod
    def put(cls, name, vectors, th, merge=False):
        """รับลายนิ้วมือจากหน้าแซน ตรวจรูปแบบก่อนเก็บ คืน None ถ้าข้อมูลผิด
        merge = รวมกับของชื่อเดิมที่มีอยู่ (ได้เห็นหลายมุมขึ้น) แทนการเขียนทับ"""
        name = clean_name(str(name))
        checked = check_vectors(vectors, th)
        if not name or not checked:
            return None
        vecs, th = checked
        with cls.lock:
            data = cls._load()
            if name not in data and len(data) >= MAX_ITEMS:
                return None
            old = data.get(name)
            if merge and old and len(old["vectors"][0]) == len(vecs[0]):
                vecs = (old["vectors"] + vecs)[-MAX_VECTORS:]
                th = (old["th"] + th) / 2
            data[name] = {"vectors": vecs, "th": round(th, 3), "at": round(time.time())}
            cls._save()
        return name

    @classmethod
    def forget(cls, name):
        with cls.lock:
            gone = cls._load().pop(name, None) is not None
            if gone:
                cls._save()
            return gone


# ---------------------------------------------------------------- ข้อสงสัย (ของที่แซนเจอเองแล้วยังไม่รู้ชื่อ)
MAX_WONDERS = 3
MAX_ASKS = 3          # ถามเรื่องเดิมได้กี่ครั้ง (ไม่มีใครตอบก็ลืมไป)
ANSWER_S = 60         # ถามแล้วรอคำตอบกี่วินาที
MAX_PHOTO = 200_000
DONT_KNOW = re.compile(r"ไม่รู้|ไม่ทราบ|ไม่บอก|ข้าม|ช่างมัน|ไม่ต้องจำ|ลืมไป|อะไรก็ได้")
ANSWER_LEAD = re.compile(r"^(?:อ๋อ|อ้อ|อันนั้น|อันนี้|นั่น|นี่|มัน|เขา)?(?:คือ|เป็น|เรียกว่า|ชื่อ|ชื่อว่า)?(?:ของ)?")


class Wonders:
    lock = threading.Lock()
    items = []        # [{id, vectors, th, photo, asks}]
    next_id = 1
    asking = None     # id ที่ถามอยู่
    asked_at = 0.0
    last = None       # เรื่องที่ถามครบแล้วถูกเอาออก แต่ยังรับคำตอบของการถามครั้งสุดท้ายได้

    @classmethod
    def add(cls, vectors, th, photo):
        checked = check_vectors(vectors, th)
        if not checked or not isinstance(photo, str) or not photo.startswith("data:image/jpeg;base64,") \
                or len(photo) > MAX_PHOTO:
            return None
        with cls.lock:
            cls.items = (cls.items + [{"id": cls.next_id, "vectors": checked[0], "th": checked[1],
                                       "photo": photo, "asks": 0}])[-MAX_WONDERS:]
            cls.next_id += 1
            return len(cls.items)

    @classmethod
    def pending(cls):
        return len(cls.items)

    @classmethod
    def next(cls):
        """ข้อสงสัยที่จะถามตอนนี้ (ถามน้อยครั้งที่สุดก่อน) แล้วจำว่ากำลังรอคำตอบ"""
        with cls.lock:
            if not cls.items:
                return None
            w = min(cls.items, key=lambda x: x["asks"])
            w["asks"] += 1
            cls.asking, cls.asked_at = w["id"], time.time()
            if w["asks"] >= MAX_ASKS:   # ถามครั้งสุดท้ายแล้ว ไม่มีใครตอบก็ลืม
                cls.items = [x for x in cls.items if x is not w]
                cls.last = w
            return {"id": w["id"], "photo": w["photo"]}

    @classmethod
    def answer(cls, text):
        """คำที่ได้ยินระหว่างรอคำตอบ: คืน reply dict หรือ None ถ้าไม่ได้รออยู่ / ไม่ใช่คำตอบ"""
        if cls.asking is None or time.time() - cls.asked_at > ANSWER_S:
            return None
        t = re.sub(r"\s", "", text)
        with cls.lock:
            w = next((x for x in cls.items if x["id"] == cls.asking), None)
            if w is None and cls.last and cls.last["id"] == cls.asking:
                w = cls.last
            cls.asking = None
            if w is not None:
                cls.items = [x for x in cls.items if x is not w]
        if w is None:
            return None
        if DONT_KNOW.search(t):
            return {"say": "ไม่เป็นไร งั้นแซนไม่จำอันนี้นะ", "emotion": "neutral", "wonderDone": True}
        name = clean_name(ANSWER_LEAD.sub("", t)) if len(t) <= 30 else None
        name = name and Items.put(name, w["vectors"], w["th"], merge=True)
        if not name:
            return {"say": "แซนฟังไม่ทัน ไว้ถามใหม่นะ", "emotion": "confused", "wonderDone": True}
        return {"say": f"อ๋อ นี่คือ{name}นี่เอง แซนจำไว้แล้ว", "emotion": "excited", "wonderDone": True, "learned": name}


# ---------------------------------------------------------------- ภารกิจ/สำรวจที่กำลังทำ
class Auto:
    kind = None       # None, "teach", "explore", "mission", "wonder"
    name = None
    started = 0.0

    @classmethod
    def start(cls, kind, name=None):
        cls.kind, cls.name, cls.started = kind, name, time.time()

    @classmethod
    def cancel(cls):
        cls.kind = cls.name = None


def parse(text):
    """คำสั่งภารกิจ/สำรวจ คืน dict สำหรับตอบหน้าแซน หรือ None ถ้าไม่ใช่"""
    t = re.sub(r"\s", "", text)
    if STOP_EXPLORE.search(t):
        was = Auto.kind == "explore"
        Auto.cancel()
        return {"say": "เลิกสำรวจแล้ว" if was else "ตอนนี้แซนไม่ได้สำรวจอยู่นะ", "emotion": "neutral", "autoStop": True}
    if LIST.search(t):
        names = Items.names()
        say = ("แซนรู้จัก " + " ".join(names)) if names else "แซนยังไม่รู้จักของอะไรเลย สอนแซนได้นะ บอกว่า จำของ แล้วตามด้วยชื่อ"
        return {"say": say, "emotion": "happy" if names else "neutral"}
    m = FORGET.match(t)
    if m:
        name = Items.find(clean_name(m.group(1)) or "")
        if name and Items.forget(name):
            return {"say": f"ลืม{name}แล้ว", "emotion": "neutral"}
        return {"say": "แซนไม่รู้จักของชื่อนี้อยู่แล้ว", "emotion": "confused"}
    m = TEACH.match(t)
    if m:
        name = clean_name(m.group(1) or m.group(2))
        if not name:
            return None
        Auto.start("teach", name)
        return {"say": f"ถือ{name}ให้แซนดูใกล้ ๆ หมุนให้ดูหลาย ๆ ด้านนะ", "emotion": "focus", "teach": name}
    m = FIND.match(t)
    if m:
        spoken = clean_name(m.group(1))
        if not spoken:
            return None
        name = Items.find(spoken)
        if not name:
            return {"say": f"แซนยังไม่รู้จัก{spoken} สอนแซนก่อนนะ บอกว่า จำของ{spoken}", "emotion": "confused"}
        item = Items.get(name)
        Auto.start("mission", name)
        return {"say": f"ได้เลย แซนจะออกตามหา{name}", "emotion": "excited",
                "mission": {"name": name, "vectors": item["vectors"], "th": item["th"]}}
    if EXPLORE.match(t):
        Auto.start("explore")
        return {"say": "ไปสำรวจกันเลย", "emotion": "excited", "explore": True}
    return None


def allow_move(kind, prog):
    """หน้าแซนขอขยับล้อระหว่างสำรวจ/ภารกิจ ท่านี้ทำได้ไหม คืน (ทำได้, เหตุผล)"""
    if kind not in ("explore", "mission", "wonder") or Auto.kind != kind:
        return False, "cancelled"
    if not isinstance(prog, str) or not AUTO_PROG.match(prog):
        return False, "bad"
    if any(int(step[1:]) > LIMIT[step[0]] for step in prog.split()):
        return False, "bad"
    return True, ""


def flip(prog):
    """สลับซ้าย/ขวา (ใช้เมื่อตั้ง FOLLOW_FLIP=1 เพราะรถหันกลับด้านกับภาพกล้อง)"""
    return prog.translate(str.maketrans("LR", "RL"))


if __name__ == "__main__":
    for s in ["จำของ หมี", "นี่คือ แก้วน้ำ ครับ", "จำตุ๊กตาไว้นะ", "หาหมี", "ไปหาตุ๊กตาหมีให้หน่อย", "หายไปไหน",
              "หันซ้าย", "ลืมหมี", "รู้จักของอะไรบ้าง", "ไปสำรวจ", "เลิกสำรวจ", "ภารกิจหาแก้วน้ำ"]:
        Auto.cancel()
        r = parse(s)
        print(f"{s!r:28} -> {r and {k: v for k, v in r.items() if k != 'mission'}}")
