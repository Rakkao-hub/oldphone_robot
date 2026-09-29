#!/data/data/com.termux/files/usr/bin/bash
# เปิดทุกอย่างของแซน: bash ~/robot/start.sh
cd ~/robot
termux-wake-lock 2>/dev/null
pgrep -x sshd >/dev/null || sshd
pkill -x llama-server 2>/dev/null  # เลิกใช้ AI คุยเล่นแล้ว ปิดทิ้งถ้ายังค้าง
pkill -f "^python brain.py"
sleep 1
# เสียงพูด: ผู้ชาย ร่าเริง (แบบ 3) ต้อง pip install edge-tts ก่อน ไม่งั้นใช้เสียง Google
export TTS_VOICE=th-TH-NiwatNeural   # ผู้ชาย / th-TH-PremwadeeNeural = ผู้หญิง
export TTS_RATE=+5%                  # ความเร็ว เช่น +10% เร็วขึ้น, -10% ช้าลง
export TTS_PITCH=+8Hz                # เสียงสูงต่ำ เช่น +20Hz แหลมขึ้น, -10Hz ทุ้มลง
nohup python brain.py > brain.log 2>&1 &
sleep 2
am start -a android.intent.action.VIEW -d "http://localhost:8080/?t=$(date +%s)" com.android.chrome >/dev/null 2>&1
echo "แซนพร้อมแล้ว (log: tail -f ~/robot/brain.log)"
