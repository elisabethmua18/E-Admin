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
    .faktur-card { background-color: white; padding: 20px; border-radius: 10px; color: black; }
    .job-card { 
        background-color: white; padding: 15px; border-radius: 10px; 
        margin-bottom: 10px; border-left: 5px solid #F19CBB;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEM DATABASE ---
DATA_FILE = "mua_master_pro.json"

def load_data():
    default_data = {
        "profile": {"nama": "Elisabeth MUA", "alamat": "", "hp": "", "ig": "", "logo_url": ""},
        "faktur_settings": {"tnc": "", "bank": "", "no_rek": "", "an": "", "signature": "", "thanks": "", "next_inv": 1},
        "master_layanan": {}, "bookings": [], "pengeluaran": []
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                # Pastikan semua kunci baru ada (Anti-Error KeyError)
                for key in default_data:
                    if key not in data: data[key] = default_data[key]
                for key in default_data["profile"]:
                    if key not in data["profile"]: data["profile"][key] = default_data["profile"][key]
                for key in default_data["faktur_settings"]:
                    if key not in data["faktur_settings"]: data["faktur_settings"][key] = default_data["faktur_settings"][key]
                return data
        except: return default_data
    return default_data

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
    pdf.cell(0, 10, st.session_state.db['profile'].get('nama', 'Elisabeth MUA'), ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"IG: {st.session_state.db['profile'].get('ig','')} | WA: {st.session_state.db['profile'].get('hp','')}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"INVOICE #{k['inv_no']}", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"Tanggal: {k['tgl']}", ln=True)
    pdf.cell(0, 5, f"Klien: {k['nama']}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 5, "RINCIAN LAYANAN:", ln=True, border='B')
    total = 0
    for p in k['paket_list']:
        sub = p['price'] * p['qty']
        pdf.cell(0, 7, f"- {p['nama']} ({p['qty']} person): Rp {sub:,}", ln=True)
        total += sub
    for m in k.get('manual_list', []):
        sub_m = m['harga'] * m.get('qty', 1)
        pdf.cell(0, 7, f"- {m['nama']} (x{m.get('qty', 1)}): Rp {sub_m:,}", ln=True)
        total += sub_m
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, f"TOTAL TAGIHAN: Rp {total:,}", ln=True)
    pdf.cell(0, 7, f"DP / DIBAYAR: Rp {k['dp']:,}", ln=True)
    pdf.cell(0, 7, f"SISA SALDO: Rp {total - k['dp']:,}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, f"Pembayaran ke: {st.session_state.db['faktur_settings'].get('bank','')} {st.session_state.db['faktur_settings'].get('no_rek','')} a/n {st.session_state.db['faktur_settings'].get('an','')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, f"TnC: {st.session_state.db['faktur_settings'].get('tnc','')}")
    pdf.ln(5)
    pdf.cell(0, 5, st.session_state.db['faktur_settings'].get('thanks','Terima Kasih'), ln=True, align='C')
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

# --- 1. BERANDA ---
if menu == "BERANDA":
    st.header("🌸 Dashboard Jadwal")
    c1, c2 = st.columns(2)
    d1 = c1.date_input("Dari", datetime.now())
    d2 = c2.date_input("Sampai", datetime.now())
    
    for idx, b in enumerate(st.session_state.db['bookings']):
        try:
            tgl_b = datetime.strptime(b['tgl'], "%d/%m/%Y").date()
            if d1 <= tgl_b <= d2:
                with st.container():
                    st.markdown(f"""
                    <div class="job-card">
                        <b>{b['nama']}</b> ({b['tgl']})<br>
                        🕔 Ready: {b['jam_ready']} | 🚗 OTW: {b.get('jam_otw','-')} ({b.get('durasi_otw','-')}m)<br>
                        🤝 Tim: {b.get('tim_type','-')} ({b.get('tim_nama','-')})
                    </div>
                    """, unsafe_allow_html=True)
                    col_btn = st.columns(3)
                    if col_btn[0].button("LUNAS", key=f"lns{idx}"):
                        st.session_state.db['bookings'][idx]['status'] = "SELESAI"; save_data(); st.rerun()
                    if col_btn[1].button("FAKTUR", key=f"fkt{idx}"):
                        st.session_state.current_fkt = b
                    if col_btn[2].button("HAPUS", key=f"del{idx}"):
                        st.session_state.db['bookings'].pop(idx); save_data(); st.rerun()
        except: pass

    if 'current_fkt' in st.session_state:
        k = st.session_state.current_fkt
        st.divider()
        st.download_button("📩 Download PDF Faktur " + k['nama'], data=generate_pdf(k), file_name=f"Faktur_{k['nama']}.pdf", mime="application/pdf")

# --- 2. INPUT JADWAL ---
elif menu == "INPUT JADWAL":
    st.header("📝 Catat Jadwal")
    with st.form("job_form", clear_on_submit=True):
        nama = st.text_input("Nama Klien")
        wa = st.text_input("WhatsApp")
        lokasi = st.text_input("Lokasi")
        tgl_job = st.date_input("Tanggal Acara")
        
        times = [time(h, m).strftime("%H:%M") for h in range(24) for m in (0, 15, 30, 45)]
        c1, c2 = st.columns(2)
        jam_m = c1.selectbox("Jam Ready", times, index=32)
        jam_otw = c2.selectbox("Jam OTW", times, index=28)
        durasi_otw = st.number_input("Durasi Perjalanan (Menit)", 30)
        
        st.write("---")
        st.write("**Hire Tim Tambahan:**")
        tim_type = st.selectbox("Tipe Tim", ["-", "Hairdo", "Hijabdo", "Asisten"])
        tim_nama = st.text_input("Nama Anggota Tim")
        
        st.write("---")
        st.write("**Pilih Paket & Person:**")
        paket_list_input = []
        for p_name, p_price in st.session_state.db['master_layanan'].items():
            qty_p = st.number_input(f"Jumlah Person untuk {p_name}", 0, key=f"in_p_{p_name}")
            if qty_p > 0:
                paket_list_input.append({"nama": p_name, "qty": qty_p, "price": p_price})
        
        st.write("---")
        st.write("**Layanan Manual (Kuantitas):**")
        manual_list_input = []
        num_manual = st.number_input("Berapa jenis item manual?", 0, 5)
        for i in range(int(num_manual)):
            cm1, cm2, cm3 = st.columns([2, 1, 1])
            m_n = cm1.text_input(f"Item {i+1}", key=f"mn_{i}")
            m_h = cm2.number_input(f"Harga {i+1}", 0, key=f"mh_{i}")
            m_q = cm3.number_input(f"Qty {i+1}", 1, key=f"mq_{i}")
            if m_n: manual_list_input.append({"nama": m_n, "harga": m_h, "qty": m_q})
            
        dp = st.number_input("DP (Down Payment)", 0)

        if st.form_submit_button("SIMPAN JADWAL"):
            if not paket_list_input and not manual_list_input:
                st.error("Pilih minimal 1 paket atau layanan manual!")
            else:
                new_booking = {
                    "inv_no": f"INV{st.session_state.db['faktur_settings']['next_inv']:04d}",
                    "nama": nama, "wa": wa, "alamat_mu": lokasi, "tgl": tgl_job.strftime("%d/%m/%Y"),
                    "jam_ready": jam_m, "jam_otw": jam_otw, "durasi_otw": durasi_otw,
                    "tim_type": tim_type, "tim_nama": tim_nama,
                    "dp": dp, "paket_list": paket_list_input, "manual_list": manual_list_input, "status": "PENDING"
                }
                st.session_state.db['bookings'].append(new_booking)
                st.session_state.db['faktur_settings']['next_inv'] += 1
                save_data(); st.success("Jadwal Disimpan!"); st.rerun()

# --- 3. PROFIL & SETTING ---
elif menu == "PROFIL & SETTING":
    st.header("👤 Profil & Faktur")
    tab1, tab2 = st.tabs(["Profil MUA", "Setting Faktur & Rekening"])
    with tab1:
        st.session_state.db['profile']['nama'] = st.text_input("Nama Bisnis", st.session_state.db['profile'].get('nama',''))
        st.session_state.db['profile']['hp'] = st.text_input("WhatsApp", st.session_state.db['profile'].get('hp',''))
        st.session_state.db['profile']['ig'] = st.text_input("Instagram", st.session_state.db['profile'].get('ig',''))
        if st.button("Simpan Profil"): save_data(); st.success("Profil Ok!")
    with tab2:
        st.session_state.db['faktur_settings']['bank'] = st.text_input("Bank", st.session_state.db['faktur_settings'].get('bank',''))
        st.session_state.db['faktur_settings']['no_rek'] = st.text_input("No Rekening", st.session_state.db['faktur_settings'].get('no_rek',''))
        st.session_state.db['faktur_settings']['an'] = st.text_input("Atas Nama", st.session_state.db['faktur_settings'].get('an',''))
        st.session_state.db['faktur_settings']['tnc'] = st.text_area("TnC (Unlimited)", st.session_state.db['faktur_settings'].get('tnc',''))
        st.session_state.db['faktur_settings']['thanks'] = st.text_input("Ucapan Terima Kasih", st.session_state.db['faktur_settings'].get('thanks',''))
        st.session_state.db['faktur_settings']['signature'] = st.text_input("Nama Tanda Tangan", st.session_state.db['faktur_settings'].get('signature',''))
        if st.button("Simpan Setting"): save_data(); st.success("Setting Ok!")

# --- 4. LAYANAN & KEUANGAN ---
elif menu == "LAYANAN":
    st.header("💄 Master Layanan")
    n_lay = st.text_input("Nama Paket Baru")
    h_lay = st.number_input("Harga", 0)
    if st.button("Tambah Paket"):
        st.session_state.db['master_layanan'][n_lay] = h_lay
        save_data(); st.rerun()
    st.write("---")
    for n, h in st.session_state.db['master_layanan'].items():
        st.write(f"✅ {n} - Rp {h:,}")

elif menu == "KEUANGAN":
    st.header("💰 Laporan Keuangan")
    bln = st.selectbox("Bulan", [f"{i:02d}" for i in range(1,13)])
    thn = st.selectbox("Tahun", ["2025", "2026"])
    total_omset = 0
    for b in st.session_state.db['bookings']:
        if b['tgl'].split("/")[1] == bln:
            sub = sum([p['price']*p['qty'] for p in b['paket_list']]) + sum([m['harga']*m.get('qty',1) for m in b.get('manual_list',[])])
            st.write(f"- {b['tgl']} | {b['nama']} | Rp {sub:,}")
            total_omset += sub
    st.metric("TOTAL OMSET", f"Rp {total_omset:,}")
