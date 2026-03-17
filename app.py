import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, time, date
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
        background-color: white; padding: 20px; border-radius: 15px; 
        margin-bottom: 10px; border-left: 10px solid #F19CBB; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .otw-info {
        color: #777; font-style: italic; font-size: 0.9em; margin: 10px 0;
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

# --- FUNGSI DOWNLOAD PDF ---
def create_pdf(booking):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"INVOICE {booking['inv_no']}", ln=True, align='C')
    pdf.set_font("Arial", "", 12)
    pdf.ln(10)
    pdf.cell(0, 10, f"Klien: {booking['nama']}", ln=True)
    pdf.cell(0, 10, f"Tanggal: {booking['tgl']}", ln=True)
    pdf.cell(0, 10, f"Lokasi: {booking['alamat_mu']}", ln=True)
    pdf.cell(0, 10, f"Total DP: Rp {booking['dp']:,}", ln=True)
    pdf.ln(10)
    pdf.cell(0, 10, "Terima kasih telah menggunakan jasa Elisabeth MUA", ln=True, align='C')
    return pdf.output(dest='S')

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

# --- MENU ---
menu = st.sidebar.radio("MENU", ["BERANDA", "INPUT JADWAL", "LAYANAN", "PROFIL & SETTING", "KEUANGAN"])

if 'input_pakets' not in st.session_state: st.session_state.input_pakets = []
if 'input_manuals' not in st.session_state: st.session_state.input_manuals = []

# --- 1. BERANDA (REVISI SESUAI PERMINTAAN) ---
if menu == "BERANDA":
    st.header("🌸 Jadwal Elisabeth MUA")
    
    # Navigasi Kalender (Tanpa tulisan Biru=Ada Job)
    selected_date = st.date_input("Pilih Tanggal", value=date.today(), key="calendar_input")
    
    st.divider()
    
    # Filter & Sortir Jadwal
    selected_str = selected_date.strftime("%d/%m/%Y")
    todays_jobs = [b for b in st.session_state.db['bookings'] if b['tgl'] == selected_str]
    todays_jobs = sorted(todays_jobs, key=lambda x: x['jam_ready'].split('-')[0])
    
    if not todays_jobs:
        st.info(f"Tidak ada jadwal untuk tanggal {selected_str}")
    else:
        for i, b in enumerate(todays_jobs):
            with st.container():
                st.markdown(f'<p class="otw-info">🚗 Jam OTW: {b["jam_otw"]} (Durasi: {b["durasi_otw"]} menit)</p>', unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="job-card">
                    <h3 style="margin:0; color:#F19CBB;">{b['nama']} - {b['inv_no']}</h3>
                    <p style="margin:5px 0;"><b>Jam Kerja:</b> {b['jam_ready']}</p>
                    <p style="margin:5px 0;"><b>Lokasi:</b> {b['alamat_mu']}</p>
