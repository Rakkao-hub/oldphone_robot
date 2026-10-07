// motion.js : ตัวช่วยขยับล้อสำหรับการเดินสำรวจและภารกิจหาของ
//
// หน้าแซนขอ brain.py ขยับทีละท่า (/api/auto/move) แล้วรอให้รถทำท่าเสร็จ (/api/robot) ก่อนดูภาพต่อ
// brain.py ตัดสินว่ายอมให้ขยับไหม ถ้าภารกิจถูกยกเลิก (มีคนสั่งอย่างอื่น พูด "หยุด" แตะจอ) จะตอบ why = 'cancelled'
// ไม่มีเซนเซอร์วัดระยะ จึงจับว่า "ชนหรือติด" จากภาพ: สั่งเดินหน้าแล้วภาพแทบไม่เปลี่ยน = ล้อหมุนแต่รถไม่ไป

const GRID_W = 32, GRID_H = 24;
const PIXEL_CHANGED = 18;
const STUCK_BELOW = 0.06;     // เดินหน้าแล้วภาพเปลี่ยนน้อยกว่าสัดส่วนนี้ = ติด/ชนอยู่
const POLL_MS = 150;
const SETTLE_MS = 350;        // รถหยุดแล้วรอภาพนิ่งอีกนิด
const MAX_WAIT_MS = 8000;

export const sleep = ms => new Promise(r => setTimeout(r, ms));

export function createMotion({ video, report = () => { }, onMoving = () => { } }) {
  const canvas = document.createElement('canvas');
  canvas.width = GRID_W; canvas.height = GRID_H;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });

  // ภาพขาวดำย่อเล็ก ไว้เทียบก่อน/หลังขยับ
  function grab() {
    ctx.drawImage(video, 0, 0, GRID_W, GRID_H);
    const px = ctx.getImageData(0, 0, GRID_W, GRID_H).data, g = new Uint8Array(GRID_W * GRID_H);
    for (let i = 0; i < g.length; i++) g[i] = (px[i * 4] * 77 + px[i * 4 + 1] * 150 + px[i * 4 + 2] * 29) >> 8;
    return g;
  }

  function changed(a, b) {
    let n = 0;
    for (let i = 0; i < a.length; i++) if (Math.abs(a[i] - b[i]) > PIXEL_CHANGED) n++;
    return n / a.length;
  }

  async function waitIdle() {
    const t0 = performance.now();
    await sleep(POLL_MS);
    while (performance.now() - t0 < MAX_WAIT_MS) {
      try {
        const s = await (await fetch('/api/robot')).json();
        if (!s.running) break;
      } catch (_) { break; }
      await sleep(POLL_MS);
    }
    await sleep(SETTLE_MS);
  }

  // ขยับหนึ่งท่า แล้วรอจนเสร็จ คืน { ok, why, stuck }
  async function step(kind, prog) {
    const before = prog[0] === 'F' ? grab() : null;
    let res;
    onMoving(true);
    try {
      const r = await fetch('/api/auto/move', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ kind, prog })
      });
      res = await r.json();
      if (res.ok) await waitIdle();
    } catch (_) {
      res = { ok: false, why: 'offline' };
    } finally {
      onMoving(false);
    }
    res.stuck = !!(res.ok && before && changed(before, grab()) < STUCK_BELOW);
    if (res.stuck) report(`${kind}: สั่ง ${prog} แต่ภาพแทบไม่เปลี่ยน น่าจะชนหรือติดอยู่`);
    return res;
  }

  async function end(kind, found = false) {
    try {
      await fetch('/api/auto/end', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ kind, found })
      });
    } catch (_) { }
  }

  return { step, end, grab, changed };
}

export const randInt = (a, b) => a + Math.floor(Math.random() * (b - a + 1));
export const side = () => (Math.random() < 0.5 ? 'L' : 'R');
