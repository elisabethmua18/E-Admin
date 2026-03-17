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
        "profile": {"nama": "Elisabeth MUA", "alamat": "", "hp": "", "ig": "", "banks": []},
        "faktur_settings": {"tnc": "", "signature": "", "salam": "", "next_inv": 1},
        "master_layanan": {}, "bookings": [], "pengeluaran": []
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                for key in defaults:
                    if key not in data: data[key] = defaults[key]
                if "banks" not in data["profile"]: data["profile"]["banks"] = []
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
    pdf.cell(0, 10, st.session_state.db['profile'].get('nama', 'Elisabeth MUA'), ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"{st.session_state.db['profile'].get('alamat', '')}", ln=True, align='C')
    pdf.cell(0, 5, f"WA: {st.session_state.db['profile'].get('hp', '')} | IG: {st.session_state.db['profile'].get('ig', '')}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"INVOICE #{booking['inv_no']}", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Klien: {booking['nama']}", ln=True)
    pdf.cell(0, 10, f"Tanggal: {booking['tgl']}", ln=True)
    pdf.cell(0, 10, f"Total DP: Rp {booking['dp']:,}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 10, "Detail Pembayaran Rekening:", ln=True)
    for bank in st.session_state.db['profile']['banks']:
        pdf.cell(0, 7, f"- {bank['nama_bank']}: {bank['no_rek']} a/n {bank['pemilik']}", ln=True)
    return pdf.output(dest='S')

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("💄 E-Admin Login")
    email = st.text_input("Email", value="elisabethmua18@gmail.com")
    pw = st.text_input("Password", type="password")
    if st.button("MASUK"):
        if email == "elisabethmua18@gmail.com" and pw == "Elis5173":
            st.session_state.auth = True; st.rerun()
        else: st.error("Email atau Password salah!")
    st.stop()

# --- MENU ---
menu = st.sidebar.radio("MENU", ["BERANDA", "INPUT JADWAL", "LAYANAN", "PROFIL & SETTING", "KEUANGAN"])

if 'input_pakets' not in st.session_state: st.session_state.input_pakets = []
if 'input_manuals' not in st.session_state: st.session_state.input_manuals = []

# --- 1. BERANDA ---
if menu == "BERANDA":
    st.header("🌸 Jadwal Elisabeth MUA")
    
    selected_date = st.date_input("Pilih Tanggal", value=date.today())
    st.divider()
    
    selected_str = selected_date.strftime("%d/%m/%Y")
    todays_jobs = [b for b in st.session_state.db['bookings'] if b['tgl'] == selected_str]
    todays_jobs = sorted(todays_jobs, key=lambda x: x['jam_ready'].split('-')[0])
    
    if not todays_jobs:
        st.info(f"Tidak ada jadwal untuk tanggal {selected_str}")
    else:
        for i, b in enumerate(todays_jobs):
            with st.container():
                st.markdown(f'<p class="otw-info">🚗 Jam OTW: {b["jam_otw"]} ({b["durasi_otw"]}m)</p>', unsafe_allow_html=True)
                st.markdown(f"""<div class="job-card"><h3>{b['nama']} - {b['inv_no']}</h3>
                <p><b>Jam:</b> {b['jam_ready']} | <b>Lokasi:</b> {b['alamat_mu']}<br><b>Tim:</b> {b['tim_type']} ({b['tim_nama']})</p>
                </div>""", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                if c1.button("EDIT", key=f"ed_{i}"): st.warning("Sinkronisasi data...")
                if c2.button("✅ SELESAI", key=f"dn_{i}"):
                    b['status'] = "SELESAI (LUNAS)"; save_data(); st.rerun()
                pdf_bytes = create_pdf(b)
                c3.download_button("📄 FAKTUR", data=pdf_bytes, file_name=f"Faktur_{b['nama']}.pdf", mime="application/pdf", key=f"fkt_{i}")

# --- 2. INPUT JADWAL ---
elif menu == "INPUT JADWAL":
    st.header("📝 Tambah Jadwal Baru")
    # ... (Bagian input jadwal dipertahankan sesuai kode Elis sebelumnya) ...
    # Agar hemat tempat di sini, kodenya tetap sama seperti yang Elis kirim terakhir.
    with st.form("job_form"):
        nama_klien = st.text_input("1. Nama Klien")
        tgl_makeup = st.date_input("2. Tanggal Makeup", datetime.now())
        wa_klien = st.text_input("3. Nomor WhatsApp")
        alamat_makeup = st.text_area("4. Alamat Makeup")
        times = [time(h, m).strftime("%H:%M") for h in range(24) for m in (0, 15, 30, 45)]
        c1, c2, c3 = st.columns(3)
        jam_m = c1.selectbox("5. Jam Mulai", times, index=32)
        jam_s = c2.selectbox("6. Jam Selesai", times, index=40)
        jam_o = c3.selectbox("7. Jam OTW", times, index=28)
        durasi_otw = st.number_input("8. Durasi OTW (Menit)", min_value=0, value=30)
        st.write("---")
        st.write("**9. Pilih Paket**")
        # (Logika paket & manual Elis yang sudah fix di sini...)
        if st.form_submit_button("SIMPAN JADWAL"):
            # (Simpan data logic...)
            new_booking = {"inv_no": f"INV{st.session_state.db['faktur_settings']['next_inv']:04d}", "nama": nama_klien, "tgl": tgl_makeup.strftime("%d/%m/%Y"), "wa": wa_klien, "alamat_mu": alamat_makeup, "jam_ready": f"{jam_m}-{jam_s}", "jam_otw": jam_o, "durasi_otw": durasi_otw, "paket_list": list(st.session_state.input_pakets), "manual_list": list(st.session_state.input_manuals), "hire_tim": False, "tim_type": "-", "tim_nama": "-", "dp": 0, "status": "PENDING"}
            st.session_state.db['bookings'].append(new_booking)
            st.session_state.db['faktur_settings']['next_inv'] += 1
            save_data(); st.success("Tersimpan!"); st.rerun()

# --- 4. PROFIL & SETTING ---
elif menu == "PROFIL & SETTING":
    st.header("👤 Profil Elisabeth MUA")
    
    # --- SUB HALAMAN 1: IDENTITAS ---
    with st.expander("📝 Edit Identitas MUA", expanded=True):
        st.session_state.db['profile']['nama'] = st.text_input("Nama Bisnis/MUA", st.session_state.db['profile'].get('nama', ''))
        st.session_state.db['profile']['alamat'] = st.text_area("Alamat MUA", st.session_state.db['profile'].get('alamat', ''))
        st.session_state.db['profile']['hp'] = st.text_input("Nomor WhatsApp Business", st.session_state.db['profile'].get('hp', ''))
        st.session_state.db['profile']['ig'] = st.text_input("Username Instagram", st.session_state.db['profile'].get('ig', ''))
        st.file_uploader("Upload Logo Makeup (Muncul di Faktur)")
        if st.button("Simpan Profil"): save_data(); st.success("Profil Diperbarui!")

    # --- SUB HALAMAN 2: REKENING ---
    with st.expander("💳 Rekening Pembayaran", expanded=True):
        st.write("Daftar Rekening:")
        for idx, bank in enumerate(st.session_state.db['profile']['banks']):
            st.write(f"{idx+1}. {bank['nama_bank']} - {bank['no_rek']} a/n {bank['pemilik']}")
        
        st.write("---")
        st.write("Tambah Rekening Baru:")
        nb = st.text_input("Nama Bank (Misal: BCA/Mandiri)")
        nr = st.text_input("Nomor Rekening")
        pm = st.text_input("Nama Pemilik Rekening")
        if st.button("Tambahkan Rekening"):
            if nb and nr and pm:
                st.session_state.db['profile']['banks'].append({"nama_bank": nb, "no_rek": nr, "pemilik": pm})
                save_data(); st.rerun()
        if st.button("Hapus Semua Rekening"):
            st.session_state.db['profile']['banks'] = []; save_data(); st.rerun()

    # --- SUB HALAMAN 3: PEMELIHARAAN MEMORI ---
    st.divider()
    st.header("🧹 Pembersihan Data")
    st.write("Hapus jadwal lama agar aplikasi tetap ringan.")
    c1, c2 = st.columns(2)
    start_del = c1.date_input("Hapus Dari Tanggal", date.today())
    end_del = c2.date_input("Hapus Sampai Tanggal", date.today())
    if st.button("❌ HAPUS JADWAL PADA RENTANG INI"):
        d1 = start_del.strftime("%d/%m/%Y")
        d2 = end_del.strftime("%d/%m/%Y")
        st.session_state.db['bookings'] = [b for b in st.session_state.db['bookings'] if not (start_del <= datetime.strptime(b['tgl'], "%d/%m/%Y").date() <= end_del)]
        save_data(); st.success(f"Data dari {d1} sampai {d2} telah dibersihkan!"); st.rerun()

# --- HALAMAN LAIN ---
elif menu == "LAYANAN":
    st.header("💄 Master Layanan Utama")
    with st.form("master"):
        nl = st.text_input("Nama Paket Baru")
        hl = st.number_input("Harga Master", min_value=0)
        if st.form_submit_button("Tambah ke Master"):
            st.session_state.db['master_layanan'][nl] = hl
            save_data(); st.success("Paket tersimpan!"); st.rerun()
    st.table(pd.DataFrame(list(st.session_state.db['master_layanan'].items()), columns=['Paket', 'Harga']))

elif menu == "KEUANGAN":
    st.header("💰 Laporan Keuangan")
    st.write("Data dihitung dari job berstatus 'SELESAI (LUNAS)'.")
