import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, time
from fpdf import FPDF

# --- CONFIG HALAMAN ---
st.set_page_config(page_title="E-Admin MUA - Elisabeth", layout="centered")

# --- STYLE CSS PINK ELIS ---
st.markdown("""
    <style>
    .stApp { background-color: #F8C8DC; }
    div.stButton > button {
        background-color: #F19CBB; color: white;
        border-radius: 10px; font-weight: bold; width: 100%;
    }
    .job-card { 
        background-color: white; padding: 15px; border-radius: 10px; 
        margin-bottom: 10px; border-left: 8px solid #F19CBB; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEM DATABASE ---
DATA_FILE = "mua_master_pro.json"

def load_data():
    defaults = {
        "profile": {"nama": "Elisabeth MUA", "alamat": "", "hp": "", "ig": ""},
        "faktur_settings": {"tnc": "", "bank": "", "no_rek": "", "an": "", "signature": "", "salam": "", "next_inv": 1},
        "master_layanan": {}, "bookings": [], "pengeluaran": []
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                for key in defaults:
                    if key not in data: data[key] = defaults[key]
                return data
        except: return defaults
    return defaults

if 'db' not in st.session_state:
    st.session_state.db = load_data()

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.db, f, indent=4)

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("💄 E-Admin Login")
    email = st.text_input("Email", value="elisabethmua18@gmail.com")
    pw = st.text_input("Password", type="password")
    if st.button("MASUK"):
        if email == "elisabethmua18@gmail.com" and pw == "Elis5173":
            st.session_state.auth = True
            st.rerun()
        else: st.error("Email atau Password salah!")
    st.stop()

# --- MENU UTAMA ---
menu = st.sidebar.radio("MENU", ["BERANDA", "INPUT JADWAL", "LAYANAN", "PROFIL & SETTING", "KEUANGAN"])

# --- SESSION STATE UNTUK DINAMIS INPUT ---
if 'n_paket' not in st.session_state: st.session_state.n_paket = 1
if 'n_manual' not in st.session_state: st.session_state.n_manual = 0

# --- 1. BERANDA ---
if menu == "BERANDA":
    st.header("🌸 Jadwal Elisabeth MUA")
    st.write("Daftar jadwal akan muncul di sini setelah diinput.")

# --- 2. INPUT JADWAL (REVISI LENGKAP) ---
elif menu == "INPUT JADWAL":
    st.header("📝 Tambah Jadwal Baru")
    
    with st.form("form_jadwal"):
        nama_klien = st.text_input("1. Nama Klien")
        tgl_makeup = st.date_input("2. Tanggal Makeup", datetime.now()) # Popup Kalender
        wa_klien = st.text_input("3. Nomor WhatsApp")
        alamat_makeup = st.text_area("4. Alamat Makeup")
        
        # Pilihan Timeline Jam (00.00, 00.15, dst)
        times = [time(h, m).strftime("%H:%M") for h in range(24) for m in (0, 15, 30, 45)]
        c1, c2, c3 = st.columns(3)
        jam_mulai = c1.selectbox("5. Jam Mulai", times, index=32) # Default 08:00
        jam_selesai = c2.selectbox("6. Jam Selesai", times, index=40) # Default 10:00
        jam_otw = c3.selectbox("7. Jam OTW", times, index=28) # Default 07:00
        
        durasi_otw = st.number_input("8. Durasi OTW (Menit) - Ketik Manual", min_value=0, value=30)
        
        st.write("---")
        st.write("**9. Pilihan Paket**")
        paket_terpilih = []
        master_list = list(st.session_state.db['master_layanan'].keys()) if st.session_state.db['master_layanan'] else ["Belum ada paket"]
        
        # Input Paket Dinamis
        for i in range(st.session_state.n_paket):
            cp1, cp2 = st.columns([3, 1])
            p_nama = cp1.selectbox(f"Pilih Paket {i+1}", master_list, key=f"p_nama_{i}")
            p_qty = cp2.number_input(f"Qty {i+1}", min_value=1, key=f"p_qty_{i}")
            if p_nama != "Belum ada paket":
                paket_terpilih.append({"nama": p_nama, "qty": p_qty, "price": st.session_state.db['master_layanan'].get(p_nama, 0)})
        
        if st.form_submit_button("➕ Tambah Baris Paket"):
            st.session_state.n_paket += 1
            st.rerun()

        st.write("---")
        st.write("**10. Layanan Tambahan Manual**")
        manual_terpilih = []
        for j in range(st.session_state.n_manual):
            cm1, cm2, cm3 = st.columns([2, 1, 1])
            m_ket = cm1.text_input(f"Keterangan {j+1}", key=f"m_ket_{j}")
            m_hrg = cm2.number_input(f"Harga {j+1}", min_value=0, key=f"m_hrg_{j}")
            m_qty = cm3.number_input(f"Qty {j+1}", min_value=1, key=f"m_qty_{j}")
            if m_ket:
                manual_terpilih.append
