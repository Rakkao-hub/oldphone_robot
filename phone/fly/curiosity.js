// curiosity.js : ความอยากรู้ของแซน สนใจสิ่งที่ไม่เคยเห็น
//
//   ภาพกล้อง (ครึ่งซ้าย / ครึ่งขวา) -> ลายนิ้วมือของภาพ -> เทียบกับภาพที่เคยเห็น -> ไม่เหมือนอะไรเลย = ของใหม่ น่าสนใจ
//
// - ความสนใจ (0 ถึง 1) ของแต่ละฝั่งถูกส่งเข้าสมองแมลงวันเหมือนสิ่งที่ขยับ ตาจึงเหลือบไปดู และอาจหันตัวไปดูด้วย
// - มองของใหม่จนครบ LEARN_S วินาที แซนจะจำไว้ ครั้งหน้าไม่ตื่นเต้นแล้ว (ความจำเก็บใน Chrome ข้ามวันได้)
// - ลายนิ้วมือ = ภาพย่อเหลือ 4x6 ช่องต่อครึ่งภาพ เก็บความสว่าง (เทียบกับค่าเฉลี่ยของภาพ) และสี ไฟสว่างขึ้นหรือมืดลงทั้งห้องจึงไม่นับเป็นของใหม่
// - ดูเฉพาะตอนภาพนิ่งพอ (ภาพที่ขยับเป็นหน้าที่ของสัญชาตญาณส่วนอื่น)

const CELLS_X = 4, CELLS_Y = 6;   // ช่องต่อครึ่งภาพ
const LOOK_EVERY_MS = 1000;       // เทียบภาพทุกกี่มิลลิวินาที
const TOP_CELLS = 4;              // ดูเฉพาะช่องที่ต่างที่สุดกี่ช่อง (ของชิ้นเล็กอยู่แค่ไม่กี่ช่อง เฉลี่ยทั้งภาพจะจางหาย)
const NOVEL = 0.5;                // ช่องที่ต่างที่สุดต่างเฉลี่ยเกินค่านี้ = ของใหม่ (ดูค่าจริงได้ใน brain.log แล้วปรับ)
const RISE = 0.34;                // เห็นของใหม่ต่อเนื่อง ความสนใจเพิ่มครั้งละเท่านี้ (ราว 3 วิ ถึงเต็ม)
const FALL = 0.5;                 // ไม่ใช่ของใหม่ ความสนใจเหลือเท่านี้ทุกรอบ
const FALL_MOVING = 0.9;          // ภาพกำลังขยับ (ดูไม่ถนัด) ความสนใจค่อย ๆ ลดแค่นี้
const LEARN_S = 3;                // สนใจเต็มที่นานกี่วินาทีแล้วจำไว้
const MAX_MEMORY = 400;           // จำได้กี่ภาพ (เกินแล้วลืมภาพที่ไม่ได้เห็นนานที่สุด)
const STORE_KEY = 'sand.curiosity.v1';
const SAVE_MS = 60000;

export function createCuriosity({ gridW, gridH, onNovel = () => { } }) {
  const half = gridW / 2, cw = half / CELLS_X, ch = gridH / CELLS_Y, dims = CELLS_X * CELLS_Y * 3;
  let memory = load();       // [{ sig: Float32Array, seen: เวลา }]
  let dirty = false, lastLook = 0, savedAt = performance.now();
  const side = [{ interest: 0, full: 0 }, { interest: 0, full: 0 }];   // [ซ้าย, ขวา]
  const stats = { novel: 0, learned: 0, minD: Infinity, maxD: 0 };

  function load() {
    try {
      const raw = JSON.parse(localStorage.getItem(STORE_KEY) || '[]');
      return raw.filter(m => m.s && m.s.length === dims).map(m => ({ sig: Float32Array.from(m.s), seen: m.t || 0 }));
    } catch (_) { return []; }
  }

  function save() {
    dirty = false;
    try {
      const raw = memory.map(m => ({ s: Array.from(m.sig, v => Math.round(v * 100) / 100), t: m.seen }));
      localStorage.setItem(STORE_KEY, JSON.stringify(raw));
    } catch (_) { }   // เก็บไม่ได้ก็แค่ลืมเมื่อปิดหน้า
  }

  // ลายนิ้วมือของครึ่งภาพ (h = 0 ซ้าย, 1 ขวา) จากพิกเซล RGBA ขนาด gridW x gridH
  function signature(px, h) {
    const sig = new Float32Array(dims);
    let k = 0, mean = 0;
    for (let cy = 0; cy < CELLS_Y; cy++) {
      for (let cx = 0; cx < CELLS_X; cx++) {
        let r = 0, g = 0, b = 0, n = 0;
        for (let y = cy * ch; y < (cy + 1) * ch; y++) {
          for (let x = h * half + cx * cw; x < h * half + (cx + 1) * cw; x++) {
            const i = (y * gridW + x) * 4;
            r += px[i]; g += px[i + 1]; b += px[i + 2]; n++;
          }
        }
        r /= n; g /= n; b /= n;
        const light = (r + g + b) / 3 + 1;
        sig[k++] = light;
        sig[k++] = (r - g) / light;            // สีแดง-เขียว ไม่ขึ้นกับความสว่าง
        sig[k++] = (b - (r + g) / 2) / light;  // สีน้ำเงิน-เหลือง
        mean += light;
      }
    }
    mean /= CELLS_X * CELLS_Y;
    for (let i = 0; i < dims; i += 3) sig[i] = sig[i] / mean - 1;   // ความสว่างเทียบค่าเฉลี่ยของภาพ
    return sig;
  }

  // ภาพสองภาพต่างกันแค่ไหน: ความต่างเฉลี่ยของ TOP_CELLS ช่องที่ต่างที่สุด (0 = เหมือนเป๊ะ)
  const cellD = new Float32Array(CELLS_X * CELLS_Y);
  function distance(a, b) {
    for (let c = 0, i = 0; c < cellD.length; c++, i += 3) {
      cellD[c] = Math.abs(a[i] - b[i]) + Math.abs(a[i + 1] - b[i + 1]) + Math.abs(a[i + 2] - b[i + 2]);
    }
    cellD.sort();
    let sum = 0;
    for (let c = cellD.length - TOP_CELLS; c < cellD.length; c++) sum += cellD[c];
    return sum / TOP_CELLS;
  }

  // ภาพนี้ต่างจากภาพที่จำได้ใกล้ที่สุดแค่ไหน และภาพนั้นคือภาพไหน
  function nearest(sig) {
    let best = Infinity, at = null;
    for (const m of memory) {
      const d = distance(sig, m.sig);
      if (d < best) { best = d; at = m; }
    }
    return [best, at];
  }

  function remember(sig) {
    memory.push({ sig, seen: Date.now() });
    if (memory.length > MAX_MEMORY) {
      memory.sort((a, b) => b.seen - a.seen);
      memory.length = MAX_MEMORY;
    }
    dirty = true;
    stats.learned++;
  }

  function calm(s, k) {
    s.interest = s.interest * k < 0.05 ? 0 : s.interest * k;
  }

  return {
    // เรียกทุกรอบสัญชาตญาณ: px = พิกเซลภาพล่าสุด, still = ภาพนิ่งพอให้เทียบ คืน [ความสนใจซ้าย, ขวา]
    look(px, still, now) {
      if (dirty && now - savedAt > SAVE_MS) { savedAt = now; save(); }
      if (now - lastLook < LOOK_EVERY_MS) return [side[0].interest, side[1].interest];
      lastLook = now;
      for (let h = 0; h < 2; h++) {
        const s = side[h];
        if (!still) { calm(s, FALL_MOVING); continue; }
        const sig = signature(px, h);
        const [d, match] = nearest(sig);
        if (Number.isFinite(d)) { stats.minD = Math.min(stats.minD, d); stats.maxD = Math.max(stats.maxD, d); }
        if (d > NOVEL) {
          const before = s.interest;
          s.interest = Math.min(1, s.interest + RISE);
          if (before === 0) { stats.novel++; onNovel(h === 0 ? 'L' : 'R'); }   // เพิ่งสังเกตเห็น
          if (s.interest >= 1 && ++s.full >= LEARN_S) { remember(sig); s.interest = 0; s.full = 0; }
        } else {
          if (match) match.seen = Date.now();   // เห็นซ้ำ = ยังไม่ลืม
          calm(s, FALL);
          s.full = 0;
        }
      }
      return [side[0].interest, side[1].interest];
    },
    // หยุดดูชั่วคราว (ภาพเลื่อน) ความสนใจที่ค้างอยู่หายไป
    reset() { for (const s of side) { s.interest = 0; s.full = 0; } },
    // สรุปสำหรับ brain.log แล้วล้างตัวนับ
    summary() {
      const text = `ความอยากรู้: จำภาพได้ ${memory.length} ภาพ · เจอของใหม่ ${stats.novel} ครั้ง · จำเพิ่ม ${stats.learned} ภาพ` +
        (Number.isFinite(stats.minD) ? ` · ความต่าง ${stats.minD.toFixed(2)}-${stats.maxD.toFixed(2)} (เกิน ${NOVEL} = ใหม่)` : '');
      Object.assign(stats, { novel: 0, learned: 0, minD: Infinity, maxD: 0 });
      return text;
    },
    forget() { memory = []; dirty = true; save(); },
    debug() { return { memory: memory.length, left: side[0].interest, right: side[1].interest }; },
  };
}
