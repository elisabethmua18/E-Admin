import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, time
from fpdf import FPDF

# --- CONFIG HALAMAN ---
st.set_page_config(page_title="E-Admin MUA - Elisabeth", layout="centered")

# --- STYLE CSS PINK ---
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

# --- SISTEM DATABASE ANTI-ERROR ---
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
                for k in defaults["profile"]:
                    if k not in data["profile"]: data["profile"][k] = defaults["profile"][k]
                for k in defaults["faktur_settings"]:
                    if k not in data["faktur_settings"]: data["faktur_settings"][k] = defaults["faktur_settings"][k]
                return data
        except: return defaults
    return defaults

if 'db' not in st.session_state:
    st.session_state.db = load_data()

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.db, f, indent=4)

# --- FUNGSI GENERATE PDF ---
def generate_pdf(k):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, st.session_state.db['profile'].get('nama', 'Elisabeth MUA'), ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, st.session_state.db['profile'].get('alamat', ''), ln=True, align='C')
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
    pdf.cell(0, 8, f"SISA SALDO TERUTANG: Rp {total - k.get('dp', 0):,}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, f"Pembayaran Via: {st.session_state.db['faktur_settings'].get('bank','')} {st.session_state.db['faktur_settings'].get('no_rek','')} a/n {st.session_state.db['faktur_settings'].get('an','')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, f"Terms & Conditions:\n{st.session_state.db['faktur_settings'].get('tnc','')}")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 10, st.session_state.db['faktur_settings'].get('salam', 'Terima Kasih!'), ln=True, align='C')
    return pdf.output()

# --- LOGIN ---
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

# --- 1. BERANDA (FIXED DISPLAY) ---
if menu == "BERANDA":
    st.header("🌸 Jadwal Elisabeth MUA")
    c1, c2 = st.columns(2)
    d1 = c1.date_input("Dari Tanggal", datetime.now()) # Popup kalender
    d2 = c2.date_input("Sampai Tanggal", datetime.now())
    
    sorted_b = sorted(st.session_state.db['bookings'], key=lambda x: x.get('jam_ready', '00:00'))
    
    for idx, b in enumerate(sorted_b):
        try:
            tgl_b = datetime.strptime(b['tgl'], "%d/%m/%Y").date()
            if d1 <= tgl_b <= d2:
                with st.container():
                    st.markdown(f"""
                    <div class="job-card">
                        <b style="font-size:20px; color:#F19CBB;">{b.get('nama','')}</b><br>
                        📅 <b>{b.get('tgl','')}</b><br>
                        🕔 Jam: <b>{b.get('jam_ready','-')}</b><br>
                        🚗 OTW: <b>{b.get('jam_otw','-')}</b><br>
                        🤝 Tim: {b.get('tim_type','-')} ({b.get('tim_nama','-')})
                    </div>
                    """, unsafe_allow_html=True)
                    cols = st.columns(4)
                    if cols[0].button("LUNAS", key=f"lns{idx}"):
                        b['status'] = "SELESAI"; save_data(); st.rerun()
                    if cols[1].button("EDIT", key=f"edt{idx}"):
                        st.info("Fitur edit sedang sinkronisasi")
                    if cols[2].button("FAKTUR", key=f"fkt{idx}"):
                        st.session_state.fkt_preview = b
                    if cols[3].button("HAPUS", key=f"del{idx}"):
                        st.session_state.db['bookings'].remove(b); save_data(); st.rerun()
        except: pass

    if 'fkt_preview' in st.session_state:
        k = st.session_state.fkt_preview
        st.divider()
        st.download_button("📩 Download PDF Faktur " + k['nama'], data=generate_pdf(k), file_name=f"Faktur_{k['nama']}.pdf", mime="application/pdf")

# --- 2. INPUT JADWAL (FIXED INPUTS) ---
elif menu == "INPUT JADWAL":
    st.header("📝 Catat Jadwal")
    with st.form("job_form", clear_on_submit=True):
        nama = st.text_input("Nama Klien")
        wa = st.text_input("WhatsApp")
        lokasi = st.text_area("Lokasi Acara")
        tgl_job = st.date_input("Tanggal Acara", datetime.now()) # Popup Kalender
        
        times = [time(h, m).strftime("%H:%M") for h in range(24) for m in (0, 15, 30, 45)]
        c1, c2, c3 = st.columns(3)
        jam_m = c1.selectbox("Jam Mulai", times, index=32)
        jam_s = c2.selectbox("Jam Selesai", times, index=40)
        jam_otw = c3.selectbox("Jam OTW", times, index=28)
        
        st.write("---")
        hire_tim = st.radio("Hire Tim Tambahan?", ["Tidak", "Ya"])
        tim_type = st.selectbox("Jenis Tim", ["Hairdo", "Hijabdo", "Asisten"]) if hire_tim == "Ya" else "-"
        tim_nama = st.text_input("Nama Anggota Tim") if hire_tim == "Ya" else "-"
        
        st.write("---")
        st.write("**Pilih Paket:**")
        input_pakets = []
        for p_name, p_price in st.session_state.db['master_layanan'].items():
            qty = st.number_input(f"Person: {p_name} (Rp {p_price:,})", min_value=0, key=f"p_{p_name}")
            if qty > 0: input_pakets.append({"nama": p_name, "qty": qty, "price": p_price})
        
        st.write("---")
        st.write("**Layanan Manual Tambahan:**")
        input_manuals = []
        num_m = st.number_input("Tambah baris manual", 0, 10)
        for i in range(num_m):
            cm1, cm2, cm3 = st.columns([2, 1, 1])
            m_nama = cm1.text_input(f"Keterangan {i+1}", key=f"mn{i}")
            m_hrg = cm2.number_input(f"Harga {i+1}", 0, key=f"mh{i}")
            m_qty = cm3.number_input(f"Qty {i+1}", 1, key=f"mq{i}")
            if m_nama: input_manuals.append({"nama": m_nama, "harga": m_hrg, "qty": m_qty})
            
        dp = st.number_input("DP (Down Payment)", 0)

        if st.form_submit_button("SIMPAN JADWAL"):
            new_b = {
                "inv_no": f"INV{st.session_state
