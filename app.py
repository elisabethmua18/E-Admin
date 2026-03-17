import streamlit as st
import json
import os
import pandas as pd
import base64
from datetime import datetime, time, date

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
        margin-bottom: 5px; border-left: 10px solid #F19CBB; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .faktur-box {
        background-color: white; padding: 30px; border: 1px solid #eee; border-radius: 10px;
        color: black; line-height: 1.5; font-family: 'Arial', sans-serif; position: relative;
    }
    .stempel-lunas {
        position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-20deg);
        border: 5px solid red; color: red; font-size: 40px; font-weight: bold;
        padding: 10px 20px; border-radius: 10px; opacity: 0.5; pointer-events: none; z-index: 99;
    }
    .otw-info {
        color: #777; font-style: italic; font-size: 0.9em; margin: 5px 0 20px 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEM DATABASE ---
DATA_FILE = "mua_master_pro.json"

def load_data():
    initial_bookings = [
        {"inv_no": "INV0005", "nama": "Kak Angel", "tgl": "17/03/2026", "wa": "08xxxx", "alamat_mu": "Tembalang", "jam_ready": "14:00-16:00", "jam_otw": "16:15", "durasi_otw": 15, "paket_list": [], "manual_list": [], "hire_tim": True, "tim_type": "Hairdo", "tim_nama": "Selly", "dp": 0, "status": "PENDING"},
        {"inv_no": "INV0006", "nama": "Kak Reyki", "tgl": "17/03/2026", "wa": "08xxxx", "alamat_mu": "Hotel Aruman", "jam_ready": "13:00-15:00", "jam_otw": "12:15", "durasi_otw": 30, "paket_list": [], "manual_list": [], "hire_tim": True, "tim_type": "Hairdo", "tim_nama": "Ovie", "dp": 0, "status": "PENDING"}
    ]
    defaults = {
        "profile": {"nama": "Elisabeth MUA", "alamat": "", "hp": "", "ig": "", "bank": "", "no_rek": "", "an": "", "logo_base64": ""},
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

# --- MENU ---
menu = st.sidebar.radio("MENU", ["BERANDA", "INPUT JADWAL", "LAYANAN", "PROFIL & SETTING", "KEUANGAN"])

# --- 1. BERANDA ---
if menu == "BERANDA":
    st.header("🌸 Jadwal Elisabeth MUA")
    selected_date = st.date_input("Pilih Tanggal", value=date(2026, 3, 17))
    st.divider()
    
    selected_str = selected_date.strftime("%d/%m/%Y")
    list_job = [b for b in st.session_state.db['bookings'] if b.get('tgl') == selected_str]
    list_job = sorted(list_job, key=lambda x: x.get('jam_ready', '00:00').split('-')[0])
    
    if not list_job:
        st.info("Tidak ada jadwal.")
    else:
        for i, b in enumerate(list_job):
            with st.container():
                edit_info = f" | 🕒 Edit Terakhir: {b['last_edit']}" if 'last_edit' in b else ""
                st.markdown(f"""
                <div class="job-card">
                    <h3 style="margin:0; color:#F19CBB;">{b.get('nama','-')} - {b.get('inv_no','-')}</h3>
                    <p style="margin:5px 0;"><b>Jam Kerja:</b> {b.get('jam_ready','-')} | <b>Lokasi:</b> {b.get('alamat_mu','-')}</p>
                    <p style="margin:5px 0;"><b>Tim:</b> {b.get('tim_type','-')} ({b.get('tim_nama','-')})</p>
                    <p style="margin:5px 0; font-size:0.8em; color:gray;"><b>Status:</b> {b.get('status','PENDING')}{edit_info}</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f'<p class="otw-info">🚗 Jam OTW: {b.get("jam_otw","-")} ({b.get("durasi_otw","-")}m)</p>', unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                if c1.button("EDIT", key=f"ed_{i}"):
                    st.session_state.edit_data = b
                    st.session_state.input_pakets = b.get('paket_list', [])
                    st.session_state.input_manuals = b.get('manual_list', [])
                    st.warning("Data dimuat! Silakan klik tab 'INPUT JADWAL'")
                
                if c2.button("✅ SELESAI", key=f"dn_{i}"):
                    b['status'] = f"LUNAS HARI H ({datetime.now().strftime('%d/%m/%Y')})"
                    save_data(); st.rerun()
                
                if c3.button("📄 FAKTUR", key=f"fkt_{i}"):
                    st.session_state.current_faktur = b

    if 'current_faktur' in st.session_state:
        f = st.session_state.current_faktur
        p = st.session_state.db['profile']
        s = st.session_state.db['faktur_settings']
        
        logo_html = ""
        if p.get('logo_base64'):
            logo_html = f'<img src="data:image/png;base64,{p["logo_base64"]}" style="width:70px; position: absolute; left: 10px; top: 10px;">'
        
        is_lunas = "LUNAS" in f.get('status', '')
        stempel = '<div class="stempel-lunas">LUNAS</div>' if is_lunas else ""
        
        total_p = sum([(item.get('price',0) * item.get('qty',1)) for item in f.get('paket_list', [])])
        total_m = sum([(item.get('harga',0) * item.get('qty',1)) for item in f.get('manual_list', [])])
        total_semua = total_p + total_m
        dp_val = f.get('dp', 0)
        sisa = total_semua - dp_val

        tnc_html = s.get('tnc','').replace('\\n','<br>').replace('\n','<br>')

        st.divider()
        nota_html = f"""
        <div class="faktur-box">
            {stempel}
            <div style="position: relative; min-height: 100px; padding-left: 90px;">
                {logo_html}
                <div style="text-align: center;">
                    <h2 style="margin:0; color:#F19CBB;">{p.get('nama','')}</h2>
                    <p style="margin:0; font-size:12px;">{p.get('alamat','')}<br>WA: {p.get('hp','')} | IG: {p.get('ig','')}</p>
                </div>
            </div>
            <hr style="border: 1px solid #eee;">
            <p><b>INVOICE #{f.get('inv_no','')}</b></p>
            <table style="width:100%; font-size: 14px;">
                <tr><td style="width:35%;">Nama Klien</td><td>: {f.get('nama','')}</td></tr>
                <tr><td>WhatsApp</td><td>: {f.get('wa','-')}</td></tr>
                <tr><td>Tanggal</td><td>: {f.get('tgl','')}</td></tr>
                <tr><td>Lokasi</td><td>: {f.get('alamat_mu','')}</td></tr>
                <tr><td>Jam Kerja</td><td>: {f.get('jam_ready','')}</td></tr>
            </table>
            <br>
            <p style="border-bottom: 1px solid #eee; padding-bottom: 5px;"><b>RINCIAN LAYANAN:</b></p>
            <div style="font-size: 13px;">"""
        
        for item in f.get('paket_list', []):
            nota_html += f"<div style='display:flex; justify-content:space-between;'><span>• {item.get('nama','')} (x{item.get('qty',1)})</span><span>Rp {item.get('price',0)*item.get('qty',1):,}</span></div>"
        for item_m in f.get('manual_list', []):
            nota_html += f"<div style='display:flex; justify-content:space-between;'><span>• {item_m.get('nama','')} (x{item_m.get('qty',1)})</span><span>Rp {item_m.get('harga',0)*item_m.get('qty',1):,}</span></div>"
        
        sisa_teks = f"<span style='color:green;'>{f.get('status')}</span>" if is_lunas else f"Rp {sisa:,}"

        nota_html += f"""</div>
            <hr style="border: 1px dashed #eee; margin: 15px 0;">
            <table style="width:100%; font-weight: bold; font-size: 15px;">
                <tr><td>TOTAL TAGIHAN</td><td style="text-align:right;">Rp {total_semua:,}</td></tr>
                <tr><td>DP DITERIMA</td><td style="text-align:right;">Rp {dp_val:,}</td></tr>
                <tr><td>SISA PELUNASAN</td><td style="text-align:right;">{sisa_teks}</td></tr>
            </table>
            <br>
            <div style="background-color: #f9f9f9; padding: 10px; border-radius: 5px; font-size: 12px;">
                <b>REKENING PEMBAYARAN:</b><br>{p.get('bank','')} {p.get('no_rek','')} a/n {p.get('an','')}
            </div>
            <br>
            <p style="font-size:11px; color: #555;"><b>S&K:</b><br>{tnc_html}</p>
            <center><p style="margin-top:20px; font-weight: bold;">{s.get('salam','')}</p></center>
            <div style="text-align:right; margin-top:10px;"><p>Ttd,<br><br><b>{s.get('signature','')}</b></p></div>
        </div>"""
        st.markdown(nota_html, unsafe_allow_html=True)
        st.download_button(label="💾 DOWNLOAD IMAGE-NOTA", data=nota_html, file_name=f"Invoice_{f.get('nama','klien')}.html", mime="text/html")
        if st.button("Tutup Preview"): del st.session_state.current_faktur; st.rerun()

# --- 2. INPUT JADWAL ---
elif menu == "INPUT JADWAL":
    st.header("📝 Tambah Jadwal Baru")
    edit_data = st.session_state.get('edit_data', {})
    with st.container():
        nama_klien = st.text_input("1. Nama Klien", value=edit_data.get('nama', ""))
        try:
            tgl_def = datetime.strptime(edit_data['tgl'], "%d/%m/%Y") if edit_data else datetime.now()
        except: tgl_def = datetime.now()
        tgl_makeup = st.date_input("2. Tanggal Makeup", tgl_def)
        wa_klien = st.text_input("3. Nomor WhatsApp", value=edit_data.get('wa', ""))
        alamat_makeup = st.text_area("4. Alamat Makeup", value=edit_data.get('alamat_mu', ""))
        times = [time(h, m).strftime("%H:%M") for h in range(24) for m in (0, 15, 30, 45)]
        jam_m = st.selectbox("5. Jam Mulai", times, index=32)
