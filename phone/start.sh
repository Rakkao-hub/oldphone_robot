#!/data/data/com.termux/files/usr/bin/bash
# เปิดทุกอย่างของแซน: bash ~/robot/start.sh
cd ~/robot
termux-wake-lock 2>/dev/null
pgrep -x sshd >/dev/null || sshd
pkill -x llama-server 2>/dev/null  # เลิกใช้ AI คุยเล่นแล้ว ปิดทิ้งถ้ายังค้าง
pkill -f "^python brain.py"
sleep 1
nohup python brain.py > brain.log 2>&1 &
sleep 2
am start -a android.intent.action.VIEW -d "http://localhost:8080/?t=$(date +%s)" com.android.chrome >/dev/null 2>&1
echo "แซนพร้อมแล้ว (log: tail -f ~/robot/brain.log)"
