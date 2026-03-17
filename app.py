import streamlit as st
import json
import os
import pandas as pd
import base64
from datetime import datetime, time, date

st.set_page_config(page_title="E-Admin MUA - Elisabeth", layout="centered")

st.markdown("""
<style>
.stApp { background-color: #F8C8DC; }
div.stButton > button {
    background-color: #F19CBB; color: white;
    border-radius: 10px; font-weight: bold; width: 100%;
}
.job-card {  
    background-color: white; padding: 20px; border-radius: 15px;  
    margin-bottom: 5px; border-left: 10px solid #F19CBB;
}
.faktur-box {
    background-color: white; padding: 30px; border-radius: 10px;
}
.stempel-lunas {
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%) rotate(-20deg);
    border: 5px solid red; color: red;
    font-size: 40px; font-weight: bold;
    padding: 10px 20px; opacity: 0.4;
}
</style>
""", unsafe_allow_html=True)

DATA_FILE = "mua_master_pro.json"

def load_data():
    return {
        "profile": {"nama": "Elisabeth MUA"},
        "faktur_settings": {"next_inv": 1},
        "master_layanan": {},
        "bookings": [],
        "pengeluaran": []
    }

if 'db' not in st.session_state:
    st.session_state.db = load_data()

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.db, f)

# LOGIN (TIDAK DIUBAH)
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("💄 Login")
    if st.button("MASUK"):
        st.session_state.auth = True
        st.rerun()
    st.stop()

menu = st.sidebar.radio("MENU", ["BERANDA"])

# ===============================
# BERANDA + FAKTUR FIX
# ===============================
if menu == "BERANDA":

    st.header("Jadwal")

    # DATA CONTOH
    if not st.session_state.db['bookings']:
        st.session_state.db['bookings'] = [{
            "inv_no": "INV001",
            "nama": "Client A",
            "tgl": "17/03/2026",
            "paket_list": [{"nama": "Makeup", "qty": 1, "price": 500000}],
            "manual_list": [],
            "dp": 100000,
            "status": "PENDING"
        }]

    for i, b in enumerate(st.session_state.db['bookings']):
        st.write(b['nama'])

        if st.button("FAKTUR", key=i):
            st.session_state.current_faktur = b

    # =========================
    # 🔥 FAKTUR FIX TOTAL
    # =========================
    if 'current_faktur' in st.session_state:

        f = st.session_state.current_faktur

        # 🔥 AMAN (TIDAK AKAN ERROR)
        paket_list = f.get('paket_list') or []
        manual_list = f.get('manual_list') or []

        total_p = 0
        for item in paket_list:
            total_p += item.get('price', 0) * item.get('qty', 1)

        total_m = 0
        for item in manual_list:
            total_m += item.get('harga', 0) * item.get('qty', 1)

        total = total_p + total_m
        dp = f.get('dp', 0) or 0
        sisa = total - dp

        st.markdown(f"""
        <div class="faktur-box">
        <h3>INVOICE {f.get('inv_no')}</h3>
        <p>Nama: {f.get('nama')}</p>

        <hr>

        <b>Rincian:</b>
        """, unsafe_allow_html=True)

        # PAKET
        for item in paket_list:
            st.write(f"{item.get('nama')} x{item.get('qty')} = Rp {item.get('price') * item.get('qty'):,}")

        # MANUAL
        for item in manual_list:
            st.write(f"{item.get('nama')} x{item.get('qty')} = Rp {item.get('harga') * item.get('qty'):,}")

        st.markdown(f"""
        <hr>
        <b>Total:</b> Rp {total:,}<br>
        <b>DP:</b> Rp {dp:,}<br>
        <b>Sisa:</b> Rp {0 if f.get('status') == 'SELESAI (LUNAS)' else sisa:,}
        </div>
        """, unsafe_allow_html=True)

        if st.button("Tutup"):
            del st.session_state.current_faktur
            st.rerun()
