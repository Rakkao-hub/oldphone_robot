// wonder.js : โหมดสงสัย แซนเจอของที่ไม่เคยเห็น -> ไปดูใกล้ ๆ จดจำ ถ่ายรูปเก็บไว้ -> เห็นคนแล้วเอารูปมาถามว่าคืออะไร
//
//   1. ความอยากรู้ (curiosity.js) เห็นของใหม่ฝั่งไหน แซนหันไปทางนั้น (ถ้าขยับล้อได้)
//   2. จดลายนิ้วมือของกลางภาพราว 3 วิ + ถ่ายรูปเล็ก ๆ ส่งให้ brain.py เก็บเป็น "ข้อสงสัย" (ค้างได้ไม่เกิน 3 เรื่อง)
//   3. face.html เห็นหน้าคน -> โชว์รูป ถาม "อันนี้คืออะไรเหรอ" -> คนตอบชื่อ -> brain.py จำเป็นของชิ้นหนึ่ง
//      (หลังจากนั้นสั่ง "หา<ชื่อ>" ได้เลย เหมือนของที่สอนเอง)
import { capture, snapshot, toLists } from './mission.js';

const ROUNDS = 8, EVERY_MS = 350;

export async function wonder({ video, motion, side, canMove, shouldStop = () => false, report = () => { } }) {
  // หันไปหาของ แล้วดูกลางภาพ / ขยับไม่ได้ (ชาร์จอยู่) ดูฝั่งที่เห็นแทน
  let cx = 0.5;
  if (canMove && side) {
    const r = await motion.step('wonder', side + '30');
    if (!r.ok && r.why !== 'busy') return { ok: false, why: r.why };
    if (!r.ok) cx = side === 'L' ? 0.28 : 0.72;
  } else if (side) cx = side === 'L' ? 0.28 : 0.72;
  const crops = [{ cx, cy: 0.5, s: 0.6 }, { cx, cy: 0.5, s: 0.45 }];
  const got = await capture({ video, crops, rounds: ROUNDS, every: EVERY_MS, shouldStop });
  if (!got) return { ok: false, why: 'stopped' };
  const photo = snapshot(video, crops[0]);
  const res = await (await fetch('/api/wonder', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ vectors: toLists(got.samples), th: got.th, photo }),
  })).json();
  report(`สงสัย: เก็บรูปของใหม่ไว้ถาม (คล้ายกันเอง ${got.selfSim.toFixed(2)} คล้ายฉากรอบ ๆ ${got.edgeSim.toFixed(2)}) ` +
    (res.ok ? `ค้างถาม ${res.pending} เรื่อง` : 'เก็บไม่ได้'));
  return { ok: !!res.ok };
}
