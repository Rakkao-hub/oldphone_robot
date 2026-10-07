// explore.js : เดินสำรวจ (ส่วนหนึ่งของสัญชาตญาณ)
//
// ทีละก้าว: หยุดมอง -> ให้สมองแมลงวันเลือกทิศ -> เดินหน้าสั้น ๆ
//   - ทิศมาจากสัญชาตญาณล้วน ๆ (instinct.lean): ของที่ขยับหรือของใหม่ข้างไหนดึงดูดกว่า หันไปทางนั้นแล้วเดินไป
//     ยิ่งสมองเอียงมากยิ่งหันมาก ตอนงอนสมองต่อสายไขว้ จึงหันหนีแทน
//   - ไม่มีอะไรกระตุ้น: หันมองไปเรื่อย ๆ ทางเดิม (ไม่เดิน) หันครบ IDLE_TURNS ครั้งยังไม่เจออะไร ค่อยเดินไปที่ใหม่
//   - เดินหน้าแล้วภาพไม่เปลี่ยน (ชนหรือติด) -> ถอย แล้วหันไปทางอื่นไกล ๆ (รีเฟล็กซ์ ทิศสุ่ม)
// แซนเริ่มสำรวจเองตอนเบื่อ (ตื่นอยู่ ไม่มีใครคุย ไม่เห็นหน้าใคร) หรือเมื่อพูด "ไปสำรวจ"
import { sleep, randInt, side } from './motion.js';

const STEPS = 10;              // สำรวจครั้งหนึ่งกี่ก้าว (หันมองหรือเดิน นับเป็นก้าวละครั้ง) แบตเปลี่ยนค่านี้ได้
const MAX_MS = 120000;
const FORWARD = [15, 25];     // ก้าวละกี่ ซม.
const LEAN_MIN = 0.15;        // สมองเอียงไปข้างหนึ่งเกินนี้ถึงจะหัน
const TURN_DEG = [20, 60];    // เอียงน้อย -> 20 องศา, เอียงสุด -> 60 องศา
const LOOK_MS = 1500;         // หยุดมองก่อนแต่ละก้าว (ให้สมองได้ดูภาพ ทั้งของที่ขยับและของใหม่)
const IDLE_TURN = [35, 50];   // ไม่มีอะไรกระตุ้น หันมองครั้งละกี่องศา
const IDLE_TURNS = 3;         // หันมองเปล่า ๆ ติดกันกี่ครั้งแล้วเดินไปที่ใหม่

export async function explore({ motion, lean = () => 0, steps: maxSteps = STEPS, shouldStop = () => false, onEvent = () => { } }) {
  const t0 = performance.now(), lookDir = side();   // หันมองทางเดิมตลอดรอบนี้ ดูทั่วห้องไม่วนกลับที่เดิม
  let steps = 0, bumps = 0, idle = 0;
  const go = async prog => {
    const r = await motion.step('explore', prog);
    if (!r.ok && r.why === 'busy') { await sleep(1000); return r; }   // รถยังทำท่าอื่นอยู่ รอแล้วไปต่อ
    if (!r.ok) throw new Error(r.why);                                 // ถูกยกเลิก / ต่อรถไม่ได้ -> เลิกสำรวจ
    return r;
  };
  try {
    while (steps < maxSteps && performance.now() - t0 < MAX_MS && !shouldStop()) {
      await sleep(LOOK_MS);
      if (shouldStop()) break;
      const want = lean();
      steps++;
      if (Math.abs(want) >= LEAN_MIN) {
        idle = 0;
        onEvent('curious');
        const k = Math.min(1, Math.abs(want));
        await go((want > 0 ? 'L' : 'R') + Math.round(TURN_DEG[0] + (TURN_DEG[1] - TURN_DEG[0]) * k));
      } else if (++idle <= IDLE_TURNS) {   // ไม่มีอะไรกระตุ้น หันมองไปเรื่อย ๆ
        await go(lookDir + randInt(...IDLE_TURN));
        continue;
      } else idle = 0;                     // หันมองจนทั่วแล้วไม่มีอะไร เดินไปที่ใหม่
      if (shouldStop()) break;
      const fwd = await go('F' + randInt(...FORWARD));
      if (fwd.stuck) {
        bumps++;
        onEvent('bump');
        await go('B15');
        await go(side() + randInt(100, 160));
      }
    }
  } catch (e) {
    return { steps, bumps, stopped: e.message };
  } finally {
    await motion.end('explore');
  }
  return { steps, bumps, stopped: shouldStop() ? 'stopped' : '' };
}
