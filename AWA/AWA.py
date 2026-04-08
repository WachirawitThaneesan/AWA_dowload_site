import os
import time
import re
import base64
import json
import pyautogui
import time
from io import BytesIO

import requests
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk  # ⭐ ใช้ customtkinter
from pypdf import PdfReader
from PIL import Image
import pytesseract

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    WebDriverException,
)
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# 🔁 ใช้ OpenAI (GPT-5 Mini)
from openai import OpenAI

import shutil
from dotenv import load_dotenv
load_dotenv()

import requests
import hashlib
import platform
import uuid
import sys
from tkinter import messagebox
import ctypes
import mouse


# ================== PATH พื้นฐานแบบ portable ==================

try:
    # 1. เช็คสิทธิ์ Admin
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
except:
    is_admin = False

if is_admin:
    # 2. ถ้าเป็น Admin แล้ว: จะข้ามส่วน 'else' ไปทำงานที่โค้ดส่วนอื่นต่อด้านล่าง
    print("✅ รันด้วยสิทธิ์ Admin แล้ว. ทำงานต่อ...")
    # **********************************************
    # * วางโค้ดหลักของโปรแกรมที่คุณต้องการรัน Admin ที่นี่ *
    # **********************************************

else:
    # 3. ถ้ายังไม่เป็น Admin: สั่ง Windows ให้รันโปรแกรมนี้ใหม่ในโหมด Admin (UAC popup จะเด้ง)
    print("⚠️ ยังไม่ได้สิทธิ์ Admin. กำลังร้องขอสิทธิ์ Admin...")
    
    # sys.executable คือตัวไฟล์ .exe หรือ python.exe ที่กำลังรันอยู่
    ctypes.windll.shell32.ShellExecuteW(
        None, 
        "runas",            # verb เพื่อร้องขอสิทธิ์ Admin
        sys.executable, 
        " ".join(sys.argv), # ส่ง arguments เดิมทั้งหมดไปด้วย
        None, 
        1
    )
    
    # 4. ปิดตัวโปรแกรมตัวเก่า (ตัวที่ไม่ใช่ Admin) ทันที
    print("⏳ ปิดตัวที่ไม่ใช่ Admin. โปรดรอตัว Admin เปิดขึ้นมาใหม่...")
    sys.exit()

# -------------------------------------------------------------------
# โค้ดส่วนอื่นของโปรแกรมจะเริ่มต้นจากบรรทัดนี้ *เฉพาะ* เมื่อรันด้วยสิทธิ์ Admin แล้ว
print("โปรแกรมหลักเริ่มทำงาน (รันในโหมด Admin)")
    
myappid = 'AWA.AutoGrading.App.v2'  # <-- เปลี่ยนชื่อตรงนี้
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception as e:
    print(f"Set AppID Error: {e}")

if getattr(sys, "frozen", False):
    # ตอนรันเป็น .exe (PyInstaller)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # ตอนรันเป็น .py ปกติ
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        BASE_DIR = os.getcwd()


# 2. ⭐ กำหนด ENV_PATH (สำหรับไฟล์ .env ที่ฝังอยู่ข้างใน)
if getattr(sys, "frozen", False):
    # กรณีเป็น .exe ให้ไปหาในโฟลเดอร์ชั่วคราวที่ PyInstaller แตกไฟล์ออกมา (_MEIPASS)
    internal_path = sys._MEIPASS
    ENV_PATH = os.path.join(internal_path, ".env")
else:
    # กรณีรัน .py ปกติ ให้หาในโฟลเดอร์โปรเจกต์
    ENV_PATH = os.path.join(BASE_DIR, ".env")

print("[DEBUG] .env path =", ENV_PATH, "exists =", os.path.exists(ENV_PATH))

load_dotenv(dotenv_path=ENV_PATH, override=True)

# ดึง Path ของโฟลเดอร์ Documents ของ User คนปัจจุบัน
#user_docs = os.path.expanduser("~/Documents")

# ตั้งชื่อโฟลเดอร์สำหรับเก็บข้อมูลโปรแกรมเรา
#APP_DATA_DIR = os.path.join(user_docs, "AutoGradeBot_Data")

# สร้างโฟลเดอร์หลักเตรียมไว้ (ถ้ายังไม่มี)
#os.makedirs(APP_DATA_DIR, exist_ok=True)

DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
CREDS_PATH = os.path.join(BASE_DIR, "creds.json")
LICENSE_PATH = os.path.join(BASE_DIR, "license.json")

# สร้างโฟลเดอร์ Downloads เตรียมไว้
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def resource_path(relative_path):
    import sys, os
    try:
        # PyInstaller จะใช้โฟลเดอร์ชั่วคราวชื่อ _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # โหมดรันปกติ ใช้โฟลเดอร์โปรเจกต์
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# โลโก้บนหน้าจอหลัก
current_dir = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(current_dir, "logo.png")


# icon ของหน้าต่าง / taskbar
current_dir = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(current_dir, "app.ico")
APP_ICON_PATH = ICON_PATH


# NEW: สำหรับอ่านไฟล์ .docx
try:
    import docx as docx_lib
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

# ประเภทไฟล์ที่ระบบรองรับ
SUPPORTED_EXTS = {
    ".pdf",
    ".txt",
    ".docx",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff"
}

# ประเภทไฟล์สมุดโน้ตที่ไม่รองรับ
UNSUPPORTED_NOTE_EXTS = {
    ".goodnotes",
    ".goodnotes5",
}



# ====== Tkinter/customtkinter Globals & Theme ======
root = None          # main CTk root (ซ่อนอยู่)


# ================== THEME: Microsoft Teams (Light) ==================
TEAMS_MAIN_BG      = "#F3F2F1"   # พื้นหลังหลัก (เทาอ่อน)
TEAMS_CARD_BG      = "#FFFFFF"   # การ์ด / panel สีขาว
TEAMS_SIDEBAR_BG   = "#ECE7E5"   # โทนชมพูเทา sidebar
TEAMS_BORDER       = "#E1DFDD"   # เส้นขอบอ่อน ๆ

TEAMS_PRIMARY      = "#5d5bd4"   # ม่วงหลัก
TEAMS_PRIMARY_HOVER= "#3454E2"   # hover ม่วงอมฟ้า

TEAMS_TEXT_MAIN    = "#201F1E"   # ตัวอักษรหลัก
TEAMS_TEXT_MUTED   = "#605E5C"   # ตัวอักษรเทา
TEAMS_TEXT_LIGHT   = "#A19F9D"   # ตัวอักษรจาง

# ================== customtkinter Status Window ==================

status_win = None
log_box = None

_progress_label = None      # แสดง 15 / 40 และ %
_progress_bar = None        # แถบ progress
_current_student_label = None   # ตอนนี้กำลังตรวจ: ชื่อคน
_summary_label = None       # ข้อความใหญ่ตอนตรวจเสร็จ

_phase_label = None         # ไว้ใช้ข้อความย่อย ๆ ถ้าต้องการ
_status_logo_image = None   # กัน GC

_total_students = 0         # จำนวนคนที่ต้องตรวจทั้งหมด


def get_hwid():
    raw = f"{platform.node()}-{platform.processor()}-{uuid.getnode()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


LICENSE_SERVER = "https://web-production-0ca76.up.railway.app"

def check_license(key: str) -> bool:
    """
    ส่ง key + hwid ไปที่ license server
    ถ้า valid → คืน True
    ถ้าไม่ผ่าน → ขึ้นกล่อง error และคืน False
    """
    try:
        payload = {
            "key": key,
            "hwid": get_hwid(),
        }

        # 🔥 ยิงไปที่ /check โดยตรง
        url = f"{LICENSE_SERVER}/check"
        resp = requests.post(url, json=payload, timeout=8)

        # debug ดูทุกครั้ง
        try:
            data = resp.json()
        except Exception:
            messagebox.showerror(
                "License server error",
                f"Cannot parse server response:\nHTTP {resp.status_code}\n{resp.text}",
            )
            return False

        print("[LICENSE] server response:", data)

        if not isinstance(data, dict):
            messagebox.showerror(
                "License server error",
                f"Unexpected response type:\n{data}",
            )
            return False

        # ✅ รองรับทั้งรูปแบบ {"ok": true, ...} และ {"valid": true, ...}
        if data.get("ok") is True or data.get("valid") is True:
            return True

        # ❌ เคสไม่ผ่าน
        reason = data.get("reason") or "License not valid."
        messagebox.showerror("Invalid License", reason)
        return False

    except Exception as e:
        messagebox.showerror("Network Error", f"Cannot verify license:\n{e}")
        return False


def load_saved_license_key() -> str | None:
    """โหลด key จาก license.json (ถ้ามี)"""
    if not os.path.exists(LICENSE_PATH):
        return None
    try:
        with open(LICENSE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("key") or None
    except Exception:
        return None


def save_license_key(key: str):
    """บันทึก key ลง license.json"""
    try:
        with open(LICENSE_PATH, "w", encoding="utf-8") as f:
            json.dump({"key": key}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[WARN] เซฟ license key ไม่สำเร็จ:", e)

import ctypes
import time

def switch_keyboard_to_english():
    """
    ส่งคำสั่งไปยังหน้าต่างที่ Active อยู่ (เช่น Chrome หรือ Desktop)
    ให้เปลี่ยนภาษาแป้นพิมพ์เป็น English (US)
    """
    try:
        user32 = ctypes.windll.user32
        
        # 1. หา Handle ของหน้าต่างที่กำลังโฟกัสอยู่ (Active Window)
        hwnd = user32.GetForegroundWindow()
        
        # 2. ค่าคงที่ Windows API
        WM_INPUTLANGCHANGEREQUEST = 0x0050  # คำสั่ง "ขอเปลี่ยนภาษา"
        
        # 3. รหัสภาษา English (US)
        # 0x0409 คือ English (United States)
        # ปกติค่า HKL (Handle to Keyboard Layout) จะใช้ format 0xHHHHLLLL
        # โดยทั่วไปสำหรับ US จะเป็น 0x04090409
        HKL_ENGLISH = 0x04090409 
        
        # 4. ส่ง Message ไปที่หน้าต่างนั้นโดยตรง
        # PostMessage(window_handle, message_id, flags, language_handle)
        user32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, HKL_ENGLISH)
        
        # 5. รอสักนิดให้ Windows ประมวลผล
        time.sleep(0.2)
        
        # ตรวจสอบ (Optional): เช็คว่าเปลี่ยนจริงไหม (Debug)
        # thread_id = user32.GetWindowThreadProcessId(hwnd, 0)
        # current_layout = user32.GetKeyboardLayout(thread_id)
        # print(f"[DEBUG] Current Layout ID: {hex(current_layout & 0xFFFF)}")

    except Exception as e:
        print(f"[WARN] ไม่สามารถเปลี่ยนภาษาได้: {e}")

import ctypes
import time

def focus_desktop_force():
    """
    ค้นหาหน้าต่าง Desktop (Progman) และบังคับ Focus 
    เพื่อให้ Windows รู้ว่าเราอยู่ที่ Desktop แล้ว
    """
    try:
        user32 = ctypes.windll.user32
        
        # 1. ค้นหา Handle ของหน้าต่าง Desktop (ชื่อคลาสคือ 'Progman')
        hwnd_desktop = user32.FindWindowW(u"Progman", None)
        
        if hwnd_desktop:
            # 2. บังคับให้ Desktop เป็นหน้าต่างหลัก (Active)
            user32.SetForegroundWindow(hwnd_desktop)
            print("[INFO] Force Focus ไปที่ Desktop (Progman) สำเร็จ")
        else:
            print("[WARN] หาหน้าต่าง Desktop ไม่เจอ")
            
        time.sleep(0.5) # รอให้ Windows สลับ Focus

    except Exception as e:
        print(f"[WARN] Focus Desktop ไม่สำเร็จ: {e}")

def close_created_desktop():
    """
    ปิด Desktop ที่โปรแกรมสร้าง (Win + Ctrl + F4)
    Windows จะสลับกลับไป Desktop ก่อนหน้าให้อัตโนมัติ
    """
    try:   
        focus_desktop_force()
        pyautogui.hotkey("winleft", "ctrl", "f4")
        time.sleep(0.5)
    except Exception as e:
        print("[WARN] ปิด Desktop ไม่สำเร็จ:", e)


def create_and_switch_to_desktop2():
    # Win + Ctrl + D = สร้าง desktop ใหม่และสลับไป
    print("[INFO] กำลังสร้างและสลับไป Desktop 2...")
    user32 = ctypes.windll.user32
    
    # รหัสปุ่ม: VK_LWIN(0x5B), VK_CONTROL(0x11), D(0x44)
    
    # 1. กด Win + Ctrl ค้างไว้
    user32.keybd_event(0x11, 0, 0, 0) # Ctrl Down
    user32.keybd_event(0x5B, 0, 0, 0) # Win Down
    time.sleep(0.1)
    
    # 2. กดปุ่ม D (สร้าง Desktop)
    user32.keybd_event(0x44, 0, 0, 0) # D Down
    time.sleep(0.1)
    user32.keybd_event(0x44, 0, 2, 0) # D Up
    
    # 3. ปล่อย Win + Ctrl
    user32.keybd_event(0x5B, 0, 2, 0) # Win Up
    user32.keybd_event(0x11, 0, 2, 0) # Ctrl Up
    
    # 4. รอให้ Animation การสไลด์หน้าจอจบ (สำคัญมาก)
    time.sleep(1.5)

def switch_back_to_desktop1():
    # Win + Ctrl + Left = ย้อนกลับไป desktop ก่อนหน้า
    pyautogui.hotkey("winleft", "ctrl", "left")
    time.sleep(1)

def init_progress(total_students: int):
    """กำหนดจำนวนคนที่ต้องตรวจทั้งหมด + reset progress bar"""
    global _total_students, _progress_label, _progress_bar
    _total_students = max(int(total_students or 0), 0)

    if _progress_label is not None:
        if _total_students > 0:
            _progress_label.configure(
                text=f"0 / {_total_students} Student (0%)"
            )
        else:
            _progress_label.configure(
                text="0 / 0 Student (0%)"
            )

    if _progress_bar is not None:
        _progress_bar.set(0.0)


def update_progress(done_count: int):
    """อัปเดต progress bar และตัวเลข 15 / 40 (xx%)"""
    global _total_students, _progress_label, _progress_bar

    done_count = int(done_count or 0)
    total = max(_total_students, 0)

    if total <= 0:
        percent = 0
        frac = 0.0
    else:
        percent = int(done_count * 100 / total)
        frac = min(max(done_count / total, 0.0), 1.0)

    if _progress_label is not None:
        if total > 0:
            _progress_label.configure(
                text=f"{done_count} / {total} Students ({percent}%)"
            )
        else:
            _progress_label.configure(
                text=f"{done_count} / 0 Students (0%)"
            )

    if _progress_bar is not None:
        _progress_bar.set(frac)


def set_current_student(name: str | None):
    """อัปเดตข้อความตอนนี้กำลังตรวจ: ..."""
    global _current_student_label
    if _current_student_label is None:
        return

    if not name:
        _current_student_label.configure(text="The system is retrieving student writing data.")
    else:
        _current_student_label.configure(
            text=f"Please wait a moment while the system is generating feedback \n Students Name : {name}"
        )


def show_finished_message():
    """แสดงข้อความใหญ่เมื่อระบบตรวจเสร็จทั้งหมดแล้ว"""
    global _summary_label
    if _summary_label is not None:
        _summary_label.configure(
            text="The work has been inspected. 🎉\nYou can check the results in Microsoft Teams.",
            text_color=TEAMS_PRIMARY,
        )
    # ถ้ามี progress bar และรู้จำนวนทั้งหมด → บังคับให้เป็น 100%
    if _total_students > 0:
        update_progress(_total_students)


myappid = 'mycompany.myproduct.subproduct.version' 
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


def init_root_if_needed():
    """สร้าง CTk root ถ้ายังไม่มี + ตั้งธีม + บังคับ Icon"""
    global root
    if root is None:
        # 1. ตั้ง App ID ตรงนี้เลย (ก่อนสร้าง root) เอาให้ชัวร์
        # เปลี่ยนเลข version ด้านหลังเป็นเลขมั่วๆ เช่น v.999 เพื่อหนี Cache เก่า
        myappid = 'AWA.AutoGrade.App.version.9999' 
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        root = ctk.CTk()
        
        # 2. บังคับใส่ Icon ทันทีที่สร้างเสร็จ
        try:
            if os.path.exists(APP_ICON_PATH):
                root.iconbitmap(APP_ICON_PATH)
            else:
                print(f"❌ Icon not found at: {APP_ICON_PATH}")
        except Exception as e:
            print(f"⚠️ Icon Error: {e}")

        root.withdraw() # ซ่อนหน้าต่างหลักไว้ก่อน
        root.title("Teams Auto Grading")
        root.configure(fg_color=TEAMS_MAIN_BG)



def tk_yield():
    """อัปเดต UI ให้ไม่ขึ้น Not Responding ระหว่างงานยาว ๆ"""
    global root
    if root is None:
        return
    try:
        root.update_idletasks()
        root.update()
    except Exception:
        pass


_log_visible = False   # state ว่ากล่อง log โชว์อยู่ไหม

def create_status_window(selected_class: str, selected_assignment: str):
    """
    สร้างหน้าต่างสถานะแบบเต็มจอ
    - แสดงชื่อ Class ที่เลือก
    - แสดงชื่อ Assignment ที่เลือก
    - แสดง progress bar 15/40 + %
    - แสดงข้อความใหญ่ "ตอนนี้กำลังตรวจ: ชื่อคน"
    - ตอนจบใช้ show_finished_message() เพื่อขึ้นข้อความใหญ่
    """
    global status_win, log_box
    global _progress_label, _progress_bar, _current_student_label, _summary_label, _phase_label
    global root

    init_root_if_needed()
    

    status_win = ctk.CTkToplevel(root)
    status_win.title("AWA – Auto grading status")
    status_win.after(200, lambda: status_win.wm_iconbitmap(ICON_PATH))
    status_win.configure(fg_color=TEAMS_MAIN_BG)
    status_win.resizable(True, True)

    # ทำให้เต็มจอ
    sw = status_win.winfo_screenwidth()
    sh = status_win.winfo_screenheight()
    status_win.geometry(f"{sw}x{sh}+0+0")
    try:
        status_win.state("zoomed")  # Windows
    except Exception:
        pass

    # ---------- Header ----------
    header = ctk.CTkFrame(status_win, fg_color=TEAMS_CARD_BG, corner_radius=0)
    header.pack(fill="x", padx=0, pady=(0, 4))

    titles_frame = ctk.CTkFrame(header, fg_color="transparent")
    titles_frame.pack(side="left", padx=24, pady=12)

    # ⭐ บรรทัดบน: ชื่อคลาส
    ctk.CTkLabel(
        titles_frame,
        text=f"Class: {selected_class}",
        font=ctk.CTkFont("Segoe UI", size=18, weight="bold"),
        text_color=TEAMS_TEXT_MAIN,
    ).pack(anchor="w")

    # ⭐ บรรทัดล่าง: ชื่อ Assignment ที่กำลังตรวจ
    ctk.CTkLabel(
        titles_frame,
        text=f"Assignment: {selected_assignment}",
        font=ctk.CTkFont("Segoe UI", size=16),
        text_color=TEAMS_TEXT_MUTED,
    ).pack(anchor="w")

    # ---------- Main content ----------
    main = ctk.CTkFrame(status_win, fg_color=TEAMS_MAIN_BG)
    main.pack(fill="both", expand=True, padx=40, pady=20)

    center = ctk.CTkFrame(
        main,
        fg_color=TEAMS_CARD_BG,
        corner_radius=20,
        border_color=TEAMS_BORDER,
        border_width=1,
    )
    center.pack(expand=True, fill="both", padx=40, pady=20)

    # progress label
    _progress_label = ctk.CTkLabel(
        center,
        text="0 / 0 Student (0%)",
        font=ctk.CTkFont("Segoe UI", size=26, weight="bold"),
        text_color=TEAMS_TEXT_MAIN,
    )
    _progress_label.pack(pady=(40, 10))

    # progress bar
    _progress_bar = ctk.CTkProgressBar(
        center,
        width=600,
        height=20,
        corner_radius=10,
        fg_color="#EDEBE9",
        progress_color=TEAMS_PRIMARY,
    )
    _progress_bar.set(0.0)
    _progress_bar.pack(pady=(0, 40))

    # current student label
    _current_student_label = ctk.CTkLabel(
        center,
        text="The system is retrieving student writing data.",
        font=ctk.CTkFont("Segoe UI", size=24, weight="bold"),
        text_color=TEAMS_TEXT_MUTED,
        wraplength=800,
        justify="center",
    )
    _current_student_label.pack(pady=(0, 30))

    # summary / finished text
    _summary_label = ctk.CTkLabel(
        center,
        text="",
        font=ctk.CTkFont("Segoe UI", size=28, weight="bold"),
        text_color=TEAMS_PRIMARY,
        wraplength=900,
        justify="center",
    )
    _summary_label.pack(pady=(0, 30))

    # phase label เล็ก ๆ ด้านล่าง
    _phase_label = ctk.CTkLabel(
        center,
        text="ระบบกำลังเตรียมเริ่มตรวจงาน...",
        font=ctk.CTkFont("Segoe UI", size=14),
        text_color=TEAMS_TEXT_MUTED,
    )
    _phase_label.pack(side="bottom", pady=20)

    # ❌ ไม่สร้าง log panel แล้ว
    log_box = None

    tk_yield()
    return status_win, None


def set_phase_status(msg: str):
    global _phase_label, status_win, root

    print(f"[PHASE] {msg}")

    if _phase_label is not None:
        try:
            _phase_label.configure(text=msg)
            _phase_label.update_idletasks()
        except Exception:
            pass

    if msg.startswith("เสร็จสิ้นทั้งหมด"):
        try:
            messagebox.showinfo(
                "ตรวจงานเสร็จแล้ว",
                "ระบบตรวจงานเสร็จเรียบร้อยแล้ว\nจะปิดโปรแกรมให้ทันที"
            )
        except Exception:
            pass

        try:
            if status_win is not None:
                status_win.destroy()
        except Exception:
            pass

        try:
            if root is not None:
                root.quit()
        except Exception:
            pass


def bring_status_to_front():
    """ดันหน้าต่าง GradeFlow ขึ้นมาอยู่ข้างหน้า"""
    global status_win
    if status_win is None:
        return
    try:
        status_win.deiconify()
        status_win.lift()
        status_win.attributes("-topmost", True)
        status_win.after(800, lambda: status_win.attributes("-topmost", False))
    except Exception:
        pass


def set_status(msg: str):
    """เขียน log + console เท่านั้น (ไม่ไปยุ่งกับสถานะหลักของผู้ใช้)"""
    global log_box

    print(msg)

    if log_box is not None:
        try:
            log_box.configure(state="normal")
            log_box.insert("end", msg + "\n")
            log_box.see("end")
            log_box.configure(state="disabled")
        except Exception:
            pass

    # ทุกครั้งที่มี log ใหม่ → อัปเดต UI กันค้าง
    tk_yield()


# ================== LOGIN WINDOW ==================


def load_saved_credentials():
    if not os.path.exists(CREDS_PATH):
        return None, None
    try:
        with open(CREDS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("email") or None, data.get("password") or None
    except Exception:
        return None, None


def save_credentials(email: str, password: str):
    try:
        with open(CREDS_PATH, "w", encoding="utf-8") as f:
            json.dump({"email": email, "password": password}, f)
    except Exception as e:
        print("[WARN] เซฟ credentials ไม่สำเร็จ:", e)


def clear_credentials():
    try:
        if os.path.exists(CREDS_PATH):
            os.remove(CREDS_PATH)
    except Exception as e:
        print("[WARN] ลบ creds.json ไม่ได้:", e)

def ask_license_key_window() -> str | None:
    """
    popup ให้ผู้ใช้ใส่ License Key
    คืนค่าเป็น string ถ้ากด Continue
    คืนค่า None ถ้ากด Cancel / ปิดหน้าต่าง
    """
    global root
    init_root_if_needed()

    win = ctk.CTkToplevel(root)
    win.title("Enter License Key")
    win.after(200, lambda: win.wm_iconbitmap(ICON_PATH))
    win.geometry("420x220")
    win.resizable(False, False)
    win.grab_set()
    win.configure(fg_color=TEAMS_MAIN_BG)

    outer = ctk.CTkFrame(
        win,
        fg_color=TEAMS_CARD_BG,
        corner_radius=12,
        border_color=TEAMS_BORDER,
        border_width=1,
    )
    outer.pack(expand=True, padx=24, pady=24, fill="both")

    ctk.CTkLabel(
        outer,
        text="License verification",
        font=ctk.CTkFont("Segoe UI", size=16, weight="bold"),
        text_color=TEAMS_TEXT_MAIN,
    ).pack(pady=(16, 4))

    ctk.CTkLabel(
        outer,
        text="Please enter your license key to continue.",
        font=ctk.CTkFont("Segoe UI", size=12),
        text_color=TEAMS_TEXT_MUTED,
    ).pack(pady=(0, 12))

    key_var = tk.StringVar(value="")

    entry = ctk.CTkEntry(
        outer,
        placeholder_text="XXXX-XXXX-XXXX-XXXX",
        width=320,
        height=36,
        textvariable=key_var,
        fg_color=TEAMS_CARD_BG,
        border_color="#E1DFDD",
        text_color=TEAMS_TEXT_MAIN,
    )
    entry.pack(pady=(4, 16))

    result = {"key": None}

    def on_ok():
        k = key_var.get().strip()
        if not k:
            messagebox.showwarning(
                "Missing license",
                "Please enter your license key.",
                parent=win,
            )
            return
        result["key"] = k
        win.destroy()

    def on_cancel():
        result["key"] = None
        win.destroy()

    btn_row = ctk.CTkFrame(outer, fg_color="transparent")
    btn_row.pack(fill="x", padx=8, pady=(4, 8))

    ok_btn = ctk.CTkButton(
        btn_row,
        text="Continue",
        fg_color=TEAMS_PRIMARY,
        hover_color=TEAMS_PRIMARY_HOVER,
        text_color="#FFFFFF",
        command=on_ok,
        width=120,
    )
    ok_btn.pack(side="right", padx=(8, 0))

    cancel_btn = ctk.CTkButton(
        btn_row,
        text="Exit",
        fg_color="#EDEBE9",
        hover_color="#D2D0CE",
        text_color=TEAMS_TEXT_MAIN,
        command=on_cancel,
        width=90,
    )
    cancel_btn.pack(side="right")

    win.bind("<Return>", lambda e: on_ok())
    win.protocol("WM_DELETE_WINDOW", on_cancel)

    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"+{sw//2 - win.winfo_width()//2}+{sh//2 - win.winfo_height()//2}")

    entry.focus_set()

    root.wait_window(win)
    return result["key"]



def login_window():
    global root

    init_root_if_needed()

    saved_email, saved_password = load_saved_credentials()
    has_saved = bool(saved_email and saved_password)

    # ============ สร้าง Window ============
    win = ctk.CTkToplevel(root)
    win.title("AWA - Sign in")
    win.after(200, lambda: win.wm_iconbitmap(ICON_PATH))
    win.geometry("380x580")
    win.resizable(False, False)
    win.grab_set()
    win.configure(fg_color=TEAMS_MAIN_BG)   # ⭐ พื้นหลังเทาอ่อนแบบ Teams

    # ============ Layout หลัก (center) ============
    frame = ctk.CTkFrame(
        win,
        fg_color=TEAMS_CARD_BG,             # ⭐ การ์ดขาวเหมือนหน้าจอมือถือในตัวอย่าง
        corner_radius=18
    )
    frame.pack(expand=True, padx=20, pady=20, fill="both")

    # ---------- โลโก้ Teams ----------
    try:
        logo_path = LOGO_PATH
        if os.path.exists(logo_path):
            logo_img = ctk.CTkImage(
                light_image=Image.open(logo_path),
                dark_image=Image.open(logo_path),
                size=(180, 180)
            )
            logo_label = ctk.CTkLabel(frame, image=logo_img, text="")
            logo_label.pack(pady=(10, 10))

    except Exception:
        ctk.CTkLabel(
            frame,
            text="AWA",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=TEAMS_TEXT_MAIN
        ).pack(pady=20)

    # ---------- Header ----------
    ctk.CTkLabel(
        frame,
        text="AWA",
        font=ctk.CTkFont(size=24, weight="bold"),
        text_color=TEAMS_TEXT_MAIN
    ).pack(pady=(5, 0))

    ctk.CTkLabel(
        frame,
        text="Automated Writing Assessment",
        font=ctk.CTkFont(size=14),
        text_color=TEAMS_TEXT_MUTED     # ⭐ เทาแบบ Teams
    ).pack(pady=(2, 20))

    # ---------- Input ----------
    email_var = tk.StringVar(value=saved_email or "")
    pass_var = tk.StringVar(value=saved_password or "")
    remember_var = tk.BooleanVar(value=has_saved)

    email_entry = ctk.CTkEntry(
        frame,
        placeholder_text="Enter email or phone",
        width=280,
        height=40,
        textvariable=email_var,
        fg_color=TEAMS_CARD_BG,
        border_color="#E1DFDD",
        text_color=TEAMS_TEXT_MAIN
    )
    email_entry.pack(pady=(5, 15))

    pass_entry = ctk.CTkEntry(
        frame,
        placeholder_text="Password",
        show="*",
        width=280,
        height=40,
        textvariable=pass_var,
        fg_color=TEAMS_CARD_BG,
        border_color="#E1DFDD",
        text_color=TEAMS_TEXT_MAIN
    )
    pass_entry.pack(pady=(5, 5))

    # 1. ตัวแปรสำหรับ Checkbox Show Password
    show_pass_var = tk.BooleanVar(value=False)
    
    # 2. ฟังก์ชันสำหรับสลับการแสดงผล
    def toggle_password_visibility():
        """สลับการตั้งค่า 'show' ของช่องรหัสผ่าน"""
        if show_pass_var.get():
            # ถ้าถูกติ๊ก (ต้องการแสดง) ให้ตั้งค่า show เป็น "" (แสดงตัวอักษร)
            pass_entry.configure(show="")
        else:
            # ถ้าไม่ถูกติ๊ก (ต้องการซ่อน) ให้ตั้งค่า show เป็น "*" (ซ่อนรหัสผ่าน)
            pass_entry.configure(show="*")

    # 3. Checkbox Show Password
    show_pass_chk = ctk.CTkCheckBox(
        frame,
        text="Show password",
        variable=show_pass_var,
        command=toggle_password_visibility, # <--- เรียกฟังก์ชันนี้เมื่อมีการติ๊ก
        text_color=TEAMS_TEXT_MUTED,
        border_color=TEAMS_TEXT_MUTED,
        fg_color=TEAMS_PRIMARY,
        hover_color=TEAMS_PRIMARY_HOVER
    )
    # จัดให้อยู่ทางซ้าย (ใช้ place หรือ grid) หรือจัดชิดซ้ายของ frame ย่อยถ้าต้องการ
    # ในตัวอย่างนี้ ใช้ pack เหมือนเดิม แต่ให้พิจารณาการจัดวางใน UI จริงของคุณ
    show_pass_chk.pack(pady=(0, 5), padx=40, anchor="w")

    # ---------- Remember me ----------
    chk = ctk.CTkCheckBox(
        frame,
        text="Remember me",
        variable=remember_var,
        text_color=TEAMS_TEXT_MUTED,
        border_color=TEAMS_TEXT_MUTED,
        fg_color=TEAMS_PRIMARY,
        hover_color=TEAMS_PRIMARY_HOVER
    )
    chk.pack(pady=(0, 10))

    # ---------- ฟังก์ชันปุ่ม ----------
    def on_login():
        email = email_var.get().strip()
        password = pass_var.get()

        if not email or not password:
            messagebox.showwarning(
                "Missing info",
                "Please enter both email and password",
                parent=win
            )
            return

        if remember_var.get():
            save_credentials(email, password)
        else:
            clear_credentials()

        win.destroy()

    # 🔴 ฟังก์ชันยกเลิก / กดกากบาท
    def on_cancel():
        # ไม่ต้องเปลี่ยนค่า is_cancelled (ให้เป็น True เหมือนเดิม)
        print("User cancelled login.")
        
        # ลบ Desktop ทันที
        try: close_created_desktop()
        except: pass

        # ทำให้ main() รู้ว่า user ยกเลิก → return ค่าว่างๆ
        email_var.set("")
        pass_var.set("")
        win.destroy()

    # ---------- Sign in Button ----------
    login_btn = ctk.CTkButton(
        frame,
        text="Sign in",
        width=280,
        height=42,
        corner_radius=8,
        fg_color=TEAMS_PRIMARY,          # ⭐ ม่วง Teams
        hover_color=TEAMS_PRIMARY_HOVER,
        text_color="#FFFFFF",
        command=on_login
    )
    login_btn.pack(pady=(10, 5))

    # Enter = login
    win.bind("<Return>", lambda e: on_login())
    # กากบาท (ปิดหน้าต่าง) = cancel
    win.protocol("WM_DELETE_WINDOW", on_cancel)


    # จัดกลางจอ
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"+{sw//2 - 190}+{sh//2 - 290}")

    email_entry.focus_set()

    root.wait_window(win)
    return email_var.get(), pass_var.get()


# ================== GPT-5 MINI (OpenAI) ==================


def get_openai_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
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
    model = os.environ.get("GPT_MINI_MODEL", "gpt-5-mini")

    try:
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as e:
        set_status(f"[AI] ❌ เรียก GPT-5 Mini แล้ว error: {e}")
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


def extract_score_from_ai_text(text: str):
    m = re.search(r"คะแนน:\s*(\d+)", text)
    if not m:
        return None
    return int(m.group(1))

def looks_like_prompt_echo(ai_text: str) -> bool:
    if not ai_text:
        return False
    lowered = ai_text.lower()
    bad_markers = [
        "========== student writing ==========",
        "จงประเมินงานนี้ตามขั้นตอนต่อไปนี้",
        "กติกาสำคัญ",
        "ให้ตอบกลับโดยใช้รูปแบบนี้",
    ]
    return any(m.lower() in lowered for m in bad_markers)


def grade_file_with_ai(
    file_name: str,
    file_url: str | None,
    file_text: str | None,
    file_bytes: bytes | None,
    student_name: str,
    assignment_name: str,
    status_text: str,
    max_score: int | None,
):
    """
    เวอร์ชันใหม่:
    - ถ้ามี file_bytes → แนบไฟล์จริงเข้า GPT ด้วย input_file
    - ไม่ใช้ OCR Tesseract อีกต่อไป
    - ถ้าโหมด input_file error → fallback ไปใช้โหมดเก่า (ส่งข้อความย่อ)
    """

    set_status(f"[AI] เรียก GPT-5 Mini ประเมินงานของ {student_name}: {file_name}")

    # ==== 1) เตรียม preview จาก file_text เฉพาะไว้ใช้ log / fallback เท่านั้น ====
    if file_text:
        text = file_text.strip()
        if len(text) > 4000:
            body_preview = text[:4000] + "\n\n... (ตัดให้สั้นเพื่อส่งเข้า AI) ..."
        else:
            body_preview = text
    else:
        body_preview = "(ไม่มีข้อความที่อ่านได้จากไฟล์ หรือเป็นรูป/ไฟล์ที่ OCR/ตัวอ่านไม่ดึงออกมา)"

    # ข้อความเสริมเรื่องคะแนนเต็มจาก Teams
    if max_score is not None:
        extra_score_info = (
            f"\nข้อมูลเพิ่ม: งานนี้ในระบบ Teams มีคะแนนเต็ม {max_score} คะแนน\n"
            f"กรุณาให้คะแนนเป็นจำนวนเต็มตั้งแต่ 1 ถึง {max_score} ตามคุณภาพของงานเขียน\n"
        )
    else:
        extra_score_info = ""

    # ==== 2) system prompt เหมือนเดิม ====
    system_prompt = """
คุณคืออาจารย์ผู้ชายชาวไทย สอน Writing ภาษาอังกฤษให้นักศึกษามหาวิทยาลัย
ให้ตรวจงานเขียนจากไฟล์แนบ แล้วให้คะแนนและ feedback สั้น ๆ
เหมือนอาจารย์เขียนในช่อง Feedback ของ Microsoft Teams

ข้อกำหนดสำคัญ / Requirements:
- ให้คะแนนตามเกณฑ์คะแนนเต็มที่กำหนด (เช่น เต็ม 10 ก็ใช้ช่วง 1–10)
- บรรทัดแรกต้องขึ้นต้นด้วย: คะแนน: X  (X เป็นจำนวนเต็ม)  **ห้ามเปลี่ยนคำว่า "คะแนน:"**
- ห้ามพูดถึงคำว่า prompt, rubric, model, AI, system หรือข้อจำกัดของตนเอง
- ใช้น้ำเสียงสุภาพ เป็นกันเอง เหมือนอาจารย์คุยกับนักศึกษา
- ไม่ต้องบอกให้นักศึกษาส่งงานแก้ หรือส่งงานใหม่ (No resubmission request)
- ให้แสดงส่วนภาษาไทยทั้งหมดก่อน แล้วตามด้วยส่วนภาษาอังกฤษทั้งหมด
- เน้นกระชับ ไม่เขียนยาวเกินไป

รูปแบบคำตอบ (Response format):

1) บรรทัดแรก (คะแนน / Score):
คะแนน: X

2) ส่วนภาษาไทย (Thai Section) [TH] สรุปและข้อเสนอแนะ:
[TH] สรุปโดยรวม:
- … (1–2 bullet สั้น ๆ)

[TH] ข้อเสนอแนะ:
- … (1–3 bullet แนะนำสิ่งที่ควรปรับปรุง)

[TH] ข้อผิดพลาดที่ควรสังเกต:
- Grammar: จุดที่ผิด / ตัวอย่างสั้น ๆ (ไม่เกิน 1–2 จุด)
- Vocabulary / Word choice: (ถ้ามี ไม่เกิน 1–2 จุด)
- Sentence structure: (ถ้ามี ไม่เกิน 1–2 จุด)

3) ส่วนภาษาอังกฤษ (English Section) [EN] Summary & Feedback:
[EN] Overall summary:
- … (1–2 short bullets)

[EN] Suggestions:
- … (1–3 short bullets on how to improve)

[EN] Error notes:
- Grammar: wrong → correct, with a brief explanation
- Vocabulary / Sentence structure: only if really important

เงื่อนไขเพิ่มเติม:
- ถ้างานเขียนดีมาก ให้ชมชัด ๆ ทั้งภาษาไทยและอังกฤษอย่างสั้น ๆ
- ถ้างานอ่อน ให้ให้กำลังใจ พร้อมข้อเสนอแนะที่ทำตามได้จริง
- หลีกเลี่ยงย่อหน้าที่ยาวเกินไป แบ่งเป็น bullet ให้ชัดเจน
""".strip()

    # ==== 3) user instruction สำหรับโหมดไฟล์ ====
    instructions_file_mode = f"""
นี่คือรายละเอียดงาน:

- ชื่อนักศึกษา: {student_name}
- ชื่อ assignment: {assignment_name}
- สถานะในระบบ (turned-in / late ฯลฯ): {status_text}
- คะแนนเต็มของงานนี้: {max_score}

ไฟล์แนบคือชิ้นงานของนักศึกษา (อาจเป็น PDF, รูปที่เขียนบน iPad, Word หรือไฟล์อื่น ๆ)
ให้คุณอ่าน/วิเคราะห์จากไฟล์แนบโดยตรง แล้วให้คะแนนและ feedback ตามรูปแบบที่กำหนดใน system prompt

{extra_score_info}
""".strip()

    # ==== 4) user prompt สำหรับ fallback โหมดข้อความ (ของเดิม) ====
    user_prompt_text_mode = f"""
นี่คือรายละเอียดงาน:

- ชื่อนักศึกษา: {student_name}
- ชื่อ assignment: {assignment_name}
- สถานะในระบบ (turned-in / late ฯลฯ): {status_text}
- คะแนนเต็มของงานนี้: {max_score}

ให้คุณประเมินคะแนนตั้งแต่ 0 ถึง {max_score} โดยเลือกคะแนนที่เหมาะสมที่สุดตามคุณภาพของงานเขียน

นี่คือย่อหน้าที่นักศึกษาเขียน (ดึงมาจากไฟล์):

========== STUDENT WRITING ==========
{body_preview}
====================================
""".strip()

    client = get_openai_client()
    model = os.environ.get("GPT_MINI_MODEL", "gpt-5-mini")

    ai_text = None

    # ==== 5) พยายามใช้โหมด input_file / input_image ก่อน (เฉพาะชนิดที่รองรับ) ====
    if file_bytes:
        name_lower = file_name.lower()

        # เดา mime-type
        if name_lower.endswith(".pdf"):
            mime = "application/pdf"
        elif name_lower.endswith(".txt"):
            mime = "text/plain"
        elif name_lower.endswith(".png"):
            mime = "image/png"
        elif name_lower.endswith((".jpg", ".jpeg")):
            mime = "image/jpeg"
        elif name_lower.endswith(".gif"):
            mime = "image/gif"
        elif name_lower.endswith(".bmp"):
            mime = "image/bmp"
        elif name_lower.endswith((".tif", ".tiff")):
            mime = "image/tiff"
        else:
            mime = "application/octet-stream"

        is_image = name_lower.endswith((
            ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff"
        ))

        try:
            base64_string = base64.b64encode(file_bytes).decode("utf-8")

            if is_image:
                # ⭐ รูปภาพ → ใช้ input_image (vision)
                resp = client.responses.create(
                    model=model,
                    input=[
                        {
                            "role": "system",
                            "content": [
                                {"type": "input_text", "text": system_prompt},
                            ],
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "input_text", "text": instructions_file_mode},
                            ],
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "input_image",
                                    "image_url": f"data:{mime};base64,{base64_string}",
                                }
                            ],
                        },
                    ],
                )
            elif name_lower.endswith(".pdf"):
                # ⭐ PDF เท่านั้นที่ใช้ input_file ได้ (จาก error: รองรับเฉพาะ PDF)
                resp = client.responses.create(
                    model=model,
                    input=[
                        {
                            "role": "system",
                            "content": [
                                {"type": "input_text", "text": system_prompt},
                            ],
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "input_file",
                                    "filename": file_name,
                                    "file_data": f"data:{mime};base64,{base64_string}",
                                },
                                {
                                    "type": "input_text",
                                    "text": instructions_file_mode,
                                },
                            ],
                        },
                    ],
                )
            else:
                # ❗ docx / txt / อื่น ๆ → ใช้โหมดข้อความแทน (ไม่ใช้ input_file)
                set_status(
                    "[AI] ℹ ไฟล์ชนิดนี้ (เช่น DOCX/TXT) จะไม่ส่งเข้าโหมด input_file "
                    "เพราะ model รองรับเฉพาะ PDF — จะใช้โหมดข้อความ (preview text) แทน"
                )
                resp = None

            if resp is not None:
                ai_text = getattr(resp, "output_text", None)
                if not ai_text:
                    try:
                        chunks = []
                        output = getattr(resp, "output", []) or []
                        for item in output:
                            content = getattr(item, "content", []) or []
                            for c in content:
                                t = getattr(c, "text", None) or getattr(c, "output_text", None)
                                if t:
                                    chunks.append(t)
                        ai_text = "".join(chunks).strip() or None
                    except Exception as e:
                        set_status(f"[AI] ⚠ fallback รวม output (input_file/input_image) ไม่สำเร็จ: {e}")

        except Exception as e:
            set_status(f"[AI] ❌ เรียก GPT-5 Mini แบบ input_file/input_image แล้ว error: {e}")
    else:
        set_status("[AI] ⚠ ไม่มี file_bytes จะใช้โหมดข้อความเดิมแทน")


    # ==== 6) ถ้าโหมดไฟล์ไม่สำเร็จ → fallback ไปโหมดข้อความเดิม ====
    if not ai_text:
        set_status("[AI] ⚠ คำตอบจากโหมด input_file ว่างหรือ error → fallback ไปใช้โหมดข้อความเดิม")
        try:
            ai_text = call_gpt5mini_raw(system_prompt, user_prompt_text_mode)
        except Exception as e:
            set_status(f"[AI] ❌ เรียก GPT-5 Mini แบบข้อความแล้ว error: {e}")
            return None, None

    # ถ้ายังว่างอยู่ก็ยอมแพ้
    if not ai_text:
        set_status("[AI] ❌ ได้ผลลัพธ์ว่างเปล่าจาก GPT-5 Mini (ทุกโหมด)")
        return None, None

    print("\n[AI] ====== Feedback จาก GPT-5 Mini ======")
    print(ai_text)
    print("=====================================\n")

    score = extract_score_from_ai_text(ai_text)
    if score is not None:
        max_str = str(max_score) if max_score is not None else "?"
        set_status(f"[AI] ดึงคะแนนจาก AI ได้: {score}/{max_str}")
    else:
        set_status("[AI] ⚠ ดึงคะแนนจากข้อความ AI ไม่ได้ จะไม่กรอกช่องคะแนนอัตโนมัติ")

    return ai_text, score

# ================== OCR / FILE UTIL ==================


def is_supported_file(filename: str) -> bool:
    if not filename:
        return False
    fname = filename.lower().strip()

    if any(fname.endswith(ext) for ext in UNSUPPORTED_NOTE_EXTS):
        set_status(f"[INFO] พบไฟล์ GoodNotes ที่ระบบอัตโนมัติไม่รองรับ: {fname}")
        return False

    return any(fname.endswith(ext) for ext in SUPPORTED_EXTS)


def extract_text_from_bytes(filename: str, data: bytes) -> str | None:
    name_lower = filename.lower()

    # ✅ txt: อ่านเป็นข้อความตรง ๆ เอาไว้ใช้ fallback
    if name_lower.endswith(".txt"):
        try:
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                text = data.decode("cp874", errors="ignore")
            if not text.strip():
                set_status(f"[WARN] อ่าน txt {filename} แล้วได้ข้อความว่างเปล่า")
            else:
                set_status(f"[INFO] อ่าน txt {filename} ได้ความยาว {len(text)} ตัวอักษร")
            return text
        except Exception as e:
            set_status(f"[WARN] อ่าน txt ไม่สำเร็จ: {e}")
            return None

    # ✅ docx: ใช้ python-docx อ่านแล้วแปลงเป็นข้อความ
    if name_lower.endswith(".docx") and HAS_DOCX:
        try:
            from io import BytesIO
            doc = docx_lib.Document(BytesIO(data))
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            text = "\n".join(paragraphs)
            if not text.strip():
                set_status(f"[WARN] อ่าน docx {filename} แล้วได้ข้อความว่างเปล่า")
            else:
                set_status(f"[INFO] อ่าน docx {filename} ได้ความยาว {len(text)} ตัวอักษร")
            return text or None
        except Exception as e:
            set_status(f"[WARN] อ่าน docx ไม่สำเร็จ: {e}")
            return None

    # ❌ pdf / รูปภาพ → ไม่ดึง text (ให้ GPT อ่านไฟล์โดยตรงหรือ OCR ในอนาคต)
    set_status(
        f"[INFO] ข้ามการดึง text ของไฟล์ {filename} (pdf/docx/รูป) "
        "จะให้ GPT อ่านจากไฟล์โดยตรงถ้ารองรับ หรือใช้ fallback mode"
    )
    return None

def clean_ocr_text(raw: str) -> str:
    if not raw:
        return ""

    bad_keywords = [
        "Open options for resource",
        "Copy link",
        "Download",
        "Share",
        "Microsoft Teams",
        "Assignments",
        "Open in browser",
        "Open in desktop app",
    ]

    cleaned_lines = []
    for line in raw.splitlines():
        strip = line.strip()
        if not strip:
            cleaned_lines.append(strip)
            continue
        if any(k.lower() in strip.lower() for k in bad_keywords):
            continue
        cleaned_lines.append(strip)

    return "\n".join(cleaned_lines).strip()

# ================== HTTP session จาก Selenium ==================


def build_requests_session_from_driver(driver) -> requests.Session:
    session = requests.Session()
    for c in driver.get_cookies():
        cookie_dict = {
            "domain": c.get("domain"),
            "name": c.get("name"),
            "value": c.get("value"),
            "path": c.get("path", "/"),
        }
        session.cookies.set(**cookie_dict)

    try:
        ua = driver.execute_script("return navigator.userAgent;")
        session.headers.update({"User-Agent": ua})
    except Exception:
        pass

    return session


def download_file_via_session(session: requests.Session, url: str) -> bytes | None:
    if not url:
        set_status("[WARN] download_file_via_session ถูกเรียกด้วย url ว่าง")
        return None
    try:
        short_url = url if len(url) < 120 else url[:117] + "..."
        set_status(f"[DEBUG] เริ่มดาวน์โหลดไฟล์จาก: {short_url}")
        resp = session.get(url, stream=True, timeout=30)
        set_status(
            f"[DEBUG] ผลการดาวน์โหลด: status={resp.status_code}, "
            f"content-type={resp.headers.get('Content-Type', 'unknown')}"
        )
        resp.raise_for_status()
        content = resp.content
        set_status(f"[DEBUG] ขนาดไฟล์ที่ได้ = {len(content)} bytes")
        return content
    except Exception as e:
        set_status(f"[WARN] ดาวน์โหลดไฟล์จาก {url} ไม่สำเร็จ: {e}")
        return None

# ================== LOGIN / NAVIGATE TEAMS ==================


def login_to_microsoft(driver, email: str, password: str):
    wait = WebDriverWait(driver, 20)

    try:
        set_status("[INFO] รอช่องใส่ email (i0116)...")
        email_input = wait.until(EC.presence_of_element_located((By.ID, "i0116")))
        email_input.clear()
        email_input.send_keys(email)

        for _ in range(3):
            try:
                next_btn = wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9")))
                next_btn.click()
                set_status("[INFO] ใส่ email และกด Next แล้ว")
                break
            except StaleElementReferenceException:
                time.sleep(1)
    except TimeoutException:
        set_status("[INFO] ไม่พบหน้าใส่อีเมล อาจจะ login อยู่แล้ว หรือหน้าไม่ใช่ standard login")
        return

    try:
        set_status("[INFO] รอช่องใส่ password (i0118)...")
        password_input = wait.until(EC.presence_of_element_located((By.ID, "i0118")))
        password_input.clear()
        password_input.send_keys(password)

        for _ in range(3):
            try:
                sign_in_btn = wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9")))
                sign_in_btn.click()
                set_status("[INFO] ใส่ password และกด Sign in แล้ว")
                break
            except StaleElementReferenceException:
                time.sleep(1)
    except TimeoutException:
        set_status("[WARN] ไม่เจอช่องใส่ password - อาจจะมี MFA หรือ login ไว้อยู่แล้ว")
        return

    set_status("[INFO] ตรวจหน้าต่าง Stay signed in...")
    for _ in range(10):
        time.sleep(1)
        tk_yield()
        try:
            btn_no = driver.find_element(By.ID, "idBtn_Back")
            if btn_no.is_displayed():
                btn_no.click()
                set_status("[INFO] กด 'No' แล้ว")
                break
        except Exception:
            pass


def wait_for_teams_page(driver, timeout=60, poll_interval=1.0):
    set_status("[INFO] รอให้หน้า Teams โหลดการ์ดคลาส/ทีม...")

    xpath_cards = (
        "//div[contains(@data-tid,'team-card')]"
        " | //div[contains(@data-tid,'class-card')]"
        " | //div[contains(@data-tid,'edu-class-card')]"
    )

    end_time = time.time() + timeout
    last_error = None

    while time.time() < end_time:
        tk_yield()
        try:
            elems = driver.find_elements(By.XPATH, xpath_cards)
            if elems:
                set_status(f"[INFO] ✅ พบการ์ด Team/Class อย่างน้อย {len(elems)} อันแล้ว")
                time.sleep(2)
                tk_yield()
                return True
        except (StaleElementReferenceException, WebDriverException) as e:
            last_error = e
        except Exception as e:
            last_error = e
        time.sleep(poll_interval)

    set_status("[WARN] ⏰ รอจนครบเวลาแล้วยังไม่เจอการ์ด Team/Class เลย")
    if last_error:
        print("[DEBUG] last error ก่อนหมดเวลา:", repr(last_error))
    return False


def normalize_course_name(aria: str) -> str:
    if not aria:
        return ""
    name = aria.strip()
    name = re.sub(r"\s+Team\s+\d+\s+of\s+\d+.*$", "", name, flags=re.IGNORECASE)
    return name.strip()


def is_probably_classroom(name: str) -> bool:
    if not name:
        return False
    n = name.lower().strip()
    if "ctrl+shift" in n:
        return False

    bad_keywords = [
        "activity",
        "calendar",
        "calls",
        "chat",
        "search box",
        "search suggestions",
        "open office app launcher",
        "resize larger",
        "resize smaller",
        "settings and more",
        "view more apps",
        "apps",
        "profile picture",
        "status available",
        "create and join teams and channels",
    ]
    if any(k in n for k in bad_keywords):
        return False

    if n in ("classes", "class", "teams", "team"):
        return False
    if re.search(r"team\s+\d+\s+of\s+\d+", n):
        return False
    if len(n) <= 3:
        return False
    return True


def get_classrooms_from_page(driver):
    set_status("[INFO] กำลังสำรวจรายชื่อ Classroom / Classes จากหน้า Teams ...")

    class_names = set()
    
    # ⭐ แก้ไข 1: เพิ่ม XPath ให้ครอบคลุมทั้ง Teams เก่าและใหม่
    xpath_cards_list = [
        # แบบมาตรฐาน (New Teams often uses this)
        "//div[contains(@class, 'team-card')]",
        "//div[contains(@data-tid, 'team-card')]",
        # แบบ Component
        "//app-team-card",
        # แบบหาจากชื่อโดยตรง (ชื่อทีมมักอยู่ใน tag h3 หรือ div ที่มี class name)
        "//h3", 
        "//div[contains(@class, 'name')]",
        # แบบหาจาก Accessibility Label (แม่นยำที่สุด)
        "//*[@aria-label and contains(@aria-label, 'Team card for')]" 
    ]

    # ⭐ แก้ไข 2: เพิ่มจำนวนรอบเป็น 15 รอบ (รอบละ 1 วิ) = รอสูงสุด 15 วิ
    max_attempts = 15
    
    for attempt in range(1, max_attempts + 1):
        # ใช้ smart_sleep ถ้ามี หรือ time.sleep ธรรมดา
        try:
            smart_sleep(driver, 1) 
        except:
            time.sleep(1)
            
        tk_yield()
        
        # เช็คว่า Browser ปิดไหม
        try:
            if not driver.title: raise Exception("Browser Closed")
        except:
            raise Exception("BrowserClosedByUser")

        total_cards_found_in_loop = 0
        
        # วนหาตาม XPath ทุกแบบ
        for xp in xpath_cards_list:
            try:
                elements = driver.find_elements(By.XPATH, xp)
            except:
                elements = []
            
            for el in elements:
                raw_name = ""
                
                # 1. ลองดึงจาก aria-label (แม่นสุด)
                try:
                    raw_name = el.get_attribute("aria-label")
                except: pass

                # 2. ถ้าไม่มี ลองดึงจาก title
                if not raw_name:
                    try: raw_name = el.get_attribute("title")
                    except: pass
                
                # 3. ถ้าไม่มี ลองดึงจาก text ด้านใน
                if not raw_name:
                    try: raw_name = el.text
                    except: pass
                
                if raw_name:
                    # คลีนชื่อ: ลบคำว่า "Team card for" ที่ Teams ชอบแถมมา
                    clean_name = raw_name.replace("Team card for", "").strip()
                    # เอาแค่บรรทัดแรก
                    clean_name = clean_name.split('\n')[0].strip()
                    
                    if clean_name:
                        # ใช้ฟังก์ชันเดิมของคุณเช็ค
                        short = normalize_course_name(clean_name)
                        if is_probably_classroom(short):
                            class_names.add(short)
                            total_cards_found_in_loop += 1

        print(f"[DEBUG] รอบสแกน {attempt}/{max_attempts}, พบชื่อสะสม: {len(class_names)}")
        
        # ถ้าเจอชื่อแล้ว และผ่านไปอย่างน้อย 3 รอบ (เพื่อให้แน่ใจว่าโหลดครบ) ก็หยุดได้
        if len(class_names) > 0 and attempt >= 3:
            break

        # Scroll ลงเพื่อกระตุ้น Lazy Load
        try:
            driver.execute_script("window.scrollBy(0, 300);")
        except:
            pass

    names_list = sorted(list(class_names))
    
    if not names_list:
        set_status("[WARN] ไม่พบ Classroom เลย (หน้าเว็บอาจเปลี่ยน หรือยังโหลดไม่เสร็จ)")
    else:
        set_status(f"[INFO] พบ Classroom / Classes ทั้งหมด: {len(names_list)} รายการ")
        for n in names_list:
            print("   -", n)

    return names_list


def choose_classroom_window(classroom_list):
    global root

    if not classroom_list:
        messagebox.showinfo("ไม่มีรายการ", "ยังไม่เจอ Classroom / Team ใด ๆ ในหน้า Teams", parent=root)
        return None

    win = ctk.CTkToplevel(root)
    win.title("Choose a class")
    win.after(200, lambda: win.wm_iconbitmap(ICON_PATH))

    # ⭐ เพิ่ม: ให้หน้าต่างนี้อยู่บนสุดเสมอ (เพื่อทับหน้า Loading)
    win.attributes('-topmost', True)
    
    # 1. ตั้งค่าเต็มจอ
    win.state("zoomed") 
    win.resizable(True, True)
    win.grab_set()
    win.configure(fg_color=TEAMS_MAIN_BG)

    # 2. สร้าง Frame หลัก (Card) แบบกำหนดขนาดใหญ่ และจัดกึ่งกลาง
    card_width = 1000  # ปรับความกว้างกล่องตรงนี้
    card_height = 750  # ปรับความสูงกล่องตรงนี้

    outer = ctk.CTkFrame(
        win,
        width=card_width,
        height=card_height,
        fg_color=TEAMS_CARD_BG,
        corner_radius=20, # เพิ่มความโค้งมน
        border_color=TEAMS_BORDER,
        border_width=2,
    )
    # ใช้ place เพื่อจัดกึ่งกลางหน้าจอเป๊ะๆ
    outer.place(relx=0.5, rely=0.5, anchor="center")
    
    # สั่งให้ Frame ไม่หดตามเนื้อหาภายใน (เพื่อให้คงขนาด card_width/height ไว้)
    outer.pack_propagate(False) 

    # --- ส่วนเนื้อหาด้านใน (ปรับขนาด Font ให้ใหญ่ขึ้น) ---

    ctk.CTkLabel(
        outer,
        text="Choose a class",
        # ปรับ Font Title ให้ใหญ่ขึ้น (32)
        font=ctk.CTkFont("Segoe UI", size=32, weight="bold"),
        text_color=TEAMS_TEXT_MAIN,
    ).pack(pady=(40, 10)) # เพิ่มระยะห่าง

    ctk.CTkLabel(
        outer,
        text="Select the class you want to be auto graded.",
        # ปรับ Font คำอธิบายให้ใหญ่ขึ้น (18)
        font=ctk.CTkFont("Segoe UI", size=18),
        text_color=TEAMS_TEXT_MUTED,
    ).pack(pady=(0, 20))

    scroll = ctk.CTkScrollableFrame(
        outer,
        fg_color="#FAF9F8",
        corner_radius=12,
    )
    scroll.pack(fill="both", expand=True, padx=40, pady=(10, 20)) # เพิ่มขอบข้าง (padx)

    selected_var = tk.StringVar(value="")

    def on_radio_click(name):
        selected_var.set(name)

    for name in classroom_list:
        rb = ctk.CTkRadioButton(
            scroll,
            text=name,
            variable=selected_var,
            value=name,
            # ปรับ Font ตัวเลือกให้ใหญ่ขึ้น (20)
            font=ctk.CTkFont("Segoe UI", size=20),
            height=40, # เพิ่มความสูงปุ่มกด
            radiobutton_width=24, # เพิ่มขนาดวงกลม
            radiobutton_height=24,
            text_color=TEAMS_TEXT_MAIN,
            border_color=TEAMS_TEXT_MUTED,
            fg_color=TEAMS_PRIMARY,
            hover_color=TEAMS_PRIMARY_HOVER,
            command=lambda n=name: on_radio_click(n),
        )
        rb.pack(anchor="w", pady=8, padx=15) # เพิ่มระยะห่างแต่ละบรรทัด

    btn_row = ctk.CTkFrame(outer, fg_color="transparent")
    btn_row.pack(fill="x", padx=40, pady=(10, 40))

    result = {"selected": None}

    def on_ok():
        val = selected_var.get().strip()
        if not val:
            # ปรับขนาด popup warning (ต้องใช้ dialog ของ ctk ถ้าจะปรับ font แต่ใช้ default ไปก่อนได้)
            messagebox.showwarning("ยังไม่ได้เลือก", "กรุณาเลือก Classroom / Team ก่อน", parent=win)
            return
        result["selected"] = val
        win.destroy()

    def on_cancel():
        print("User cancelled login.")
        try: close_created_desktop()
        except: pass
        win.destroy()

    # --- ปรับขนาดปุ่มกด ---
    ok_btn = ctk.CTkButton(
        btn_row,
        text="Continue",
        fg_color=TEAMS_PRIMARY,
        hover_color=TEAMS_PRIMARY_HOVER,
        text_color="#FFFFFF",
        font=ctk.CTkFont("Segoe UI", size=18, weight="bold"), # Font ใหญ่
        height=50, # ปุ่มสูง
        width=180, # ปุ่มกว้าง
        command=on_ok,
    )
    ok_btn.pack(side="right", padx=(15, 0))

    cancel_btn = ctk.CTkButton(
        btn_row,
        text="Cancel",
        fg_color="#EDEBE9",
        hover_color="#D2D0CE",
        text_color=TEAMS_TEXT_MAIN,
        font=ctk.CTkFont("Segoe UI", size=18), # Font ใหญ่
        height=50, # ปุ่มสูง
        width=140, # ปุ่มกว้าง
        command=on_cancel,
    )
    cancel_btn.pack(side="right")

    win.update_idletasks()
    root.wait_window(win)
    return result["selected"]
def open_classroom(driver, name: str) -> bool:
    wait = WebDriverWait(driver, 30)
    set_status(f"[INFO] กำลังพยายามเข้า: {name!r}")

    xpaths = [
        f'//div[contains(@data-tid,"team-card")]//*[contains(normalize-space(.), "{name}")]',
        f'//*[@aria-label and contains(@aria-label, "{name}")]',
        f'//span[@title="{name}"]',
        f'//div[@title="{name}"]',
        f'//*[@title and contains(@title, "{name}")]',
    ]

    last_exc = None

    for xp in xpaths:
        print(f"[DEBUG] ลองหา element ด้วย XPath: {xp}")
        try:
            elem = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
            set_status(f"[INFO] ✅ เจอ element ที่คลิกได้ด้วย XPath: {xp}")

            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                    elem,
                )
                time.sleep(0.5)
                tk_yield()
            except Exception as e_scroll:
                print("[WARN] scrollIntoView มีปัญหา:", e_scroll)

            try:
                elem.click()
            except (ElementClickInterceptedException, StaleElementReferenceException):
                driver.execute_script("arguments[0].click();", elem)

            set_status("[INFO] ✅ คลิกเข้า Classroom / Team เรียบร้อยแล้ว")
            return True

        except Exception as e:
            print(f"[DEBUG] หา/คลิก ด้วย XPath นี้ไม่สำเร็จ: {xp} -> {e}")
            last_exc = e
            continue

    set_status("[ERROR] หา Classroom / Team ตามชื่อที่เลือกไม่เจอเลย หรือคลิกไม่สำเร็จ")
    if last_exc:
        print("        Last error:", last_exc)
    return False


def open_assignments_in_class(driver, down_times: int = 1):
    wait = WebDriverWait(driver, 20)
    time.sleep(2)
    tk_yield()

    set_status("[INFO] กำลังมองหาเมนู Assignments ในกล่องรายการ...")

    try:
        # ⭐ เทคนิค: เจาะจงหาปุ่มที่อยู่ภายใน "กล่องรายชื่อ (Tree List)" เท่านั้น
        # 1. หา Container ที่เป็น virtual-tree-list-scroll-container
        # 2. ข้างในนั้นต้องมี div id="classroom" (จาก HTML ที่คุณให้มา)
        # หรือถ้า id เปลี่ยน ให้หาคำว่า Assignments ข้างในกล่องนั้นแทน
        
        target_xpath = (
            "//div[contains(@class, 'virtual-tree-list-scroll-container')]"  # 1. เข้ากล่องนี้ก่อน
            "//div[@id='classroom']"                                          # 2. หาตัวที่มี id="classroom"
        )
        
        # หรือเผื่อ id="classroom" หายไป ให้ใช้ XPath สำรองแบบหาจาก Text ภายในกล่องเดิม
        backup_xpath = (
            "//div[contains(@class, 'virtual-tree-list-scroll-container')]"
            "//*[contains(text(), 'Assignments')]"
        )

        try:
            # ลองหาด้วย ID ก่อน (แม่นยำสุด)
            assignments_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, target_xpath))
            )
        except TimeoutException:
            # ถ้าหา ID ไม่เจอ ให้ลองหาจาก Text ในกล่องเดิม
            print("[DEBUG] ไม่เจอ id='classroom' ลองหาจาก text แทน")
            assignments_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, backup_xpath))
            )

    except TimeoutException:
        set_status("[ERROR] หาเมนู Assignments ในกล่องไม่เจอ (หน้าเว็บอาจเปลี่ยนโครงสร้าง)")
        return False

    # ⭐ สั่ง Scroll ในกล่อง (เผื่อจอเล็กแล้วเมนู Assignments ตกขอบล่าง)
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", assignments_btn)
    time.sleep(0.5)
    tk_yield()

    # สั่งคลิก
    try:
        assignments_btn.click()
        set_status("[INFO] ✅ คลิกเมนู 'Assignments' (จากกล่อง Tree List) แล้ว")
    except (ElementClickInterceptedException, StaleElementReferenceException):
        driver.execute_script("arguments[0].click();", assignments_btn)
        set_status("[INFO] ใช้ JS คลิกเมนู 'Assignments' แล้ว")

    # รอโหลด content ด้านขวา
    time.sleep(5)
    tk_yield()
    return True

def switch_to_assignments_iframe(driver):
    time.sleep(2)
    tk_yield()
    try:
        driver.switch_to.default_content()
    except Exception:
        pass

    frames = driver.find_elements(By.TAG_NAME, "iframe")
    if not frames:
        set_status("[ERROR] ไม่พบ iframe ใด ๆ บนหน้านี้")
        return False

    set_status(f"[DEBUG] พบ iframe ทั้งหมด {len(frames)} ตัว")
    target = None
    for i, f in enumerate(frames, start=1):
        title = (f.get_attribute("title") or "").strip()
        src = (f.get_attribute("src") or "").strip()
        print(f"  {i}. title={title!r}, src={src[:80]!r}")
        if "assignments" in title.lower() or "assignments" in src.lower():
            target = f

    if target is None:
        set_status("[WARN] ไม่เจอ iframe ที่มีคำว่า 'assignments' ใช้อันแรกแทน")
        target = frames[0]

    driver.switch_to.frame(target)
    set_status("[INFO] ✅ สลับเข้า iframe ของ Assignments แล้ว")
    return True

def scroll_to_bottom(driver):
    try:
        last_height = 0
        for _ in range(15):
            driver.execute_script("window.scrollBy(0, window.innerHeight * 0.8);")
            time.sleep(0.4)
            tk_yield()
            new_height = driver.execute_script("return window.pageYOffset;")
            if new_height == last_height:
                break
            last_height = new_height
    except Exception:
        pass


def click_ready_to_grade_tab(driver):
    if not switch_to_assignments_iframe(driver):
        return False

    wait = WebDriverWait(driver, 20)
    time.sleep(2)
    tk_yield()

    set_status("[INFO] กำลังหาแท็บ 'Ready to grade' ...")

    try:
        elems = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//*[contains(normalize-space(text()), 'Ready to grade')]")
            )
        )
    except TimeoutException:
        set_status("[ERROR] ไม่เจอ text 'Ready to grade' ภายใน iframe เลย")
        return False

    elems = [e for e in elems if e.is_displayed()]
    if not elems:
        set_status("[ERROR] ไม่มี element 'Ready to grade' ที่มองเห็นใน iframe")
        return False

    target = min(elems, key=lambda e: e.location.get("y", 9999))

    actions = ActionChains(driver)
    try:
        actions.move_to_element(target).pause(0.2).click().perform()
        set_status("[INFO] ✅ คลิกแท็บ 'Ready to grade' แล้ว")
    except (ElementClickInterceptedException, StaleElementReferenceException):
        try:
            target.send_keys(Keys.ENTER)
            set_status("[INFO] ✅ ส่ง ENTER ไปที่แท็บ 'Ready to grade' แล้ว")
        except Exception as e2:
            set_status(f"[ERROR] คลิก 'Ready to grade' ไม่สำเร็จ: {e2}")
            return False

    time.sleep(3)
    tk_yield()
    return True


def is_valid_assignment_title(title: str):
    t = title.strip()
    tl = t.lower()
    if not t:
        return False

    # 🔹 ตัด header ที่เป็นวันในสัปดาห์ (Mon, Monday, Tue,...)
    day_words = [
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "mon", "tue", "tues", "wed", "thu", "thur", "thurs", "fri", "sat", "sun", "today", "yesterday"
    ]

    # 🔹 ตัด header ที่เป็นเดือน (June, Jun, September, Sep,...)
    month_words = [
        "january", "february", "march", "april", "may", "june", "july",
        "august", "september", "october", "november", "december",
        "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec"
    ]

    # ทำให้ normalize หน่อย เผื่อเป็น "Monday," หรือ "June  "
    normalized = re.sub(r"[.,:]", " ", tl)   # ตัด , . :
    normalized = " ".join(normalized.split())  # ลด space ซ้ำ

    # ถ้าทั้งบรรทัดคือชื่อวัน/เดือนอย่างเดียว → ไม่ใช่ assignment
    if normalized in day_words or normalized in month_words:
        return False

    # ---------- เงื่อนไขเดิมของคุณ ----------
    if tl in ("assignment", "assignments"):
        return False

    # เช่น "Week 1", "Unit 2" ที่สั้นเกินไป/ก้ำกึ่ง
    if re.match(r"^[A-Za-z]{3,}\s+\d{1,2}(st|nd|rd|th)?$", t):
        return False

    if len(t) <= 1 and not t.isdigit():
        return False

    return True


def get_assignments_from_ready_to_grade(driver):
    # 1. ลองสลับ Iframe ก่อน (ถ้ามี)
    if not switch_to_assignments_iframe(driver):
        return []

    set_status("[INFO] กำลังสแกนรายการ assignment จากหน้า Ready to grade ...")

    assignments = []
    seen_titles = set()

    # ย้าย List คำศัพท์มาไว้นอก Loop จะได้ไม่ต้องประกาศใหม่ทุกรอบ
    month_words = [
        "jan", "january", "feb", "february", "mar", "march", "apr", "april", "may",
        "jun", "june", "jul", "july", "aug", "august", "sep", "sept", "september",
        "oct", "october", "nov", "november", "dec", "december",
    ]
    day_words = [
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "mon", "tue", "tues", "wed", "thu", "thur", "thurs", "fri", "sat", "sun"
    ]

    # ⭐ Loop รอสูงสุด 15 รอบ (15 วินาที)
    max_attempts = 15
    
    for attempt in range(1, max_attempts + 1):
        # ใช้ smart_sleep สั้นๆ เพื่อเช็ค Browser
        try: smart_sleep(driver, 1)
        except: time.sleep(1)
        
        tk_yield()

        # เช็คว่า Browser ยังอยู่ไหม
        try:
            if not driver.title: raise Exception("Browser Closed")
        except:
            raise Exception("BrowserClosedByUser")

        # หา Elements (ใช้ XPath เดิมที่ครอบคลุม)
        try:
            elems = driver.find_elements(
                By.XPATH,
                "//*[@role='row']"
                " | //div[contains(., 'Due at')]"
                " | //div[contains(., 'Due ')]"
                " | //div[contains(., 'กำหนดส่ง')]"
            )
        except Exception:
            elems = []

        # เริ่มกระบวนการคัดแยก (Parsing)
        current_loop_assignments = []
        current_loop_titles = set()

        for el in elems:
            try:
                # เช็คความสูง Element (ถ้าเป็น element ซ่อนอยู่ ไม่ต้องเอามา)
                if not el.is_displayed(): continue 
                txt = (el.text or "").strip()
            except:
                continue
                
            if not txt: continue

            lower = txt.lower()
            # กรองเบื้องต้น
            if "due at" not in lower and "due " not in lower and "กำหนดส่ง" not in lower:
                continue

            # ตัดคำว่า Due... ออก
            title_part = txt
            for key in ["Due at", "Due ", "กำหนดส่ง"]:
                if key in txt:
                    title_part = txt.split(key, 1)[0].strip()
                    break
            
            if not title_part: continue

            # แยกบรรทัด
            lines = [l.strip() for l in title_part.splitlines() if l.strip()]
            if not lines: continue

            first = lines[0]
            rest = lines[1:] if len(lines) > 1 else []

            # เช็คว่าเป็นบรรทัดวันที่หรือไม่ (Header)
            first_l = first.lower()
            tokens = re.sub(r"[.,]", " ", first_l).split()
            
            has_day_or_month = any(tok in day_words or tok in month_words for tok in tokens)
            has_number = any(re.search(r"\d", tok) for tok in tokens)

            # Logic เลือกชื่อ Assignment
            if has_day_or_month and has_number and rest:
                title_line = rest[0]
            else:
                title_line = first

            title_line = title_line.strip()
            
            # ตรวจสอบความถูกต้องของชื่อ (ถ้ามีฟังก์ชันนี้อยู่แล้ว)
            if not is_valid_assignment_title(title_line):
                continue
                
            # เช็คซ้ำในรอบนี้
            if title_line not in seen_titles and title_line not in current_loop_titles:
                current_loop_titles.add(title_line)
                current_loop_assignments.append((title_line, el))

        # [DEBUG]
        print(f"[DEBUG] รอบสแกน Assignment {attempt}/{max_attempts}, พบ: {len(current_loop_assignments)} รายการ")

        # ⭐ ถ้าเจอแล้ว หยุดรอทันที! (ไม่ต้องรอครบ 15 วิ)
        if current_loop_assignments:
            assignments = current_loop_assignments
            break
        
        # ถ้ายังไม่เจอ ลอง Scroll ลงนิดนึงเผื่อ Lazy Load
        try:
            driver.execute_script("window.scrollBy(0, 300);")
        except:
            pass

    # สรุปผล
    set_status(f"[INFO] พบ assignment ทั้งหมดใน Ready to grade: {len(assignments)} รายการ")
    for t, _ in assignments:
        print("   -", t)

    return assignments

def choose_assignment_in_ready_to_grade(driver):
    global root

    assignments = get_assignments_from_ready_to_grade(driver)
    if not assignments:
        messagebox.showinfo("ไม่มีรายการ", "ไม่พบ assignment ใด ๆ ในหน้า Ready to grade", parent=root)
        return None  # ❗ เปลี่ยนเป็น None

    titles = [t for (t, _) in assignments]

    win = ctk.CTkToplevel(root)
    win.title("Choose an assignment")
    win.after(200, lambda: win.wm_iconbitmap(ICON_PATH))

    # ⭐ เพิ่ม: ให้หน้าต่างนี้อยู่บนสุดเสมอ (เพื่อทับหน้า Loading)
    win.attributes('-topmost', True)
    
    # --- 1. ปรับให้เต็มจอ ---
    win.state("zoomed") 
    win.resizable(True, True)
    win.grab_set()
    win.configure(fg_color=TEAMS_MAIN_BG)

    # --- 2. สร้าง Frame กลางจอ (Card) ---
    # กำหนดขนาด Card ให้ใหญ่ขึ้น
    card_width = 1000 
    card_height = 750

    outer = ctk.CTkFrame(
        win,
        width=card_width,
        height=card_height,
        fg_color=TEAMS_CARD_BG,
        corner_radius=20,
        border_color=TEAMS_BORDER,
        border_width=2,
    )
    # ใช้ place จัดกึ่งกลาง
    outer.place(relx=0.5, rely=0.5, anchor="center")
    outer.pack_propagate(False) # ล็อคขนาดไม่ให้หด

    # --- 3. เนื้อหาด้านใน (ปรับ Font ให้ใหญ่) ---
    ctk.CTkLabel(
        outer,
        text="Choose an assignment",
        font=ctk.CTkFont("Segoe UI", size=32, weight="bold"), # Font ใหญ่ 32
        text_color=TEAMS_TEXT_MAIN,
    ).pack(pady=(40, 10))

    ctk.CTkLabel(
        outer,
        text="Select the assignment you want to be auto graded.",
        font=ctk.CTkFont("Segoe UI", size=18), # Font ใหญ่ 18
        text_color=TEAMS_TEXT_MUTED,
    ).pack(pady=(0, 20))

    scroll = ctk.CTkScrollableFrame(
        outer,
        fg_color="#FAF9F8",
        corner_radius=12,
    )
    scroll.pack(fill="both", expand=True, padx=40, pady=(10, 20))

    selected_var = tk.StringVar(value="")

    def on_radio_click(name):
        selected_var.set(name)

    for t in titles:
        rb = ctk.CTkRadioButton(
            scroll,
            text=t,
            variable=selected_var,
            value=t,
            font=ctk.CTkFont("Segoe UI", size=20), # Font ตัวเลือกใหญ่ 20
            height=40,            # ความสูงบรรทัด
            radiobutton_width=24, # ขนาดวงกลม
            radiobutton_height=24,
            text_color=TEAMS_TEXT_MAIN,
            border_color=TEAMS_TEXT_MUTED,
            fg_color=TEAMS_PRIMARY,
            hover_color=TEAMS_PRIMARY_HOVER,
            command=lambda name=t: on_radio_click(name),
        )
        rb.pack(anchor="w", pady=8, padx=15)

    btn_row = ctk.CTkFrame(outer, fg_color="transparent")
    btn_row.pack(fill="x", padx=40, pady=(10, 40))

    result = {"chosen_title": None}

    def on_ok():
        val = selected_var.get().strip()
        if not val:
            messagebox.showwarning("ยังไม่ได้เลือก", "กรุณาเลือก assignment ก่อน", parent=win)
            return
        result["chosen_title"] = val
        win.destroy()

    def on_cancel():
        print("User cancelled login.")
        try: close_created_desktop()
        except: pass
        win.destroy()

    # --- 4. ปุ่มกด (Button) ใหญ่ขึ้น ---
    ok_btn = ctk.CTkButton(
        btn_row,
        text="Continue",
        fg_color=TEAMS_PRIMARY,
        hover_color=TEAMS_PRIMARY_HOVER,
        text_color="#FFFFFF",
        font=ctk.CTkFont("Segoe UI", size=18, weight="bold"), # Font ปุ่ม
        height=50,
        width=180,
        command=on_ok,
    )
    ok_btn.pack(side="right", padx=(15, 0))

    cancel_btn = ctk.CTkButton(
        btn_row,
        text="Cancel",
        fg_color="#EDEBE9",
        hover_color="#D2D0CE",
        text_color=TEAMS_TEXT_MAIN,
        font=ctk.CTkFont("Segoe UI", size=18), # Font ปุ่ม
        height=50,
        width=140,
        command=on_cancel,
    )
    cancel_btn.pack(side="right")

    win.update_idletasks()
    
    # ส่วนนี้ลบ geometry กลางจอแบบเก่าออกได้เลย เพราะเราใช้ zoomed แล้ว
    # sw = win.winfo_screenwidth() ...
    
    win.protocol("WM_DELETE_WINDOW", on_cancel)
    root.wait_window(win)

    chosen_title = result["chosen_title"]
    if not chosen_title:
        set_status("[INFO] ผู้ใช้ยกเลิกการเลือก assignment")
        return None 
    
    set_status(f"[INFO] คุณเลือก assignment: {chosen_title!r}")

    # ----------- logic เดิมด้านล่าง = ใช้ chosen_title เพื่อหา row แล้วคลิก -----------

    if not switch_to_assignments_iframe(driver):
        return None
    time.sleep(1)
    tk_yield()

    target_row = None
    for title, row in assignments:
        try:
            if title == chosen_title and row.is_displayed():
                target_row = row
                break
        except Exception:
            continue

    if target_row is None:
        set_status("[DEBUG] หา row จาก assignments list ไม่เจอ ลองสแกน DOM ใหม่ด้วยชื่อแทน")
        try:
            elems = driver.find_elements(
                By.XPATH,
                f"//*[normalize-space(text())={repr(chosen_title)}]"
            )
        except Exception:
            elems = []

        elems = [e for e in elems if e.is_displayed()]
        if elems:
            elem = elems[0]
            try:
                target_row = elem.find_element(
                    By.XPATH, "ancestor::*[@role='row'][1]"
                )
            except Exception:
                target_row = elem

    if target_row is None:
        set_status(
            f"[ERROR] หา assignment ที่ชื่อ {chosen_title!r} ไม่เจอใน DOM (ทั้งจาก list เดิมและสแกนใหม่)"
        )
        return None

    clickable = None
    try:
        candidates = target_row.find_elements(
            By.XPATH,
            ".//a[contains(@href,'assignments')]"
            " | .//button[@role='link' or @role='button']"
            " | .//*[@role='link']"
            " | .//span"
        )
    except Exception:
        candidates = []

    for c in candidates:
        try:
            if not c.is_displayed():
                continue
            txt = (c.text or "").strip()
            aria = (c.get_attribute("aria-label") or "").strip()
            if chosen_title in txt or chosen_title in aria:
                clickable = c
                break
        except Exception:
            continue

    if clickable is None:
        clickable = target_row

    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center', inline:'center'});",
            clickable
        )
        time.sleep(0.5)
        tk_yield()
    except Exception:
        pass

    try:
        ActionChains(driver).move_to_element(clickable).pause(0.2).click().perform()
        set_status("[INFO] ✅ คลิกการ์ด assignment แล้ว")
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", clickable)
            set_status("[INFO] ✅ คลิกการ์ด assignment ด้วย JS แล้ว")
        except Exception as e2:
            set_status(f"[ERROR] คลิกการ์ด assignment {chosen_title!r} ไม่สำเร็จ: {e2}")
            return None

    time.sleep(5)
    tk_yield()

    try:
        driver.switch_to.default_content()
    except Exception:
        pass

    # 💡 สำคัญ: ตอนจบให้ส่งชื่อ assignment กลับไป
    return chosen_title


def get_current_assignment_title(driver) -> str:
    """
    ดึงชื่อ assignment ปัจจุบันแบบแม่นยำที่สุด
    """
    # 1) หา element ที่มี aria-label พวก "Assignment details for ..."
    try:
        elems = driver.find_elements(
            By.XPATH,
            "//*[@aria-label[contains(., 'Assignment') and contains(., 'details')]]"
        )
        for el in elems:
            aria = el.get_attribute("aria-label") or ""
            m = re.search(r"Assignment details for (.+)", aria)
            if m:
                title = m.group(1).strip()
                if title and title.lower() != "assignment":
                    return title
    except Exception:
        pass

    # 2) หา data-tid ของ assignment title โดยตรง
    try:
        el = driver.find_element(By.XPATH, "//*[@data-tid='assignment-title']")
        text = el.text.strip()
        if text and text.lower() != "assignment":
            return text
    except Exception:
        pass

    # 3) หา h1/h2 แบบเดิมแต่ต้องกรองคำว่า "Assignment"
    candidates = ["//h1", "//h2"]
    for xp in candidates:
        try:
            el = driver.find_element(By.XPATH, xp)
            text = el.text.strip()
            if text and text.lower() != "assignment":
                return text
        except Exception:
            continue

    return "Unknown assignment"


def go_back_to_students_table(driver) -> bool:
    if not switch_to_assignments_iframe(driver):
        return False

    time.sleep(1)
    tk_yield()

    try:
        rows = driver.find_elements(By.XPATH, "//*[@role='row']")
        for r in rows:
            try:
                txt = (r.text or "").lower()
            except Exception:
                continue
            if "status" in txt or "สถานะ" in txt:
                return True
    except Exception:
        pass

    try:
        back_candidates = driver.find_elements(
            By.XPATH,
            "//button[contains(@aria-label,'Back') or contains(@data-tid,'back')]"
            " | //button[contains(.,'Back') or contains(.,'กลับ') or contains(.,'ย้อนกลับ')]"
        )
        for b in back_candidates:
            if b.is_displayed():
                try:
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", b
                    )
                except Exception:
                    pass
                b.click()
                time.sleep(2)
                tk_yield()
                return True
    except Exception:
        pass

    try:
        driver.back()
        time.sleep(2)
        tk_yield()
        return True
    except Exception:
        return False

# ================== APPLY FEEDBACK ==================


def apply_feedback_and_score_for_current_student(driver, feedback_text, score):
    set_status("[AUTO] กำลังเติม feedback ...")

    if not switch_to_assignments_iframe(driver):
        set_status("[ERROR] เข้า iframe ของ Assignments ไม่ได้")
        return

    wait = WebDriverWait(driver, 20)

    feedback_box = None
    fb_xpaths = [
        "//div[@role='textbox' and @contenteditable='true']",
        "//div[@contenteditable='true']",
        "//textarea[contains(@aria-label,'Feedback') or contains(@aria-label,'ข้อเสนอแนะ')]",
    ]
    for xp in fb_xpaths:
        try:
            elems = driver.find_elements(By.XPATH, xp)
            elems = [e for e in elems if e.is_displayed()]
            if elems:
                feedback_box = elems[0]
                break
        except Exception:
            pass

    if feedback_box is None:
        set_status("[ERROR] ไม่พบช่อง feedback เลย")
        return

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", feedback_box)
    except Exception:
        pass

    js_insert_fb = """
        const box = arguments[0];
        const text = arguments[1];

        if (!box) return;

        if (box.tagName && box.tagName.toLowerCase() === 'textarea') {
            box.focus();
            box.value = text;
        } else {
            box.focus();
            box.innerHTML = '';
            const lines = text.split('\\n');
            for (let line of lines) {
                const p = document.createElement('p');
                p.textContent = line;
                box.appendChild(p);
            }
        }

        const ev1 = new Event('input',  { bubbles: true });
        const ev2 = new Event('change', { bubbles: true });
        box.dispatchEvent(ev1);
        box.dispatchEvent(ev2);
    """
    try:
        driver.execute_script(js_insert_fb, feedback_box, feedback_text)
        set_status("[AUTO] ใส่ feedback สำเร็จ ✓")
    except Exception as e:
        set_status(f"[ERROR] JS injection feedback ล้มเหลว: {e}")
        return

    time.sleep(0.6)
    tk_yield()

    if score is not None:
        score_input = None
        score_xpaths = [
            "//input[@data-test='points-input']",
            "//input[contains(@aria-label,'Grade must be out of')]",
            "//input[contains(@aria-label,'point') or contains(@aria-label,'คะแนน')]",
            "//input[@type='text' and @maxlength='12']",
        ]
        for xp in score_xpaths:
            try:
                elems = driver.find_elements(By.XPATH, xp)
                elems = [e for e in elems if e.is_displayed() and e.is_enabled()]
                if elems:
                    score_input = elems[0]
                    break
            except Exception:
                pass

        if score_input is None:
            set_status("[WARN] ไม่พบช่องกรอกคะแนน (points-input)")
        else:
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", score_input
                )
            except Exception:
                pass

            try:
                score_input.click()
            except Exception:
                pass

            # เคลียร์ค่าเก่าออกให้หมด
            try:
                score_input.clear()
            except Exception:
                pass
            try:
                score_input.send_keys(Keys.CONTROL, "a")
                score_input.send_keys(Keys.DELETE)
            except Exception:
                pass
            try:
                driver.execute_script("arguments[0].value = '';", score_input)
            except Exception:
                pass

            # ✔ ใส่คะแนนแค่ครั้งเดียว
            score_str = str(score)
            try:
                score_input.send_keys(score_str)
                actual_val = driver.execute_script(
                    "return arguments[0].value;", score_input
                )
                set_status(
                    f"[AUTO] ใส่คะแนนในช่อง: ต้องเป็น {score_str}, DOM value ตอนนี้ = {actual_val!r}"
                )
            except Exception as e:
                set_status(f"[ERROR] ใส่คะแนนล้มเหลว: {e}")

    submit_btn = None
    submit_xpaths = [
        "//button[@data-test='return-button']",
        "//button[contains(.,'Return')]",
        "//button[contains(.,'ส่งกลับ')]",
        "//button[contains(.,'ส่งคะแนน')]",
    ]
    for xp in submit_xpaths:
        try:
            elems = driver.find_elements(By.XPATH, xp)
            elems = [e for e in elems if e.is_displayed() and e.is_enabled()]
            if elems:
                submit_btn = elems[0]
                break
        except Exception:
            pass

    if submit_btn is None:
        set_status("[ERROR] หา ปุ่ม Return/ส่งกลับ ไม่เจอ")
    else:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
            time.sleep(0.3)
            tk_yield()
            try:
                submit_btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", submit_btn)
            set_status("[AUTO] ✅ กดปุ่ม Return/ส่งกลับ เรียบร้อยแล้ว")
        except Exception as e:
            set_status(f"[ERROR] กดปุ่มส่งกลับล้มเหลว: {e}")

    try:
        driver.switch_to.default_content()
    except Exception:
        pass

# ================== DOWNLOAD จากปุ่มสามจุด ==================


def click_three_dots_and_download(driver, file_elem, file_name, download_dir) -> str | None:
    wait = WebDriverWait(driver, 20)
    os.makedirs(download_dir, exist_ok=True)

    set_status(f"[INFO] จะพยายามใช้จุดสามจุดแล้วดาวน์โหลดไฟล์ {file_name}")

    safe_original_name = re.sub(r'[\\/*?:"<>|]', "_", file_name)
    browser_download_path = os.path.join(download_dir, safe_original_name)
    tmp_path = browser_download_path + ".crdownload"

    # ลบไฟล์เก่าที่ค้างอยู่ก่อน
    for p in (browser_download_path, tmp_path):
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

    # ---------- หาและคลิกปุ่มจุดสามจุด ----------
    three_dot = None

    try:
        three_dot = file_elem.find_element(
            By.XPATH,
            ".//following::button[@data-test='attachment-options-button'][1]"
        )
    except Exception:
        three_dot = None

    if three_dot is None:
        try:
            xpath = (
                f"//button[@data-test='attachment-options-button' "
                f" and contains(@aria-label, \"{file_name}\")]"
            )
            three_dot = driver.find_element(By.XPATH, xpath)
        except Exception:
            three_dot = None

    if three_dot is None:
        try:
            three_dot = driver.find_element(
                By.XPATH,
                "//button[@data-test='attachment-options-button' "
                " or @title='More attachment options' "
                " or contains(@aria-label,'Open options for resource:')]"
            )
        except Exception:
            three_dot = None

    if three_dot is None:
        set_status("[WARN] หาเมนูจุดสามจุด (More options) ไม่เจอเลย")
        return None

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", three_dot)
    except Exception:
        pass

    try:
        ActionChains(driver).move_to_element(three_dot).pause(0.1).click().perform()
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", three_dot)
        except Exception as e:
            set_status(f"[ERROR] คลิกปุ่ม More options ไม่สำเร็จ: {e}")
            return None

    set_status(f"[INFO] คลิกจุดสามจุดของไฟล์ {file_name} แล้ว")

    # ---------- หาเมนู Download จาก popup menu GLOBAL ----------
    download_item = None

    for attempt in range(3):
        try:
            # popup menu ของ Teams จะเป็น div role="menu" หรือ dialog
            menu = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@role='menu' or @role='dialog']")
                )
            )

            # หา "Download / ดาวน์โหลด" ภายใน popup นั้น
            candidates = menu.find_elements(
                By.XPATH,
                ".//*[contains(normalize-space(.),'Download') or "
                "contains(normalize-space(.),'ดาวน์โหลด')]"
            )

            candidates = [c for c in candidates if c.is_displayed()]
            if candidates:
                download_item = candidates[0]
                break

        except StaleElementReferenceException:
            set_status("[WARN] popup menu กลายเป็น stale ลองหาใหม่อีกครั้ง...")
            time.sleep(0.4)
        except TimeoutException:
            break
        except Exception as e:
            set_status(f"[WARN] หา popup menu ไม่สำเร็จรอบที่ {attempt+1}: {e}")
            time.sleep(0.4)

    if download_item is None:
        set_status("[ERROR] ไม่พบเมนู Download / ดาวน์โหลด ใน pop-up เมนู")
        return None

    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", download_item)
    except Exception:
        pass

    try:
        download_item.click()
    except StaleElementReferenceException:
        # ถ้า stale ระหว่างคลิก ให้หาใหม่ใน popup แล้วคลิกอีกรอบ
        try:
            menu = driver.find_element(By.XPATH, "//div[@role='menu' or @role='dialog']")
            download_item = menu.find_element(
                By.XPATH,
                ".//*[contains(normalize-space(.),'Download') or "
                "contains(normalize-space(.),'ดาวน์โหลด')]"
            )
            download_item.click()
        except Exception as e:
            set_status(f"[ERROR] คลิกเมนู Download ไม่สำเร็จ (stale ซ้ำ): {e}")
            return None
    except Exception as e:
        try:
            driver.execute_script("arguments[0].click();", download_item)
        except Exception as e2:
            set_status(f"[ERROR] คลิกเมนู Download ไม่สำเร็จ: {e2}")
            return None

    set_status(f"[INFO] คลิกเมนู Download ของไฟล์ {file_name} แล้ว กำลังรอให้ดาวน์โหลดเสร็จ...")

    # ---------- รอให้ไฟล์โหลดเสร็จ ----------
    finished = False
    for _ in range(60):
        if os.path.exists(browser_download_path) and not os.path.exists(tmp_path):
            finished = True
            break
        time.sleep(1)
        tk_yield()

    if not finished:
        set_status(
            f"[ERROR] รอจนเกินเวลาแล้วยังไม่พบไฟล์ที่ดาวน์โหลดเสร็จ: {browser_download_path}"
        )
        return None

    set_status(f"[INFO] ✅ ดาวน์โหลดเสร็จแล้ว: {browser_download_path}")
    return browser_download_path

# ================== MAIN GRADING LOOP ==================

def get_assignment_max_score(driver) -> int | None:
    """
    พยายามดึง 'คะแนนเต็ม' จากหน้า Assignments
    เช่น เจอข้อความแบบ '0 / 4', '3 / 10 points' ฯลฯ
    """
    if not switch_to_assignments_iframe(driver):
        return None

    try:
        elems = driver.find_elements(By.XPATH, "//*[contains(text(),'/')]")
    except Exception:
        return None

    max_score = None
    for el in elems:
        try:
            text = (el.text or "").strip()
        except Exception:
            continue
        if not text or "/" not in text:
            continue

        m = re.search(r"/\s*(\d+)\s*(?:points?|pts?|คะแนน)?\b", text, flags=re.IGNORECASE)
        if not m:
            continue
        try:
            val = int(m.group(1))
        except ValueError:
            continue

        if val > 0:
            max_score = val
            break

    if max_score is not None:
        set_status(f"[INFO] เดาคะแนนเต็มของ assignment นี้จากหน้าเว็บ ≈ {max_score}")
    else:
        set_status("[INFO] หา 'คะแนนเต็ม' จากหน้า assignment ไม่เจอ จะไม่ส่งให้ AI")

    return max_score


def extract_max_score(driver):
    """
    ดึง 'คะแนนเต็ม' จากหน้าให้คะแนนของนักศึกษาใน Assignment
    ตัวอย่าง DOM:
        <div class="points-context__8NmZn max-points__a-lWD"> / 10</div>
    ถ้าหาไม่เจอ → คืนค่า 4 เป็นค่า default (สำหรับ rubric 1–4)
    """
    try:
        # 1) หา element ที่เป็น / 10 ตาม class ที่เห็น
        elems = driver.find_elements(
            By.XPATH,
            "//div[contains(@class,'max-points') or contains(@class,'points-context')]"
        )
        for e in elems:
            text = (e.text or "").strip()
            # คาดหวังรูปแบบเช่น "/ 10" หรือ " /10"
            m = re.search(r"/\s*(\d+)", text)
            if m:
                val = int(m.group(1))
                if val > 0:
                    set_status(f"[INFO] พบคะแนนเต็มจาก DOM: {val}")
                    return val
    except Exception as ex:
        set_status(f"[WARN] extract_max_score เจอ error: {ex}")

    # 2) fallback: พยายามมองหา string ที่มี / ตัวเลข ทั่วหน้า
    try:
        elems = driver.find_elements(By.XPATH, "//*[contains(normalize-space(text()), '/')]")
        for e in elems:
            text = (e.text or "").strip()
            m = re.search(r"/\s*(\d+)", text)
            if m:
                val = int(m.group(1))
                if val > 0:
                    set_status(f"[INFO] เดาคะแนนเต็มจากข้อความอื่นในหน้า ≈ {val}")
                    return val
    except Exception:
        pass

    set_status("[INFO] หา 'คะแนนเต็ม' จาก DOM ไม่เจอ ใช้ค่า default = 4")
    return 4  # fallback ถ้าหาไม่เจอ




def extract_student_name(row_elem):
    """
    พยายามดึงชื่อเต็มนักศึกษาจาก row ในตาราง:
    - ลองดูจาก aria-label ก่อน (เช่น 'Open work for Somchai Prasertpanich')
    - ถ้าไม่ได้ → title
    - ถ้าไม่ได้ → span ข้างในที่มีชื่อดูเหมือนชื่อคน
    - สุดท้าย fallback จากบรรทัดแรกของ row.text
    """
    # 1) aria-label
    try:
        aria = row_elem.get_attribute("aria-label") or ""
        if aria.strip():
            m = re.search(r"for\s+(.+)", aria, flags=re.IGNORECASE)
            if m:
                return m.group(1).strip()
    except Exception:
        pass

    # 2) title
    try:
        ttl = row_elem.get_attribute("title") or ""
        if ttl.strip():
            return ttl.strip()
    except Exception:
        pass

    # 3) spans ภายใน (เผื่อ Teams เก็บชื่อเป็น span)
    try:
        spans = row_elem.find_elements(By.XPATH, ".//span")
        for s in spans:
            t = (s.text or "").strip()
            # heuristic ง่าย ๆ: ยาว >= 3 และมีช่องว่าง (ชื่อจริง + นามสกุล)
            if len(t) >= 3 and " " in t:
                return t
    except Exception:
        pass

    # 4) fallback จาก text ทั้งก้อน
    try:
        raw = (row_elem.text or "").strip()
        line0 = raw.splitlines()[0].strip()
        if line0:
            return line0
    except Exception:
        pass

    return None

def estimate_students_to_grade(driver) -> int:
    """
    สแกนตารางนักเรียน 1 รอบ เพื่อประมาณจำนวนคนที่ status = turned_in / turned_in_late
    ใช้ logic เดียวกับ loop ตรวจจริง แต่ไม่เรียก AI
    """
    if not switch_to_assignments_iframe(driver):
        return 0

    set_status("[INFO] กำลังนับจำนวนนักศึกษาที่ต้องตรวจทั้งหมด...")

    names = set()

    try:
        driver.execute_script("window.scrollTo(0, 0);")
    except Exception:
        pass

    max_scroll_attempts = 12
    last_scroll_y = -1

    for _ in range(max_scroll_attempts):
        time.sleep(0.8)
        tk_yield()
        try:
            rows = driver.find_elements(By.XPATH, "//*[@role='row']")
        except Exception:
            rows = []

        for r in rows:
            try:
                row_text = (r.text or "").strip()
            except Exception:
                continue
            if not row_text:
                continue

            tl = row_text.lower()
            if "status" in tl or "สถานะ" in tl:
                continue

            student_name = extract_student_name(r)
            if not student_name:
                continue

            status = "unknown"
            if "not turned in" in tl or "ยังไม่ได้ส่ง" in tl:
                status = "not_turned_in"
            elif "turned in late" in tl or "ส่งช้า" in tl:
                status = "turned_in_late"
            elif "turned in again" in tl:
                status = "turned_in"
            elif "turned in" in tl or "ส่งแล้ว" in tl:
                status = "turned_in"
            elif "viewed" in tl or "ดูแล้ว" in tl:
                status = "viewed"
            elif "handed in" in tl or "ส่งแล้ว" in tl:
                status = "handed_in"
            elif "handed in late" in tl or "ส่งแล้ว" in tl:
                status = "handed_in_late"
            elif "handed in again" in tl or "ส่งแล้ว" in tl:
                status = "handed_in"

            if status in ("turned_in", "turned_in_late", "handed_in", "handed_in_late"):
                names.add(student_name)

        # เลื่อนลง
        try:
            current_y = driver.execute_script("return window.scrollY;")
        except Exception:
            current_y = None

        try:
            driver.execute_script("window.scrollBy(0, window.innerHeight * 0.7);")
        except Exception:
            break

        if current_y is not None and current_y == last_scroll_y:
            break
        last_scroll_y = current_y

    # กลับไปบนสุด
    try:
        driver.execute_script("window.scrollTo(0, 0);")
    except Exception:
        pass

    total = len(names)
    set_status(f"[INFO] พบจำนวนนักศึกษาที่ต้องตรวจทั้งหมด ≈ {total} คน")
    return total


def process_all_students_in_current_assignment(driver):
    """
    ไล่ตรวจนักศึกษาใน assignment ปัจจุบัน
    - ตรวจเฉพาะ status: turned_in / turned_in_late (ไม่ตรวจ viewed)
    - ไล่บนลงล่าง
    - ใช้ window.scrollBy เหมือนเวอร์ชันที่เคยเลื่อนได้
    - วนสแกนหน้าสูงสุด 3 รอบ (เผื่อมีนักศึกษาส่งงานเพิ่มระหว่างรัน)
    """
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    assignment_name = get_current_assignment_title(driver)
    set_status(f"[INFO] กำลังไล่ตรวจนักเรียนใน assignment: {assignment_name!r} ...")

    # ประมาณจำนวนคนที่ต้องตรวจทั้งหมด แล้วเซ็ต progress เริ่มต้น
    total_to_grade = estimate_students_to_grade(driver)
    init_progress(total_to_grade)
    set_current_student(None)

    processed_students = set()
    session = build_requests_session_from_driver(driver)

    MIN_TEXT_LEN = 80

    max_rounds = 3
    for round_idx in range(1, max_rounds + 1):
        set_status(f"[ROUND] 🔁 เริ่มตรวจรอบที่ {round_idx}/{max_rounds}")
        if not switch_to_assignments_iframe(driver):
            set_status("[ERROR] เข้า iframe ของ Assignments ไม่ได้ หยุดตรวจงาน")
            return

        # กลับไปบนสุดของหน้า
        try:
            driver.execute_script("window.scrollTo(0, 0);")
        except Exception:
            pass
        time.sleep(1)
        tk_yield()

        checked_someone_this_round = False

        scroll_attempts = 0
        max_scroll_attempts = 10  # ⭐ เพิ่มให้เยอะขึ้น กันกรณีจอเตี้ย / รายชื่อยาว

        while True:
            if not switch_to_assignments_iframe(driver):
                set_status("[ERROR] เข้า iframe ของ Assignments ไม่ได้ระหว่างรอบ ตรวจหยุดตรงนี้")
                return

            time.sleep(1)
            tk_yield()

            try:
                rows = driver.find_elements(By.XPATH, "//*[@role='row']")
            except Exception as e:
                set_status(f"[ERROR] หาแถวนักเรียนไม่เจอ: {e}")
                return

            candidate_row = None
            candidate_status = None
            candidate_name = None

            # 🔽 ไล่บนลงล่างเพื่อหานักเรียนคนถัดไปที่ยังไม่ตรวจ
            for r in rows:
                try:
                    row_text = (r.text or "").strip()
                except Exception:
                    continue
                if not row_text:
                    continue

                tl = row_text.lower()

                # ข้ามหัวตาราง
                if "status" in tl or "สถานะ" in tl:
                    continue

                # ✅ ใช้ชื่อเต็มจาก extract_student_name
                student_name = extract_student_name(r)
                if not student_name:
                    continue

                # ข้ามคนที่ตรวจไปแล้ว
                if student_name in processed_students:
                    continue

                status = "unknown"
                if "not turned in" in tl or "ยังไม่ได้ส่ง" in tl:
                    status = "not_turned_in"
                elif "turned in late" in tl or "ส่งช้า" in tl:
                    status = "turned_in_late"
                elif "turned in again" in tl:
                    status = "turned_in"
                elif "turned in" in tl or "ส่งแล้ว" in tl:
                    status = "turned_in"
                elif "viewed" in tl or "ดูแล้ว" in tl:
                    status = "viewed"
                elif "handed in" in tl or "ส่งแล้ว" in tl:
                    status = "handed_in"
                elif "handed in late" in tl or "ส่งแล้ว" in tl:
                    status = "handed_in_late"
                elif "handed in again" in tl or "ส่งแล้ว" in tl:
                    status = "handed_in"

                # ❌ ไม่ตรวจ viewed ตามที่สั่ง
                if status not in ("turned_in", "turned_in_late", "handed_in", "handed_in_late"):
                    continue

                candidate_row = r
                candidate_status = status
                candidate_name = student_name
                break

            # ถ้ายังไม่เจอใครในหน้าปัจจุบัน → เลื่อนลง
            if candidate_row is None or not candidate_name:
                if scroll_attempts < max_scroll_attempts:
                    scroll_attempts += 1
                    set_status(
                        f"[INFO] ไม่เจอนักเรียนเพิ่มในจอปัจจุบัน → เลื่อนลง "
                        f"(scroll {scroll_attempts}/{max_scroll_attempts})"
                    )
                    try:
                        # ก่อนเลื่อน ดูตำแหน่งเดิมไว้
                        current_y = driver.execute_script("return window.pageYOffset;")
                    except Exception:
                        current_y = None

                    try:
                        driver.execute_script("window.scrollBy(0, window.innerHeight * 0.7);")
                    except Exception:
                        pass

                    time.sleep(1)
                    tk_yield()

                    # ถ้าเลื่อนแล้ว y ไม่เปลี่ยน → น่าจะสุดจริง ๆ แล้ว
                    try:
                        new_y = driver.execute_script("return window.pageYOffset;")
                    except Exception:
                        new_y = None

                    if current_y is not None and new_y is not None and new_y == current_y:
                        set_status("[INFO] ดูเหมือนเลื่อนถึงท้ายสุดของตารางแล้วในรอบนี้")
                        break

                    continue  # ไปหา rows ใหม่หลังเลื่อน
                else:
                    # เลื่อนครบตามจำนวนที่กำหนดแล้ว → ถือว่าสุดหน้าจอในรอบนี้
                    set_status("[INFO] เลื่อนลงจนครบโควต้าในรอบนี้แล้ว ไม่พบคนใหม่เพิ่ม")
                    break

            # ------ เจอนักเรียนที่จะตรวจในรอบนี้ ------
            checked_someone_this_round = True
            set_status(f"[INFO] ตรวจนักเรียน: {candidate_name} (status={candidate_status})")
            set_current_student(candidate_name)

            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", candidate_row
                )
                time.sleep(0.3)
                tk_yield()
                candidate_row.click()
            except Exception as e:
                set_status(f"[WARN] คลิกเข้าแถวนักเรียน {candidate_name} ไม่สำเร็จ: {e}")
                processed_students.add(candidate_name)
                continue

            time.sleep(2)
            tk_yield()

            # ---------- หาไฟล์แนบ ----------
            files_info = []
            try:
                file_elems = driver.find_elements(
                    By.XPATH,
                    "//button[contains(@aria-label,'Open') or contains(@data-tid,'attachment')]"
                    " | //a[contains(@data-tid,'attachment') or contains(@aria-label,'file')]"
                )
            except Exception as e:
                set_status(f"[WARN] หาไฟล์แนบไม่เจอสำหรับ {candidate_name}: {e}")
                file_elems = []

            set_status(
                f"[INFO] พบ element ที่อาจเป็นไฟล์แนบ: {len(file_elems)} อัน สำหรับ {candidate_name}"
            )

            for fe in file_elems:
                try:
                    label = (fe.get_attribute("aria-label") or fe.text or "").strip()
                    href = fe.get_attribute("href") or fe.get_attribute("data-href") or ""
                except Exception:
                    continue

                if not label:
                    continue

                file_name = label
                m = re.search(r"Open options for resource:\s*(.+)", file_name, flags=re.IGNORECASE)
                if m:
                    original = file_name
                    file_name = m.group(1).strip()
                    set_status(f"[DEBUG] ปรับชื่อไฟล์จาก {original!r} -> {file_name!r}")

                if any(file_name.lower().endswith(ext) for ext in UNSUPPORTED_NOTE_EXTS):
                    set_status(f"[INFO] พบไฟล์ GoodNotes ที่ไม่รองรับ: {file_name}")
                    continue

                if not is_supported_file(file_name):
                    set_status(f"[INFO] ข้ามไฟล์ (ไม่ได้อยู่ในประเภทที่รองรับ): {file_name}")
                    continue

                set_status(f"[INFO] ไฟล์ที่รองรับ: {file_name}")
                files_info.append((file_name, href, fe))

            if not files_info:
                set_status(
                    f"[INFO] ไม่มีไฟล์ที่เป็น pdf/txt/docx/รูปภาพ ให้ตรวจสำหรับ {candidate_name} "
                    "ระบบจะไม่ส่งคะแนนอัตโนมัติสำหรับนักเรียนคนนี้"
                )
                processed_students.add(candidate_name)
                try:
                    go_back_to_students_table(driver)
                except Exception:
                    pass
                continue

            file_name, href, file_elem = files_info[0]

            file_text_raw = None
            file_bytes = None
            downloaded_path = None

            # ---------- ดาวน์โหลดไฟล์ ----------
            if href:
                set_status(f"[INFO] ไฟล์ {file_name} มี href → ดาวน์โหลดด้วย HTTP session ปัจจุบัน")
                file_bytes = download_file_via_session(session, href)
                if not file_bytes:
                    set_status(
                        f"[INFO] ดาวน์โหลดไฟล์ \"{file_name}\" ไม่สำเร็จ "
                        "จะไม่ส่งคะแนนอัตโนมัติสำหรับนักเรียนคนนี้"
                    )
                    processed_students.add(candidate_name)
                    try:
                        go_back_to_students_table(driver)
                    except Exception:
                        pass
                    continue

                file_text_raw = extract_text_from_bytes(file_name, file_bytes)

            else:
                set_status(
                    f"[INFO] ไฟล์ {file_name} ไม่มี href → ใช้เมนูจุดสามจุดแล้วกด Download ลง {DOWNLOAD_DIR}"
                )

                downloaded_path = click_three_dots_and_download(
                    driver, file_elem, file_name, DOWNLOAD_DIR
                )
                if not downloaded_path:
                    processed_students.add(candidate_name)
                    try:
                        go_back_to_students_table(driver)
                    except Exception:
                        pass
                    continue

                try:
                    with open(downloaded_path, "rb") as f:
                        file_bytes = f.read()
                except Exception as e:
                    set_status(f"[ERROR] เปิดไฟล์ที่ดาวน์โหลดมาไม่สำเร็จ: {e}")
                    processed_students.add(candidate_name)
                    try:
                        go_back_to_students_table(driver)
                    except Exception:
                        pass
                    continue

                file_text_raw = extract_text_from_bytes(file_name, file_bytes)

                try:
                    if os.path.exists(downloaded_path):
                        os.remove(downloaded_path)
                        set_status(f"[DEBUG] ลบไฟล์ชั่วคราว {downloaded_path} เรียบร้อยแล้ว")
                except Exception as e:
                    set_status(f"[WARN] ลบไฟล์ชั่วคราวไม่สำเร็จ: {e}")

            # ---------- วิเคราะห์ข้อความจากไฟล์ ----------
            file_text = clean_ocr_text(file_text_raw) if file_text_raw else ""

            # ถ้าไฟล์สั้นมากหรือเป็นภาพแต่ OCR ไม่เจอ → ก็ตรวจอยู่ดี
            if not file_text:
                file_text = "(no readable text extracted from the file)"

            # ✅ ดึงคะแนนเต็มจาก DOM ของหน้าให้คะแนน (เช่น / 10)
            max_score = extract_max_score(driver)

            # ---------- ส่งเข้า AI ----------
            ai_text, score = grade_file_with_ai(
                file_name=file_name,
                file_url=None,
                file_text=file_text,
                file_bytes=file_bytes,
                student_name=candidate_name,
                assignment_name=assignment_name,
                status_text=candidate_status,
                max_score=max_score,
            )

            if not ai_text:
                set_status(
                    f"[INFO] AI ประเมินไฟล์ \"{file_name}\" ไม่สำเร็จ "
                    "จะไม่ส่งคะแนนอัตโนมัติสำหรับนักเรียนคนนี้"
                )
                processed_students.add(candidate_name)
                try:
                    go_back_to_students_table(driver)
                except Exception:
                    pass
                continue

            apply_feedback_and_score_for_current_student(
                driver,
                feedback_text=ai_text,
                score=score,
            )
            processed_students.add(candidate_name)

            # อัปเดต progress หลังตรวจคนนี้เสร็จ
            update_progress(len(processed_students))
            set_current_student(None)

            try:
                go_back_to_students_table(driver)
            except Exception:
                pass

        if not checked_someone_this_round:
            set_status(
                f"[INFO] ✅ ไม่มีนักเรียนใหม่ให้ตรวจในรอบที่ {round_idx} "
                f"(ตรวจไปทั้งหมด {len(processed_students)} คน) หยุด loop แล้ว"
            )
            break

    set_status(f"[INFO] ✅ ตรวจเสร็จแล้วใน assignment นี้ (รวม {len(processed_students)} คน)")


# ================== POPUP เตือนก่อนเริ่ม AUTO ==================


def confirm_start_auto_grading() -> bool:
    """
    เวอร์ชันใหม่: ไม่ต้องให้ user กด OK แล้ว
    ฟังก์ชันนี้จะคืนค่า True ตลอด เพื่อให้ flow เดินต่ออัตโนมัติ
    (ข้อความเตือนใช้ banner สีเหลืองบนหน้าจอแทน)
    """
    return True

# ================== RUN GRADING ON CURRENT ASSIGNMENT ==================


def run_grading_flow_on_current_assignment(driver):
    # เข้า iframe ถ้าเข้าไม่ได้ก็หยุดเลย
    if not switch_to_assignments_iframe(driver):
        return

    # ไม่ต้อง popup ยืนยันแล้ว แค่ขึ้น banner เตือน
    if not confirm_start_auto_grading():
        set_status("[INFO] ผู้ใช้กดยกเลิก ไม่เริ่มตรวจอัตโนมัติ")
        try:
            driver.switch_to.default_content()
        except Exception:
            pass
        return

    # แสดงแถบเตือนสีเหลืองด้านล่าง
    set_status("[INFO] เริ่มตรวจ assignment นี้โดยอัตโนมัติ ...")

    process_all_students_in_current_assignment(driver)

    try:
        driver.switch_to.default_content()
    except Exception:
        pass

    set_status("✅ จบการไล่ตรวจ assignment ปัจจุบันแล้ว (auto)")
    set_phase_status("เสร็จสิ้น: ตรวจงานใน Assignment นี้เรียบร้อยแล้ว 🎉")

    # แสดงข้อความใหญ่ในหน้าต่างสถานะ
    show_finished_message()
    bring_status_to_front()

def is_driver_alive(driver):
    """ เช็คชีพจร Chrome """
    try:
        if not driver: return False
        _ = driver.title # ลองคุยดู ถ้าคุยไม่รู้เรื่องแสดงว่าตายแล้ว
        return True
    except:
        return False

def smart_sleep(driver, seconds):
    """ หลับแบบตื่นตัว: เช็คทุก 0.1 วินาที ถ้าปิด Chrome จะเด้งออกทันที """
    import time
    end_time = time.time() + seconds
    while time.time() < end_time:
        if not is_driver_alive(driver):
            raise Exception("BrowserClosedByUser") 
        time.sleep(0.1)
        tk_yield()

# ✅ 1. เพิ่มฟังก์ชันเช็คสถานะ Chrome ไว้ด้านบน (หรือนอก main)
def is_driver_alive(driver):
    try:
        if not driver: return False
        _ = driver.title  # ลองดึงชื่อ Title ถ้าปิดไปแล้วจะ Error
        return True
    except (WebDriverException, Exception):
        return False

# ✅ 2. ฟังก์ชัน Sleep แบบฉลาด (เช็ค Chrome ทุก 0.5 วิ)
def smart_sleep(driver, seconds):
    import time
    end_time = time.time() + seconds
    while time.time() < end_time:
        if not is_driver_alive(driver):
            raise Exception("BrowserClosedByUser") # ⛔ ถ้าเจอว่าปิด ให้โยน Error ทันที
        time.sleep(0.5)
        tk_yield() # ให้ UI ไม่ค้าง

def force_go_home():
    """ ไม้ตาย: บังคับกลับ Desktop 1 แบบรุนแรง (Aggressive Switch) """
    print("[INFO] 🏠 กำลังบังคับสลับกลับ Desktop 1...")
    user32 = ctypes.windll.user32
    
    # 1. กระตุ้น Focus ด้วยการกดปุ่ม ESC เบาๆ (เพื่อให้หลุดจาก Ghost Window)
    user32.keybd_event(0x1B, 0, 0, 0); user32.keybd_event(0x1B, 0, 2, 0)
    time.sleep(0.05)

    # 2. กด Win + Ctrl ค้างไว้
    user32.keybd_event(0x11, 0, 0, 0) # Ctrl Down
    user32.keybd_event(0x5B, 0, 0, 0) # Win Down
    time.sleep(0.05)
    
    # 3. รัวปุ่มลูกศรซ้าย 5 ครั้ง
    for i in range(5):
        user32.keybd_event(0x25, 0, 0, 0); user32.keybd_event(0x25, 0, 2, 0)
        time.sleep(0.05)
        
    # 4. ปล่อยปุ่ม
    user32.keybd_event(0x5B, 0, 2, 0) # Win Up
    user32.keybd_event(0x11, 0, 2, 0) # Ctrl Up
    
    # ⭐ รอให้ Animation จบจริงๆ (สำคัญที่สุด)
    print("[INFO] ⏳ รอ Windows Animation...")
    time.sleep(1.0)

def auto_click_for_seconds(seconds=5, interval=0.1):
    """
    คลิกเมาส์ซ้ายรัว ๆ เป็นเวลา seconds วินาที
    interval = ระยะห่างระหว่างคลิก (วินาที)
    """
    end_time = time.time() + seconds
    while time.time() < end_time:
        pyautogui.click()
        time.sleep(interval)

def show_loading_screen(root, title_text="Processing", message_text="Please wait, loading data..."):
    """
    สร้างหน้าต่าง Status เต็มจอ
    คืนค่า 3 ตัว: (window, message_label, title_label)
    """
    
    loading_win = ctk.CTkToplevel(root)
    try:
        # วิธีที่ 1: ตั้งค่า iconbitmap โดยตรง (บางครั้งต้องทำซ้ำหลังจาก window load)
        loading_win.iconbitmap(ICON_PATH) 
        
        # วิธีที่ 2 (แบบที่คุณใช้): ใช้ after เพื่อรอให้หน้าต่าง create เสร็จสมบูรณ์
        loading_win.after(200, lambda: loading_win.iconbitmap(ICON_PATH))
    except Exception as e:
        print(f"Warning: Could not set icon: {e}")
    loading_win.title("Status")

    # =========================================================
    # 1. สร้างฟังก์ชันปิดหน้าต่าง (ไว้บนสุดเพื่อกัน Error)
    # =========================================================
    def on_close_click():
        print("[INFO] User clicked X button")
        try: 
            close_created_desktop()  # สั่งลบ Desktop 2
        except: 
            pass
        
        try:
            loading_win.destroy()    # สั่งปิดหน้าต่าง
        except:
            pass

    # ผูกปุ่ม X ทันทีที่สร้างหน้าต่างเสร็จ
    try:
        loading_win.protocol("WM_DELETE_WINDOW", on_close_click)
    except Exception as e:
        print(f"Warning: Could not bind close event: {e}")

    # พยายามโหลด Icon
    try: loading_win.after(200, lambda: loading_win.wm_iconbitmap(ICON_PATH))
    except: pass

    # ตั้งค่าหน้าต่าง
    loading_win.state("zoomed")
    loading_win.resizable(True, True)
    loading_win.attributes('-topmost', True) # อยู่บนสุดเสมอ
    loading_win.grab_set() 
    loading_win.configure(fg_color=TEAMS_MAIN_BG)

    # =========================================================
    # 2. สร้าง Frame กลางจอ (outer) **ต้องสร้างก่อน Label**
    # =========================================================
    card_width = 1000
    card_height = 750

    outer = ctk.CTkFrame(
        loading_win,
        width=card_width,
        height=card_height,
        fg_color=TEAMS_CARD_BG,
        corner_radius=20,
        border_color=TEAMS_BORDER,
        border_width=2,
    )
    outer.place(relx=0.5, rely=0.5, anchor="center")
    outer.pack_propagate(False)

    # =========================================================
    # 3. สร้าง Label และ Content (ใช้ outer เป็นพ่อ)
    # =========================================================
    
    # ⭐ Label หัวข้อ (Title) -> เก็บลงตัวแปรเพื่อ return
    label_title = ctk.CTkLabel(
        outer,
        text=title_text,
        font=ctk.CTkFont("Segoe UI", size=40, weight="bold"),
        text_color=TEAMS_PRIMARY,
    )
    label_title.pack(pady=(150, 20))

    # ⭐ Label รายละเอียด (Message) -> เก็บลงตัวแปรเพื่อ return
    label_msg = ctk.CTkLabel(
        outer,
        text=message_text,
        font=ctk.CTkFont("Segoe UI", size=24),
        text_color=TEAMS_TEXT_MAIN,
    )
    label_msg.pack(pady=(0, 40))

    # Progress Bar
    progress = ctk.CTkProgressBar(
        outer,
        width=600,
        height=20,
        corner_radius=10,
        progress_color=TEAMS_PRIMARY,
        mode="determinate" 
    )
    progress.pack(pady=20)
    progress.set(0)

    # ปุ่ม Cancel
    btn_cancel = ctk.CTkButton(
        outer,
        text="Cancel",
        font=ctk.CTkFont("Segoe UI", size=18, weight="bold"),
        fg_color="#5d5bd4",
        hover_color="#5d5bd4",
        height=40,
        width=200,
        command=on_close_click # ใช้ฟังก์ชันตัวบนได้เลย
    )
    btn_cancel.pack(pady=(40, 20))

    # Animation Loop
    def animate_progress():
        try:
            if not loading_win.winfo_exists(): return
        except: return

        current_val = progress.get()
        if current_val < 0.6: increment = 0.005
        elif current_val < 0.85: increment = 0.002
        elif current_val < 0.95: increment = 0.0005
        else: increment = 0

        new_val = current_val + increment
        progress.set(new_val)
        loading_win.after(20, animate_progress)

    # เริ่ม Animation
    animate_progress()
    loading_win.update()

    # ⭐ Return 3 ค่าตามที่ main ต้องการ
    return loading_win, label_msg, label_title
# ================== MAIN ==================


def main():
    global status_win, root
    closed_by_user = False

    init_root_if_needed()

    # ตัวแปรสำหรับจัดการหน้า Loading
    loading_win = None
    loading_msg = None
    loading_title_label = None

    switch_keyboard_to_english()     # ⭐เปลี่ยนเป็น English ก่อน
    time.sleep(1)
    # ⭐ --------- สร้าง Desktop 2 ก่อนเริ่มทำงาน ---------
    create_and_switch_to_desktop2()
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # ⭐ ใช้ try/finally เพื่อให้ cleanup ทำงานทุกกรณี
    driver = None
    try:
        # ---------- STEP 0: Login ----------
        email, password = login_window()
        if email is None or password is None or email == "":
            print("⛔ ยกเลิก: ไม่ได้กรอก email หรือ password")
            return
        
        loading_win, loading_msg, loading_title = show_loading_screen(root, "System Starting", "Initializing Chrome Driver...")
               
        
        # ✅ แก้ไขจุดที่ 1: สั่งให้หน้าต่าง Loading ลอยอยู่เหนือทุกโปรแกรมเสมอ
        if loading_win:
            loading_win.attributes('-topmost', True) 
            loading_win.update()

        # ⭐ [แก้ไข] ฟังก์ชันช่วยอัปเดตทั้ง Title และ Message
        def set_loading_state(new_title=None, new_msg=None):
            if loading_win and loading_win.winfo_exists():
                if new_title and loading_title:
                    loading_title.configure(text=new_title)
                if new_msg and loading_msg:
                    loading_msg.configure(text=new_msg)
                loading_win.update()

        # ---------- STEP 1: เปิด Chrome / เข้า Teams ----------
        set_phase_status("ขั้นตอนที่ 1: กำลังเปิด Chrome และเข้า Microsoft Teams...")
        set_loading_state(new_msg="Opening Chrome Browser...")
        set_status("[INFO] เริ่มเปิดเบราว์เซอร์และเข้า Teams...")
        set_status("[INFO] กำลังเตรียม ChromeDriver (ครั้งแรกอาจใช้เวลา 10–30 วินาที)...")
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        prefs = {
            "download.default_directory": DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        try:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )

            # ✅ แก้ไขจุดที่ 2: ดึงหน้า Loading กลับมาอยู่ข้างหน้าสุดอีกครั้ง
            # (เผื่อ Chrome แย่งซีนไป ให้เราแย่งคืนมาทันที)
            if loading_win:
                loading_win.lift()  
                loading_win.attributes('-topmost', True)
                loading_win.update()
            
            # 🔥 Check 1: เช็คทันทีหลังเปิด (เผื่อเปิดแล้วเด้งดับ)
            if not is_driver_alive(driver): 
                raise Exception("BrowserClosedByUser")

            set_status("[INFO] ✅ เปิด Chrome เรียบร้อย กำลังไปที่หน้า Teams...")
            set_loading_state(new_msg="Navigate to Microsoft Teams...")  # ⭐ อัปเดตข้อความ
        except Exception as e:
            # ถ้า Error เพราะ User ปิด ให้โยน Error ต่อไปเลย เพื่อไปลบ Desktop
            if "BrowserClosedByUser" in str(e): 
                return
            
            set_status(f"[ERROR] เปิด Chrome ไม่สำเร็จ: {e}")
            messagebox.showerror(
                "เปิด Chrome ไม่ได้",
                f"ไม่สามารถเปิด Chrome/WebDriver ได้:\n{e}"
            )
            return

        bring_status_to_front()

        # 🔥 หุ้ม block การทำงานด้วย try เพื่อดักจับ Browser ปิด
        try:
            # 🔥 Check 2: ก่อนสั่งไป URL
            if not is_driver_alive(driver): raise Exception("BrowserClosedByUser")

            driver.get("https://teams.microsoft.com")
            set_loading_state(new_msg="Logging in...")
            set_status("[INFO] เปิดหน้า https://teams.microsoft.com แล้ว กำลังเตรียมหน้า Login ...")
            
            # 🔥 Check 3: ใช้ smart_sleep แทน time.sleep
            smart_sleep(driver, 3) 
            
            tk_yield()

            # 🔥 Check 4: ก่อน Login
            if not is_driver_alive(driver): raise Exception("BrowserClosedByUser")

            login_to_microsoft(driver, email, password)
            set_loading_state(new_msg="Waiting for Teams Dashboard...")
            set_status("[INFO] รอโหลด UI ของ Teams...")

            # -----------------------------------------------------------
            # 🔥 Check 5: เปลี่ยนการรอ wait_for_teams_page เป็น Loop ที่ฉลาดขึ้น
            # เพื่อให้ตรวจจับได้ว่า "User กดปิด Chrome ระหว่างรอหน้าเว็บโหลดหรือไม่"
            # -----------------------------------------------------------
            found_teams = False
            is_login_failed = False
            start_wait = time.time()
            timeout = 180 # รอ 60 วินาที
            
            while time.time() - start_wait < timeout:
                # 1. เช็คว่า Chrome ยังอยู่ไหม (ถ้าไม่อยู่ -> Error -> ไปลบ Desktop)
                if not is_driver_alive(driver):
                    raise Exception("BrowserClosedByUser")
                
                # 2. ลองเช็คว่าเจอหน้า Teams หรือยัง
                # (คุณอาจต้องปรับแก้เงื่อนไขนี้ตามฟังก์ชัน wait_for_teams_page เดิมของคุณ)
                try:
                    # ตัวอย่าง: เช็ค title หรือ element
                    if "Microsoft Teams" in driver.title or \
                       len(driver.find_elements(By.CSS_SELECTOR, "div.team-card, app-team-card")) > 0:
                        found_teams = True
                        break

                    # ⭐ 3. เพิ่มการตรวจจับ Login ล้มเหลว: 
                    # ถ้าเจอ element ของหน้า Login (เช่น ช่องกรอกอีเมล) 
                    # แสดงว่ารหัสผิดและถูกนำกลับมาหน้าเดิม
                    # (คุณอาจต้องปรับ CSS_SELECTOR ให้ตรงกับหน้า Login จริงของ Microsoft)
                    if len(driver.find_elements(By.CSS_SELECTOR, 'input[type="email"]')) > 0 or \
                       "Sign in" in driver.title:
                        
                        # ให้เวลาอีกนิดหน่อย เผื่อกำลังโหลด
                        if time.time() - start_wait > 15: # ⭐ ให้เวลาอย่างน้อย 15 วินาทีในการโหลด
                            is_login_failed = True
                            break # ออกจาก loop ทันทีเมื่อ Login ล้มเหลว

                except:
                    pass

                time.sleep(1)
                tk_yield()

            # -----------------------------------------------------------
            # ⭐ เพิ่มเงื่อนไขการแจ้งเตือนและการกลับไปหน้า Login
            # -----------------------------------------------------------
            if is_login_failed:
                set_status("⛔ Login ล้มเหลว: Username หรือ Password ไม่ถูกต้อง")
                
                # ปิดหน้า Loading ก่อน
                if loading_win:
                    loading_win.destroy()
                    loading_win = None
                
                # แจ้งเตือนผู้ใช้
                messagebox.showerror(
                    "Login ล้มเหลว", 
                    "Username หรือ Password ไม่ถูกต้อง\nโปรดลองใหม่อีกครั้ง"
                )
                
                # ต้องปิด Driver ตรงนี้ เพื่อให้โปรแกรม `return` และไป `finally` 
                # แล้วเริ่ม `main()` ใหม่ (หากคุณทำซ้ำ) หรือจบการทำงาน
                if driver:
                    driver.quit() 
                    driver = None # ตั้งเป็น None เพื่อให้ finally ไม่พยายามปิดซ้ำ
                
                # ไม่ต้องไปต่อ ให้ return ทันที (ซึ่งจะจบ `try` และไป `finally`)
                return

            if not found_teams:
                # เช็คครั้งสุดท้ายเผื่อปิดตอนวินาทีท้ายๆ
                if not is_driver_alive(driver): raise Exception("BrowserClosedByUser")
                
                set_status("⛔ ไม่สามารถตรวจพบการ์ด Team/Class ภายในเวลา 60 วิ")
                messagebox.showerror("เกิดข้อผิดพลาด", "ไม่เจอการ์ด Team/Class ในเวลา 60 วิ")
                return

        except Exception as e:
            # ดักจับถ้าเป็นเคสปิด Browser
            if "BrowserClosedByUser" in str(e) or not is_driver_alive(driver):
                print("[INFO] ผู้ใช้ปิด Browser หรือยกเลิกการทำงาน")
                closed_by_user = True      # ✅บันทึกว่า user ปิดเอง
                return
            else:
                raise e

        print("\n==============================")
        print("✅ Login ผ่าน และหน้า Teams โหลดเสร็จ")
        print("==============================\n")

        # ---------- STEP 2: เลือก Classroom ----------
        set_phase_status("ขั้นตอนที่ 2: ระบบกำลังตรวจจับ classes ทั้งหมดใน Team โปรดรอสักครู่...")
        set_status("[INFO] กำลังรอให้หน้า Teams Dashboard โหลดการ์ดห้องเรียน (8 วินาที)...")
        set_loading_state(new_msg="Scanning for Classrooms...")
        classroom_names = get_classrooms_from_page(driver)
        # ⭐ [สำคัญ] ปิดหน้า Loading ตรงนี้ ก่อนจะแสดงหน้าเลือก Class
        #if loading_win:
            #loading_win.destroy()
            #loading_win = None
        selected_name = choose_classroom_window(classroom_names)
        
        if not selected_name:
            set_status("⛔ ยกเลิก: ไม่ได้เลือก Classroom / Team")
            return

        set_status(f"[INFO] คุณเลือก: {selected_name!r}")
        set_phase_status(f"กำลังเข้า Classroom / Team: {selected_name}")
        ok = open_classroom(driver, selected_name)

        # ---------- STEP 3: เข้า Assignments → Ready to grade ----------
        if not ok:
            set_status("⚠ เปิด Classroom / Team ไม่สำเร็จ ลองตรวจ DOM")
        else:
            print("\n✅ เปิด Classroom แล้ว → ไปหน้า Assignments → Ready to grade ...\n")
            set_status("[INFO] เข้า class แล้ว กำลังไป Assignments ...")
            set_phase_status("ขั้นตอนที่ 3: เข้าเมนู Assignments...")

            # ⭐ 1. เปิดหน้า Loading Screen
            set_loading_state(new_title="Accessing Assignments", new_msg="Navigating to Assignments tab...")

            if not open_assignments_in_class(driver, down_times=1):
                set_status("[WARN] เข้าเมนู Assignments ในคลาสไม่สำเร็จ")
            else:
                set_loading_state(new_msg="Switching to 'Ready to grade'...")

                if not click_ready_to_grade_tab(driver):
                    set_status("[WARN] คลิกแท็บ Ready to grade ไม่สำเร็จ")
                else:
                    set_status("[INFO] ตอนนี้อยู่หน้า Ready to grade แล้ว")
                    set_phase_status("ขั้นตอนที่ 3: เลือก Assignment ที่ต้องการตรวจ")
                    set_loading_state(new_msg="Scanning for assignments...")

                    #if loading_win:
                        #loading_win.destroy()
                        #loading_win = None
                    # ⭐ ชื่อ assignment ที่เลือก ได้ตรงจาก popup
                    assignment_title = choose_assignment_in_ready_to_grade(driver)
                    
                    if not assignment_title:
                        set_status("[INFO] ยกเลิกหรือเลือก assignment ไม่สำเร็จ")
                    else:
                        # ⭐ ตอนนี้แหละที่ปิดหน้า Loading ได้แล้ว เพราะเลือกงานเสร็จแล้ว
                        set_loading_state(new_msg="Initializing auto-grading process...")

                        time.sleep(1.0) 

                        if loading_win:
                            loading_win.destroy()
                            loading_win = None

                        switch_back_to_desktop1()
                        status_win, _ = create_status_window(selected_name, assignment_title)
                        bring_status_to_front()
                        tk_yield()

                        # ---------- STEP 4: ตรวจงานอัตโนมัติ ----------
                        set_phase_status("ขั้นตอนที่ 4: กำลังตรวจงานของนักศึกษาอัตโนมัติ...")
                        run_grading_flow_on_current_assignment(driver)

        # ---------- รายงานผล ----------
        set_status("👋 งานตรวจเสร็จแล้ว คุณสามารถปิดหน้าต่างนี้ได้เมื่อดู log เสร็จ")
        set_phase_status("เสร็จสิ้นแล้ว: ระบบหยุดตรวจงาน")

    finally:
        # ⭐⭐⭐ CLEANUP (ทำงานเสมอ และเรียงลำดับความสำคัญ) ⭐⭐⭐
        print("\n🧹 เริ่ม Cleanup...")

        # 1. ปิด Driver ก่อนเลย (เพื่อคืน Focus ให้ Windows Desktop เต็มที่)
        try:
            if driver: 
                print("[INFO] กำลังปิด Chrome Driver...")
                driver.quit()
                
        except: pass
        
        time.sleep(2) # รอแป๊บนึงให้หน้าต่าง Chrome หายไปจริงๆ

        try:
            close_created_desktop()
        except Exception as e:
            print(f"⚠️ ลบ Desktop 2 ไม่สำเร็จ: {e}")

        # 2. สั่งลบ Desktop 2 ทันที (ต้องทำตอนที่ยังอยู่ Desktop 2)
        # Windows จะเด้งกลับไป Desktop 1 ให้อัตโนมัติเมื่อ Desktop 2 ถูกปิด

        # 3. ถีบตัวกลับ Desktop 1 (เผื่อว่าข้อ 2 พลาด หรือเราเผลออยู่ Desktop 1 อยู่แล้ว)
        try: 
            force_go_home()
            switch_back_to_desktop1()
        except: pass     

        # 4. ลบไฟล์ขยะ
        try:
            if os.path.exists(DOWNLOAD_DIR):
                shutil.rmtree(DOWNLOAD_DIR, ignore_errors=True)
        except: pass

        # -----------------------------------------------------------
        # ⚠️ จุดสังเกตเรื่องลำดับการทำงาน (เตือนเพื่อความชัวร์)
        # ถ้าฟังก์ชัน close_created_desktop() ของคุณใช้ปุ่ม Win+Ctrl+F4
        # คุณต้องสั่ง "ลบ Desktop 2" (ข้อ 2) **ก่อน** "กลับบ้าน" (ข้อ 1) นะครับ
        # ไม่อย่างนั้นถ้าตัวกลับไป Desktop 1 แล้ว จะกดลบ Desktop 2 ไม่ได้ครับ
        # -----------------------------------------------------------

        # 🟢 แนะนำลำดับ: สั่งลบ Desktop 2 เลย (เดี๋ยว Windows ดีดกลับ Desktop 1 ให้เอง)
        try:
            close_created_desktop() 
            print("[INFO] สั่งปิด Desktop 2 แล้ว (กำลังย้ายกลับ Desktop 1 อัตโนมัติ)")
        except Exception as e:
            print(f"[WARN] ลบ Desktop 2 ไม่สำเร็จ: {e}")
            # ถ้าลบไม่สำเร็จจริงๆ ค่อยบังคับกลับบ้าน

        # 3. ลบไฟล์ Download
        try:
            if os.path.exists(DOWNLOAD_DIR):
                shutil.rmtree(DOWNLOAD_DIR, ignore_errors=True)
        except:
            pass

        # 4. ปิด Driver (ไว้หลังสุด เพื่อให้แน่ใจว่า Chrome หายไปจริงๆ)
        try:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        except:
            pass

def check_license_or_exit() -> bool:
    """
    ลองใช้ license key ที่เคยบันทึกไว้ก่อน
    ถ้าไม่มีก็ถามผู้ใช้
    ถ้าตรวจไม่ผ่าน → แจ้งเตือนและคืน False (ให้โปรแกรมปิดตัวเอง)
    """
    # 1) ลองใช้ key ที่เคยเซฟ
    saved = load_saved_license_key()
    if saved:
        if check_license(saved):
            set_status("[LICENSE] ใช้ license key เดิมและตรวจสอบผ่าน")
            return True
        else:
            set_status("[LICENSE] license เดิมไม่ผ่าน จะขอให้ผู้ใช้ใส่ใหม่")

    # 2) ขอให้ผู้ใช้ใส่ใหม่ (ให้โอกาส 2 ครั้ง)
    for _ in range(2):
        key = ask_license_key_window()
        if not key:
            # ผู้ใช้กด Exit / ปิดหน้าต่าง
            messagebox.showwarning(
                "License required",
                "This application requires a valid license key to run.",
            )
            return False

        if check_license(key):
            save_license_key(key)
            set_status("[LICENSE] ตรวจสอบ license ใหม่ผ่าน และบันทึกไว้แล้ว")
            return True

    messagebox.showerror(
        "License invalid",
        "The license key is not valid. The application will close.",
    )
    return False


if __name__ == "__main__":
    # ✅ ตรวจ license ก่อน
    if not check_license_or_exit():
        sys.exit(0)

    # ✅ เริ่มโปรแกรมหลัก
    main()

