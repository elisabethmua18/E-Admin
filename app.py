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
    </style>
    """, unsafe_allow_html=True)

# --- SISTEM DATABASE ---
DATA_FILE = "mua_master_pro.json"

def load_data():
    defaults = {
        "profile": {"nama": "Elisabeth MUA", "alamat": "", "hp": "", "ig": "", "bank": "", "no_rek": "", "an": "", "logo_base64": ""},
        "faktur_settings": {"tnc": "", "signature": "", "salam": "", "next_inv": 1},
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
                edit_label = f" | 🕒 Edit: {b['last_edit']}" if 'last_edit' in b else ""
                st.markdown(f"""
                <div class="job-card">
                    <h3 style="margin:0; color:#F19CBB;">{b.get('nama','-')} - {b.get('inv_no','-')}</h3>
                    <p style="margin:5px 0;"><b>Jam Kerja:</b> {b.get('jam_ready','-')} | <b>Lokasi:</b> {b.get('alamat_mu','-')}</p>
                    <p style="margin:5px 0; font-size:0.8em; color:gray;"><b>Status:</b> {b.get('status','PENDING')}{edit_label}</p>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                if c1.button("EDIT", key=f"ed_{i}"):
                    st.session_state.edit_data = b
                    st.session_state.input_pakets = b.get('paket_list', [])
                    st.session_state.input_manuals = b.get('manual_list', [])
                    st.warning("Data dimuat! Klik menu INPUT JADWAL")
                
                if c2.button("✅ SELESAI", key=f"dn_{i}"):
                    b['status'] = f"LUNAS HARI H ({datetime.now().strftime('%d/%m/%Y')})"
                    save_data(); st.rerun()
                
                if c3.button("📄 FAKTUR", key=f"fkt_{i}"):
                    st.session_state.current_faktur = b

    if 'current_faktur' in st.session_state:
        f = st.session_state.current_faktur
        p = st.session_state.db['profile']
        s = st.session_state.db['faktur_settings']
        
        logo_html = f'<img src="data:image/png;base64,{p["logo_base64"]}" style="width:70px; position: absolute; left: 10px; top: 10px;">' if p.get('logo_base64') else ""
        lunas = "LUNAS" in f.get('status', '')
        stempel = '<div class="stempel-lunas">LUNAS</div>' if lunas else ""
        
        t_p = sum([(item.get('price',0) * item.get('qty',1)) for item in f.get('paket_list', [])])
        t_m = sum([(item.get('harga',0) * item.get('qty',1)) for item in f.get('manual_list', [])])
        total = t_p + t_m
        sisa = total - f.get('dp', 0)

        st.divider()
        nota = f"""
        <div class="faktur-box">
            {stempel}
            <div style="text-align: center;">
                {logo_html}
                <h2 style="margin:0; color:#F19CBB;">{p.get('nama','')}</h2>
                <p style="font-size:12px;">{p.get('alamat','')}<br>WA: {p.get('hp','')} | IG: {p.get('ig','')}</p>
            </div>
            <hr>
            <b>INVOICE #{f.get('inv_no','')}</b><br>
            <small>Klien: {f.get('nama','')}<br>Tgl: {f.get('tgl','')}<br>Jam: {f.get('jam_ready','')}</small>
            <hr>
            <div style="font-size:13px;">
        """
        for item in f.get('paket_list', []):
            nota += f"<div style='display:flex; justify-content:space-between;'><span>{item['nama']}</span><span>Rp {item['price']*item['qty']:,}</span></div>"
        for item_m in f.get('manual_list', []):
            nota += f"<div style='display:flex; justify-content:space-between;'><span>{item_m['nama']}</span><span>Rp {item_m['harga']*item_m['qty']:,}</span></div>"
        
        warna_sisa = "color:green;" if lunas else "color:red;"
        teks_sisa = f.get('status') if lunas else f"Rp {sisa:,}"

        nota += f"""
            </div>
            <hr>
            <table style="width:100%; font-weight:bold;">
                <tr><td>TOTAL</td><td style="text-align:right;">Rp {total:,}</td></tr>
                <tr style="{warna_sisa}"><td>SISA</td><td style="text-align:right;">{teks_sisa}</td></tr>
            </table>
            <p style="font-size:10px;">TnC:<br>{s.get('tnc','').replace('\\n','<br>').replace('\n','<br>')}</p>
        </div>"""
        st.markdown(nota, unsafe_allow_html=True)
        if st.button("Tutup Preview"): del st.session_state.current_faktur; st.rerun()

# --- 2. INPUT JADWAL ---
elif menu == "INPUT JADWAL":
    st.header("📝 Tambah Jadwal")
    edit_data = st.session_state.get('edit_data', {})
    
    nama_klien = st.text_input("Nama Klien", value=edit_data.get('nama', ""))
    tgl_makeup = st.date_input("Tanggal", value=datetime.strptime(edit_data['tgl'], "%d/%m/%Y") if edit_data else date.today())
    
    times = [time(h, m).strftime("%H:%M") for h in range(24) for m in (0, 15, 30, 45)]
    c1, c2 = st.columns(2)
    jam_m = c1.selectbox("Jam Mulai", times, index=32)
    jam_s = c2.selectbox("Jam Selesai", times, index=40)
    
    dp_value = st.number_input("DP", min_value=0, value=edit_data.get('dp', 0))
    
    # --- LOGIK CEK BENTROK ---
    bentrok = False
    if nama_klien:
        tgl_cek = tgl_makeup.strftime("%d/%m/%Y")
        for b in st.session_state.db['bookings']:
            if b['tgl'] == tgl_cek and b['inv_no'] != edit_data.get('inv_no'):
                j_lama = b['jam_ready'].split('-')
                if not (jam_s <= j_lama[0] or jam_m >= j_lama[1]):
                    st.error(f"⚠️ BENTROK dengan {b['nama']} ({b['jam_ready']})")
                    bentrok = True

    if st.button("💾 SIMPAN JADWAL") and not bentrok:
        if not nama_klien:
            st.error("Nama wajib diisi")
        else:
            if edit_data:
                st.session_state.db['bookings'] = [b for b in st.session_state.db['bookings'] if b.get('inv_no') != edit_data.get('inv_no')]
            
            new_booking = {
                "inv_no": edit_data.get('inv_no', f"INV{st.session_state.db['faktur_settings'].get('next_inv', 1):04d}"),
                "nama": nama_klien, "tgl": tgl_makeup
