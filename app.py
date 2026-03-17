import streamlit as st
import json
import os
import pandas as pd
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
    .job-card { 
        background-color: white; padding: 20px; border-radius: 15px; 
        margin-bottom: 15px; border-left: 10px solid #F19CBB; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEM DATABASE ---
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
    pdf.cell(0, 10, f"INVOICE {booking['inv_no']}", ln=True, align='C')
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Klien: {booking['nama']}", ln=True)
    pdf.cell(0, 10, f"Tanggal: {booking['tgl']}", ln=True)
    pdf.cell(0, 10, f"Total DP: Rp {booking['dp']:,}", ln=True)
    pdf.cell(0, 10, f"Status: {booking['status']}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("💄 E-Admin Login")
    email = st.text_input("Email", value="elisabethmua18@gmail.com")
    pw = st.text_input("Password", type="password")
    if st.button("MASUK"):
        if email == "elisabethmua18@gmail.com" and pw == "Elis5173":
            st.session_state.auth = True
            st.rerun()
        else: st.error("Email atau Password salah!")
    st.stop()

# --- MENU ---
menu = st.sidebar.radio("MENU", ["BERANDA", "INPUT JADWAL", "LAYANAN", "PROFIL & SETTING", "KEUANGAN"])

if 'input_pakets' not in st.session_state: st.session_state.input_pakets = []
if 'input_manuals' not in st.session_state: st.session_state.input_manuals = []

# --- 1. BERANDA (SEKARANG SUDAH MUNCUL JADWALNYA) ---
if menu == "BERANDA":
    st.header("🌸 Jadwal Elisabeth MUA")
    
    if not st.session_state.db['bookings']:
        st.info("Belum ada jadwal yang disimpan. Silakan ke menu INPUT JADWAL.")
    else:
        # Menampilkan dari yang terbaru diinput
        for i, b in enumerate(reversed(st.session_state.db['bookings'])):
            with st.container():
                st.markdown(f"""
                <div class="job-card">
                    <h3 style="margin:0; color:#F19CBB;">{b['nama']} - {b['inv_no']}</h3>
                    <p style="margin:5px 0;"><b>Tanggal:</b> {b['tgl']} | <b>Jam Ready:</b> {b['jam_ready']}</p>
                    <p style="margin:5px 0;"><b>Lokasi:</b> {b['alamat_mu']}</p>
                    <p style="margin:5px 0;"><b>Tim:</b> {b['tim_type']} ({b['tim_nama']})</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Tombol Download PDF untuk tiap invoice
                pdf_data = create_pdf(b)
                st.download_button(
                    label=f"📄 Download Faktur {b['nama']}",
                    data=pdf_data,
                    file_name=f"Faktur_{b['nama']}.pdf",
                    mime="application/pdf",
                    key=f"pdf_{i}"
                )

# --- 2. INPUT JADWAL ---
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
        master_layanan_list = list(st.session_state.db['master_layanan'].keys())
        col_sel, col_add = st.columns([3, 1])
        selected_p = col_sel.selectbox("Cari Paket Master", ["-- Pilih Paket --"] + master_layanan_list)
        if col_add.button("PILIH PAKET"):
            if selected_p != "-- Pilih Paket --":
                st.session_state.input_pakets.append({"nama": selected_p, "qty": 1, "price": st.session_state.db['master_layanan'][selected_p]})
        
        for i, item in enumerate(st.session_state.input_pakets):
            cp1, cp2, cp3 = st.columns([3, 1, 0.5])
            cp1.markdown(f"**{item['nama']}**")
            item['qty'] = cp2.number_input("Qty", min_value=1, key=f"qty_p_{i}", value=item['qty'])
            if cp3.button("❌", key=f"del_p_{i}"):
                st.session_state.input_pakets.pop(i)
                st.rerun()

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
                st.session_state.input_manuals.pop(j)
                st.rerun()

        st.write("---")
        # NOMOR 11 PINDAH KE DP
        dp_value = st.number_input("11. DP (Down Payment)", min_value=0)
        
        st.write("---")
        # BAGIAN TIM DENGAN 3 OPSI
        st.write("**Hire Tim**")
        hire_tim = st.checkbox("Gunakan Tim Tambahan?")
        if hire_tim:
            ct1, ct2 = st.columns(2)
            tim_type = ct1.selectbox("Jenis Tim", ["Hairdo", "Hijabdo", "Hairdo + Hijabdo"])
            tim_nama = ct2.text_input("Nama Anggota Tim")
        else:
            tim_type = "-"
            tim_nama = "-"

        st.write("---")
        if st.button("💾 SIMPAN JADWAL KE DATABASE"):
            if not nama_klien:
                st.error("Nama Klien wajib diisi!")
            else:
                new_booking = {
                    "inv_no": f"INV{st.session_state.db['faktur_settings'].get('next_inv', 1):04d}",
                    "nama": nama_klien,
                    "tgl": tgl_makeup.strftime("%d/%m/%Y"),
                    "wa": wa_klien,
                    "alamat_mu": alamat_makeup,
                    "jam_ready": f"{jam_m}-{jam_s}",
                    "jam_otw": jam_o,
                    "durasi_otw": durasi_otw,
                    "paket_list": list(st.session_state.input_pakets),
                    "manual_list": list(st.session_state.input_manuals),
                    "hire_tim": hire_tim,
                    "tim_type": tim_type,
                    "tim_nama": tim_nama,
                    "dp": dp_value,
                    "status": "PENDING"
                }
                st.session_state.db['bookings'].append(new_booking)
                st.session_state.db['faktur_settings']['next_inv'] += 1
                save_data()
                st.success(f"Jadwal {nama_klien} Berhasil Disimpan! Silakan cek menu BERANDA.")
                st.session_state.input_pakets = []
                st.session_state.input_manuals = []
                st.rerun()

# --- MENU LAINNYA ---
elif menu == "LAYANAN":
    st.header("💄 Master Layanan Utama")
    with st.form("master"):
        nl = st.text_input("Nama Paket Baru")
        hl = st.number_input("Harga Master", min_value=0)
        if st.form_submit_button("Tambah ke Master"):
            st.session_state.db['master_layanan'][nl] = hl
            save_data(); st.success("Paket tersimpan!"); st.rerun()
    st.write("Daftar Paket Master:")
    st.table(pd.DataFrame(list(st.session_state.db['master_layanan'].items()), columns=['Paket', 'Harga']))

elif menu == "PROFIL & SETTING":
    st.header("👤 Profil & Setting")
    st.info("Menu ini akan digunakan untuk setting Bank dan TnC di revisi berikutnya.")

elif menu == "KEUANGAN":
    st.header("💰 Laporan Keuangan")
    st.write("Data Keuangan akan ditarik dari hasil input jadwal.")
