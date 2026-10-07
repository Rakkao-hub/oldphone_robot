// energy.js : สัญชาตญาณจากแบต (แบตมือถือที่เป็นสมองของแซน อ่านจาก Chrome)
//
//   แบตเยอะ  (40% ขึ้นไป) -> คึก: ไม่ง่วงเลย เบื่อเร็ว ออกสำรวจเป็นรอบ ๆ ตลอด เดินไกลขึ้น
//   ปกติ     (30-40%)     -> สำรวจตามปกติ
//   แบตน้อย  (15-30%)     -> ไม่ค่อยอยากทำ: นาน ๆ ทีถึงออกสำรวจ เดินไม่กี่ก้าว
//   เหนื่อย   (8-15%)      -> ไม่สำรวจแล้ว ทำหน้าง่วง บ่นเหนื่อยเป็นพัก ๆ
//   ใกล้หมด  (ต่ำกว่า 8%)  -> เลิกถามข้อสงสัย เปลี่ยนเป็นอ้อนขอชาร์จเมื่อเห็นคน
//   กำลังชาร์จ             -> ห้ามขยับล้อเอง (สายชาร์จจะกระชาก) แต่ยังสงสัยและถามได้
//
// บอร์ดรถ (ถ่าน 18650) ยังไม่มีวงจรวัดแบต จึงใช้แบตมือถือแทน
// Chrome ที่ไม่ให้อ่านแบต -> ถือว่าแบตปกติตลอด

const LEVELS = [
  { name: 'full', min: 0.4 },
  { name: 'ok', min: 0.3 },
  { name: 'low', min: 0.15 },
  { name: 'tired', min: 0.08 },
  { name: 'empty', min: 0 },
];
const HYSTERESIS = 0.02;   // ต้องขึ้นเกินเส้นเท่านี้ถึงจะเลื่อนขั้นกลับ (กันขั้นแกว่งไปมาที่ขอบ)

// explore: ออกสำรวจเองได้ไหม, boredMs/restMs/steps: เบื่อเร็วแค่ไหน พักนานแค่ไหน เดินกี่ก้าว
// keepAwake: ระหว่างสำรวจไม่ง่วง, wonder: สงสัยของแล้วมาถาม, tired: ทำหน้าเหนื่อย, plead: อ้อนขอชาร์จ
const PROFILES = {
  full: { explore: true, boredMs: 8000, restMs: 15000, steps: 16, keepAwake: true, wonder: true },
  ok: { explore: true, boredMs: 20000, restMs: 60000, steps: 10, wonder: true },
  low: { explore: true, boredMs: 60000, restMs: 180000, steps: 4, wonder: true },
  tired: { explore: false, wonder: true, tired: true },
  empty: { explore: false, wonder: false, tired: true, plead: true },
};

export async function createEnergy({ report = () => { }, onChange = () => { } } = {}) {
  let battery = null, state = 'ok';
  try { battery = await navigator.getBattery(); } catch (_) { }

  function compute() {
    if (!battery) return 'ok';
    const lv = battery.level;
    const i = LEVELS.findIndex(l => l.name === state);
    // ลดขั้นทันทีเมื่อต่ำกว่าเส้น แต่จะเลื่อนขึ้นต้องเกินเส้นขั้นบนไป HYSTERESIS
    let next = LEVELS.find(l => lv >= l.min).name;
    const j = LEVELS.findIndex(l => l.name === next);
    if (j < i && lv < LEVELS[i - 1].min + HYSTERESIS) next = state;
    return next;
  }

  function update() {
    const prev = state;
    state = compute();
    if (state !== prev) {
      report(`แบต: ${Math.round(battery.level * 100)}% ${battery.charging ? 'ชาร์จอยู่' : ''} -> ${state}`);
      onChange(state, prev);
    }
  }

  if (battery) {
    state = LEVELS.find(l => battery.level >= l.min).name;
    battery.addEventListener('levelchange', update);
    battery.addEventListener('chargingchange', () => onChange(state, state, true));
    report(`แบต: ${Math.round(battery.level * 100)}% ${battery.charging ? 'ชาร์จอยู่' : ''} -> ${state}`);
  } else {
    report('แบต: Chrome นี้อ่านแบตไม่ได้ ถือว่าแบตปกติ');
  }

  return {
    get state() { return state; },
    get percent() { return battery ? Math.round(battery.level * 100) : null; },
    get charging() { return !!(battery && battery.charging); },
    // นิสัยตอนนี้ (ชาร์จอยู่ = ห้ามขยับล้อเอง)
    profile() {
      const p = { ...PROFILES[state] };
      if (battery && battery.charging) { p.explore = false; p.plead = false; p.wheels = false; } else p.wheels = true;
      return p;
    },
  };
}
