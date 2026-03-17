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
        margin-bottom: 5px; border-left: 10px solid #F19CBB; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .otw-info {
        color: #777; font-style: italic; font-size: 0.9em; margin: 5px 0 20px 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEM DATABASE ---
DATA_FILE = "mua_master_pro.json"

def load_data():
    defaults = {
        "profile": {"nama": "Elisabeth MUA", "alamat": "", "hp": "", "ig": "", "bank": "", "no_rek": "", "an": ""},
        "faktur_settings": {"tnc": "", "signature": "", "salam": "", "next_inv": 1},
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

# --- FUNGSI DOWNLOAD PDF ---
def create_pdf(booking):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, st.session_state.db['profile'].get('nama', 'Elisabeth MUA'), ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, st.session_state.db['profile'].get('alamat', ''), ln=True, align='C')
    pdf.cell(0, 5, f"WA: {st.session_state.db['profile'].get('hp', '')} | IG: {st.session_state.db['profile'].get('ig', '')}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"INVOICE #{booking['inv_no']}", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Klien: {booking['nama']}", ln=True)
    pdf.cell(0, 8, f"Tanggal Acara: {booking['tgl']}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, "RINCIAN LAYANAN:", ln=True, border='B')
    pdf.set_font("Arial", "", 10)
    total_tagihan = 0
    for p in booking.get('paket_list', []):
        sub = p['price'] * p['qty']
        pdf.cell(0, 7, f"- {p['nama']} (x{p['qty']}): Rp {sub:,}", ln=True)
        total_tagihan += sub
    for m in booking.get('manual_list', []):
        sub_m = m['harga'] * m.get('qty', 1)
        pdf.cell(0, 7, f"- {m['nama']} (x{m.get('qty', 1)}): Rp {sub_m:,}", ln=True)
        total_tagihan += sub_m
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, f"TOTAL TAGIHAN: Rp {total_tagihan:,}", ln=True)
    pdf.cell(0, 8, f"DP / SUDAH DIBAYAR: Rp {booking['dp']:,}", ln=True)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 8, f"SISA SALDO: Rp {total_tagihan - booking['dp']:,}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, f"PEMBAYARAN VIA: {st.session_state.db['profile'].get('bank', '')} {st.session_state.db['profile'].get('no_rek', '')}", ln=True)
    pdf.cell(0, 6, f"A/N: {st.session_state.db['profile'].get('an', '')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, f"TnC: {st.session_state.db['faktur_settings'].get('tnc', '')}")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 10, st.session_state.db['faktur_settings'].get('salam', ''), ln=True, align='C')
    pdf.ln(5)
    pdf.cell(0, 8, st.session_state.db['faktur_settings'].get('signature', ''), ln=True, align='R')
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
        else: st.error("Akses Ditolak!")
    st.stop()

# --- MENU ---
menu = st.sidebar.radio("MENU", ["BERANDA", "INPUT JADWAL", "LAYANAN", "PROFIL & SETTING", "KEUANGAN"])

if 'input_pakets' not in st.session_state: st.session_state.input_pakets = []
if 'input_manuals' not in st.session_state: st.session_state.input_manuals = []

# --- 1. BERANDA (REVISI URUTAN JAM & POSISI MOBIL) ---
if menu == "BERANDA":
    st.header("🌸 Jadwal Elisabeth MUA")
    selected_date = st.date_input("Pilih Tanggal", value=date.today(), key="calendar_input")
    st.divider()
    
    selected_str = selected_date.strftime("%d/%m/%Y")
    
    # FILTER SEMUA JOB DI TANGGAL TERSEBUT
    list_job = [b for b in st.session_state.db['bookings'] if b['tgl'] == selected_str]
    
    # URUTKAN BERDASARKAN JAM MULAI (Paling Pagi)
    list_job = sorted(list_job, key=lambda x: x.get('jam_ready', '00:00').split('-')[0])
    
    if not list_job:
        st.info(f"Tidak ada jadwal untuk tanggal {selected_str}")
    else:
        for i, b in enumerate(list_job):
            with st.container():
                # Tampilan Schedule
                st.markdown(f"""
                <div class="job-card">
                    <h3 style="margin:0; color:#F19CBB;">{b['nama']} - {b['inv_no']}</h3>
                    <p style="margin:5px 0;"><b>Jam Kerja:</b> {b.get('jam_ready','-')} | <b>Lokasi:</b> {b.get('alamat_mu','-')}</p>
                    <p style="margin:5px 0;"><b>Tim:</b> {b.get('tim_type','-')} ({b.get('tim_nama','-')})</p>
                    <p style="margin:5px 0;"><b>Status:</b> {b.get('status','PENDING')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # POSISI INFO OTW (DI BAWAH SCHEDULE)
                st.markdown(f'<p class="otw-info">🚗 Jam OTW: {b.get("jam_otw","-")} (Durasi: {b.get("durasi_otw","-")} menit)</p>', unsafe_allow_html=True)
                
                # TOMBOL-TOMBOL
                c1, c2, c3 = st.columns(3)
                if c1.button("EDIT", key=f"ed_{i}"): st.warning("Fitur edit sinkron...")
                if c2.button("✅ SELESAI (LUNAS)", key=f"dn_{i}"):
                    b['status'] = "SELESAI (LUNAS)"; save_data(); st.rerun()
                
                # TOMBOL FAKTUR PDF
                pdf_bytes = create_pdf(b)
                c3.download_button("📄 FAKTUR", data=pdf_bytes, file_name=f"Faktur_{b['nama']}.pdf", mime="application/pdf", key=f"dl_{i}")

# --- 2. INPUT JADWAL (TIDAK BERUBAH) ---
elif menu == "INPUT JADWAL":
    st.header("📝 Tambah Jadwal Baru")
    with st.container():
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
        master_list = list(st.session_state.db['master_layanan'].keys())
        col_sel, col_add = st.columns([3, 1])
        selected_p = col_sel.selectbox("Cari Paket Master", ["-- Pilih Paket --"] + master_list)
        if col_add.button("PILIH PAKET"):
            if selected_p != "-- Pilih Paket --":
                st.session_state.input_pakets.append({"nama": selected_p, "qty": 1, "price": st.session_state.db['master_layanan'][selected_p]})
        for i, item in enumerate(st.session_state.input_pakets):
            cp1, cp2, cp3 = st.columns([3, 1, 0.5])
            cp1.markdown(f"**{item['nama']}**")
            item['qty'] = cp2.number_input("Qty", min_value=1, key=f"qty_p_{i}", value=item['qty'])
            if cp3.button("❌", key=f"del_p_{i}"):
                st.session_state.input_pakets.pop(i); st.rerun()
        st.write("---")
        st.write("**10. Layanan Tambahan Manual**")
        if st.button("TAMBAH LAYANAN MANUAL"):
            st.session_state.input_manuals.append({"nama": "", "harga": 0, "qty": 1})
        for j, item_m in enumerate(st.session_state.input_manuals):
            cm1, cm2, cm3, cm4 = st.columns([2, 1, 1, 0.5])
            item_m['nama'] = cm1.text_input("Keterangan", key=f"m_nama_{j}", value=item_m['nama'])
            item_m['harga'] = cm2.number_input("Harga", min_value=0, key=f"m_harga_{j}", value=item_m['harga'])
            item_m['qty'] = cm3.number_input("Qty", min_value=1, key=f"m_qty_{j}", value=item_m['qty'])
            if cm4.button("❌", key=f"del_m_{j}"):
                st.session_state.input_manuals.pop(j); st.rerun()
        st.write("---")
        dp_value = st.number_input("11. DP (Down Payment)", min_value=0)
        st.write("---")
        st.write("**Hire Tim**")
        hire_tim = st.checkbox("Gunakan Tim Tambahan?")
        if hire_tim:
            ct1, ct2 = st.columns(2)
            tim_type = ct1.selectbox("Jenis Tim", ["Hairdo", "Hijabdo", "Hairdo + Hijabdo"])
            tim_nama = ct2.text_input("Nama Anggota Tim")
        else:
            tim_type = "-"; tim_nama = "-"
        st.write("---")
        if st.button("💾 SIMPAN JADWAL KE DATABASE"):
            if not nama_klien: st.error("Nama Klien wajib diisi!")
            else:
                new_booking = {"inv_no": f"INV{st.session_state.db['faktur_settings'].get('next_inv', 1):04d}", "nama": nama_klien, "tgl": tgl_makeup.strftime("%d/%m/%Y"), "wa": wa_klien, "alamat_mu": alamat_makeup, "jam_ready": f"{jam_m}-{jam_s}", "jam_otw": jam_o, "durasi_otw": durasi_otw, "paket_list": list(st.session_state.input_pakets), "manual_list": list(st.session_state.input_manuals), "hire_tim": hire_tim, "tim_type": tim_type, "tim_nama": tim_nama, "dp": dp_value, "status": "PENDING"}
                st.session_state.db['bookings'].append(new_booking)
                st.session_state.db['faktur_settings']['next_inv'] += 1
                save_data(); st.success(f"Jadwal {nama_klien} Berhasil!"); st.session_state.input_pakets = []; st.session_state.input_manuals = []; st.rerun()

# --- 3. LAYANAN (TETAP SAMA) ---
elif menu == "LAYANAN":
    st.header("💄 Master Layanan Utama")
    with st.form("master"):
        nl = st.text_input("Nama Paket Baru")
        hl = st.number_input("Harga Master", min_value=0)
        if st.form_submit_button("Tambah ke Master"):
            st.session_state.db['master_layanan'][nl] = hl; save_data(); st.rerun()
    st.table(pd.DataFrame(list(st.session_state.db['master_layanan'].items()), columns=['Paket', 'Harga']))

# --- 4. PROFIL & SETTING (TETAP SAMA) ---
elif menu == "PROFIL & SETTING":
    st.header("👤 Profil & Setting Faktur")
    t_prof, t_set = st.tabs(["PROFIL", "SETTING"])
    with t_prof:
        st.subheader("📝 Data Identitas & Bank")
        st.session_state.db['profile']['nama'] = st.text_input("Nama MUA", st.session_state.db['profile'].get('nama', ''))
        st.session_state.db['profile']['alamat'] = st.text_area("Alamat MUA", st.session_state.db['profile'].get('alamat', ''))
        st.session_state.db['profile']['hp'] = st.text_input("No WA MUA", st.session_state.db['profile'].get('hp', ''))
        st.session_state.db['profile']['ig'] = st.text_input("Akun IG MUA", st.session_state.db['profile'].get('ig', ''))
        st.file_uploader("Upload Logo MUA (.png)", type=["png"])
        st.divider()
        st.session_state.db['profile']['bank'] = st.text_input("Nama Bank", st.session_state.db['profile'].get('bank', ''))
        st.session_state.db['profile']['no_rek'] = st.text_input("No Rekening", st.session_state.db['profile'].get('no_rek', ''))
        st.session_state.db['profile']['an'] = st.text_input("Nama Pemilik Rekening", st.session_state.db['profile'].get('an', ''))
        if st.button("💾 SIMPAN PROFIL"): save_data(); st.success("Profil Berhasil Disimpan!")
    with t_set:
        st.subheader("⚙️ Aturan Faktur")
        st.session_state.db['faktur_settings']['tnc'] = st.text_area("Terms & Conditions (TnC)", st.session_state.db['faktur_settings'].get('tnc', ''), height=200)
        st.session_state.db['faktur_settings']['salam'] = st.text_area("Salam Penutup", st.session_state.db['faktur_settings'].get('salam', ''), height=100)
        st.session_state.db['faktur_settings']['signature'] = st.text_input("Signature (Tanda Tangan)", st.session_state.db['faktur_settings'].get('signature', ''))
        if st.button("💾 SIMPAN SETTING"): save_data(); st.success("Setting Berhasil Disimpan!")

elif menu == "KEUANGAN":
    st.header("💰 Laporan Keuangan")
    st.write("Dihitung dari job LUNAS.")
