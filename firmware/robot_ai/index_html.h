// index_html.h : หน้าเว็บควบคุมหุ่นยนต์ (บอร์ดเสิร์ฟเองที่ http://robot.local)
// ต้องอยู่ในโฟลเดอร์เดียวกับ robot_ai.ino
// แก้หน้าตาหรือคำสั่งของ AI ได้ในไฟล์นี้โดยตรง ด้านล่างเป็น HTML ธรรมดาทั้งก้อน
// แก้เสร็จแล้วอัปโหลดใหม่ตามปกติ
#pragma once
#include <Arduino.h>

const char INDEX_HTML[] PROGMEM = R"HTML(<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#E8EBE7">
<title>หุ่นยนต์วาดรูป</title>
<link rel="icon" href="data:,">
<!-- โหลดฟอนต์แบบไม่บล็อกหน้า ถ้าไม่มีเน็ต (โหมด Robot-AI) จะใช้ฟอนต์ในเครื่องแทน -->
<link rel="stylesheet" media="print" onload="this.media='all'" href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;600;700&display=swap">
<style>
:root {
  --board: #E8EBE7;       /* ตัวเบรดบอร์ด */
  --sheet: #F8F9F7;       /* พื้นช่องกรอก และพื้นภาพจำลอง */
  --ink: #1E2529;
  --soft: #56626A;
  --hole: #C3CAC6;        /* รูเบรดบอร์ด และเส้นขอบ */
  --motor: #F5C400;       /* สีมอเตอร์ TT */
  --motor-edge: #A88600;
  --red: #D2323A;         /* สีบอร์ด L298N และราง + */
  --red-edge: #8C1D23;
  --blue: #2D5BA6;        /* ราง - ของเบรดบอร์ด */
  --font: "Chakra Petch", "Sukhumvit Set", "Thonburi", "Noto Sans Thai", "Leelawadee UI", system-ui, sans-serif;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  color-scheme: light;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0; background: var(--board); color: var(--ink);
  font: 400 16px/1.55 var(--font);
  padding-bottom: calc(96px + env(safe-area-inset-bottom));
}
button, input, select, textarea { font: inherit; color: inherit; }
h1, h2, h3 { margin: 0; font-weight: 600; line-height: 1.25; }
h2 { font-size: 20px; }
h3 { font-size: 16px; }
p { margin: 0; }
[hidden] { display: none !important; }
:focus-visible { outline: 2.5px solid var(--blue); outline-offset: 2px; }

.wrap { max-width: 1120px; margin: 0 auto; padding: 0 18px; }
.top { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding-top: 14px; }
.brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 17px; }
.conn { display: flex; align-items: center; gap: 8px; font-size: 14px; color: var(--soft); text-align: right; }
.led { width: 10px; height: 10px; border-radius: 50%; flex: none; background: var(--hole); box-shadow: 0 0 0 3px rgba(30, 37, 41, .08); }
.conn.ok .led { background: var(--blue); }
.conn.ap .led { background: var(--motor); }
.conn.off .led { background: var(--red); }

/* รางไฟแบบเบรดบอร์ด (เส้นแดง แถวรู เส้นน้ำเงิน) ใช้คั่นแต่ละส่วน */
.rail {
  height: 14px; margin: 10px 0 18px;
  background:
    linear-gradient(var(--red), var(--red)) left top / 100% 2px no-repeat,
    linear-gradient(var(--blue), var(--blue)) left bottom / 100% 2px no-repeat,
    linear-gradient(90deg, var(--hole) 3px, transparent 3px) 4px center / 12px 3px repeat-x;
}
.warn .key { margin-top: 10px; }
.warn { background: #FFF1BF; border: 1.5px solid var(--motor-edge); border-radius: 6px; padding: 10px 14px; font-size: 15px; margin-bottom: 16px; }

.cols { display: grid; gap: 0 44px; }
@media (min-width: 940px) {
  .cols { grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr); }
  /* จอกว้าง: คอลัมน์ขวา (บังคับเอง/ตั้งค่า) ค้างอยู่บนจอ */
  .side { position: sticky; top: 8px; align-self: start; max-height: calc(100vh - 104px); overflow-y: auto; padding-right: 6px; }
}
section { padding-bottom: 28px; }

/* ช่องพิมพ์คำสั่ง (ส่วนหลักของหน้า) */
.ask-label { display: block; font-size: clamp(26px, 7vw, 34px); font-weight: 600; line-height: 1.18; margin: 2px 0 14px; }
input[type=text], input[type=password], input[type=number], input:not([type]), select, textarea {
  width: 100%; min-width: 0; background: var(--sheet);
  border: 1.5px solid var(--hole); border-radius: 6px; padding: 10px 12px;
}
input:focus, select:focus, textarea:focus { outline: none; border-color: var(--blue); box-shadow: 0 0 0 3px rgba(45, 91, 166, .18); }
#ask { min-height: 86px; resize: vertical; font-size: 20px; line-height: 1.4; padding: 14px 16px; border: 2px solid var(--ink); border-radius: 8px; }
#ask:focus { border-color: var(--ink); box-shadow: 0 0 0 4px rgba(245, 196, 0, .5); }
input[type=range] { width: 100%; margin: 0; accent-color: var(--ink); }

.chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0 18px; }
.chip { border: 1.5px solid var(--hole); background: var(--sheet); border-radius: 999px; padding: 5px 14px; font-size: 15px; cursor: pointer; }
.chip:hover { border-color: var(--ink); }
.slide { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 12px; margin: 8px 0 2px; }
.slide output { min-width: 64px; text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }
.hint { font-size: 14px; color: var(--soft); margin: 6px 0; }
.row { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin: 14px 0; }
.row.tight { flex-wrap: nowrap; margin: 8px 0; }

/* ปุ่มแบบปุ่มกด มีขอบล่างให้รู้สึกว่ากดลงไปได้ */
.key {
  font-weight: 600; font-size: 17px; line-height: 1.1; color: var(--ink);
  background: var(--motor); border: 0; border-radius: 10px; padding: 14px 20px;
  box-shadow: 0 3px 0 var(--motor-edge); cursor: pointer; white-space: nowrap;
  touch-action: manipulation; -webkit-tap-highlight-color: transparent;
}
.key:active, .key.on { transform: translateY(2px); box-shadow: 0 1px 0 var(--motor-edge); }
.key:disabled { opacity: .45; cursor: not-allowed; transform: none; }
.key.ghost { background: var(--sheet); border: 1.5px solid var(--hole); box-shadow: 0 3px 0 var(--hole); padding: 12.5px 18.5px; }
.key.ghost:active, .key.ghost.on { box-shadow: 0 1px 0 var(--hole); }
.key.stop { background: var(--red); color: #fff; box-shadow: 0 3px 0 var(--red-edge); }
.key.stop:active { box-shadow: 0 1px 0 var(--red-edge); }
.key.small { font-size: 15px; padding: 10px 14px; border-radius: 8px; }
.key.ghost.small { padding: 8.5px 12.5px; }
.notice { margin: 10px 0 0; font-size: 15px; }
.notice.bad { color: var(--red); }

/* เส้นทาง */
.route-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 2px 14px; margin-bottom: 10px; }
.meta { font-size: 14px; color: var(--soft); }
.ai-note { background: var(--sheet); border-left: 4px solid var(--motor); border-radius: 0 6px 6px 0; padding: 10px 14px; margin-bottom: 12px; }
.stage { position: relative; background: var(--sheet); border: 1.5px solid var(--hole); border-radius: 8px; overflow: hidden; }
#cv { display: block; width: 100%; height: min(86vw, 60vh, 470px); }
.empty { position: absolute; left: 0; right: 0; bottom: 0; padding: 14px 16px; font-size: 15px; color: var(--soft); }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(96px, 1fr)); gap: 10px 16px; margin: 14px 0 0; }
.stats dt { font-size: 13px; color: var(--soft); }
.stats dd { margin: 0; font-size: 18px; font-weight: 600; font-variant-numeric: tabular-nums; }
.stats dd.bad { color: var(--red); }
.refine label { display: block; font-weight: 600; margin: 4px 0 2px; }
.presets { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 6px 0 16px; }
.presets span { font-size: 14px; color: var(--soft); margin-right: 4px; }
.code summary { cursor: pointer; font-weight: 600; padding: 4px 0 8px; }
#cmds { font-family: var(--mono); font-size: 14px; line-height: 1.5; resize: vertical; }

/* บังคับเอง */
.pad { display: grid; grid-template-columns: repeat(3, 78px); grid-template-rows: repeat(3, 78px); gap: 10px; justify-content: center; margin: 16px 0 18px; }
.pad .key { padding: 0; display: grid; place-items: center; border-radius: 14px; user-select: none; -webkit-user-select: none; -webkit-touch-callout: none; touch-action: none; }
.pad .f { grid-area: 1 / 2; }
.pad .l { grid-area: 2 / 1; }
.pad .s { grid-area: 2 / 2; font-size: 16px; }
.pad .r { grid-area: 2 / 3; }
.pad .b { grid-area: 3 / 2; }
.pad .r svg { transform: scaleX(-1); }

/* แผงตั้งค่า */
details.panel > summary { list-style: none; cursor: pointer; display: flex; align-items: center; justify-content: space-between; gap: 12px; font-size: 20px; font-weight: 600; padding: 2px 0 12px; }
details.panel > summary::-webkit-details-marker { display: none; }
details.panel > summary::after { content: ""; width: 10px; height: 10px; margin-right: 6px; border-right: 2.5px solid var(--ink); border-bottom: 2.5px solid var(--ink); transform: rotate(45deg); transition: transform .2s; }
details.panel[open] > summary::after { transform: rotate(-135deg); }
ol.steps { list-style: none; counter-reset: s; padding: 0; margin: 4px 0 0; }
ol.steps > li { counter-increment: s; position: relative; padding: 0 0 22px 42px; }
ol.steps > li::before { content: counter(s); position: absolute; left: 0; top: -2px; width: 28px; height: 28px; display: grid; place-items: center; border: 2px solid var(--ink); border-radius: 5px; font-weight: 700; font-size: 14px; }
ol.steps p { font-size: 15px; margin: 4px 0 6px; }
.sw { display: flex; align-items: center; gap: 12px; padding: 5px 0; cursor: pointer; }
.sw input { appearance: none; -webkit-appearance: none; flex: none; width: 46px; height: 26px; margin: 0; border-radius: 13px; background: var(--hole); position: relative; cursor: pointer; transition: background .15s; }
.sw input::after { content: ""; position: absolute; top: 3px; left: 3px; width: 20px; height: 20px; border-radius: 50%; background: #fff; box-shadow: 0 1px 2px rgba(0, 0, 0, .25); transition: transform .15s; }
.sw input:checked { background: var(--blue); }
.sw input:checked::after { transform: translateX(20px); }
.inline { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; white-space: nowrap; }
.inline input { width: 92px; flex: none; }
.field { display: block; margin: 12px 0; font-size: 15px; }
.field > input, .field > select, .field > .row { margin-top: 4px; }
.trim { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 10px; font-size: 13px; color: var(--soft); }
.trim-out { display: block; text-align: center; font-weight: 600; margin-top: 4px; }
.sub { padding-top: 14px; border-top: 1.5px dashed var(--hole); }

/* แถบล่าง ปุ่มหยุดอยู่ตรงนี้ตลอดเวลา */
.bar { position: fixed; left: 0; right: 0; bottom: 0; z-index: 20; background: var(--ink); color: #fff; padding: 10px 0 calc(10px + env(safe-area-inset-bottom)); }
.bar .wrap { display: flex; align-items: center; gap: 16px; }
.prog { flex: 1; min-width: 0; }
.prog span { display: block; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.prog i { display: block; height: 6px; margin-top: 7px; border-radius: 3px; background: #3A454C; overflow: hidden; }
.prog b { display: block; height: 100%; width: 0; background: var(--motor); transition: width .25s linear; }
.bar .key.stop { min-width: 124px; padding: 15px 24px; font-size: 19px; }
.toast { position: fixed; left: 50%; top: 14px; transform: translateX(-50%); z-index: 30; width: max-content; max-width: min(92vw, 520px); background: var(--ink); color: #fff; border-radius: 8px; padding: 10px 16px; font-size: 15px; box-shadow: 0 6px 20px rgba(30, 37, 41, .25); }
.toast.bad { background: var(--red); }
.foot { font-size: 13px; color: var(--soft); padding: 4px 0 18px; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <div class="brand">
      <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true"><rect x="1" y="8" width="5" height="12" rx="1.5" fill="#1E2529"/><rect x="22" y="8" width="5" height="12" rx="1.5" fill="#1E2529"/><rect x="5.5" y="3" width="17" height="22" rx="4" fill="#F5C400" stroke="#1E2529" stroke-width="2"/><circle cx="14" cy="8.5" r="2.2" fill="#D2323A"/></svg>
      <span>หุ่นยนต์วาดรูป</span>
    </div>
    <div class="conn" id="conn"><span class="led"></span><span id="connText">กำลังเชื่อมต่อ</span></div>
  </header>
  <div class="rail"></div>
  <div class="warn" id="netWarn" hidden>
    <p id="netWarnText"></p>
    <button type="button" class="key small" id="retryWifi" hidden>ลองต่อ WiFi บ้านอีกครั้ง</button>
  </div>

  <div class="cols">
    <div>
      <section>
        <label class="ask-label" for="ask">อยากให้หุ่นยนต์วิ่งเป็นรูปอะไร</label>
        <textarea id="ask" rows="2" enterkeyhint="send" placeholder="เช่น วิ่งเป็นรูปหัวใจ แล้วหมุนฉลองหนึ่งรอบ"></textarea>
        <div class="chips">
          <button type="button" class="chip" data-say="วิ่งเป็นรูปหัวใจ">หัวใจ</button>
          <button type="button" class="chip" data-say="วิ่งเป็นรูปดาว 5 แฉก">ดาว 5 แฉก</button>
          <button type="button" class="chip" data-say="วิ่งเป็นรูปบ้านหลังคาจั่ว">บ้าน</button>
          <button type="button" class="chip" data-say="วิ่งเป็นตัวอักษร S">ตัว S</button>
          <button type="button" class="chip" data-say="เต้นส่ายไปมาสั้น ๆ แล้วหมุนฉลองหนึ่งรอบ">เต้น</button>
          <button type="button" class="chip" data-say="เดินหน้า 50 ซม. กลับหลังหัน แล้ววิ่งกลับมาที่เดิม">ไปแล้วกลับ</button>
        </div>
        <div class="slide">
          <label for="size">ขนาดรูป</label>
          <input type="range" id="size" min="20" max="150" step="5" value="50">
          <output id="sizeOut" for="size">50 ซม.</output>
        </div>
        <p class="hint">วัดตามด้านที่ยาวที่สุดของรูป ถ้าพิมพ์ขนาดไว้ในคำสั่ง จะใช้ขนาดนั้นแทน</p>
        <div class="row">
          <button type="button" class="key" id="aiBtn">ให้ AI คิดเส้นทาง</button>
          <button type="button" class="key ghost" id="aiCancel" hidden>ยกเลิก</button>
        </div>
        <p class="notice" id="aiMsg" hidden></p>
      </section>

      <section>
        <div class="rail"></div>
        <div class="route-head">
          <h2 id="routeTitle">เส้นทางที่จะวิ่ง</h2>
          <span class="meta" id="routeMeta"></span>
        </div>
        <p class="ai-note" id="aiNote" hidden></p>
        <div class="stage">
          <canvas id="cv" role="img" aria-label="ภาพเส้นทางมองจากด้านบน วงกลมคือจุดเริ่ม หุ่นยนต์เริ่มโดยหันหัวขึ้น"></canvas>
          <p class="empty" id="empty">ยังไม่มีเส้นทาง พิมพ์สิ่งที่อยากให้วิ่งด้านบน หรือเลือกรูปสำเร็จด้านล่าง</p>
        </div>
        <dl class="stats">
          <div><dt>คำสั่ง</dt><dd id="stCount">0</dd></div>
          <div><dt>ระยะรวม</dt><dd id="stDist">–</dd></div>
          <div><dt>ใช้เวลาราว</dt><dd id="stTime">–</dd></div>
          <div><dt>ขนาดรูป</dt><dd id="stSize">–</dd></div>
          <div><dt>จบห่างจุดเริ่ม</dt><dd id="stGap">–</dd></div>
        </dl>
        <div class="row">
          <button type="button" class="key" id="runBtn">วิ่งตามเส้นทาง</button>
          <button type="button" class="key ghost" id="simBtn">ดูจำลอง</button>
        </div>
        <div class="refine" id="refine" hidden>
          <label for="fix">อยากแก้ตรงไหน</label>
          <div class="row tight">
            <input id="fix" enterkeyhint="send" placeholder="เช่น กลับหัว หรือให้ส่วนโค้งกลมกว่านี้">
            <button type="button" class="key ghost small" id="fixBtn">ให้ AI แก้</button>
          </div>
        </div>
        <div class="presets">
          <span>รูปสำเร็จ ใช้ได้แม้ไม่มีเน็ต</span>
          <button type="button" class="key ghost small" data-preset="heart">หัวใจ</button>
          <button type="button" class="key ghost small" data-preset="star">ดาว</button>
          <button type="button" class="key ghost small" data-preset="square">สี่เหลี่ยม</button>
          <button type="button" class="key ghost small" data-preset="circle">วงกลม</button>
          <button type="button" class="key ghost small" data-preset="eight">เลข 8</button>
          <button type="button" class="key ghost small" data-preset="spiral">ก้นหอย</button>
        </div>
        <details class="code" open>
          <summary>คำสั่งพื้นฐานที่ส่งให้หุ่นยนต์</summary>
          <textarea id="cmds" rows="3" spellcheck="false" autocomplete="off" autocapitalize="characters" placeholder="F30 L90 F30"></textarea>
          <p class="hint">F เดินหน้า และ B ถอยหลัง หน่วยเซนติเมตร, L หมุนซ้าย และ R หมุนขวา หน่วยองศา, W หยุดรอ หน่วยมิลลิวินาที แก้เองได้ ภาพด้านบนจะเปลี่ยนตาม</p>
          <div class="row">
            <button type="button" class="key ghost small" id="copyBtn">คัดลอกคำสั่ง</button>
            <button type="button" class="key ghost small" id="clearBtn">ล้างเส้นทาง</button>
          </div>
        </details>
      </section>
    </div>

    <div class="side">
      <section>
        <div class="rail"></div>
        <h2>บังคับเอง</h2>
        <p class="hint">กดค้างเพื่อวิ่ง ปล่อยนิ้วแล้วหยุด บนคอมใช้ปุ่มลูกศร และกด Space เพื่อหยุด</p>
        <div class="pad">
          <button type="button" class="key f" data-drive="F" aria-label="เดินหน้า"><svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5M5.5 11.5 12 5l6.5 6.5"/></svg></button>
          <button type="button" class="key l" data-drive="L" aria-label="หมุนซ้าย"><svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 8.5A8 8 0 1 1 4.3 14"/><path d="M4 3.5V9h5.5"/></svg></button>
          <button type="button" class="key stop s" id="padStop">หยุด</button>
          <button type="button" class="key r" data-drive="R" aria-label="หมุนขวา"><svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 8.5A8 8 0 1 1 4.3 14"/><path d="M4 3.5V9h5.5"/></svg></button>
          <button type="button" class="key b" data-drive="B" aria-label="ถอยหลัง"><svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v14M5.5 12.5 12 19l6.5-6.5"/></svg></button>
        </div>
        <div class="slide">
          <label for="spd">แรงมอเตอร์</label>
          <input type="range" id="spd" min="200" max="1023" step="1" value="700">
          <output id="spdOut" for="spd">68%</output>
        </div>
      </section>

      <section>
        <div class="rail"></div>
        <details class="panel" id="calPanel">
          <summary>ปรับเทียบระยะและมุม</summary>
          <ol class="steps">
            <li>
              <h3>เช็กทิศล้อ</h3>
              <p>กดเดินหน้าค้างไว้ ถ้ารถหมุนอยู่กับที่หรือถอยหลัง ให้กลับทิศล้อที่หมุนผิด ถ้าเดินหน้าถูกแต่กดหมุนซ้ายแล้วไปทางขวา ให้สลับล้อซ้ายกับขวา</p>
              <label class="sw"><input type="checkbox" data-cfg="invL"><span>กลับทิศล้อซ้าย</span></label>
              <label class="sw"><input type="checkbox" data-cfg="invR"><span>กลับทิศล้อขวา</span></label>
              <label class="sw"><input type="checkbox" data-cfg="swapLR"><span>สลับล้อซ้ายกับขวา</span></label>
            </li>
            <li>
              <h3>ระยะทาง</h3>
              <p>วางตลับเมตรข้างรถ กดวิ่งทดสอบ แล้ววัดว่ารถไปได้จริงกี่เซนติเมตร</p>
              <div class="row tight">
                <select id="calDist" aria-label="ระยะทดสอบ" style="width:auto"><option value="30">30 ซม.</option><option value="50" selected>50 ซม.</option><option value="100">100 ซม.</option></select>
                <button type="button" class="key ghost small" id="calDistRun">วิ่งทดสอบ</button>
              </div>
              <div class="row tight">
                <label class="inline">วิ่งได้จริง <input type="number" id="calDistGot" inputmode="decimal" min="1" step="0.5"> ซม.</label>
                <button type="button" class="key small" id="calDistSave">คำนวณและบันทึก</button>
              </div>
              <label class="field">มิลลิวินาทีต่อ 1 ซม. <input type="number" data-cfg="msPerCm" step="0.1" min="1" max="500" inputmode="decimal"></label>
            </li>
            <li>
              <h3>มุมหมุน</h3>
              <p>แปะเทปชี้ตรงหน้ารถไว้เป็นจุดอ้างอิง สั่งหมุนหนึ่งรอบ แล้วดูว่าหมุนได้จริงกี่องศา เช่น ขาดไปนิดหน่อยใส่ 330 เกินไปครึ่งรอบใส่ 540</p>
              <div class="row tight"><button type="button" class="key ghost small" id="calTurnRun">หมุนทดสอบ 360°</button></div>
              <div class="row tight">
                <label class="inline">หมุนได้จริง <input type="number" id="calTurnGot" inputmode="decimal" min="10" step="5"> องศา</label>
                <button type="button" class="key small" id="calTurnSave">คำนวณและบันทึก</button>
              </div>
              <label class="field">มิลลิวินาทีต่อ 1 องศา <input type="number" data-cfg="msPerDeg" step="0.05" min="0.2" max="200" inputmode="decimal"></label>
            </li>
            <li>
              <h3>วิ่งให้ตรง</h3>
              <p>สั่งวิ่งตรง ถ้ารถเบี้ยวไปทางขวา เลื่อนไปทางลดแรงล้อซ้าย ถ้าเบี้ยวไปทางซ้าย เลื่อนไปทางลดแรงล้อขวา</p>
              <div class="row tight"><button type="button" class="key ghost small" id="calStraight">วิ่งตรง 100 ซม.</button></div>
              <div class="trim"><span>ลดแรงล้อขวา</span><input type="range" data-cfg="trim" min="-40" max="40" step="1" aria-label="ปรับสมดุลล้อ"><span>ลดแรงล้อซ้าย</span></div>
              <output class="trim-out" id="trimOut">ล้อซ้ายขวาแรงเท่ากัน</output>
            </li>
          </ol>
          <div class="sub">
            <label class="field">แรงตอนวิ่งตรง <output data-out="driveSpeed"></output><input type="range" data-cfg="driveSpeed" min="200" max="1023" step="1"></label>
            <label class="field">แรงตอนหมุน <output data-out="turnSpeed"></output><input type="range" data-cfg="turnSpeed" min="200" max="1023" step="1"></label>
            <label class="field">หยุดพักระหว่างท่า (มิลลิวินาที) <input type="number" data-cfg="pauseMs" min="0" max="3000" step="10" inputmode="numeric"></label>
            <p class="hint">รถไถลเลยจุดตอนเลี้ยว ให้เพิ่มเวลาพัก ถ้าล้อหมุนไม่ขึ้นตอนท่าสั้น ๆ ให้เพิ่มแรง</p>
            <button type="button" class="key ghost small" id="cfgReset">คืนค่าเริ่มต้น</button>
          </div>
        </details>
      </section>

      <section>
        <div class="rail"></div>
        <details class="panel" id="aiPanel">
          <summary>ตั้งค่า AI</summary>
          <label class="field" for="key">API key ของ Claude</label>
          <div class="row tight">
            <input type="password" id="key" autocomplete="off" spellcheck="false" placeholder="sk-ant-...">
            <button type="button" class="key ghost small" id="keyShow">แสดง</button>
          </div>
          <p class="hint">สร้างคีย์ได้ที่ Claude Console (platform.claude.com) คีย์จะเก็บไว้ในเบราว์เซอร์นี้เท่านั้น ไม่ได้ส่งเข้าหุ่นยนต์ ค่าใช้งานคิดตามจริง ควรตั้งวงเงินไว้ในบัญชี</p>
          <label class="field">โมเดล <input id="model" list="models" spellcheck="false" autocomplete="off"></label>
          <datalist id="models"><option value="claude-sonnet-5"><option value="claude-opus-5"><option value="claude-haiku-4-5-20251001"></datalist>
          <label class="field">ความลึกในการคิด
            <select id="effort">
              <option value="low">ต่ำ ตอบเร็วที่สุด</option>
              <option value="medium">กลาง</option>
              <option value="high">สูง ช้ากว่าแต่รอบคอบ</option>
              <option value="auto">ใช้ค่าเริ่มต้นของโมเดล</option>
            </select>
          </label>
          <label class="field">แบ่งเส้นโค้งทุก <output id="resOut"></output><input type="range" id="res" min="10" max="45" step="5" value="20"></label>
          <p class="hint">ค่าน้อย เส้นโค้งเนียนแต่คำสั่งเยอะ ค่ามาก คำสั่งน้อยและวิ่งเสร็จเร็ว</p>
          <div class="row">
            <button type="button" class="key ghost small" id="aiTest">ทดสอบการเชื่อมต่อ AI</button>
            <button type="button" class="key ghost small" id="keyDel">ลบคีย์</button>
          </div>
          <p class="notice" id="aiTestOut" hidden></p>
        </details>
      </section>
    </div>
  </div>
  <p class="foot" id="foot"></p>
</div>

<div class="bar">
  <div class="wrap">
    <div class="prog" role="status" aria-live="polite"><span id="barText">พร้อม</span><i><b id="barFill"></b></i></div>
    <button type="button" class="key stop" id="stopBtn">หยุด</button>
  </div>
</div>
<div class="toast" id="toast" role="alert" hidden></div>

<script>
(() => {
'use strict';

// ===================== ค่าคงที่ =====================
const MAX_CMDS = 300;                  // ต้องตรงกับ MAX_CMDS ในเฟิร์มแวร์
const D2R = Math.PI / 180;
const API_URL = 'https://api.anthropic.com/v1/messages';
const DEFAULT_MODEL = 'claude-sonnet-5';
const COL = { sheet: '#F8F9F7', ink: '#1E2529', soft: '#56626A', hole: '#C3CAC6', motor: '#F5C400', red: '#D2323A', blue: '#2D5BA6' };
const FONT = '"Chakra Petch","Sukhumvit Set","Thonburi","Noto Sans Thai",system-ui,sans-serif';

// คำสั่งระบบของ AI เขียนเป็นภาษาอังกฤษเพราะโมเดลทำตามได้แม่นกว่า แต่ให้ตอบชื่อและคำอธิบายเป็นภาษาไทย
const SYSTEM = `You plan routes for a small two-wheeled floor robot (differential drive). Think of it as a LOGO turtle seen from above.
The robot starts at (0,0) facing up (+y); +x is to its right. Units are centimeters and degrees.
The robot itself can only drive straight, rotate in place and wait. Your plan may also use arcs: the app converts each arc into short straight moves and small turns, rescales the route, draws it for the user, then sends it to the robot.

Reply with exactly one JSON object and nothing else (no markdown, no code fences, no comments):
{"name": "...", "note": "...", "closed": true, "exact": false, "size_cm": null, "steps": [ ... ]}

name: a short Thai name for what the robot will do.
note: one or two short Thai sentences describing the route in plain words.
closed: true if the route should end back at its start point (outline shapes), otherwise false.
exact: true only when the user gave explicit distances that must be driven as real centimeters (for example "go forward 50 cm and come back"). Use false for shapes; the app rescales them.
size_cm: the overall size the user asked for (for example "a heart 40 cm wide" gives 40), otherwise null.

Step objects:
{"op":"forward","cm":20}  drive straight ahead
{"op":"back","cm":20}  drive straight backwards
{"op":"left","deg":90}  rotate in place counterclockwise
{"op":"right","deg":90}  rotate in place clockwise
{"op":"arc","dir":"left","r":10,"deg":180}  drive forward along a circle of radius r while turning left (counterclockwise) by deg; "dir":"right" turns clockwise. The circle's center is on that side of the robot.
{"op":"goto","x":10,"y":25}  turn toward the point (measured from the start, +y = the robot's starting forward direction) and drive straight to it
{"op":"wait","ms":500}  pause
{"op":"repeat","times":5,"steps":[ ... ]}  repeat the inner steps

How to plan well:
- Work out the geometry before answering: track the robot's position and heading after every step. The drawing must look like the requested shape when viewed from above with +y pointing up, and be the right way up (for example a heart has its point at the bottom).
- A closed shape must end exactly at its start point. For an outline traced once, all heading changes, including the corner back at the start, add up to 360 degrees.
- Use arcs for rounded parts, repeat for regular polygons and stars, and goto for shapes that are easiest to describe with corner coordinates (letters, houses, arrows).
- Pick a start point on the outline that keeps the plan simple; turning first is fine. Ending with the robot facing its original direction is nice but optional.
- Typical shapes are 20 to 80 cm across. Keep the plan under about 60 steps before repeats are expanded; wiggles smaller than 3 cm are not possible for this robot.
- Requests that are not shapes (dance, patrol, spin, go and come back) are fine: plan sensible moves.
- If the robot cannot do the request (flying, grabbing things, sensing obstacles), return "steps": [] and explain why in note.
- When asked to change an earlier plan, return the complete new plan. In attached images of the simulated route, the ring marks the start, the small robot shows the starting direction (up), the solid line is what the robot will drive and the dashed line is your exact geometry.`;

// รูปสำเร็จ ใช้รูปแบบเดียวกับที่ AI ตอบกลับ (ไม่ต้องใช้เน็ต)
const PRESETS = {
  heart:  { name: 'หัวใจ', closed: true, steps: [
    { op: 'left', deg: 45 }, { op: 'forward', cm: 20 },
    { op: 'arc', dir: 'right', r: 10, deg: 180 }, { op: 'left', deg: 90 },
    { op: 'arc', dir: 'right', r: 10, deg: 180 }, { op: 'forward', cm: 20 }, { op: 'right', deg: 135 }] },
  star:   { name: 'ดาว 5 แฉก', closed: true, steps: [
    { op: 'right', deg: 18 }, { op: 'repeat', times: 5, steps: [{ op: 'forward', cm: 40 }, { op: 'right', deg: 144 }] }, { op: 'left', deg: 18 }] },
  square: { name: 'สี่เหลี่ยม', closed: true, steps: [
    { op: 'repeat', times: 4, steps: [{ op: 'forward', cm: 40 }, { op: 'right', deg: 90 }] }] },
  circle: { name: 'วงกลม', closed: true, steps: [{ op: 'arc', dir: 'right', r: 20, deg: 360 }] },
  eight:  { name: 'เลข 8', closed: true, steps: [
    { op: 'right', deg: 90 }, { op: 'arc', dir: 'left', r: 15, deg: 360 }, { op: 'arc', dir: 'right', r: 15, deg: 360 }, { op: 'left', deg: 90 }] },
  spiral: { name: 'ก้นหอย', closed: false, steps: [4, 8, 12, 16, 20].map(r => ({ op: 'arc', dir: 'right', r, deg: 180 })) }
};

// ===================== ตัวช่วยทั่วไป =====================
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
const store = {
  get(k, d) { try { const v = localStorage.getItem('robot.' + k); return v === null ? d : v; } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('robot.' + k, v); } catch (e) {} },
  del(k) { try { localStorage.removeItem('robot.' + k); } catch (e) {} }
};
class UserError extends Error {}
const fmtNum = (v, d) => String(Math.round(v * Math.pow(10, d)) / Math.pow(10, d));
const fmtDist = cm => cm >= 100 ? fmtNum(cm / 100, 2) + ' ม.' : Math.round(cm) + ' ซม.';
const pct = v => Math.round(Number(v) / 1023 * 100) + '%';
const reduceMotion = () => window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
function fmtTime(ms) {
  const s = Math.round(ms / 1000);
  return s < 60 ? s + ' วินาที' : Math.floor(s / 60) + ' นาที ' + (s % 60) + ' วินาที';
}
function norm180(a) { return ((a + 180) % 360 + 360) % 360 - 180; }

const S = {
  cfg: { driveSpeed: 650, turnSpeed: 620, msPerCm: 22, msPerDeg: 4, trim: 0, pauseMs: 150, invL: 0, invR: 0, swapLR: 0 },
  status: null, fails: 0,
  cmds: [], sim: null, plan: null, ideal: null, compiledText: '', editT: 0,
  convo: null, aiBusy: false, aiAbort: null, aiTimer: 0,
  runId: 0, runSim: null, runIdx: -1, runIdxAt: 0, runDone: false, stoppedAt: 0,
  manual: null, anim: null, reveal: 0, raf: 0
};

let toastT = 0;
function toast(msg, bad) {
  const t = $('#toast');
  t.textContent = msg; t.hidden = false; t.classList.toggle('bad', !!bad);
  clearTimeout(toastT);
  toastT = setTimeout(() => { t.hidden = true; }, bad ? 4500 : 2400);
}
function setBar(text, frac) {
  $('#barText').textContent = text;
  if (frac !== undefined) setBarFill(frac);
}
function setBarFill(frac) { $('#barFill').style.width = (Math.max(0, Math.min(1, frac)) * 100).toFixed(1) + '%'; }

// ===================== คุยกับหุ่นยนต์ =====================
async function robot(path, opt, timeout) {
  const ctl = new AbortController();
  const tm = setTimeout(() => ctl.abort(), timeout || 3000);
  try {
    const r = await fetch(path, Object.assign({ cache: 'no-store', signal: ctl.signal }, opt || {}));
    const txt = await r.text();
    let j = null;
    try { j = JSON.parse(txt); } catch (e) {}
    if (!r.ok) throw new Error((j && j.error) || ('HTTP ' + r.status));
    return j || {};
  } finally { clearTimeout(tm); }
}

function setConn(kind, s) {
  $('#conn').className = 'conn ' + kind;
  let txt = 'ติดต่อหุ่นยนต์ไม่ได้';
  if (kind === 'ok') txt = 'เชื่อมต่อแล้ว สัญญาณ' + (s.rssi > -60 ? 'ดี' : s.rssi > -72 ? 'พอใช้' : 'อ่อน');
  if (kind === 'ap') txt = 'ต่อตรงกับหุ่นยนต์ ไม่มีเน็ต';
  $('#connText').textContent = txt;
  const w = $('#netWarn'), wt = $('#netWarnText');
  w.hidden = kind === 'ok';
  $('#retryWifi').hidden = kind !== 'ap';
  if (kind === 'ap') wt.textContent = wifiReason(s) + ' ตอนนี้มือถือต่อ WiFi ของหุ่นยนต์โดยตรง จึงไม่มีอินเทอร์เน็ตให้ AI แต่ใช้รูปสำเร็จและบังคับเองได้';
  if (kind === 'off') wt.textContent = 'ตรวจว่าหุ่นยนต์เปิดอยู่ และมือถืออยู่ใน WiFi วงเดียวกับหุ่นยนต์ ถ้าเพิ่งเปิดเครื่อง รอสักครู่';
  if (s && s.ip) {
    $('#foot').textContent = 'เปิดหน้านี้ได้ที่ http://' + s.ip + (s.host && !s.ap ? ' หรือ http://' + s.host + '.local' : '');
  }
}

// อธิบายว่าทำไมบอร์ดต่อ WiFi บ้านไม่ได้ (ข้อมูลจากการสแกนตอนเปิดเครื่อง)
function wifiReason(s) {
  const name = s && s.ssid ? '"' + s.ssid + '"' : 'บ้าน';
  if (!s || s.wifiErr === undefined) return 'หุ่นยนต์ต่อ WiFi ' + name + ' ไม่สำเร็จ';
  if (s.wifiErr === 6) return 'หุ่นยนต์ต่อ WiFi ' + name + ' ไม่ได้ เพราะรหัส WiFi ไม่ถูกต้อง แก้ WIFI_PASS ในโค้ดแล้วอัปโหลดใหม่';
  if (!s.wifiSeen) return 'หุ่นยนต์มองไม่เห็น WiFi ชื่อ ' + name + ' เลย ตรวจว่าชื่อตรงทุกตัวอักษร (ตัวพิมพ์เล็กใหญ่ด้วย) เป็นคลื่น 2.4 GHz และวางหุ่นยนต์ใกล้เราเตอร์';
  if (s.wifiSeen < -80) return 'หุ่นยนต์เห็น WiFi ' + name + ' แต่สัญญาณอ่อนมาก (' + s.wifiSeen + ' dBm) ลองวางใกล้เราเตอร์';
  return 'หุ่นยนต์เห็น WiFi ' + name + ' (สัญญาณ ' + s.wifiSeen + ' dBm) แต่ต่อไม่ทันเวลา มักเกิดจากไฟเลี้ยงบอร์ดไม่พอ หรือเราเตอร์ตอบช้า ลองกดต่อใหม่';
}

let pollBusy = false;
async function poll() {
  if (pollBusy || S.manual || document.hidden) return;
  pollBusy = true;
  try {
    const s = await robot('/api/status', null, 2500);
    S.fails = 0;
    S.status = s;
    if (s.config) Object.assign(S.cfg, s.config);
    setConn(s.ap ? 'ap' : 'ok', s);
    onStatus(s);
  } catch (e) {
    if (++S.fails >= 2) setConn('off');
  } finally { pollBusy = false; }
}
function pollLoop() {
  const fast = S.status && S.status.running;
  setTimeout(() => { poll().then(pollLoop); }, fast ? 350 : 1200);
}

function onStatus(s) {
  const mine = S.runId > 0 && s.run === S.runId;
  if (s.running) {
    if (mine && s.idx !== S.runIdx) { S.runIdx = s.idx; S.runIdxAt = performance.now(); }
    $('#barText').textContent = 'กำลังวิ่งท่าที่ ' + Math.min(s.idx + 1, s.total) + ' จาก ' + s.total;
    if (mine && S.runSim) {
      if (!S.anim || S.anim.mode !== 'run') { S.anim = { mode: 'run', sim: S.runSim }; requestDraw(); }
    } else setBarFill(s.total ? s.idx / s.total : 0);
    return;
  }
  if (S.anim && S.anim.mode === 'run') { S.anim = null; requestDraw(); }
  if (s.manual) setBar('กำลังบังคับเอง', 0);
  else if (mine && s.total > 0 && s.idx >= s.total) {
    if (!S.runDone) { S.runDone = true; requestDraw(); }
    setBar('วิ่งครบแล้ว', 1);
  } else if (S.stoppedAt && performance.now() - S.stoppedAt < 3000) setBar('หยุดแล้ว', 0);
  else if (!(S.anim && S.anim.mode === 'sim')) setBar('พร้อม', 0);
}

async function runCmds(text, withPreview) {
  const cmds = parseCmds(text);
  if (!cmds.length) { toast('ยังไม่มีคำสั่งให้วิ่ง', true); return; }
  if (cmds.length > MAX_CMDS) { toast('มี ' + cmds.length + ' คำสั่ง แต่หุ่นยนต์รับได้ครั้งละ ' + MAX_CMDS, true); return; }
  if (S.manual) stopDrive();
  stopSim();
  const body = cmds.map(c => c.op + fmtNum(c.v, 2)).join(' ');
  try {
    const r = await robot('/api/run', { method: 'POST', headers: { 'Content-Type': 'text/plain' }, body }, 4000);
    S.runId = r.run; S.runIdx = -1; S.runDone = false; S.stoppedAt = 0;
    S.runSim = withPreview ? S.sim : null;
    setBar('เริ่มวิ่ง ' + r.count + ' คำสั่ง', 0);
    requestDraw();
    poll();
  } catch (e) {
    toast('ส่งคำสั่งไม่สำเร็จ ตรวจว่ายังเชื่อมต่อหุ่นยนต์อยู่', true);
  }
}

function sendStop() {
  robot('/api/stop', null, 2000).catch(() => {});
  setTimeout(() => robot('/api/stop', null, 2000).catch(() => {}), 150);  // ส่งซ้ำกันคำสั่งค้าง
}
function stopEverything() {
  if (S.manual) { clearInterval(S.manual.timer); if (S.manual.btn) S.manual.btn.classList.remove('on'); S.manual = null; }
  stopSim();
  if (S.anim) S.anim = null;
  S.stoppedAt = performance.now();
  S.runIdx = -1;
  setBar('หยุดแล้ว', 0);
  sendStop();
  requestDraw();
}

// ---------- บังคับเอง: ส่งคำสั่งซ้ำทุก 180 ms บอร์ดจะหยุดเองถ้าขาดเกิน 600 ms ----------
function startDrive(d, btn) {
  if (S.manual && S.manual.d === d) return;
  if (S.manual) { clearInterval(S.manual.timer); if (S.manual.btn) S.manual.btn.classList.remove('on'); }
  stopSim();
  const m = { d, btn, busy: false, timer: 0 };
  S.manual = m;
  if (btn) btn.classList.add('on');
  setBar('กำลังบังคับเอง', 0);
  const tick = async () => {
    if (S.manual !== m || m.busy) return;
    m.busy = true;
    try { await robot('/api/drive?d=' + d + '&s=' + $('#spd').value, null, 1500); } catch (e) {}
    m.busy = false;
  };
  tick();
  m.timer = setInterval(tick, 180);
}
function stopDrive() {
  if (!S.manual) return;
  clearInterval(S.manual.timer);
  if (S.manual.btn) S.manual.btn.classList.remove('on');
  S.manual = null;
  setBar('พร้อม', 0);
  sendStop();
}

// ===================== คำสั่งพื้นฐาน และการจำลอง =====================
// อ่านข้อความแบบเดียวกับเฟิร์มแวร์ (ค่าลบ = กลับทิศ, มีเพดานต่อคำสั่ง)
function parseCmds(text) {
  const out = [];
  const flip = { F: 'B', B: 'F', L: 'R', R: 'L', W: 'W' };
  const re = /([FBLRW])\s*([-+]?(?:\d+\.?\d*|\.\d+))/gi;
  let m;
  while ((m = re.exec(text))) {
    let op = m[1].toUpperCase(), v = parseFloat(m[2]);
    if (!isFinite(v)) continue;
    if (v < 0) { v = -v; op = flip[op]; }
    const lim = (op === 'F' || op === 'B') ? 500 : op === 'W' ? 30000 : 3600;
    if (v > lim) v = lim;
    if (v > 0) out.push({ op, v });
  }
  return out;
}

function simulate(cmds) {
  const c = S.cfg;
  let x = 0, y = 0, h = 90, dist = 0, time = 0;
  let minX = 0, maxX = 0, minY = 0, maxY = 0;
  const pts = [[0, 0]], steps = [];
  for (const k of cmds) {
    const st = { op: k.op, x0: x, y0: y, h0: h, p0: pts.length - 1, dur: 0, pause: Number(c.pauseMs) || 0 };
    if (k.op === 'F' || k.op === 'B') {
      const d = k.op === 'F' ? k.v : -k.v;
      x += d * Math.cos(h * D2R);
      y += d * Math.sin(h * D2R);
      pts.push([x, y]);
      dist += k.v;
      st.dur = k.v * c.msPerCm;
      minX = Math.min(minX, x); maxX = Math.max(maxX, x);
      minY = Math.min(minY, y); maxY = Math.max(maxY, y);
    } else if (k.op === 'L' || k.op === 'R') {
      h += k.op === 'L' ? k.v : -k.v;
      st.dur = k.v * c.msPerDeg;
    } else st.dur = k.v;
    st.x1 = x; st.y1 = y; st.h1 = h;
    time += st.dur + st.pause;
    steps.push(st);
  }
  return { pts, steps, dist, time, gap: Math.hypot(x, y), bbox: { minX, maxX, minY, maxY } };
}

function resim() {
  const cmds = parseCmds($('#cmds').value);
  const sim = simulate(cmds), n = cmds.length, bb = sim.bbox;
  S.cmds = cmds;
  S.sim = sim;
  $('#empty').hidden = n > 0;
  const cnt = $('#stCount');
  cnt.textContent = n > MAX_CMDS ? n + ' เกิน ' + MAX_CMDS : String(n);
  cnt.classList.toggle('bad', n > MAX_CMDS);
  $('#stDist').textContent = n ? fmtDist(sim.dist) : '–';
  $('#stTime').textContent = n ? fmtTime(sim.time) : '–';
  $('#stSize').textContent = n ? Math.round(bb.maxX - bb.minX) + ' × ' + Math.round(bb.maxY - bb.minY) + ' ซม.' : '–';
  $('#stGap').textContent = n ? (sim.gap < 0.5 ? 'ปิดสนิท' : fmtNum(sim.gap, 1) + ' ซม.') : '–';
  $('#runBtn').disabled = !n;
  $('#simBtn').disabled = !n;
  requestDraw();
}

function flushEdit() {
  if (!S.editT) return;
  clearTimeout(S.editT);
  S.editT = 0;
  const t = $('#cmds').value;
  if (t.trim() !== S.compiledText.trim()) S.ideal = null;
  S.runSim = null;
  S.runDone = false;
  stopSim();
  store.set('cmds', t);
  resim();
}
function onCmdsInput() {
  clearTimeout(S.editT);
  S.editT = setTimeout(() => { S.editT = 1; flushEdit(); }, 200);
}

// ===================== แปลงแผน (เส้นตรง/เส้นโค้ง) เป็นคำสั่งพื้นฐาน =====================
function flatten(steps, depth, out) {
  if (!Array.isArray(steps)) return out;
  if (depth > 6) throw new UserError('แผนนี้ซ้อนคำสั่งทำซ้ำลึกเกินไป');
  const num = v => { const n = Number(v); return isFinite(n) ? n : 0; };
  for (const st of steps) {
    if (!st || typeof st !== 'object') continue;
    if (out.length > 5000) throw new UserError('แผนนี้ยาวเกินไป ลองรูปที่ง่ายกว่านี้');
    switch (String(st.op || '').toLowerCase()) {
      case 'forward': out.push({ t: 'move', d: num(st.cm) }); break;
      case 'back': case 'backward': out.push({ t: 'move', d: -num(st.cm) }); break;
      case 'left': out.push({ t: 'turn', a: num(st.deg) }); break;
      case 'right': out.push({ t: 'turn', a: -num(st.deg) }); break;
      case 'arc': {
        const a = num(st.deg);
        out.push({ t: 'arc', r: Math.abs(num(st.r !== undefined ? st.r : st.radius)), a: String(st.dir).toLowerCase() === 'right' ? -a : a });
        break;
      }
      case 'goto': out.push({ t: 'goto', x: num(st.x), y: num(st.y) }); break;
      case 'wait': out.push({ t: 'wait', ms: Math.max(0, num(st.ms)) }); break;
      case 'repeat': {
        const n = Math.min(200, Math.max(0, Math.floor(num(st.times))));
        for (let i = 0; i < n; i++) flatten(st.steps, depth + 1, out);
        break;
      }
      default: break;  // ท่าที่ไม่รู้จักข้ามไป
    }
  }
  return out;
}

// เดินตามแผนแบบเรขาคณิตจริง: แปลง goto เป็นหมุน+เดิน, เก็บจุดของเส้นโค้งไว้วาด, หาขนาดรูป
function trace(prims) {
  let x = 0, y = 0, h = 90;
  let minX = 0, maxX = 0, minY = 0, maxY = 0;
  const res = [], pts = [[0, 0]];
  const add = () => {
    pts.push([x, y]);
    minX = Math.min(minX, x); maxX = Math.max(maxX, x);
    minY = Math.min(minY, y); maxY = Math.max(maxY, y);
  };
  for (const p of prims) {
    if (p.t === 'goto') {
      const dx = p.x - x, dy = p.y - y, d = Math.hypot(dx, dy);
      if (d < 1e-6) continue;
      const turn = norm180(Math.atan2(dy, dx) / D2R - h);
      res.push({ t: 'turn', a: turn });
      res.push({ t: 'move', d });
      h += turn; x = p.x; y = p.y; add();
    } else if (p.t === 'move') {
      x += p.d * Math.cos(h * D2R); y += p.d * Math.sin(h * D2R); add();
      res.push(p);
    } else if (p.t === 'turn') {
      h += p.a;
      res.push(p);
    } else if (p.t === 'arc') {
      const sg = p.a >= 0 ? 1 : -1;
      const cx = x + p.r * Math.cos((h + 90 * sg) * D2R), cy = y + p.r * Math.sin((h + 90 * sg) * D2R);
      const start = h - 90 * sg, n = Math.max(2, Math.ceil(Math.abs(p.a) / 5));
      for (let i = 1; i <= n; i++) {
        const ang = (start + p.a * i / n) * D2R;
        x = cx + p.r * Math.cos(ang); y = cy + p.r * Math.sin(ang); add();
      }
      h += p.a;
      res.push(p);
    } else res.push(p);
  }
  return { prims: res, pts, bbox: { minX, maxX, minY, maxY }, end: [x, y] };
}

// เส้นโค้งแบ่งเป็น (หมุนครึ่งหนึ่ง, เดินคอร์ด, หมุนครึ่งหนึ่ง) ต่อกัน แล้วรวมท่าหมุนที่ติดกัน
function discretize(prims, s, stepDeg, minChord) {
  const raw = [];
  for (const p of prims) {
    if (p.t === 'move') { if (p.d) raw.push({ k: 'M', v: p.d * s }); }
    else if (p.t === 'turn') { if (p.a) raw.push({ k: 'T', v: p.a }); }
    else if (p.t === 'wait') { if (p.ms > 0) raw.push({ k: 'W', v: p.ms }); }
    else if (p.t === 'arc') {
      const R = p.r * s, A = p.a, absA = Math.abs(A);
      if (absA < 1e-6) continue;
      if (R < 0.05) { raw.push({ k: 'T', v: A, auto: true }); continue; }
      let n = Math.min(Math.ceil(absA / stepDeg), Math.floor(R * absA * D2R / minChord));
      n = Math.max(n, Math.ceil(absA / 90), 1);
      const th = A / n, chord = 2 * R * Math.sin(Math.abs(th) * D2R / 2);
      raw.push({ k: 'T', v: th / 2, auto: true });
      for (let i = 0; i < n; i++) {
        raw.push({ k: 'M', v: chord, auto: true });
        raw.push({ k: 'T', v: i < n - 1 ? th : th / 2, auto: true });
      }
    }
  }
  // รวมท่าหมุนที่ติดกัน (แต่ไม่รวมท่าส่ายซ้ายขวาที่ผู้ใช้ตั้งใจ) และรวมท่าเดินของเส้นโค้ง
  const merged = [];
  for (const r of raw) {
    const L = merged[merged.length - 1];
    const same = L && L.k === r.k && r.k !== 'W' && (r.k === 'T'
      ? (Math.sign(L.v) === Math.sign(r.v) || L.auto || r.auto)
      : (Math.sign(L.v) === Math.sign(r.v) && (L.auto || r.auto)));
    if (same) { L.v += r.v; L.auto = L.auto && r.auto; }
    else merged.push({ k: r.k, v: r.v, auto: !!r.auto });
  }
  // ปัดเศษทีละ 0.1 แล้วยกเศษที่เหลือไปคำสั่งถัดไป มุมรวมจึงไม่คลาดสะสม
  const out = [];
  let resT = 0, resM = 0;
  const push = (op, v, lim) => {
    while (v > lim + 1e-9) { out.push(op + lim); v -= lim; }
    const q = Math.round(v * 10) / 10;
    if (q > 0) out.push(op + q);
  };
  for (const m of merged) {
    if (m.k === 'W') { push('W', Math.round(m.v), 30000); continue; }
    if (m.k === 'T') {
      const want = m.v + resT, q = Math.round(want * 10) / 10;
      resT = want - q;
      if (q) push(q > 0 ? 'L' : 'R', Math.abs(q), 3600);
    } else {
      const want = m.v + resM, q = Math.round(want * 10) / 10;
      resM = want - q;
      if (q) push(q > 0 ? 'F' : 'B', Math.abs(q), 500);
    }
  }
  return out;
}

function compilePlan(plan) {
  const geo = trace(flatten(plan.steps, 0, []));
  if (!geo.prims.length) throw new UserError(plan.note || 'แผนนี้ไม่มีท่าวิ่ง');
  const bb = geo.bbox, side = Math.max(bb.maxX - bb.minX, bb.maxY - bb.minY);
  const exact = plan.exact === true;
  const asked = Number(plan.size_cm);
  const fromText = !exact && asked > 0;
  const target = fromText ? Math.min(Math.max(asked, 5), 500) : Number($('#size').value);
  const s = !exact && side > 0.5 ? target / side : 1;
  let stepDeg = Number(store.get('res', '20')) || 20, minChord = 3, cmds = [];
  for (let i = 0; i < 6; i++) {               // ยาวเกินก็แบ่งโค้งให้หยาบลงจนพอดี
    cmds = discretize(geo.prims, s, stepDeg, minChord);
    if (cmds.length <= MAX_CMDS) break;
    stepDeg = Math.min(90, stepDeg * 1.5);
    minChord *= 1.5;
  }
  if (cmds.length > MAX_CMDS) throw new UserError('เส้นทางนี้ต้องใช้ ' + cmds.length + ' คำสั่ง เกินที่หุ่นยนต์รับได้ (' + MAX_CMDS + ') ลองรูปที่ง่ายกว่านี้');
  if (!cmds.length) throw new UserError('แผนนี้ไม่มีท่าวิ่ง');
  const gapUnits = Math.hypot(geo.end[0], geo.end[1]);
  return {
    text: cmds.join(' '), ideal: geo.pts.map(p => [p[0] * s, p[1] * s]),
    exact, fromText, target: Math.round(target), side, gapUnits, gapRatio: side > 0 ? gapUnits / side : 0
  };
}

function showPlan(plan, res, keepNote) {
  S.plan = plan;
  S.ideal = res.ideal;
  S.compiledText = res.text;
  S.runSim = null;
  S.runDone = false;
  stopSim();
  clearTimeout(S.editT);
  S.editT = 0;
  $('#cmds').value = res.text;
  store.set('cmds', res.text);
  S.reveal = reduceMotion() ? 0 : performance.now();
  resim();
  $('#routeTitle').textContent = plan.name ? 'เส้นทาง: ' + plan.name : 'เส้นทางที่จะวิ่ง';
  $('#routeMeta').textContent = res.exact ? 'วิ่งตามระยะที่สั่งจริง'
    : res.fromText ? 'ขนาดตามที่สั่ง ' + res.target + ' ซม.' : 'ปรับขนาดให้ยาว ' + res.target + ' ซม.';
  if (!keepNote) {
    $('#aiNote').hidden = !plan.note;
    $('#aiNote').textContent = plan.note || '';
  }
  $('#refine').hidden = false;
}

function recompile(onlyIfScalable) {
  if (!S.plan) return;
  if (onlyIfScalable && (S.plan.exact === true || Number(S.plan.size_cm) > 0)) return;
  if ($('#cmds').value.trim() !== S.compiledText.trim()) { toast('คำสั่งถูกแก้เองอยู่ จึงไม่ได้คำนวณเส้นทางใหม่'); return; }
  try { showPlan(S.plan, compilePlan(S.plan), true); } catch (e) { toast(e.message, true); }
}

function usePreset(k) {
  const plan = JSON.parse(JSON.stringify(PRESETS[k]));
  try {
    showPlan(plan, compilePlan(plan));
    S.convo = null;
    aiMsg('');
  } catch (e) { toast(e.message, true); }
}

function clearRoute() {
  stopSim();
  S.plan = null; S.ideal = null; S.compiledText = ''; S.convo = null; S.runSim = null; S.runDone = false;
  $('#cmds').value = '';
  store.set('cmds', '');
  $('#routeTitle').textContent = 'เส้นทางที่จะวิ่ง';
  $('#routeMeta').textContent = '';
  $('#aiNote').hidden = true;
  $('#refine').hidden = true;
  resim();
}

// ===================== วาดภาพจำลอง =====================
function requestDraw() { if (!S.raf) S.raf = requestAnimationFrame(frame); }

function frame(now) {
  S.raf = 0;
  let pose = null, again = false;
  const a = S.anim;
  if (a && a.mode === 'sim') {
    pose = simPose(a, now);
    if (pose) again = true; else stopSim();
  } else if (a && a.mode === 'run') {
    pose = runPose(a, now);
    again = true;
    const st = S.status;
    if (pose && st && st.total) setBarFill((pose.i + pose.frac) / st.total);
  }
  let reveal = 1;
  if (S.reveal) {
    reveal = Math.min(1, (now - S.reveal) / 900);
    if (reveal < 1) again = true; else S.reveal = 0;
  }
  const cv = $('#cv');
  const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
  const W = Math.max(10, Math.round(cv.clientWidth * dpr)), H = Math.max(10, Math.round(cv.clientHeight * dpr));
  if (cv.width !== W || cv.height !== H) { cv.width = W; cv.height = H; }
  renderScene(cv.getContext('2d'), W, H, dpr, { pose, reveal, full: !pose && S.runDone && S.runSim === S.sim });
  if (again) requestDraw();
}

function poseAt(st, f, i) {
  const p = { i, p0: st.p0, x: st.x0, y: st.y0, h: st.h0, frac: 1 };
  if (st.op === 'F' || st.op === 'B') { p.x = st.x0 + (st.x1 - st.x0) * f; p.y = st.y0 + (st.y1 - st.y0) * f; }
  else if (st.op === 'L' || st.op === 'R') p.h = st.h0 + (st.h1 - st.h0) * f;
  const full = st.dur + st.pause;
  p.frac = full > 0 ? st.dur * f / full : 1;
  return p;
}
function simPose(a, now) {
  const steps = a.sim.steps;
  let t = (now - a.t0) * a.speed;
  for (let i = 0; i < steps.length; i++) {
    const st = steps[i], full = st.dur + st.pause;
    if (t < full) return poseAt(st, Math.min(1, t / Math.max(1, st.dur)), i);
    t -= full;
  }
  if (steps.length && t < 1200 * a.speed) return poseAt(steps[steps.length - 1], 1, steps.length - 1);  // ค้างท่าสุดท้ายไว้ครู่หนึ่ง
  return null;
}
function runPose(a, now) {
  const steps = a.sim.steps, i = S.runIdx;
  if (i < 0 || i >= steps.length) return null;
  return poseAt(steps[i], Math.min(1, (now - S.runIdxAt) / Math.max(1, steps[i].dur)), i);
}
function toggleSim() {
  if (S.anim && S.anim.mode === 'sim') { stopSim(); return; }
  flushEdit();
  if (!S.sim || !S.sim.steps.length) return;
  if (S.anim && S.anim.mode === 'run') { toast('หุ่นยนต์กำลังวิ่งอยู่'); return; }
  S.anim = { mode: 'sim', t0: performance.now(), speed: Math.max(1, S.sim.time / 8000), sim: S.sim };
  $('#simBtn').textContent = 'หยุดจำลอง';
  requestDraw();
}
function stopSim() {
  if (S.anim && S.anim.mode === 'sim') S.anim = null;
  $('#simBtn').textContent = 'ดูจำลอง';
  requestDraw();
}

function rrect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
function polyline(ctx, pts, X, Y, frac) {
  if (pts.length < 2) return;
  let limit = Infinity;
  if (frac !== undefined && frac < 1) {
    let tot = 0;
    for (let i = 1; i < pts.length; i++) tot += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    limit = tot * frac;
  }
  ctx.beginPath();
  ctx.moveTo(X(pts[0][0]), Y(pts[0][1]));
  let acc = 0;
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1], b = pts[i], len = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (acc + len >= limit) {
      const t = len ? (limit - acc) / len : 0;
      ctx.lineTo(X(a[0] + (b[0] - a[0]) * t), Y(a[1] + (b[1] - a[1]) * t));
      break;
    }
    ctx.lineTo(X(b[0]), Y(b[1]));
    acc += len;
  }
  ctx.stroke();
}
function drawBot(ctx, x, y, h, u) {
  const s = 10 * u;
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(-(h - 90) * D2R);
  ctx.fillStyle = COL.ink;
  rrect(ctx, -s * 1.05, -s * 0.55, s * 0.38, s, 2 * u); ctx.fill();
  rrect(ctx, s * 0.67, -s * 0.55, s * 0.38, s, 2 * u); ctx.fill();
  ctx.fillStyle = COL.motor;
  ctx.strokeStyle = COL.ink;
  ctx.lineWidth = 1.8 * u;
  rrect(ctx, -s * 0.68, -s * 0.9, s * 1.36, s * 1.75, 3.5 * u); ctx.fill(); ctx.stroke();
  ctx.fillStyle = COL.red;
  ctx.beginPath(); ctx.arc(0, -s * 0.5, s * 0.2, 0, 2 * Math.PI); ctx.fill();
  ctx.restore();
}

function renderScene(ctx, W, H, u, opt) {
  const sim = S.sim, has = !!(sim && sim.steps.length);
  const ideal = has ? S.ideal : null;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = COL.sheet;
  ctx.fillRect(0, 0, W, H);

  // ขอบเขตของภาพ หน่วยเซนติเมตร
  let minX = -20, maxX = 20, minY = -10, maxY = 30;
  if (has) {
    minX = maxX = minY = maxY = 0;
    const grow = p => { minX = Math.min(minX, p[0]); maxX = Math.max(maxX, p[0]); minY = Math.min(minY, p[1]); maxY = Math.max(maxY, p[1]); };
    sim.pts.forEach(grow);
    if (ideal) ideal.forEach(grow);
    const m = Math.max(6, 0.06 * Math.max(maxX - minX, maxY - minY));
    minX -= m; maxX += m; minY -= m; maxY += m;
  }
  const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
  const bw = Math.max(30, maxX - minX), bh = Math.max(30, maxY - minY);
  const pad = 18 * u;
  const k = Math.min((W - 2 * pad) / bw, (H - 2 * pad) / bh);
  const X = x => W / 2 + (x - cx) * k;
  const Y = y => H / 2 - (y - cy) * k;

  // จุดกริดแบบรูเบรดบอร์ด
  const g = [2, 5, 10, 20, 25, 50, 100, 200, 500, 1000].find(v => v * k >= 20 * u) || 1000;
  const d = Math.max(1.5, 2.2 * u);
  ctx.fillStyle = COL.hole;
  const x0 = cx - W / 2 / k, x1 = cx + W / 2 / k, y0 = cy - H / 2 / k, y1 = cy + H / 2 / k;
  for (let gx = Math.ceil(x0 / g) * g; gx <= x1; gx += g) {
    for (let gy = Math.ceil(y0 / g) * g; gy <= y1; gy += g) ctx.fillRect(X(gx) - d / 2, Y(gy) - d / 2, d, d);
  }

  // สเกลที่มุมซ้ายบน
  const sl = g * k, sx = 14 * u, sy = 16 * u;
  ctx.strokeStyle = COL.soft;
  ctx.lineWidth = 1.5 * u;
  ctx.beginPath();
  ctx.moveTo(sx, sy - 4 * u); ctx.lineTo(sx, sy); ctx.lineTo(sx + sl, sy); ctx.lineTo(sx + sl, sy - 4 * u);
  ctx.stroke();
  ctx.fillStyle = COL.soft;
  ctx.font = (12 * u) + 'px ' + FONT;
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'left';
  ctx.fillText(g + ' ซม.', sx + sl + 6 * u, sy - 1 * u);

  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  if (ideal && ideal.length > 1) {          // เรขาคณิตตามแผน (เส้นประ)
    ctx.setLineDash([5 * u, 5 * u]);
    ctx.strokeStyle = COL.blue;
    ctx.lineWidth = 1.6 * u;
    polyline(ctx, ideal, X, Y, opt.reveal);
    ctx.setLineDash([]);
  }
  if (has) {
    const pose = opt.pose;
    let done = null;
    if (pose) done = sim.pts.slice(0, pose.p0 + 1).concat([[pose.x, pose.y]]);
    else if (opt.full) done = sim.pts;
    if (done && done.length > 1) {           // ส่วนที่วิ่งไปแล้ว แบบปากกาไฮไลต์
      ctx.strokeStyle = 'rgba(245,196,0,.6)';
      ctx.lineWidth = 11 * u;
      polyline(ctx, done, X, Y);
    }
    ctx.strokeStyle = COL.ink;                // เส้นทางที่หุ่นยนต์จะวิ่งจริง
    ctx.lineWidth = 2.6 * u;
    polyline(ctx, sim.pts, X, Y, opt.reveal);
    const e = sim.pts[sim.pts.length - 1];
    if (sim.gap > 1 && opt.reveal >= 1) {
      const q = 7 * u;
      ctx.fillStyle = COL.ink;
      ctx.fillRect(X(e[0]) - q / 2, Y(e[1]) - q / 2, q, q);
    }
  }
  // จุดเริ่ม
  ctx.strokeStyle = COL.blue;
  ctx.lineWidth = 2.2 * u;
  ctx.fillStyle = COL.sheet;
  ctx.beginPath(); ctx.arc(X(0), Y(0), 15 * u, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
  const bp = opt.pose || { x: 0, y: 0, h: 90 };
  drawBot(ctx, X(bp.x), Y(bp.y), bp.h, u);
  if (!opt.pose) {
    ctx.fillStyle = COL.blue;
    ctx.font = '600 ' + (12 * u) + 'px ' + FONT;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText('เริ่ม', X(0), Y(0) + 19 * u);
    ctx.textAlign = 'left';
  }
}

// ภาพเส้นทางขนาดเล็ก แนบไปให้ AI ดูตอนขอแก้
function snapshot() {
  const c = document.createElement('canvas');
  c.width = 512; c.height = 512;
  renderScene(c.getContext('2d'), 512, 512, 1.6, { pose: null, reveal: 1, full: false });
  return c.toDataURL('image/png').split(',')[1];
}

// ===================== AI (Claude) =====================
function aiMsg(text, bad) {
  const el = $('#aiMsg');
  el.hidden = !text;
  el.textContent = text || '';
  el.classList.toggle('bad', !!bad);
}
function setAiBusy(on, label) {
  S.aiBusy = on;
  const b = $('#aiBtn');
  b.disabled = on;
  $('#fixBtn').disabled = on;
  $('#aiCancel').hidden = !on;
  clearInterval(S.aiTimer);
  if (!on) { b.textContent = 'ให้ AI คิดเส้นทาง'; return; }
  const t0 = Date.now();
  const tick = () => { b.textContent = (label || 'AI กำลังคิด') + ' ' + Math.round((Date.now() - t0) / 1000) + ' วิ'; };
  tick();
  S.aiTimer = setInterval(tick, 500);
}
function openAiSettings() {
  const p = $('#aiPanel');
  p.open = true;
  p.scrollIntoView({ behavior: reduceMotion() ? 'auto' : 'smooth', block: 'start' });
  setTimeout(() => $('#key').focus({ preventScroll: true }), 350);
}
function apiError(status, j) {
  const m = j && j.error && j.error.message ? String(j.error.message) : '';
  const map = {
    401: 'API key ไม่ถูกต้อง ตรวจคีย์ในตั้งค่า AI', 403: 'คีย์นี้ไม่มีสิทธิ์ใช้งานโมเดลนี้',
    404: 'ไม่พบโมเดลชื่อนี้ ตรวจชื่อโมเดลในตั้งค่า AI', 413: 'ข้อมูลที่ส่งใหญ่เกินไป',
    429: 'เรียกใช้ถี่เกินไป รอสักครู่แล้วลองใหม่', 500: 'เซิร์ฟเวอร์ AI ขัดข้อง ลองใหม่อีกครั้ง',
    529: 'เซิร์ฟเวอร์ AI มีงานล้น ลองใหม่อีกครั้ง'
  };
  let t = map[status] || 'AI ตอบกลับด้วยข้อผิดพลาด ' + status;
  if (/credit/i.test(m)) t = 'เครดิต API หมด เติมเครดิตใน Claude Console ก่อน';
  return m ? t + ' (' + m + ')' : t;
}
async function readJson(r) { try { return await r.json(); } catch (e) { return null; } }

async function callClaude(messages, opts) {
  opts = opts || {};
  const key = $('#key').value.trim();
  if (!key) throw new UserError('ยังไม่มี API key ใส่คีย์ในหัวข้อตั้งค่า AI ก่อน');
  const body = { model: $('#model').value.trim() || DEFAULT_MODEL, max_tokens: opts.maxTokens || 16000, messages };
  if (!opts.noSystem) body.system = SYSTEM;
  const effort = opts.effort || $('#effort').value;
  if (effort && effort !== 'auto') body.output_config = { effort };
  const ctl = new AbortController();
  let timedOut = false;
  S.aiAbort = ctl;
  const timer = setTimeout(() => { timedOut = true; ctl.abort(); }, 180000);
  const send = () => fetch(API_URL, {
    method: 'POST', signal: ctl.signal, body: JSON.stringify(body),
    headers: {
      'content-type': 'application/json',
      'x-api-key': key,
      'anthropic-version': '2023-06-01',
      'anthropic-dangerous-direct-browser-access': 'true'   // จำเป็นเมื่อเรียกจากเบราว์เซอร์โดยตรง
    }
  });
  try {
    let r = await send();
    let j = await readJson(r);
    if (r.status === 400 && body.output_config && /effort|output_config/i.test(JSON.stringify(j || ''))) {
      delete body.output_config;             // บางโมเดลไม่รองรับการตั้งความลึก ส่งใหม่โดยไม่ใส่
      r = await send();
      j = await readJson(r);
    }
    if (!r.ok) throw new UserError(apiError(r.status, j));
    const text = ((j && j.content) || []).filter(b => b.type === 'text').map(b => b.text).join('\n').trim();
    if (!text) {
      if (j && j.stop_reason === 'max_tokens') throw new UserError('AI คิดนานจนเกินขีดจำกัด ลองลดความลึกในการคิด หรือขอรูปที่ง่ายลง');
      if (j && j.stop_reason === 'refusal') throw new UserError('AI ไม่รับคำขอนี้ ลองเปลี่ยนคำสั่ง');
      throw new UserError('AI ไม่ได้ตอบข้อความกลับมา ลองอีกครั้ง');
    }
    return text;
  } catch (e) {
    if (e instanceof UserError) throw e;
    if (e.name === 'AbortError') throw new UserError(timedOut ? 'AI ใช้เวลานานเกินไป ลองลดความลึกในการคิด' : 'ยกเลิกแล้ว');
    throw new UserError('ติดต่อ AI ไม่ได้ ตรวจว่ามือถือมีอินเทอร์เน็ต ถ้าต่อ WiFi ของหุ่นยนต์โดยตรงจะใช้ AI ไม่ได้');
  } finally {
    clearTimeout(timer);
    S.aiAbort = null;
  }
}

function parsePlan(text) {
  const a = text.indexOf('{'), b = text.lastIndexOf('}');
  if (a < 0 || b <= a) throw new UserError('AI ไม่ได้ตอบเป็นแผนการวิ่ง ลองกดอีกครั้ง');
  let p;
  try { p = JSON.parse(text.slice(a, b + 1)); } catch (e) { throw new UserError('อ่านแผนจาก AI ไม่ออก ลองกดอีกครั้ง'); }
  if (!p || typeof p !== 'object') throw new UserError('อ่านแผนจาก AI ไม่ออก ลองกดอีกครั้ง');
  if (!Array.isArray(p.steps)) p.steps = [];
  p.name = typeof p.name === 'string' ? p.name.slice(0, 60) : '';
  p.note = typeof p.note === 'string' ? p.note.slice(0, 400) : '';
  return p;
}
function withImage(text) {
  try {
    return [{ type: 'image', source: { type: 'base64', media_type: 'image/png', data: snapshot() } }, { type: 'text', text }];
  } catch (e) { return text; }
}

async function askAI(refine) {
  if (S.aiBusy) return;
  flushEdit();
  const input = refine ? $('#fix') : $('#ask');
  const text = input.value.trim();
  if (!text) {
    toast(refine ? 'พิมพ์ก่อนว่าอยากแก้ตรงไหน' : 'พิมพ์ก่อนว่าอยากให้หุ่นยนต์วิ่งเป็นรูปอะไร');
    input.focus();
    return;
  }
  if (!$('#key').value.trim()) {
    toast('ใส่ API key ของ Claude ก่อน', true);
    openAiSettings();
    return;
  }
  aiMsg('');
  let msgs;
  if (refine) {
    msgs = S.convo ? S.convo.slice() : [];
    let ctx = '';
    if (!S.convo) {
      ctx = S.plan && $('#cmds').value.trim() === S.compiledText.trim()
        ? 'Current plan: ' + JSON.stringify({ name: S.plan.name, closed: S.plan.closed, exact: S.plan.exact, size_cm: S.plan.size_cm, steps: S.plan.steps }) + '\n'
        : 'Current robot commands (F/B cm, L/R degrees, W ms): ' + $('#cmds').value.trim() + '\n';
    }
    msgs.push({ role: 'user', content: withImage(ctx + 'The user wants this change: "' + text + '". The attached image shows the current simulated route. Return the complete updated plan as JSON.') });
  } else {
    msgs = [{ role: 'user', content: 'User request: ' + text }];
  }
  setAiBusy(true);
  try {
    let reply = await callClaude(msgs);
    msgs.push({ role: 'assistant', content: reply });
    let plan = parsePlan(reply);
    if (!plan.steps.length) {
      aiMsg(plan.note || 'AI บอกว่าหุ่นยนต์ทำคำขอนี้ไม่ได้', true);
      S.convo = msgs;
      return;
    }
    let res = compilePlan(plan);
    showPlan(plan, res);
    // ตรวจอัตโนมัติ: รูปที่ควรปิดแต่จำลองแล้วไม่กลับมาที่จุดเริ่ม ให้ AI แก้หนึ่งรอบ
    if (plan.closed && res.gapRatio > 0.05) {
      setAiBusy(true, 'AI กำลังตรวจแก้');
      msgs.push({ role: 'user', content: withImage('Automatic check: I simulated your plan. It ends ' + res.gapUnits.toFixed(1) + ' units from its start point while the shape is about ' + res.side.toFixed(1) + ' units across (your units, before rescaling), so the outline is not closed. The attached image shows the result. Fix the geometry and return the complete corrected plan as JSON.') });
      try {
        const reply2 = await callClaude(msgs);
        const plan2 = parsePlan(reply2);
        const res2 = plan2.steps.length ? compilePlan(plan2) : null;
        msgs.push({ role: 'assistant', content: reply2 });
        if (res2 && res2.gapRatio < res.gapRatio) {
          plan = plan2;
          res = res2;
          showPlan(plan, res);
        }
      } catch (e) {
        if (msgs[msgs.length - 1].role === 'user') msgs.pop();
        if (e.message === 'ยกเลิกแล้ว') throw e;
        aiMsg('ตรวจแก้รอบสองไม่สำเร็จ จึงใช้แผนแรกไปก่อน (' + e.message + ')');
      }
    }
    S.convo = msgs;
    if (refine) input.value = '';
    if (res.gapRatio > 0.05 && plan.closed) aiMsg('รูปนี้ยังปิดไม่สนิท ลองพิมพ์บอกให้ AI แก้ หรือกดคิดใหม่');
  } catch (e) {
    aiMsg(e.message, true);
    if (refine) toast(e.message, true);
  } finally {
    setAiBusy(false);
  }
}

async function testAI() {
  const out = $('#aiTestOut');
  out.hidden = false;
  out.classList.remove('bad');
  out.textContent = 'กำลังทดสอบ';
  try {
    const t = await callClaude([{ role: 'user', content: 'Reply with the single word OK.' }], { maxTokens: 1024, effort: 'low', noSystem: true });
    out.textContent = 'เชื่อมต่อได้ โมเดล ' + ($('#model').value.trim() || DEFAULT_MODEL) + ' ตอบว่า ' + t.slice(0, 40);
  } catch (e) {
    out.textContent = e.message;
    out.classList.add('bad');
  }
}

// ===================== ค่าปรับเทียบ =====================
function fillCfg() {
  $$('[data-cfg]').forEach(el => {
    if (document.activeElement === el) return;
    const v = S.cfg[el.dataset.cfg];
    if (v === undefined) return;
    if (el.type === 'checkbox') el.checked = !!Number(v);
    else if (el.dataset.cfg === 'msPerCm' || el.dataset.cfg === 'msPerDeg') el.value = Number(v).toFixed(2);
    else el.value = v;
  });
  updateOutputs();
}
function updateOutputs() {
  $$('[data-out]').forEach(o => { o.textContent = pct($('[data-cfg="' + o.dataset.out + '"]').value); });
  const t = Number($('[data-cfg="trim"]').value);
  $('#trimOut').textContent = t === 0 ? 'ล้อซ้ายขวาแรงเท่ากัน' : t > 0 ? 'ลดแรงล้อซ้าย ' + t + '%' : 'ลดแรงล้อขวา ' + (-t) + '%';
  $('#spdOut').textContent = pct($('#spd').value);
  $('#sizeOut').textContent = $('#size').value + ' ซม.';
  $('#resOut').textContent = $('#res').value + ' องศา';
}
async function saveCfg(obj, okMsg) {
  try {
    const c = await robot('/api/config?' + new URLSearchParams(obj).toString(), null, 3000);
    Object.assign(S.cfg, c);
    fillCfg();
    resim();
    toast(okMsg || 'บันทึกแล้ว');
  } catch (e) {
    toast('บันทึกไม่สำเร็จ ติดต่อหุ่นยนต์ไม่ได้', true);
    fillCfg();
  }
}

// ===================== ผูกปุ่มต่าง ๆ =====================
function bind() {
  $('#aiBtn').addEventListener('click', () => askAI(false));
  $('#fixBtn').addEventListener('click', () => askAI(true));
  $('#aiCancel').addEventListener('click', () => { if (S.aiAbort) S.aiAbort.abort(); });
  const enter = (el, fn) => el.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); fn(); }
  });
  enter($('#ask'), () => askAI(false));
  enter($('#fix'), () => askAI(true));
  $$('[data-say]').forEach(b => b.addEventListener('click', () => { $('#ask').value = b.dataset.say; $('#ask').focus(); }));
  $$('[data-preset]').forEach(b => b.addEventListener('click', () => usePreset(b.dataset.preset)));

  $('#size').addEventListener('input', updateOutputs);
  $('#size').addEventListener('change', () => { store.set('size', $('#size').value); recompile(true); });
  $('#res').addEventListener('input', updateOutputs);
  $('#res').addEventListener('change', () => { store.set('res', $('#res').value); recompile(false); });
  $('#spd').addEventListener('input', () => { updateOutputs(); store.set('spd', $('#spd').value); });

  $('#cmds').addEventListener('input', onCmdsInput);
  $('#runBtn').addEventListener('click', () => { flushEdit(); runCmds($('#cmds').value, true); });
  $('#simBtn').addEventListener('click', toggleSim);
  $('#clearBtn').addEventListener('click', clearRoute);
  $('#copyBtn').addEventListener('click', () => {
    const t = $('#cmds').value.trim();
    if (!t) return;
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(t).then(() => toast('คัดลอกแล้ว'), () => toast('คัดลอกไม่ได้', true));
      return;
    }
    const ta = $('#cmds');                   // หน้า http ธรรมดาใช้ clipboard API ไม่ได้ จึงใช้วิธีเลือกข้อความ
    ta.focus();
    ta.select();
    try { document.execCommand('copy'); toast('คัดลอกแล้ว'); } catch (e) { toast('เลือกข้อความไว้แล้ว กดคัดลอกเองได้เลย'); }
  });

  $('#stopBtn').addEventListener('click', stopEverything);
  $('#retryWifi').addEventListener('click', () => {
    if (!confirm('หุ่นยนต์จะรีสตาร์ตแล้วลองต่อ WiFi บ้านประมาณ 30 วินาที ถ้าต่อสำเร็จ WiFi Robot-AI จะหายไป ให้มือถือกลับไปต่อ WiFi บ้านแล้วเปิดหน้านี้ด้วยที่อยู่ของหุ่นยนต์ ถ้าไม่สำเร็จ Robot-AI จะกลับมา ทำต่อไหม?')) return;
    robot('/api/restart', null, 2000).catch(() => {});
    toast('กำลังรีสตาร์ตหุ่นยนต์');
  });
  $('#padStop').addEventListener('click', stopEverything);
  $$('[data-drive]').forEach(btn => {
    btn.addEventListener('pointerdown', e => {
      e.preventDefault();
      try { btn.setPointerCapture(e.pointerId); } catch (err) {}
      startDrive(btn.dataset.drive, btn);
    });
    const end = () => { if (S.manual && S.manual.btn === btn) stopDrive(); };
    ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(t => btn.addEventListener(t, end));
    btn.addEventListener('contextmenu', e => e.preventDefault());
  });
  const KEYS = { ArrowUp: 'F', KeyW: 'F', ArrowDown: 'B', KeyS: 'B', ArrowLeft: 'L', KeyA: 'L', ArrowRight: 'R', KeyD: 'R' };
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { stopEverything(); return; }
    const tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select' || e.target.isContentEditable) return;
    if (e.code === 'Space') { e.preventDefault(); stopEverything(); return; }
    const d = KEYS[e.code];
    if (!d || e.metaKey || e.ctrlKey || e.altKey) return;
    e.preventDefault();
    if (!e.repeat) startDrive(d, $('[data-drive="' + d + '"]'));
  });
  document.addEventListener('keyup', e => { if (S.manual && S.manual.d === KEYS[e.code]) stopDrive(); });
  window.addEventListener('blur', stopDrive);
  document.addEventListener('visibilitychange', () => { if (document.hidden) stopDrive(); else poll(); });

  $$('[data-cfg]').forEach(el => {
    el.addEventListener('input', updateOutputs);
    el.addEventListener('change', () => {
      const k = el.dataset.cfg;
      saveCfg({ [k]: el.type === 'checkbox' ? (el.checked ? 1 : 0) : el.value });
    });
  });
  $('#cfgReset').addEventListener('click', () => {
    if (confirm('คืนค่าปรับเทียบทั้งหมดเป็นค่าเริ่มต้น?')) saveCfg({ reset: 1 }, 'คืนค่าเริ่มต้นแล้ว');
  });
  $('#calDistRun').addEventListener('click', () => runCmds('F' + $('#calDist').value, false));
  $('#calTurnRun').addEventListener('click', () => runCmds('R360', false));
  $('#calStraight').addEventListener('click', () => runCmds('F100', false));
  $('#calDistSave').addEventListener('click', () => {
    const want = Number($('#calDist').value), got = parseFloat($('#calDistGot').value);
    if (!(got > 0)) { toast('ใส่ระยะที่วัดได้จริงก่อน', true); return; }
    const v = S.cfg.msPerCm * want / got;
    saveCfg({ msPerCm: v.toFixed(3) }, 'ปรับเป็น ' + v.toFixed(2) + ' มิลลิวินาทีต่อ ซม. แล้ว');
    $('#calDistGot').value = '';
  });
  $('#calTurnSave').addEventListener('click', () => {
    const got = parseFloat($('#calTurnGot').value);
    if (!(got > 0)) { toast('ใส่มุมที่หมุนได้จริงก่อน', true); return; }
    const v = S.cfg.msPerDeg * 360 / got;
    saveCfg({ msPerDeg: v.toFixed(3) }, 'ปรับเป็น ' + v.toFixed(2) + ' มิลลิวินาทีต่อองศา แล้ว');
    $('#calTurnGot').value = '';
  });

  $('#key').addEventListener('change', () => store.set('key', $('#key').value.trim()));
  $('#keyShow').addEventListener('click', () => {
    const k = $('#key'), show = k.type === 'password';
    k.type = show ? 'text' : 'password';
    $('#keyShow').textContent = show ? 'ซ่อน' : 'แสดง';
  });
  $('#keyDel').addEventListener('click', () => { $('#key').value = ''; store.del('key'); toast('ลบคีย์ออกจากเบราว์เซอร์นี้แล้ว'); });
  $('#model').addEventListener('change', () => store.set('model', $('#model').value.trim()));
  $('#effort').addEventListener('change', () => store.set('effort', $('#effort').value));
  $('#aiTest').addEventListener('click', testAI);

  window.addEventListener('resize', requestDraw);
  if (window.ResizeObserver) new ResizeObserver(requestDraw).observe($('#cv'));
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(requestDraw);
}

function init() {
  $('#key').value = store.get('key', '');
  $('#model').value = store.get('model', DEFAULT_MODEL);
  $('#effort').value = store.get('effort', 'medium');
  $('#res').value = store.get('res', '20');
  $('#size').value = store.get('size', '50');
  $('#spd').value = store.get('spd', '700');
  $('#cmds').value = store.get('cmds', '');
  bind();
  fillCfg();
  resim();
  robot('/api/config', null, 3000).then(c => { Object.assign(S.cfg, c); fillCfg(); resim(); }).catch(() => {});
  poll();
  pollLoop();
}
init();
})();
</script>
</body>
</html>
)HTML";
