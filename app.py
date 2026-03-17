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
        margin-top: 20px;
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

# --- SISTEM LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    st.markdown("<h2 style='text-align: center; color: #F19CBB;'>🌸 Login E-Admin MUA 🌸</h2>", unsafe_allow_html=True)
    with st.container():
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            if email == "elisabethmua18@gmail.com" and password == "Elis5173":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Email atau Password salah!")

if not st.session_state.logged_in:
    login_page()
    st.stop()

# --- SISTEM DATABASE ---
DATA_FILE = "mua_master_pro.json"

def load_data():
    initial_bookings = []
    defaults = {
        "profile": {"nama": "Elisabeth MUA", "alamat": "", "hp": "", "ig": "", "bank": "", "no_rek": "", "an": "", "logo_base64": ""},
        "faktur_settings": {"tnc": "", "signature": "", "salam": "", "next_inv": 1},
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
if st.sidebar.button("LOGOUT"):
    st.session_state.logged_in = False
    st.rerun()

# --- 1. BERANDA ---
if menu == "BERANDA":
    st.header("🌸 Jadwal Elisabeth MUA")
    selected_date = st.date_input("Pilih Tanggal", value=date.today())
    st.divider()
    
    selected_str = selected_date.strftime("%d/%m/%Y")
    list_job = [b for b in st.session_state.db['bookings'] if b.get('tgl') == selected_str]
    list_job = sorted(list_job, key=lambda x: x.get('jam_ready', '00:00').split('-')[0])
    
    if not list_job:
        st.info("Tidak ada jadwal.")
    else:
        for i, b in enumerate(list_job):
            with st.container():
                st.markdown(f"""
                <div class="job-card">
                    <h3 style="margin:0; color:#F19CBB;">{b.get('nama','-')} - {b.get('inv_no','-')}</h3>
                    <p style="margin:5px 0;"><b>Jam Kerja:</b> {b.get('jam_ready','-')} | <b>Lokasi:</b> {b.get('alamat_mu','-')}</p>
                    <p style="margin:5px 0;"><b>Tim:</b> {b.get('tim_type','-')} ({b.get('tim_nama','-')})</p>
                    <p style="margin:5px 0;"><b>Status:</b> {b.get('status','PENDING')}</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f'<p class="otw-info">🚗 Jam OTW: {b.get("jam_otw","-")} ({b.get("durasi_otw","-")}m)</p>', unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                if c1.button("EDIT", key=f"ed_{i}"):
                    st.session_state.edit_data = b
                    st.session_state.input_pakets = b.get('paket_list', [])
                    st.session_state.input_manuals = b.get('manual_list', [])
                    st.warning("Data dimuat! Silakan buka menu 'INPUT JADWAL'")
                
                if c2.button("✅ SELESAI", key=f"dn_{i}"):
                    b['status'] = "SELESAI (LUNAS)"
                    save_data(); st.rerun()
                
                if c3.button("📄 FAKTUR", key=f"fkt_{i}"):
                    st.session_state.current_faktur = b

    if 'current_faktur' in st.session_state:
        f = st.session_state.current_faktur
        p = st.session_state.db['profile']
        s = st.session_state.db['faktur_settings']
        
        logo_html = f'<img src="data:image/png;base64,{p["logo_base64"]}" style="width:70px; position: absolute; left: 10px; top: 10px;">' if p.get('logo_base64') else ""
        
        # PERBAIKAN DI SINI: Menambahkan else "" agar tidak SyntaxError
        stempel = '<div class="stempel-lunas">LUNAS</div>' if f.get('status') == "SELESAI (LUNAS)" else ""
        
        total_p = sum([(item.get('price',0) * item.get('qty',1)) for item in f.get('paket_list', [])])
        total_m = sum([(item.get('harga',0) * item.get('qty',1)) for item in f.get('manual_list', [])])
        total_semua = total_p + total_m
        dp_val = f.get('dp', 0)
        sisa = total_semua - dp_val

        tnc_rapi = s.get('tnc','').replace('\n', '<br>')

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
            <div style="font-size: 13px;">
        """
        for item in f.get('paket_list', []):
            nota_html += f"<div style='display:flex; justify-content:space-between;'><span>• {item.get('nama','')} (x{item.get('qty',1)})</span><span>Rp {item.get('price',0)*item.get('qty',1):,}</span></div>"
        for item_m in f.get('manual_list', []):
            nota_html += f"<div style='display:flex; justify-content:space-between;'><span>• {item_m.get('nama','')} (x{item_m.get('qty',1)})</span><span>Rp {item_m.get('harga',0)*item_m.get('qty',1):,}</span></div>"
        
        nota_html += f"""
            </div>
            <hr style="border: 1px dashed #eee; margin: 15px 0;">
            <table style="width:100%; font-weight: bold; font-size: 15px;">
                <tr><td>TOTAL TAGIHAN</td><td style="text-align:right;">Rp {total_semua:,}</td></tr>
                <tr><td>DP DITERIMA</td><td style="text-align:right;">Rp {dp_val:,}</td></tr>
                <tr><td>SISA PELUNASAN</td><td style="text-align:right; color:{'green' if sisa <= 0 else 'red'};">Rp {sisa:,}</td></tr>
            </table>
            <br>
            <div style="background-color: #f9f9f9; padding: 10px; border-radius: 5px; font-size: 12px;">
                <b>REKENING PEMBAYARAN:</b><br>{p.get('bank','')} {p.get('no_rek','')} a/n {p.get('an','')}
            </div>
            <br>
            <p style="font-size:11px; color: #555;"><b>S&K:</b><br>{tnc_rapi}</p>
            <center><p style="margin-top:20px; font-weight: bold;">{s.get('salam','')}</p></center>
            <div style="text-align:right; margin-top:10px;"><p>Ttd,<br><br><b>{s.get('signature','')}</b></p></div>
        </div>
        """
        st.markdown(nota_html, unsafe_allow_html=True)
        st.download_button(label="💾 DOWNLOAD NOTA", data=nota_html, file_name=f"Invoice_{f.get('nama','klien')}.html", mime="text/html")
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
        jam_s = st.selectbox("6. Jam Selesai", times, index=40)
        jam_o = st.selectbox("7. Jam OTW", times, index=28)
        durasi_otw = st.number_input("8. Durasi OTW (Menit)", min_value=0, value=edit_data.get('durasi_otw', 30))
        st.write("---")
        st.write("**9. Pilih Paket**")
        master_list = list(st.session_state.db['master_layanan'].keys())
        col_sel, col_add = st.columns([3, 1])
        selected_p = col_sel.selectbox("Cari Paket Master", ["-- Pilih Paket --"] + master_list)
        if 'input_pakets' not in st.session_state: st.session_state.input_pakets = []
        if col_add.button("PILIH PAKET"):
            if selected_p != "-- Pilih Paket --":
                st.session_state.input_pakets.append({"nama": selected_p, "qty": 1, "price": st.session_state.db['master_layanan'][selected_p]})
        for i, item in enumerate(st.session_state.input_pakets):
            cp1, cp2, cp3 = st.columns([3, 1, 0.5])
            cp1.markdown(f"**{item.get('nama','')}**")
            item['qty'] = cp2.number_input("Qty", min_value=1, key=f"qty_p_{i}", value=item.get('qty', 1))
            if cp3.button("❌", key=f"del_p_{i}"): st.session_state.input_pakets.pop(i); st.rerun()
        st.write("---")
        st.write("**10. Layanan Tambahan Manual**")
        if 'input_manuals' not in st.session_state: st.session_state.input_manuals = []
        if st.button("TAMBAH LAYANAN MANUAL"):
            st.session_state.input_manuals.append({"nama": "", "harga": 0, "qty": 1})
        for j, item_m in enumerate(st.session_state.input_manuals):
            cm1, cm2, cm3, cm4 = st.columns([2, 1, 1, 0.5])
            item_m['nama'] = cm1.text_input("Keterangan", key=f"m_nama_{j}", value=item_m.get('nama',''))
            item_m['harga'] = cm2.number_input("Harga", min_value=0, key=f"m_harga_{j}", value=item_m.get('harga',0))
            item_m['qty'] = cm3.number_input("Qty", min_value=1, key=f"m_qty_{j}", value=item_m.get('qty',1))
            if cm4.button("❌", key=f"del_m_{j}"): st.session_state.input_manuals.pop(j); st.rerun()
        st.write("---")
        dp_value = st.number_input("11. DP (Down Payment)", min_value=0, value=edit_data.get('dp', 0))
        st.write("---")
        st.write("**Hire Tim**")
        hire_tim = st.checkbox("Gunakan Tim Tambahan?", value=edit_data.get('hire_tim', False))
        if hire_tim:
            ct1, ct2 = st.columns(2)
            tim_type = ct1.selectbox("Jenis Tim", ["Hairdo", "Hijabdo", "Hairdo + Hijabdo"])
            tim_nama = ct2.text_input("Nama Anggota Tim", value=edit_data.get('tim_nama', ""))
        else:
            tim_type = "-"; tim_nama = "-"
        st.write("---")
        if st.button("💾 SIMPAN JADWAL KE DATABASE"):
            if not nama_klien: st.error("Nama Klien wajib diisi!")
            else:
                if edit_data:
                    st.session_state.db['bookings'] = [b for b in st.session_state.db['bookings'] if b.get('inv_no') != edit_data.get('inv_no')]
                
                new_booking = {
                    "inv_no": edit_data.get('inv_no', f"INV{st.session_state.db['faktur_settings'].get('next_inv', 1):04d}"),
                    "nama": nama_klien, "tgl": tgl_makeup.strftime("%d/%m/%Y"), "wa": wa_klien, "alamat_mu": alamat_makeup,
                    "jam_ready": f"{jam_m}-{jam_s}", "jam_otw": jam_o, "durasi_otw": durasi_otw,
                    "paket_list": list(st.session_state.input_pakets), "manual_list": list(st.session_state.input_manuals),
                    "hire_tim": hire_tim, "tim_type": tim_type, "tim_nama": tim_nama, "dp": dp_value, "status": edit_data.get('status', 'PENDING')
                }
                st.session_state.db['bookings'].append(new_booking)
                if not edit_data:
                    st.session_state.db['faktur_settings']['next_inv'] += 1
                if 'edit_data' in st.session_state: del st.session_state.edit_data
                save_data(); st.success("Tersimpan!"); st.session_state.input_pakets = []; st.session_state.input_manuals = []; st.rerun()

# --- 3. LAYANAN ---
elif menu == "LAYANAN":
    st.header("💄 Master Layanan Utama")
    with st.form("master"):
        nl = st.text_input("Nama Paket Baru")
        hl = st.number_input("Harga Master", min_value=0)
        if st.form_submit_button("Tambah ke Master"):
            st.session_state.db['master_layanan'][nl] = hl; save_data(); st.rerun()
    st.table(pd.DataFrame(list(st.session_state.db['master_layanan'].items()), columns=['Paket', 'Harga']))

# --- 4. PROFIL & SETTING ---
elif menu == "PROFIL & SETTING":
    st.header("👤 Profil & Setting Faktur")
    t_prof, t_set = st.tabs(["PROFIL", "SETTING"])
    with t_prof:
        st.session_state.db['profile']['nama'] = st.text_input("Nama MUA"),
