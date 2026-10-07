// fly_brain.js : สมองแมลงวันจิ๋ว รันใน Chrome บนมือถือ (ไม่ต้องติดตั้งอะไรเพิ่ม)
//
// ผังสายไฟจริง 500 เซลล์รอบเซลล์ DNp20 ของแมลงวันผลไม้ (ไฟล์ dnp20.json) จำลองแบบ leaky integrate-and-fire
// โค้ดนี้แปลตรงตัวมาจาก fly_brain.py ในโปรเจกต์ fly_brain_test (ข้อ 8) ตัวเลขทุกตัวเหมือนกัน
//
//   ค่าเซนเซอร์ซ้าย-ขวา (0 ถึง 1)  ->  step()  ->  turn (-1 ถึง 1)   บวก = ฝั่งซ้ายชนะ, ลบ = ฝั่งขวาชนะ
//
// ผังสายไฟเป็นของจริง แต่พฤติกรรมของเซลล์เป็นแบบจำลองอย่างง่าย และการเลือกว่าเสียบเซนเซอร์เข้าเซลล์ไหน
// เป็นการตัดสินใจของเรา ไม่ใช่ข้อเท็จจริงทางชีววิทยา

// พารามิเตอร์ของเซลล์ (หน่วย: มิลลิวินาที และ มิลลิโวลต์)
const DT = 0.5;            // ก้าวเวลาของการจำลอง
const V_REST = -52.0;      // ศักย์ขณะพัก
const V_THRESHOLD = -45.0; // ถึงค่านี้เซลล์จะยิง
const TAU_M = 20.0;        // ศักย์รั่วกลับค่าพักเร็วแค่ไหน
const TAU_SYN = 5.0;       // สัญญาณเข้าจางหายเร็วแค่ไหน
const REFRACTORY = 2.2;    // หลังยิงแล้วพักกี่มิลลิวินาที
const W_SYN = 0.275;       // หนึ่ง synapse ดันสัญญาณเข้ากี่มิลลิโวลต์

const TURN_FULL_HZ = 100.0; // ซ้ายกับขวายิงต่างกันเท่านี้ = สุดทาง
const SMOOTHING = 0.5;      // เฉลี่ยกับรอบก่อนหน้า ให้ผลไม่กระตุก

// ตัวสุ่มที่ตั้งค่าเริ่มได้ (รันซ้ำได้ผลเดิม ใช้ตอนทดสอบ)
function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export class FlyBrain {
  // circuit = เนื้อหาของ dnp20.json
  // sensorType = ชนิดเซลล์ที่เซนเซอร์ไปกระตุ้น, crossed = ต่อไขว้ (เซนเซอร์ซ้ายไปกระตุ้นซีกขวา)
  constructor(circuit, { sensorType = 'VS', crossed = false, maxHz = 100, seed = 1 } = {}) {
    const n = this.n = circuit.n;
    this.maxHz = maxHz;
    this.random = mulberry32(seed);

    // สายขาออกของแต่ละเซลล์ เก็บเรียงต่อกัน: สายของเซลล์ j อยู่ที่ตำแหน่ง outStart[j] ถึง outStart[j+1]
    const count = new Int32Array(n + 1);
    for (const j of circuit.pre) count[j + 1]++;
    for (let j = 0; j < n; j++) count[j + 1] += count[j];
    this.outStart = count;
    this.outPost = new Int32Array(circuit.pre.length);
    this.outW = new Float64Array(circuit.pre.length);
    const fill = count.slice();
    for (let e = 0; e < circuit.pre.length; e++) {
      const j = circuit.pre[e], at = fill[j]++;
      this.outPost[at] = circuit.post[e];
      this.outW[at] = circuit.w[e] * circuit.sign[j] * W_SYN;
    }

    const cells = (type, side) => {
      const out = [];
      for (let i = 0; i < n; i++) if (circuit.type[i] === type && circuit.side[i] === side) out.push(i);
      return out;
    };
    this.outL = cells(circuit.target, 'L');
    this.outR = cells(circuit.target, 'R');
    this.sensL = cells(sensorType, 'L');
    this.sensR = cells(sensorType, 'R');
    if (!this.sensL.length || !this.sensR.length || !this.outL.length || !this.outR.length) {
      throw new Error(`วงจรนี้ไม่มีเซลล์ ${sensorType} หรือ ${circuit.target} ครบทั้งสองซีก`);
    }
    this.crossed = crossed;

    this.v = new Float64Array(n);
    this.g = new Float64Array(n);
    this.restLeft = new Float64Array(n);
    this.spikes = new Int32Array(n);
    this.firedFlag = new Uint8Array(n);
    this.fired = new Int32Array(n);
    this.reset();
  }

  // ล้างสถานะ: ทุกเซลล์กลับไปอยู่ที่ศักย์พัก
  reset() {
    this.v.fill(V_REST);
    this.g.fill(0);
    this.restLeft.fill(0);
    this.rateL = 0;
    this.rateR = 0;
  }

  setCrossed(crossed) { this.crossed = !!crossed; }

  // เดินเวลาในสมองไป ms มิลลิวินาที โดยมีค่าเซนเซอร์ left / right (0 ถึง 1) กระตุ้นอยู่ตลอดช่วง
  // สถานะของเซลล์ค้างต่อจากรอบก่อน จึงเรียกซ้ำ ๆ เป็นวงรอบได้เลย
  step(left, right, ms = 50) {
    left = Math.min(1, Math.max(0, left));
    right = Math.min(1, Math.max(0, right));
    const stimL = this.crossed ? this.sensR : this.sensL;
    const stimR = this.crossed ? this.sensL : this.sensR;
    const chanceL = left * this.maxHz * DT / 1000, chanceR = right * this.maxHz * DT / 1000;
    const { n, v, g, restLeft, spikes, fired, firedFlag, outStart, outPost, outW, random } = this;
    const kSyn = DT / TAU_SYN, kM = DT / TAU_M;
    spikes.fill(0);

    const steps = Math.round(ms / DT);
    for (let s = 0; s < steps; s++) {
      let nFired = 0;
      for (let i = 0; i < n; i++) {
        g[i] -= g[i] * kSyn;                                   // สัญญาณเข้าค่อย ๆ จาง
        if (restLeft[i] <= 0) {
          v[i] += (g[i] - (v[i] - V_REST)) * kM;               // รั่วกลับค่าพัก + ถูกสัญญาณเข้าดัน
          if (v[i] >= V_THRESHOLD) { firedFlag[i] = 1; fired[nFired++] = i; }
        }
        restLeft[i] -= DT;
      }
      // เซลล์รับสัญญาณที่เซนเซอร์บังคับให้ยิง
      if (chanceL > 0) for (const i of stimL) if (random() < chanceL && !firedFlag[i]) { firedFlag[i] = 1; fired[nFired++] = i; }
      if (chanceR > 0) for (const i of stimR) if (random() < chanceR && !firedFlag[i]) { firedFlag[i] = 1; fired[nFired++] = i; }
      // เซลล์ที่ยิง: กลับค่าพัก แล้วส่งสัญญาณต่อไปตามสายไฟ
      for (let k = 0; k < nFired; k++) {
        const j = fired[k];
        firedFlag[j] = 0;
        v[j] = V_REST;
        restLeft[j] = REFRACTORY;
        spikes[j]++;
        for (let e = outStart[j]; e < outStart[j + 1]; e++) g[outPost[e]] += outW[e];
      }
    }

    const seconds = ms / 1000;
    const mean = idx => { let sum = 0; for (const i of idx) sum += spikes[i]; return sum / idx.length / seconds; };
    this.rateL = SMOOTHING * this.rateL + (1 - SMOOTHING) * mean(this.outL);
    this.rateR = SMOOTHING * this.rateR + (1 - SMOOTHING) * mean(this.outR);
    const turn = Math.min(1, Math.max(-1, (this.rateL - this.rateR) / TURN_FULL_HZ));
    return { rateL: this.rateL, rateR: this.rateR, turn };
  }
}
