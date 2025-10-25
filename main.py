from flask import Flask, request, jsonify, Response
import requests
import os
import sys

app = Flask(__name__)

# อ่านค่าจาก Environment Variables ของ Render (จากแท็บ "Environment")
OPENAI_KEY = os.environ.get("OPENAI_KEY")
PROXY_TOKEN = os.environ.get("PROXY_TOKEN")

# ตรวจสอบตอนเริ่มทำงาน
if not OPENAI_KEY or not PROXY_TOKEN:
    print("!!! ERROR: Missing OPENAI_KEY or PROXY_TOKEN in Render Environment", file=sys.stderr)
    # เราจะไม่ sys.exit(1) เพื่อให้ Server ตื่นมาแสดง Error ได้

@app.route("/chat", methods=["POST"])
def chat():
    # ตรวจสอบอีกครั้งเผื่อตัวแปรหาย
    if not OPENAI_KEY or not PROXY_TOKEN:
        print("-> [500 Error] Server is misconfigured. Secrets are missing.", file=sys.stderr)
        return jsonify({"error": "server_misconfigured"}), 500
        
    # 1. ตรวจสอบรหัสผ่านจาก MT5 (Authorization: Bearer <TOKEN>)
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or auth.split(" ", 1)[1] != PROXY_TOKEN:
        print(f"-> [401 Unauthorized] Invalid Token from MT5. EA Sent: {auth}", file=sys.stderr)
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "invalid_json"}), 400
    
    print(f"-> OK: Forwarding request for model: {data.get('model')}")

    # 2. เตรียมส่งต่อให้ OpenAI
    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}

    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers, json=data, timeout=30 # 30 วินาที
        )
        # 3. ส่งคำตอบ (ไม่ว่าจะเป็น 200, 400, 401) กลับไปให้ MT5
        return r.content, r.status_code
    except Exception as e:
        print(f"-> [502 Bad Gateway] Error connecting to OpenAI: {e}", file=sys.stderr)
        return jsonify({"error": "upstream_error", "message": str(e)}), 502

@app.route("/", methods=["GET"])
def home():
    # หน้าสำหรับทดสอบว่า Server "ตื่น" หรือยัง
    return jsonify({"status": "running", "message": "MT5 'Whale' Proxy on Render is ready!"})

if __name__ == "__main__":
    # Render จะใช้ port 10000 ภายใน แต่เราไม่ต้องสนใจ
    print("Starting Flask server for Render...")
    app.run(host="0.0.0.0", port=10000)
