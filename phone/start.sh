#!/data/data/com.termux/files/usr/bin/bash
# เปิดทุกอย่างของแซน: bash ~/robot/start.sh
cd ~/robot
termux-wake-lock 2>/dev/null
pgrep -x sshd >/dev/null || sshd
MODEL=${MODEL:-$HOME/models/qwen3-1.7b-q4_0.gguf}
if ! pgrep -x llama-server >/dev/null && [ -f "$MODEL" ]; then
  nohup llama-server -m "$MODEL" --jinja --host 127.0.0.1 --port 8081 -t 4 -c 2048 > ~/models/llama.log 2>&1 &
fi
pkill -f "^python brain.py"
sleep 1
nohup python brain.py > brain.log 2>&1 &
sleep 2
am start -a android.intent.action.VIEW -d "http://localhost:8080/?t=$(date +%s)" com.android.chrome >/dev/null 2>&1
echo "แซนพร้อมแล้ว (log: tail -f ~/robot/brain.log)"
