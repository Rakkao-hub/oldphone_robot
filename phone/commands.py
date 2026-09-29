# commands.py : แปลงคำพูดภาษาไทยเป็นคำสั่งรถ (F/B/L/R/W แบบเดียวกับที่บอร์ดเข้าใจ)
# ไม่ต้องใช้ AI ทำงานทันที ใช้กับคำสั่งที่พูดบ่อย ๆ ถ้าไม่ตรงอะไรเลยจะคืน None ให้ AI คุยต่อ
import math
import random
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
    total = cu = 0
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

# ประโยคที่แซนพูดตอบ เขียนแบบภาษาพูดและสุ่มให้ไม่ซ้ำทุกครั้ง ({n} = ตัวเลข)
# คำลงท้าย ครับ/ค่ะ brain.py เติมให้เองตามเสียงที่เลือก จึงไม่ต้องใส่ในนี้
SAY = {
    "stop":     ["หยุดแล้ว", "โอเค หยุดแล้ว", "เบรกแล้ว"],
    "forward":  ["เดินหน้า {n} เซน", "ไปข้างหน้า {n} เซนนะ", "โอเค เดินหน้า {n} เซน"],
    "back":     ["ถอยหลัง {n} เซน", "ถอยให้ {n} เซนนะ", "โอเค ถอยหลัง {n} เซน"],
    "turn":     ["เลี้ยว{dir}", "หัน{dir}นะ", "โอเค เลี้ยว{dir}"],
    "turn_deg": ["เลี้ยว{dir} {n} องศา", "หัน{dir} {n} องศานะ"],
    "shape":    ["ได้เลย ดูแซนวาด{shape}นะ", "จัดไป วิ่งเป็น{shape}", "ได้เลย เดี๋ยววาด{shape}ให้ดู"],
    "follow":   ["ได้เลย แซนจะหันหน้าตามนะ", "โอเค เดินไปทางไหน แซนจะหันตาม"],
    "dance":    ["ดูท่าเต้นนะ", "เอาล่ะ แซนจะเต้นแล้วนะ", "จัดไป ท่าเต้นพิเศษ"],
    "about":    ["กลับหลังหัน", "หันหลังแล้วนะ"],
    "spin":     ["หมุน {n} รอบ", "หมุนติ้ว {n} รอบเลย"],
    "still":    ["อยู่นิ่ง {n} วินาที", "โอเค แซนจะนิ่ง {n} วินาที"],
}


# โหมดอุทาน: เล่นเสียงที่กำหนดไว้
#   ถ้ามีไฟล์ phone/sounds/<ชื่อ>.mp3 (หรือ .wav .ogg .m4a) แซนจะเล่นไฟล์นั้น
#   ถ้ายังไม่มีไฟล์ แซนพูดคำใน "say" ด้วยเสียงตัวเองแทน
#   เพิ่มเสียงใหม่: เพิ่มบรรทัดในนี้ + วางไฟล์ชื่อเดียวกันใน phone/sounds/
#   words = คำที่ใช้เรียก เช่น "อุทานว้าว" / "ทำเสียงเย้"
EXCLAIMS = {
    "wow":  {"words": "ว้าว|โอ้โห|โห", "say": "ว้าววว", "emotion": "surprised"},
    "yay":  {"words": "เย้|ไชโย", "say": "เย้ เย้", "emotion": "happy"},
    "oops": {"words": "อุ๊ย|โอ๊ะ|ตายแล้ว", "say": "อุ๊ย", "emotion": "surprised"},
    "hmm":  {"words": "หืม|อืม|งง", "say": "หืมมม", "emotion": "confused"},
    "aww":  {"words": "โธ่|เสียดาย|เศร้า", "say": "โธ่ เสียดายจัง", "emotion": "sad"},
    "haha": {"words": "หัวเราะ|ฮ่า|ฮา|555|ขำ", "say": "ฮา ฮา ฮา", "emotion": "happy"},
    "ahhh": {"words": "อ่า|อ้า|อา", "say": "อ่า", "emotion": "surprised"},
    "sing": {"words": "ร้องเพลง|เพลง", "say": "ลา ลา ลา", "emotion": "happy"},
}


def exclaim(key=None, t=""):
    """คืนคำสั่งอุทาน: ระบุชื่อ (key) / หาจากคำในประโยค (t) / ไม่เจอก็สุ่ม"""
    if key not in EXCLAIMS:
        key = next((k for k, e in EXCLAIMS.items() if re.search(e["words"], t)), None) or random.choice(list(EXCLAIMS))
    e = EXCLAIMS[key]
    return {"exclaim": key, "say": e["say"], "emotion": e["emotion"]}


def say(kind, **kw):
    return random.choice(SAY[kind]).format(**kw)


DANCE = "L30 R60 L60 R30 F8 B8 R180 L180 F8 B8 L360"
MAX_STILL = 30  # บอร์ดรับ W ได้สูงสุด 30000 มิลลิวินาที


def still(sec):
    """อยู่นิ่ง sec วินาที -> คำสั่งบอร์ด W<มิลลิวินาที> เช่น still(1.5) = "W1500" """
    return f"W{round(min(max(sec, 0.1), MAX_STILL) * 1000)}"


def intro_script():
    """สคริปต์แนะนำตัว: แต่ละท่อน = (ประโยคที่พูด, สีหน้า, ท่าขยับ)
    แซนพูดไปพร้อมขยับ พอพูดจบและขยับเสร็จทั้งคู่ค่อยขึ้นท่อนถัดไป
    แก้/เพิ่มท่อนได้ตามใจ (คำลงท้าย ครับ/ค่ะ brain.py เติมให้เอง)

    ท่าขยับ: F<ซม.> B<ซม.> L<องศา> R<องศา> ต่อกันด้วยช่องว่าง
    จังหวะอยู่นิ่ง: still(วินาที) เช่น "F10 " + still(1) + " B10" = เดินหน้า นิ่ง 1 วิ แล้วถอย
    ท่อนเงียบ:     ("", "happy", still(2))  = ไม่พูด อยู่นิ่ง 2 วิ
    ท่อนอุทาน:     ("!wow", "surprised", "")  = เล่นเสียงอุทาน wow (ชื่อจาก EXCLAIMS ด้านบน)
    ไม่ขยับเลย:     ใส่ท่าขยับเป็น "" """
    return [
        ("อ่าาาาาาาาาาาาา", "happy", "L25 R50 L50 R25"),
        ("", "happy", still(1)),  # เว้นจังหวะให้คนฟังทักกลับ
        ("แซนเป็นหุ่นยนต์รถคันเล็ก ที่มีมือถือเป็นสมองและหน้าตา", "neutral", "F15 " + still(1) + " B15"),
        ("แซนฟังคำสั่งเสียงภาษาไทยได้ ทั้งเดินหน้า ถอยหลัง เลี้ยวซ้าย เลี้ยวขวา", "listening", "F10 B10 L90 R180 L90"),
        ("วาดรูปบนพื้นได้ด้วย อย่างรูปดาวแบบนี้", "happy", shape_program("star", 25)),
        ("ถ้าบอกว่าตามมา แซนจะหันหน้าตามคุณไปเลย", "happy", "R360"),
        ("ยินดีที่ได้รู้จักนะ", "happy", "F6 " + still(0.3) + " B6"),
    ]


def parse(text):
    """คืน dict {prog, say, emotion} หรือ {stop: True, ...} หรือ None ถ้าไม่ใช่คำสั่งรถ"""
    t = text.translate(THAI_DIGITS).replace(" ", "").lower()
    for wrong, right in MISHEARD.items():
        t = t.replace(wrong, right)

    if re.search("หยุด|เบรก|พอแล้ว|stop", t):
        return {"stop": True, "say": say("stop"), "emotion": "neutral"}

    for word, shape in SHAPES.items():
        if word in t and re.search("วาด|วิ่ง|เดิน|ทำ|เป็นรูป|หมุน", t):
            size = to_cm(t.replace(word, ""), 30)
            size = min(max(size, 10), 150)
            return {"prog": shape_program(shape, size), "emotion": "happy",
                    "say": say("shape", shape=SHAPE_NAMES[shape])}

    if re.search("อุทาน|ทำเสียง|หัวเราะ|ร้องเพลง", t):
        return exclaim(t=re.sub("อุทาน|ทำเสียง", "", t))
    if re.search("ผิวปาก|พริ้วปาก|หวีด|whistle", t):
        return {"sound": {"type": "whistle"}, "say": "", "emotion": "happy"}

    # จับเฉพาะรูปที่เป็นคำสั่งจริง: "รอ" ต้องขึ้นต้นประโยคหรือตามด้วยตัวเลข/ก่อน/แป๊บ
    # ไม่งั้น "รอบ", "รองรับ", "ขอบคุณรอ..." ในประโยคทั่วไปจะกลายเป็นคำสั่งอยู่นิ่ง
    wait = re.search(r"อยู่นิ่ง|นิ่งๆ|^นิ่ง|^รอ(?!บ|ง)|รอก่อน|รอแป๊บ|รอสัก|รอ\d|^พัก|พักก่อน|พัก\d", t)
    if wait:
        sec = min(find_number(t) or 3, MAX_STILL)
        if "นาที" in t and "วินาที" not in t:
            sec = MAX_STILL
        return {"prog": still(sec), "say": say("still", n=fmt(sec)), "emotion": "neutral"}

    if re.search("แนะนำตัว|เป็นใคร|ชื่ออะไร|คือใคร", t):
        return {"script": intro_script(), "say": "", "emotion": "happy"}

    if re.search("ตามฉัน|ตามมา|ตามหน้า|ตามหนู|ตามเรา|ตามผม|ตามเค้า|ตามไป|หันตาม|มองตาม|follow", t):
        return {"follow": True, "say": say("follow"), "emotion": "happy"}

    if "เต้น" in t:
        return {"prog": DANCE, "say": say("dance"), "emotion": "happy", "music": "dance"}

    if re.search("กลับหลังหัน|หันหลัง", t):
        return {"prog": "R180", "say": say("about"), "emotion": "neutral"}
    spin = re.search("หมุน.*รอบ|หมุนตัว", t)
    if spin:
        n = int(min(max(find_number(t) or 1, 1), 3))
        return {"prog": f"R{360 * n}", "say": say("spin", n=n), "emotion": "happy"}

    if "ถอย" in t:
        cm = min(to_cm(t, 20), 300)
        return {"prog": f"B{fmt(cm)}", "say": say("back", n=fmt(cm)), "emotion": "neutral"}
    turn = re.search("(เลี้ยว|หัน|หมุน|ไป|^)(ทาง)?(ซ้าย|ขวา)", t)
    if turn:
        n = find_number(t)
        deg = min(n or 90, 720)
        left = turn.group(3) == "ซ้าย"
        return {"prog": f"{'L' if left else 'R'}{fmt(deg)}", "emotion": "neutral",
                "say": say("turn_deg", dir=turn.group(3), n=fmt(deg)) if n else say("turn", dir=turn.group(3))}

    # เช็กหลังเลี้ยว เพราะ "ไปทางซ้าย" ก็มีคำว่า ไป
    if re.search("เดิน|วิ่ง|ข้างหน้า|ไปหน้า|ตรงไป|ไปเลย|ออกตัว|มานี่|มาหา|^ไป$|^หน้า$|go", t):
        cm = min(to_cm(t, 30), 300)
        return {"prog": f"F{fmt(cm)}", "say": say("forward", n=fmt(cm)), "emotion": "happy"}

    return None


if __name__ == "__main__":
    for s in ["เดินหน้า 50 เซนติเมตร", "ถอยหลังหนึ่งเมตร", "เลี้ยวซ้าย", "หันขวา 45 องศา",
              "วิ่งเป็นรูปหัวใจ", "วาดสี่เหลี่ยม 40", "วาดวงกลมขนาดหกสิบ", "เต้นหน่อย",
              "หยุด", "วันนี้อากาศดีไหม", "เดินหน้า สองร้อยห้าสิบ"]:
        print(f"{s!r:30} -> {parse(s)}")
