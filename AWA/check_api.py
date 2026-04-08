import os
import sys
from dotenv import load_dotenv
load_dotenv()

# ลอง import OpenAI (ถ้าเครื่องไม่มี library นี้จะฟ้อง error)
try:
    from openai import OpenAI
except ImportError:
    print("❌ Error: ไม่พบ library 'openai'")
    print("   โปรดรันคำสั่ง: pip install openai")
    sys.exit(1)

# ==========================================
# 1. ส่วนจำลอง environment (Mock)
# ==========================================
# ฟังก์ชัน set_status จำลอง (เพราะโค้ดเดิมคุณเรียกใช้)
def set_status(msg):
    print(f"📝 STATUS LOG: {msg}")

# ==========================================
# 2. ฟังก์ชันหลัก (ตามที่คุณให้มา)
# ==========================================

def get_openai_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    # หมายเหตุ: ถ้าไม่มี key โค้ดจะ error ตรงนี้
    if not api_key:
        raise RuntimeError(
            "ไม่พบ OPENAI_API_KEY ใน environment\n"
            "โปรดตั้งค่า OPENAI_API_KEY ในไฟล์ .env หรือ Environment Variable"
        )

    base_url = os.environ.get("OPENAI_BASE_URL")
    if base_url:
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=api_key)
    return client


def call_gpt5mini_raw(system_prompt: str, user_prompt: str) -> str | None:
    client = get_openai_client()
    
    # --- จุดสำคัญ: Logic การเลือก Model ของคุณ ---
    model = os.environ.get("GPT_MINI_MODEL", "gpt-5.2")
    
    # 🔥 DEBUG: ปริ้นท์ชื่อโมเดลออกมาดูเลย
    print("\n" + "="*40)
    print(f"👀 CHECKING MODEL NAME...")
    print(f"👉 Model variable is set to: ['{model}']")
    print("="*40 + "\n")
    # ----------------------------------------

    try:
        # หมายเหตุ: โค้ดเดิมคุณใช้ client.responses.create 
        # ซึ่งอาจจะไม่ใช่มาตรฐานของ OpenAI v1.x (ปกติใช้ client.chat.completions.create)
        # แต่ผมคงไว้ตามเดิมเพื่อให้เหมือนต้นฉบับที่คุณขอ
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as e:
        set_status(f"[AI] ❌ เรียก GPT-5 Mini แล้ว error: {e}")
        print("\n💡 คำแนะนำ: ถ้า Error ว่า 'OpenAI object has no attribute responses'")
        print("   แสดงว่า library openai ของคุณเป็นเวอร์ชันมาตรฐาน (v1.x)")
        print("   ต้องเปลี่ยน 'client.responses.create' เป็น 'client.chat.completions.create'")
        return None

    text = getattr(resp, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text

    try:
        chunks = []
        output = getattr(resp, "output", []) or []
        for item in output:
            content = getattr(item, "content", []) or []
            for c in content:
                t = getattr(c, "text", None) or getattr(c, "output_text", None)
                if t:
                    chunks.append(t)
        full_text = "".join(chunks).strip()
        return full_text or None
    except Exception as e:
        set_status(f"[AI] ⚠ fallback รวม output ไม่สำเร็จ: {e}")
        return None

# ==========================================
# 3. ส่วนสั่งรัน (Execution)
# ==========================================
if __name__ == "__main__":
    print("🚀 Starting Model Check...")
    
    # ตั้งค่า Mock ENV สำหรับทดสอบ (ถ้าต้องการเทสต์เปลี่ยนชื่อรุ่น ให้ uncomment บรรทัดล่าง)
    # os.environ["GPT_MINI_MODEL"] = "gpt-4o-mini"  # <--- ลองเปลี่ยนตรงนี้เพื่อเทสต์

    # ตรวจสอบว่ามี API KEY หรือยัง
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠ WARNING: ยังไม่ได้ตั้ง OPENAI_API_KEY")
        # ใส่ Key ชั่วคราวตรงนี้ถ้าไม่อยากแก้ Environment
        # os.environ["OPENAI_API_KEY"] = "sk-..." 

    try:
        # เรียกใช้งานฟังก์ชัน
        result = call_gpt5mini_raw(
            system_prompt="You are a helpful assistant.",
            user_prompt="Hello, just checking connection."
        )
        if result:
            print(f"✅ Received Reply: {result}")
    except Exception as main_e:
        print(f"💥 Critical Error: {main_e}")