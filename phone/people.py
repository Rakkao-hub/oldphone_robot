# people.py : จำหน้าและชื่อคน (Python ล้วน)
#
#   เจอหน้าคนที่ไม่รู้จัก -> หน้าแซนถาม "ชื่ออะไรเหรอ" -> ตอบ "ต้น" / "ผมชื่อต้น" -> จำหน้าคู่กับชื่อ
#   เจอหน้าคนที่รู้จัก   -> "สวัสดีต้น" (หน้าแซนเทียบเอง ไม่ทักคนเดิมซ้ำบ่อย ๆ)
#   "ผมชื่อต้น" / "หนูชื่อมิว" (ตอนแซนเห็นหน้า) -> จำหน้าคนที่อยู่ตรงหน้าตอนนั้นเลย (ใช้สอนเพิ่มหรือแก้ชื่อผิดได้)
#   "แซนรู้จักใครบ้าง" / "ลืมหน้าต้น"
#
# ลายนิ้วมือหน้า = ตัวเลข 128 ตัวจาก face-api (คำนวณใน Chrome) เก็บในไฟล์ .people.json บนมือถือเครื่องนี้เท่านั้น
import json
import os
import re
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, ".people.json")
MAX_PEOPLE = 20
MAX_VECTORS = 24
DIM = 128
ANSWER_S = 60

POLITE = re.compile(r"(ครับผม|ครับ|ค่ะ|คะ|นะ|จ้ะ|จ้า|จ๊ะ|น้า|ไง|แหละ|เอง)+$")
INTRO = re.compile(r"^(?:สวัสดี)?(?:ผม|ฉัน|หนู|เรา|กู|ข้า|พี่|น้อง|ดิฉัน|เค้า|เขา)?(?:ชื่อ|ชื่อว่า|คือ)(.+)$")
NO_TELL = re.compile(r"ไม่บอก|ความลับ|ไม่อยากบอก|ข้าม|ไม่ต้องจำ")
LIST = re.compile(r"รู้จักใครบ้าง|จำใครได้บ้าง|จำหน้าใครได้บ้าง")
FORGET = re.compile(r"^ลืมหน้า(.+)$")


def clean_name(s):
    s = POLITE.sub("", s.strip())
    return s if 0 < len(s) <= 20 else None


def check_vectors(vectors):
    if not isinstance(vectors, list) or not 1 <= len(vectors) <= MAX_VECTORS:
        return None
    try:
        vecs = [[round(float(x), 5) for x in v] for v in vectors]
    except (TypeError, ValueError):
        return None
    return vecs if all(len(v) == DIM for v in vecs) else None


class People:
    lock = threading.Lock()
    data = None   # {ชื่อ: {"vectors": [[128 ตัว], ...], "at": เวลาเจอล่าสุด}}

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
    def all(cls):
        with cls.lock:
            return {n: p["vectors"] for n, p in cls._load().items()}

    @classmethod
    def put(cls, name, vectors):
        """จำหน้า (รวมกับหน้าที่จำไว้แล้วของชื่อเดิม ได้หลายมุมขึ้น) คืนชื่อ หรือ None ถ้าข้อมูลผิด/เต็ม"""
        name, vecs = clean_name(str(name or "")), check_vectors(vectors)
        if not name or not vecs:
            return None
        with cls.lock:
            data = cls._load()
            if name not in data and len(data) >= MAX_PEOPLE:
                return None
            old = data.get(name, {}).get("vectors", [])
            data[name] = {"vectors": (old + vecs)[-MAX_VECTORS:], "at": round(time.time())}
            cls._save()
        return name

    @classmethod
    def find(cls, spoken):
        with cls.lock:
            names = list(cls._load())
        if spoken in names:
            return spoken
        close = [n for n in names if n in spoken or spoken in n]
        return max(close, key=len) if close else None

    @classmethod
    def forget(cls, name):
        with cls.lock:
            gone = cls._load().pop(name, None) is not None
            if gone:
                cls._save()
            return gone


class Ask:
    """แซนเพิ่งถามชื่อคนแปลกหน้า: เก็บหน้าไว้รอคำตอบ"""
    vectors = None
    at = 0.0

    @classmethod
    def start(cls, vectors):
        vecs = check_vectors(vectors)
        if vecs:
            cls.vectors, cls.at = vecs, time.time()
        return bool(vecs)

    @classmethod
    def answer(cls, text):
        """คำที่ได้ยินระหว่างรอชื่อ (ที่ไม่ใช่คำสั่ง): คืน reply dict หรือ None"""
        if cls.vectors is None or time.time() - cls.at > ANSWER_S:
            return None
        t = re.sub(r"\s", "", text)
        vecs, cls.vectors = cls.vectors, None
        if NO_TELL.search(t):
            return {"say": "ไม่เป็นไร ไว้ค่อยบอกก็ได้", "emotion": "shy", "personDone": True}
        m = INTRO.match(t)
        name = clean_name(m.group(1) if m else t) if len(t) <= 25 else None
        name = name and People.put(name, vecs)
        if not name:
            return {"say": "แซนฟังไม่ทัน ไว้ถามใหม่นะ", "emotion": "confused", "personDone": True}
        return {"say": f"ยินดีที่ได้รู้จักนะ {name}", "emotion": "love", "personDone": True, "met": name}


def parse(text):
    """คำสั่งเรื่องคน คืน reply dict หรือ None"""
    t = re.sub(r"\s", "", text)
    if LIST.search(t):
        names = list(People.all())
        return {"say": ("แซนรู้จัก " + " ".join(names)) if names else "แซนยังไม่รู้จักใครเลย มาแนะนำตัวกันหน่อยสิ",
                "emotion": "happy"}
    m = FORGET.match(t)
    if m:
        name = People.find(clean_name(m.group(1)) or "")
        if name and People.forget(name):
            return {"say": f"ลืมหน้า{name}แล้ว", "emotion": "neutral"}
        return {"say": "แซนไม่รู้จักคนชื่อนี้อยู่แล้ว", "emotion": "confused"}
    m = INTRO.match(t)
    if m and re.match(r"^(?:สวัสดี)?(?:ผม|ฉัน|หนู|เรา|กู|ข้า|พี่|น้อง|ดิฉัน|เค้า)", t):   # แนะนำตัวเอง ไม่ใช่ "นี่คือ..."
        name = clean_name(m.group(1))
        if name:   # หน้าแซนจับหน้าคนตรงหน้าแล้วส่งมาที่ /api/people
            return {"say": f"สวัสดี{name} ขอดูหน้าใกล้ ๆ หน่อยนะ", "emotion": "happy", "learnFace": name}
    return None


if __name__ == "__main__":
    for s in ["ผมชื่อต้น", "หนู ชื่อ มิว ค่ะ", "ฉันชื่อแม่", "แซนรู้จักใครบ้าง", "ลืมหน้าต้น", "นี่คือหมี", "ชื่ออะไร", "เดินหน้า"]:
        print(f"{s!r:22} -> {parse(s)}")
    Ask.vectors, Ask.at = [[0.0] * DIM], time.time()
    print("ตอบชื่อ 'ผมชื่อต้นครับ' ->", {k: v for k, v in (Ask.answer("ผมชื่อต้นครับ") or {}).items() if k != "say"})
