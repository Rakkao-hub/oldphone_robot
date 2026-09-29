#!/usr/bin/env bash
# deploy.sh : ส่งโค้ดใน phone/ ขึ้นมือถือ (~/robot) แล้วเริ่มแซนใหม่
#   ต้องตั้ง SSH ชื่อ "phone" ไว้ใน ~/.ssh/config และเปิด sshd ใน Termux ก่อน
#   ใช้เครื่องอื่น: PHONE=ชื่อหรือ user@ip ./deploy.sh
set -e
PHONE=${PHONE:-phone}
cd "$(dirname "$0")/phone"

echo "→ เช็กว่าต่อมือถือได้ไหม..."
if ! ssh -o ConnectTimeout=15 "$PHONE" true 2>/dev/null; then
  echo "✗ ต่อมือถือไม่ได้: เปิด Termux แล้วพิมพ์  termux-wake-lock; sshd  (มือถือต้องอยู่ WiFi เดียวกับ Mac)"
  exit 1
fi

# scp ใช้กับ Termux ไม่ได้ จึงส่งผ่าน ssh ทีละไฟล์
for f in brain.py commands.py face.html start.sh; do
  ssh "$PHONE" "cat > ~/robot/$f" < "$f"
  echo "  ✓ $f"
done

# ไฟล์เสียงอุทาน (phone/sounds/) ส่งเฉพาะไฟล์เสียง และลบไฟล์บนมือถือที่ใน Mac ไม่มีแล้ว
ssh "$PHONE" 'mkdir -p ~/robot/sounds'
keep=$(cd sounds && ls *.mp3 *.wav *.ogg *.m4a 2>/dev/null | tr '\n' ' ')
ssh "$PHONE" "cd ~/robot/sounds && for f in *.mp3 *.wav *.ogg *.m4a; do [ -f \"\$f\" ] || continue; case \" $keep \" in *\" \$f \"*) ;; *) rm -f \"\$f\"; echo \"  ✗ ลบ sounds/\$f\";; esac; done"
for f in sounds/*.mp3 sounds/*.wav sounds/*.ogg sounds/*.m4a; do
  [ -f "$f" ] || continue
  ssh "$PHONE" "cat > ~/robot/$f" < "$f"
  echo "  ✓ $f"
done

echo "→ เริ่มแซนใหม่..."
ssh "$PHONE" 'bash ~/robot/start.sh'
echo "✓ เสร็จแล้ว ปิดแท็บแซนเก่าใน Chrome แล้วแตะปลุกแซนในแท็บใหม่"
