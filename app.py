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
    margin-bottom: 5px; border-left: 10px solid #F19CBB; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
}
.faktur-box {
    background-color: white; padding: 30px; border: 1px solid #eee; border-radius: 10px;
    color: black; line-height: 1.5; font-family: 'Arial', sans-serif; position: relative;
}
.stempel-lunas {
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-20deg);
    border: 5px solid red; color: red; font-size: 40px; font-weight: bold;
    padding: 10px 20px; border-radius: 10px; opacity: 0.4; pointer-events: none;
}
.otw-info {
    color: #777; font-style: italic; font-size: 0.9em; margin: 5px 0 20px 10px;
}
</style>
""", unsafe_allow_html=True)

DATA_FILE = "mua_master_pro.json"

def load_data():
    initial_bookings = [
        {"inv_no": "INV0005", "nama": "Kak Angel", "tgl": "17/03/2026", "wa": "08xxxx", "alamat_mu": "Tembalang", "jam_ready": "14:00-16:00", "jam_otw": "16:15", "durasi_otw": 15, "paket_list": [], "manual_list": [], "hire_tim": True, "tim_type": "Hairdo", "tim_nama": "Selly", "dp": 0, "status": "PENDING"},
        {"inv_no": "INV0006", "nama": "Kak Reyki", "tgl": "17/03/2026", "wa": "08xxxx", "alamat_mu": "Hotel Aruman", "jam_ready": "13:00-15:00", "jam_otw": "12:15", "durasi_otw": 30, "paket_list": [], "manual_list": [], "hire_tim": True, "tim_type": "Hairdo", "tim_nama": "Ovie", "dp": 0, "status": "PENDING"}
    ]
    defaults = {
        "profile": {"nama": "Elisabeth MUA", "alamat": "", "hp": "", "ig": "", "bank": "", "no_rek": "", "an": ""},
        "faktur_settings": {"tnc": "", "signature": "", "salam": "", "next_inv": 7},
        "master_layanan": {}, "bookings": initial_bookings, "pengeluaran": []
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

menu = st.sidebar.radio("MENU", ["BERANDA", "INPUT JADWAL", "LAYANAN", "PROFIL & SETTING", "KEUANGAN"])

if menu == "BERANDA":
    st.header("🌸 Jadwal Elisabeth MUA")
    selected_date = st.date_input("Pilih Tanggal", value=date(2026, 3, 17))
    st.divider()
    
    selected_str = selected_date.strftime("%d/%m/%Y")
    list_job = [b for b in st.session_state.db['bookings'] if b['tgl'] == selected_str]
    list_job = sorted(list_job, key=lambda x: x.get('jam_ready', '00:00').split('-')[0])
    
    if not list_job:
        st.info(f"Tidak ada jadwal.")
    else:
        for i, b in enumerate(list_job):
            with st.container():
                st.markdown(f"""
                <div class="job-card">
                    <h3 style="margin:0; color:#F19CBB;">{b['nama']} - {b['inv_no']}</h3>
                    <p style="margin:5px 0;"><b>Jam Kerja:</b> {b['jam_ready']} | <b>Lokasi:</b> {b['alamat_mu']}</p>
                    <p style="margin:5px 0;"><b>Tim:</b> {b['tim_type']} ({b['tim_nama']})</p>
                    <p style="margin:5px 0;"><b>Status:</b> {b.get('status','PENDING')}</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f'<p class="otw-info">🚗 Jam OTW: {b["jam_otw"]} ({b["durasi_otw"]}m)</p>', unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                if c2.button("✅ SELESAI", key=f"dn_{i}"):
                    b['status'] = "SELESAI (LUNAS)"
                    save_data()
                    st.rerun()
                
                if c3.button("📄 FAKTUR", key=f"fkt_{i}"):
                    st.session_state.current_faktur = b

    if 'current_faktur' in st.session_state:
        f = st.session_state.current_faktur
        p = st.session_state.db['profile']
        s = st.session_state.db['faktur_settings']
        
        total_p = sum([int(item['price']) * int(item['qty']) for item in f.get('paket_list', [])])
        total_m = sum([int(item['harga']) * int(item['qty']) for item in f.get('manual_list', [])])
        total_semua = total_p + total_m

        dp = int(f.get('dp', 0))
        sisa_tagihan = max(total_semua - dp, 0)

        stempel = '<div class="stempel-lunas">LUNAS</div>' if f.get('status') == "SELESAI (LUNAS)" else ""
        
        nota_html = f"""
        <div class="faktur-box">
            {stempel}
            <center>
                <h2 style="margin:0; color:#F19CBB;">{p['nama']}</h2>
            </center>
            <hr>
            <p><b>INVOICE #{f['inv_no']}</b></p>

            <b>TOTAL TAGIHAN:</b> Rp {total_semua:,}<br>
            <b>DP:</b> Rp {dp:,}<br>
            <b>SISA PELUNASAN:</b> Rp {0 if f.get('status') == "SELESAI (LUNAS)" else sisa_tagihan:,}
        </div>
        """
        st.markdown(nota_html, unsafe_allow_html=True)
