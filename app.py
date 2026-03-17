import streamlit as st
import json
import os
import pandas as pd
# [Image of a cloud-based business management dashboard for beauty professionals]
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
    .faktur-card { background-color: white; padding: 20px; border-radius: 10px; color: black; border: 1px solid #ddd; }
    .job-card { 
        background-color: white; padding: 15px; border-radius: 10px; 
        margin-bottom: 10px; border-left: 8px solid #F19CBB; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEM DATABASE AMAN ---
DATA_FILE = "mua_master_pro.json"

def load_data():
    defaults = {
        "profile": {"nama": "Elisabeth MUA", "alamat": "", "hp": "", "ig": ""},
        "faktur_settings": {"tnc": "", "bank": "", "no_rek": "", "an": "", "signature": "", "thanks": "", "salam": "", "next_inv": 1},
        "master_layanan": {}, "bookings": [], "pengeluaran": []
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                for key, val in defaults.items():
                    if key not in data: data[key] = val
                return data
        except: return defaults
    return defaults

if 'db' not in st.session_state:
    st.session_state.db = load_data()

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.db, f, indent=4)

# --- FUNGSI PDF ---
def generate_pdf(k):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, st.session_state.db['profile'].get('nama', ''), ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"{st.session_state.db['profile'].get('alamat', '')}", ln=True, align='C')
    pdf.cell(0, 5, f"WA: {st.session_state.db['profile'].get('hp', '')} | IG: {st.session_state.db['profile'].get('ig', '')}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"INVOICE #{k.get('inv_no','')}", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Nama Klien: {k.get('nama','')}", ln=True)
    pdf.cell(0, 6, f"Tanggal: {k.get('tgl','')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, "RINCIAN LAYANAN:", ln=True, border='B')
    pdf.set_font("Arial", "", 10)
    total = 0
    for p in k.get('paket_list', []):
        sub = p['price'] * p.get('qty', 1)
        pdf.cell(0, 7, f"- {p['nama']} ({p.get('qty', 1)} person): Rp {sub:,}", ln=True)
        total += sub
    for m in k.get('manual_list', []):
        sub_m = m['harga'] * m.get('qty', 1)
        pdf.cell(0, 7, f"- {m['nama']} (x{m.get('qty', 1)}): Rp {sub_m:,}", ln=True)
        total += sub_m
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, f"TOTAL TAGIHAN: Rp {total:,}", ln=True)
    pdf.cell(0, 8, f"DP / SUDAH DIBAYAR: Rp {k.get('dp', 0):,}", ln=True)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 8, f"SISA SALDO: Rp {total - k.get('dp', 0):,}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, f"Pembayaran: {st.session_state.db['faktur_settings'].get('bank','')} {st.session_state.db['faktur_settings'].get('no_rek','')} a/n {st.session_state.db['faktur_settings'].get('an','')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, f"S&K: {st.session_state.db['faktur_settings'].get('tnc','')}")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 10, st.session_state.db['faktur_settings'].get('salam', 'Terima Kasih!'), ln=True, align='C')
    return pdf.output()

# --- LOGIN (REVISI EMAIL) ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("💄 E-Admin Login")
    email = st.text_input("Email", value="elisabethmua18@gmail.com")
    pw = st.text_input("Password", type="password")
    if st.button("MASUK"):
        if email == "elisabethmua18@gmail.com" and pw == "Elis5173":
            st.session_state.auth = True; st.rerun()
        else: st.error("Akses Ditolak!")
    st.stop()

# --- MENU ---
menu = st.sidebar.radio("MENU", ["BERANDA", "INPUT JADWAL", "LAYANAN", "PROFIL & SETTING", "KEUANGAN"])

# --- 1. BERANDA ---
if
