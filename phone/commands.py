# commands.py : แปลงคำพูดภาษาไทยเป็นคำสั่งรถ (F/B/L/R/W แบบเดียวกับที่บอร์ดเข้าใจ)
# ไม่ต้องใช้ AI ทำงานทันที ใช้กับคำสั่งที่พูดบ่อย ๆ ถ้าไม่ตรงอะไรเลยจะคืน None ให้ AI คุยต่อ
import math
import re

THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
NUM_WORDS = {"ศูนย์": 0, "หนึ่ง": 1, "เอ็ด": 1, "สอง": 2, "ยี่": 2, "สาม": 3, "สี่": 4,
             "ห้า": 5, "หก": 6, "เจ็ด": 7, "แปด": 8, "เก้า": 9}
MULTS = {"สิบ": 10, "ร้อย": 100, "พัน": 1000}
NUM_RUN = re.compile("(?:" + "|".join(list(NUM_WORDS) + list(MULTS)) + ")+")
NUM_TOKEN = re.compile("|".join(list(NUM_WORDS) + list(MULTS)))

SHAPES = {"หัวใจ": "heart", "วงกลม": "circle", "สี่เหลี่ยม": "square",
          "สามเหลี่ยม": "triangle", "ดาว": "star"}
SHAPE_NAMES = {"heart": "รูปหัวใจ", "circle": "วงกลม", "square": "สี่เหลี่ยม",
               "triangle": "สามเหลี่ยม", "star": "รูปดาว"}


def thai_words_to_int(run):
    total = cur = 0
    for tok in NUM_TOKEN.findall(run):
        if tok in NUM_WORDS:
            cur = NUM_WORDS[tok]
        else:
            total += (cur or 1) * MULTS[tok]
            cur = 0
    return total + cur


def find_number(text):
    """หาตัวเลขตัวแรกในประโยค รองรับทั้ง 30, ๓๐ และ สามสิบ"""
    m = re.search(r"\d+(?:\.\d+)?", text)
    if m:
        return float(m.group())
    m = NUM_RUN.search(text)
    if m:
        return float(thai_words_to_int(m.group()))
    return None


def to_cm(text, default):
    n = find_number(text)
    if n is None:
        return default
    if "เมตร" in text and not re.search("เซนติเมตร|มิลลิเมตร", text):
        n *= 100
    return n


def fmt(v):
    return str(int(v)) if abs(v - round(v)) < 0.05 else f"{v:.1f}"


def join_program(cmds):
    """รวมคำสั่งเลี้ยวที่ติดกัน เช่น R7.5 R7.5 -> R15 ให้โปรแกรมสั้นลง"""
    out = []
    for op, v in cmds:
        if out and out[-1][0] == op and op in "LR":
            out[-1] = (op, out[-1][1] + v)
        else:
            out.append((op, v))
    return " ".join(op + fmt(v) for op, v in out if v > 0)


def arc_right(radius, degrees, steps_per_90=6):
    steps = max(2, round(degrees / 90 * steps_per_90))
    turn = degrees / steps
    seg = 2 * radius * math.sin(math.radians(turn / 2))
    cmds = []
    for _ in range(steps):
        cmds += [("R", turn / 2), ("F", seg), ("R", turn / 2)]
    return cmds


def shape_program(shape, size):
    s = size
    if shape == "square":
        cmds = [("F", s), ("R", 90)] * 4
    elif shape == "triangle":
        cmds = [("F", s), ("R", 120)] * 3
    elif shape == "star":
        cmds = [("F", s), ("R", 144)] * 5
    elif shape == "circle":
        cmds = arc_right(s / 2, 360)
    else:  # heart : เริ่มที่ปลายแหลมด้านล่าง หันหน้าขึ้น
        cmds = [("L", 45), ("F", s)] + arc_right(s / 2, 180) + [("L", 90)] \
            + arc_right(s / 2, 180) + [("F", s), ("R", 135)]
    return join_program(cmds)


# คำที่ระบบฟังเสียงของ Google ฟังผิดบ่อย (เจอจาก brain.log จริง)
MISHEARD = {"เดือนหน้า": "เดินหน้า", "เดินน่า": "เดินหน้า", "เลี่ยว": "เลี้ยว", "เรียวซ้าย": "เลี้ยวซ้าย",
            "เรียวขวา": "เลี้ยวขวา", "ถอยหลังง": "ถอยหลัง"}

DANCE = "L30 R60 L60 R30 F8 B8 R180 L180 F8 B8 L360"


def parse(text):
    """คืน dict {prog, say, emotion} หรือ {stop: True, ...} หรือ None ถ้าไม่ใช่คำสั่งรถ"""
    t = text.translate(THAI_DIGITS).replace(" ", "").lower()
    for wrong, right in MISHEARD.items():
        t = t.replace(wrong, right)

    if re.search("หยุด|เบรก|พอแล้ว|stop", t):
        return {"stop": True, "say": "หยุดแล้ว", "emotion": "neutral"}

    for word, shape in SHAPES.items():
        if word in t and re.search("วาด|วิ่ง|เดิน|ทำ|เป็นรูป|หมุน", t):
            size = to_cm(t.replace(word, ""), 30)
            size = min(max(size, 10), 150)
            return {"prog": shape_program(shape, size), "emotion": "happy",
                    "say": f"ได้เลย จะวิ่งเป็น{SHAPE_NAMES[shape]} ขนาด {fmt(size)} เซนติเมตร"}

    if re.search("ตามฉัน|ตามมา|ตามหน้า|ตามหนู|ตามเรา|ตามผม|ตามเค้า|ตามไป|follow", t):
        return {"follow": True, "say": "ได้เลย แซนจะตามไปนะ", "emotion": "happy"}

    if "เต้น" in t:
        return {"prog": DANCE, "say": "ดูท่าเต้นนะ", "emotion": "happy"}

    if re.search("กลับหลังหัน|หันหลัง", t):
        return {"prog": "R180", "say": "กลับหลังหัน", "emotion": "neutral"}
    if re.search("หมุนรอบ|หมุนตัว", t):
        return {"prog": "R360", "say": "หมุนหนึ่งรอบ", "emotion": "happy"}

    if "ถอย" in t:
        cm = min(to_cm(t, 20), 300)
        return {"prog": f"B{fmt(cm)}", "say": f"ถอยหลัง {fmt(cm)} เซนติเมตร", "emotion": "neutral"}
    turn = re.search("(เลี้ยว|หัน|หมุน|ไป)(ทาง)?(ซ้าย|ขวา)", t)
    if turn:
        deg = find_number(t) or 90
        deg = min(deg, 720)
        left = turn.group(3) == "ซ้าย"
        return {"prog": f"{'L' if left else 'R'}{fmt(deg)}", "emotion": "neutral",
                "say": f"เลี้ยว{turn.group(3)} {fmt(deg)} องศา"}

    # เช็กหลังเลี้ยว เพราะ "ไปทางซ้าย" ก็มีคำว่า ไป
    if re.search("เดิน|วิ่ง|ข้างหน้า|ไปหน้า|ตรงไป|ไปเลย|ออกตัว|มานี่|มาหา|^ไป$|^หน้า$|go", t):
        cm = min(to_cm(t, 30), 300)
        return {"prog": f"F{fmt(cm)}", "say": f"เดินหน้า {fmt(cm)} เซนติเมตร", "emotion": "happy"}

    return None


if __name__ == "__main__":
    for s in ["เดินหน้า 50 เซนติเมตร", "ถอยหลังหนึ่งเมตร", "เลี้ยวซ้าย", "หันขวา 45 องศา",
              "วิ่งเป็นรูปหัวใจ", "วาดสี่เหลี่ยม 40", "วาดวงกลมขนาดหกสิบ", "เต้นหน่อย",
              "หยุด", "วันนี้อากาศดีไหม", "เดินหน้า สองร้อยห้าสิบ"]:
        print(f"{s!r:30} -> {parse(s)}")
