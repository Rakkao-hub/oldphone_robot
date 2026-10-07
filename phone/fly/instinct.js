// instinct.js : ชั้นสัญชาตญาณของแซน: เหลือบตา หันตัวตามสิ่งที่ขยับ สนใจของใหม่ และสะดุ้งถอยหนีของที่พุ่งเข้าหา
//
//   กล้องหน้า -> มีอะไรขยับทางซ้ายหรือขวาของภาพ -> ความเคยชิน -> สมองแมลงวันจิ๋ว (fly_brain.js) -> เหลือบตาไปทางนั้น
//   ถ้าสมองเอียงไปข้างเดียวแรง ๆ ต่อเนื่อง -> ขอ brain.py หันตัวไปทางนั้นครั้งละนิด (brain.py ตัดสินอีกทีว่าหันได้ไหม)
//   ของที่ไม่เคยเห็น (curiosity.js) -> เป็นสิ่งเร้าเข้าสมองเหมือนของที่ขยับ
//   ภาพเปลี่ยนมากขึ้นเรื่อย ๆ โดยเริ่มจากกลางภาพ (ของพุ่งเข้าหากล้อง) -> สะดุ้ง ขอ brain.py ถอยหลังนิดหนึ่ง
//
// - ทำงานเฉพาะตอนแซนตื่น ว่าง และไม่เห็นหน้าใคร (ถ้าเห็นหน้า ตาจะมองหน้าคนแบบเดิม)
// - ความเคยชิน: ของที่ขยับซ้ำ ๆ ฝั่งเดิม (พัดลม ทีวี) จะถูกสนใจน้อยลงเรื่อย ๆ หยุดขยับสักพักแล้วกลับมาสนใจใหม่
// - อารมณ์จากคำชม/ตำหนิ: ปกติหรืออารมณ์ดี = มองไปหาสิ่งที่ขยับ, งอน (ถูกดุ) = สลับสายไฟเป็นแบบไขว้ มองหนี
// - ภาพขยับทั้งจอพร้อมกัน (แซนหมุนตัวเอง หรือมีคนเปิดปิดไฟ) จะถูกมองข้าม
// - ทุก 1 นาทีเขียนลง brain.log ว่าสมองใช้เวลาคำนวณเท่าไร ไว้ดูว่ามือถือรับไหวไหม
import { FlyBrain } from './fly_brain.js';
import { createCuriosity } from './curiosity.js';

const TICK_MS = 100;           // ดูภาพและเดินสมองทุกกี่มิลลิวินาที
const GRID_W = 32, GRID_H = 24; // ย่อภาพกล้องเหลือเท่านี้ก่อนเทียบ (เบาเครื่อง และไม่ไวต่อจุดรบกวนเล็ก ๆ)
const PIXEL_CHANGED = 18;      // จุดที่ความสว่างต่างจากภาพก่อนหน้าเกินนี้ (จาก 255) ถือว่าขยับ
const INPUT_GAIN = 3;          // สัดส่วนจุดที่ขยับในครึ่งภาพ x ค่านี้ = ค่าเซนเซอร์ (สูงสุด 1)
const GLOBAL_CHANGE = 0.45;    // ทั้งสองครึ่งขยับเกินสัดส่วนนี้ = ภาพขยับทั้งจอ ไม่ใช่สิ่งที่น่ามอง
const TAU_UP = 3;              // เห็นของขยับต่อเนื่องกี่วินาทีถึงเริ่มชิน
const TAU_DOWN = 30;           // เลิกขยับกี่วินาทีถึงหายชิน
const GAZE_MIN = 0.25;         // สมองต้องเอียงไปข้างหนึ่งเกินนี้ ตาถึงจะขยับ
const GAZE_GAIN = 0.9;         // เหลือบแรงแค่ไหน
const GAZE_HOLD_MS = 350;      // ผลจากสมองเก่ากว่านี้ไม่ใช้
const SULK_BELOW = -0.3;       // อารมณ์ต่ำกว่านี้ = งอน
const BODY_MIN = 0.5;          // สมองต้องเอียงไปข้างหนึ่งเกินนี้ ถึงจะคิดหันตัว (ตาใช้แค่ GAZE_MIN)
const BODY_TICKS = 4;          // ต้องเอียงข้างเดิมติดกันกี่รอบ (4 รอบ = 0.4 วิ) กันหันเพราะแวบเดียว
const BODY_GAP_MS = 3000;      // ขอหันตัวได้อย่างมากทุกกี่มิลลิวินาที (brain.py กำหนดระยะจริงตามความจำคำชม/ตำหนิ)
const BODY_DEG = [25, 45];     // หันกี่องศา: เอียงน้อย -> 25, เอียงสุด -> 45
const BODY_SETTLE_MS = 1500;   // หลังหันตัว หยุดดูภาพนานเท่านี้ (ภาพทั้งจอเลื่อนตอนหมุน)
const CURIOUS_GAIN = 0.6;       // ความสนใจของใหม่ x ค่านี้ = ค่าเซนเซอร์ (ของที่ขยับสูงสุด 1)
const STILL_BELOW = 0.03;      // ภาพเปลี่ยนน้อยกว่าสัดส่วนนี้ = ภาพนิ่ง ใช้ดูของใหม่ได้
const LOOM_TICKS = 4;          // ดูย้อนหลังกี่รอบ: ส่วนที่ถูกบังต้องกว้างขึ้นทุกรอบ (0.4 วิ)
const LOOM_START = 0.15;       // รอบแรกถูกบังน้อยกว่านี้ (ก่อนหน้านั้นยังสงบ)
const LOOM_END = 0.5;          // รอบสุดท้ายถูกบังเกินครึ่งภาพ (ของมาใกล้มากแล้ว)
const LOOM_CENTER = 1.5;       // ช่วงแรกกลางภาพต้องเปลี่ยนมากกว่าทั้งภาพเท่านี้ (พุ่งตรงเข้ามา ไม่ใช่เดินผ่านข้าง ๆ)
const STARTLE_GAP_MS = 8000;   // สะดุ้งได้อย่างมากทุกกี่มิลลิวินาที
const STARTLE_SETTLE_MS = 2000;
const REPORT_MS = 60000;

export async function createInstinct({ video, report, canRun, canTurn = () => false, onTurn = async () => false,
                                       onCurious = () => { }, onStartle = () => { } }) {
  const circuit = await (await fetch('/fly/dnp20.json')).json();
  const brain = new FlyBrain(circuit, { sensorType: 'VS', seed: (Date.now() & 0xffff) + 1 });

  const canvas = document.createElement('canvas');
  canvas.width = GRID_W; canvas.height = GRID_H;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  const gray = new Uint8Array(GRID_W * GRID_H), prev = new Uint8Array(GRID_W * GRID_H);
  const half = GRID_W / 2, halfPixels = half * GRID_H;
  const curiosity = createCuriosity({ gridW: GRID_W, gridH: GRID_H, onNovel: side => { if (canRun()) onCurious(side); } });

  let on = true, mood = 0, havePrev = false, pausedUntil = 0, held = false;
  let habL = 0, habR = 0;                  // ความเคยชินของแต่ละฝั่ง (0 = สดใหม่, ใกล้ 1 = ชินแล้ว)
  let inL = 0, inR = 0, turn = 0, turnAt = -1e9, quiet = 99, looking = false;
  let streak = 0, bodyAt = -1e9;          // streak: เอียงข้างเดิมมากี่รอบ (+ ซ้าย, - ขวา)
  let lastPx = null, still = false, curL = 0, curR = 0, startleAt = -1e9;
  const recent = [];                       // ภาพขาวดำ LOOM_TICKS + 1 รอบล่าสุด (ใช้จับของพุ่งเข้าหา)
  const stats = { ticks: 0, ms: 0, maxMs: 0, looks: 0, turns: 0, startles: 0, global: 0, since: performance.now(), first: true };

  function sense(now) {
    ctx.drawImage(video, 0, 0, GRID_W, GRID_H);
    const px = ctx.getImageData(0, 0, GRID_W, GRID_H).data;
    let changedL = 0, changedR = 0;
    for (let i = 0; i < gray.length; i++) {
      gray[i] = (px[i * 4] * 77 + px[i * 4 + 1] * 150 + px[i * 4 + 2] * 29) >> 8;
      if (havePrev && Math.abs(gray[i] - prev[i]) > PIXEL_CHANGED) {
        if (i % GRID_W < half) changedL++; else changedR++;
      }
    }
    prev.set(gray);
    lastPx = px;
    recent.push(gray.slice());
    if (recent.length > LOOM_TICKS + 1) recent.shift();
    if (!havePrev) { havePrev = true; recent.length = 0; still = false; return [0, 0]; }
    const fracL = changedL / halfPixels, fracR = changedR / halfPixels;
    still = (fracL + fracR) / 2 < STILL_BELOW;
    if (looming()) { startle(now); return [0, 0]; }
    if (fracL > GLOBAL_CHANGE && fracR > GLOBAL_CHANGE) { stats.global++; return [0, 0]; }
    return [Math.min(1, fracL * INPUT_GAIN), Math.min(1, fracR * INPUT_GAIN)];
  }

  // ส่วนของภาพ a ที่ต่างจากภาพตั้งต้น ref: { all: ทั้งภาพ, mid: กลางภาพ }
  function covered(a, ref) {
    let all = 0, mid = 0;
    for (let i = 0; i < a.length; i++) {
      if (Math.abs(a[i] - ref[i]) <= PIXEL_CHANGED) continue;
      all++;
      const x = i % GRID_W, y = (i / GRID_W) | 0;
      if (x >= GRID_W / 4 && x < GRID_W * 3 / 4 && y >= GRID_H / 4 && y < GRID_H * 3 / 4) mid++;
    }
    return { all: all / a.length, mid: mid / (a.length / 4) };
  }

  // ของพุ่งเข้าหา: เทียบกับภาพก่อนเริ่ม ส่วนที่ถูกบังกว้างขึ้นทุกรอบ จนเกินครึ่งภาพ และเริ่มบังจากกลางภาพก่อน
  // (เปิดไฟ = เปลี่ยนทีเดียวทั้งภาพ, คนเดินผ่าน = เริ่มจากขอบ, แซนหมุนตัวเอง = หยุดดูภาพอยู่แล้ว)
  function looming() {
    if (recent.length < LOOM_TICKS + 1) return false;
    const c = recent.slice(1).map(a => covered(a, recent[0]));
    for (let i = 1; i < c.length; i++) if (c[i].all <= c[i - 1].all) return false;
    return c[0].all < LOOM_START && c[c.length - 1].all > LOOM_END &&
      c[0].all > 0.005 && c[0].mid >= c[0].all * LOOM_CENTER;
  }

  function startle(now) {
    recent.length = 0;
    if (now - startleAt < STARTLE_GAP_MS) return;
    startleAt = now;
    stats.startles++;
    pausedUntil = Math.max(pausedUntil, now + STARTLE_SETTLE_MS);
    curiosity.reset();
    onStartle();
  }

  function tick() {
    const now = performance.now();
    const active = on && !held && now >= pausedUntil && video.readyState >= 2 && canRun();
    if (active) {
      [inL, inR] = sense(now);
      [curL, curR] = now >= pausedUntil ? curiosity.look(lastPx, still, now) : [0, 0];
    } else { inL = inR = 0; curL = curR = 0; havePrev = false; }

    // ความเคยชิน: เพิ่มตามสิ่งที่เห็น ลดเองตามเวลา (คิดต่อแม้ตอนพัก จะได้หายชินระหว่างที่ไม่ได้มอง)
    const dt = TICK_MS / 1000;
    habL += (inL * (1 - habL) / TAU_UP - habL / TAU_DOWN) * dt;
    habR += (inR * (1 - habR) / TAU_UP - habR / TAU_DOWN) * dt;
    // ความอยากรู้บวกเข้าไปทีหลัง ความเคยชินกับของที่ขยับจึงไม่ไปลดความสนใจของใหม่
    const effL = Math.min(1, inL * (1 - habL) + CURIOUS_GAIN * curL), effR = Math.min(1, inR * (1 - habR) + CURIOUS_GAIN * curR);

    // ไม่มีอะไรขยับมาครึ่งวินาทีแล้ว สมองเงียบสนิทแน่นอน ไม่ต้องคำนวณ (ประหยัดแบต)
    quiet = effL > 0 || effR > 0 ? 0 : quiet + 1;
    if (quiet > 5) { turn = 0; streak = 0; brain.rateL = brain.rateR = 0; return report_(now); }

    const t0 = performance.now();
    turn = brain.step(effL, effR, TICK_MS).turn;
    const spent = performance.now() - t0;
    turnAt = now;
    stats.ticks++; stats.ms += spent; stats.maxMs = Math.max(stats.maxMs, spent);
    bodyCheck(now);
    report_(now);
  }

  // หันตัว: turn บวก = ของขยับอยู่ซ้ายของภาพ -> หันซ้าย (ทิศเดียวกับโหมดตามหน้า) ตอนงอนสายไขว้ จึงหันหนีแทน
  function bodyCheck(now) {
    const side = Math.abs(turn) >= BODY_MIN ? Math.sign(turn) : 0;
    streak = side && Math.sign(streak) === side ? streak + side : side;
    if (Math.abs(streak) < BODY_TICKS || now - bodyAt < BODY_GAP_MS || !canTurn()) return;
    const k = Math.min(1, (Math.abs(turn) - BODY_MIN) / (1 - BODY_MIN));
    const deg = Math.round(BODY_DEG[0] + (BODY_DEG[1] - BODY_DEG[0]) * k);
    bodyAt = now; streak = 0;
    onTurn(turn > 0 ? 'L' : 'R', deg).then(ok => {
      if (!ok) return;   // brain.py ไม่ให้หัน (เพิ่งหันไป / คนเพิ่งสั่ง) ดูภาพต่อตามปกติ
      stats.turns++;
      pausedUntil = Math.max(pausedUntil, performance.now() + BODY_SETTLE_MS);   // ความอยากรู้ค้างไว้ หันเสร็จแล้วดูต่อ
    }, () => { });
  }

  function report_(now) {
    if (now - stats.since < (stats.first ? 15000 : REPORT_MS)) return;
    if (stats.ticks) {
      report(`สัญชาตญาณ: สมองคำนวณเฉลี่ย ${(stats.ms / stats.ticks).toFixed(2)} ms ต่อรอบ (สูงสุด ${stats.maxMs.toFixed(1)}) · ` +
        `${stats.ticks} รอบ · เหลือบตา ${stats.looks} ครั้ง · หันตัว ${stats.turns} ครั้ง · สะดุ้ง ${stats.startles} ครั้ง · มองข้ามภาพขยับทั้งจอ ${stats.global} ครั้ง · อารมณ์ ${mood}`);
    }
    report(curiosity.summary());
    Object.assign(stats, { ticks: 0, ms: 0, maxMs: 0, looks: 0, turns: 0, startles: 0, global: 0, since: now, first: false });
  }

  setInterval(tick, TICK_MS);
  report(`สัญชาตญาณพร้อม: สมองแมลงวัน ${brain.n} เซลล์ ${brain.outW.length} สายเชื่อม`);

  return {
    // ตาควรเหลือบไปทางไหน: คืนค่า -1 ถึง 1 (แบบเดียวกับ tgt.lx ของหน้าแซน) หรือ null = ไม่มีอะไรน่ามอง
    // ของขยับทางซ้ายของภาพ -> ค่าบวก ซึ่งตรงกับที่ face.html ใช้มองตามหน้าคน (lx = -x)
    gaze(now) {
      const want = on && now - turnAt < GAZE_HOLD_MS && Math.abs(turn) >= GAZE_MIN;
      if (want && !looking) stats.looks++;
      looking = want;
      return want ? Math.max(-1, Math.min(1, turn * GAZE_GAIN)) : null;
    },
    // รับสถานะจาก brain.py ({instinct, mood} ที่มากับ /api/state และ /api/hear)
    update(state) {
      if (typeof state.instinct === 'boolean' && state.instinct !== on) {
        on = state.instinct;
        report('สัญชาตญาณ: ' + (on ? 'เปิด' : 'ปิด'));
      }
      if (typeof state.mood === 'number') {
        mood = state.mood;
        const sulk = mood <= SULK_BELOW;
        if (sulk !== brain.crossed) {
          brain.setCrossed(sulk);
          report('สัญชาตญาณ: ' + (sulk ? 'งอน สลับเป็นสายไขว้ (มองหนี)' : 'หายงอน กลับเป็นสายตรง (มองหา)'));
        }
      }
    },
    // หยุดรับภาพชั่วคราว (เช่นตอนแซนเพิ่งได้คำสั่งขยับ ภาพทั้งจอจะเลื่อน)
    pause(ms) { pausedUntil = Math.max(pausedUntil, performance.now() + ms); },
    // หยุดดูภาพระหว่างรถขยับเพราะสำรวจ/ภารกิจ (ภาพเลื่อนทั้งจอ ดูเหมือนของพุ่งเข้าหา) ปล่อยแล้วรอภาพนิ่งอีกนิด
    hold(v) {
      held = !!v;
      if (!held) pausedUntil = Math.max(pausedUntil, performance.now() + 500);
    },
    // สมองแมลงวันอยากไปทางไหนตอนนี้: บวก = ซ้าย, ลบ = ขวา, 0 = ไม่มีอะไรกระตุ้น (การเดินสำรวจใช้เลือกทิศ)
    // รวมทั้งของที่ขยับและของใหม่ และตอนงอนสายไขว้ = อยากไปทางตรงข้าม
    lean(now = performance.now()) { return on && now - turnAt < 1500 ? turn : 0; },
    forgetSeen() { curiosity.forget(); },
    debug() { return { curiosity: curiosity.debug(), curL, curR, still, on, mood, crossed: brain.crossed, inL, inR, habL, habR, turn, streak, quiet, ticks: stats.ticks, global: stats.global }; },
  };
}
