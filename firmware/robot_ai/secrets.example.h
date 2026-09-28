// secrets.example.h : คัดลอกไฟล์นี้เป็น secrets.h แล้วใส่ค่าจริง (secrets.h จะไม่ถูกอัปขึ้น GitHub)
// ESP8266 ใช้ได้แค่ WiFi คลื่น 2.4 GHz
#pragma once

// WiFi บ้าน
const char* WIFI_SSID = "ชื่อ WiFi บ้าน";
const char* WIFI_PASS = "รหัส WiFi บ้าน";

// Hotspot ของมือถือที่เป็นสมอง ใช้เมื่อมองไม่เห็น WiFi บ้าน (เช่นเอารถออกไปข้างนอก)
// ตั้งชื่อ/รหัส Hotspot ในมือถือให้ตรงกับนี้ และเลือกแบนด์ 2.4 GHz
const char* PHONE_SSID = "RobotBrain";
const char* PHONE_PASS = "ตั้งรหัสอย่างน้อย 8 ตัว";

// รหัส WiFi "Robot-AI" ที่บอร์ดปล่อยเองตอนต่อ WiFi ไม่ติด (อย่างน้อย 8 ตัว)
const char* AP_PASS = "ตั้งรหัสอย่างน้อย 8 ตัว";
