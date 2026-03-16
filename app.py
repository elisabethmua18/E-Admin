import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="E-Admin MUA - Elisabeth", page_icon="💄")

# --- DATABASE LOGIC ---
DATA_FILE = "mua_master_pro.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "profile": {"nama": "Elisabeth MUA", "alamat": "", "hp": "", "ig": "", "logo_url": ""},
        "faktur_settings": {"tnc": "", "bank": "", "no_rek": "", "an": "", "signature": "", "next_inv": 1},
        "master_layanan": {}, "bookings": [], "pengeluaran": []
    }

if 'db' not in st.session_state:
    st.session_state.db = load_data()

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.db, f, indent=4)

# --- LOGIN SESSION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- UI STYLE ---
st.markdown("""
    <style>
    .main { background-color: #F8C8DC; }
    .stButton>button { width: 100%; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN PAGE ---
if not st.session_state.logged_in:
    st.title("💄 E-Admin Login")
    email = st.text_input("Email", value="elisabeth@mua.id")
    password = st.text_input("Password", type="password", help="Elis5173")
    if st.button("MASUK"):
        if email == "elisabeth@mua.id" and password == "Elis5173":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Email atau Password salah!")
    st.stop()

# --- SIDEBAR NAVIGASI ---
menu = st.sidebar.radio("Navigasi", ["Dashboard", "Input Jadwal", "Layanan", "Profil & Setting", "Keuangan (NETT)"])

# --- DASHBOARD ---
if menu == "Dashboard":
    st.title(f"🌸 Dashboard {st.session_state.db['profile']['nama']}")
    
    col1, col2 = st.columns(2)
    tgl_start = col1.date_input("Dari Tanggal", datetime.now())
    tgl_end = col2.date_input("Sampai Tanggal", datetime.now())

    if st.button("Hapus Job Massal (Rentang di atas)", type="secondary"):
        st.session_state.db['bookings'] = [b for b in st.session_state.db['bookings'] if not (tgl_start.strftime("%d/%m/%Y") <= b['tgl'] <= tgl_end.strftime("%d/%m/%Y"))]
        save_data()
        st.success("Data berhasil dibersihkan")
        st.rerun()

    st.divider()
    
    for idx, b in enumerate(st.session_state.db['bookings']):
        b_tgl_dt = datetime.strptime(b['tgl'], "%d/%m/%Y").date()
        if tgl_start <= b_tgl_dt <= tgl_end:
            status = "✅ LUNAS" if b.get('status') == "SELESAI" else "⏳ PENDING"
            with st.container():
                st.subheader(f"{b['jam_ready']} | {b['nama']}")
                st.text(f"Lokasi: {b['alamat_mu']} | Status: {status}")
                c1, c2, c3 = st.columns(3)
                if b.get('status') != "SELESAI":
                    if c1.button("Set LUNAS", key=f"lns_{idx}"):
                        st.session_state.db['bookings'][idx]['status'] = "SELESAI"
                        save_data(); st.rerun()
                if c2.button("Detail Faktur", key=f"fkt_{idx}"):
                    st.session_state.current_faktur = b
                    st.info(f"Faktur #{b['inv_no']} untuk {b['nama']} siap dicetak.")
                if c3.button("Hapus", key=f"del_{idx}"):
                    st.session_state.db['bookings'].pop(idx)
                    save_data(); st.rerun()
                st.caption(f"--- OTW Lokasi Berikutnya: {b['otw']} ---")

# --- INPUT JADWAL ---
elif menu == "Input Jadwal":
    st.title("📝 Input Jadwal Baru")
    with st.form("input_form"):
        nama = st.text_input("Nama Klien")
        wa = st.text_input("WhatsApp Klien")
        lokasi = st.text_input("Alamat Lokasi")
        tgl = st.date_input("Tanggal", datetime.now())
        jam = st.text_input("Jam Mulai-Selesai", "08:00-10:00")
        otw = st.text_input("Info OTW", "07:00 (30m)")
        dp = st.number_input("Jumlah DP", min_value=0)
        paket = st.selectbox("Pilih Paket", list(st.session_state.db['master_layanan'].keys()) if st.session_state.db['master_layanan'] else ["Default"])
        
        submitted = st.form_submit_state = st.form_submit_button("SIMPAN JADWAL")
        if submitted:
            new_booking = {
                "inv_no": f"INV{st.session_state.db['faktur_settings']['next_inv']:04d}",
                "nama": nama, "wa": wa, "alamat_mu": lokasi, "tgl": tgl.strftime("%d/%m/%Y"),
                "jam_ready": jam, "otw": otw, "dp": dp,
                "paket_list": [{"nama": paket, "qty": 1, "price": st.session_state.db['master_layanan'].get(paket, 0)}],
                "manual_list": [], "status": "PENDING"
            }
            st.session_state.db['bookings'].append(new_booking)
            st.session_state.db['faktur_settings']['next_inv'] += 1
            save_data()
            st.success("Jadwal tersimpan!")

# --- KEUANGAN ---
elif menu == "Keuangan (NETT)":
    st.title("💰 Laporan Keuangan")
    bln = st.selectbox("Bulan", [f"{i:02d}" for i in range(1, 13)], index=int(datetime.now().month)-1)
    thn = st.selectbox("Tahun", ["2025", "2026"], index=1)
    
    omset = 0
    for b in st.session_state.db['bookings']:
        if b['tgl'].split("/")[1] == bln and b['tgl'].split("/")[2] == thn:
            total_inv = sum([p['price'] for p in b['paket_list']])
            omset += total_inv if b.get('status') == "SELESAI" else b['dp']
    
    exp = sum([x['nominal'] for x in st.session_state.db['pengeluaran'] if x['bulan'] == bln and x['tahun'] == thn])
    
    st.metric("Total Omset (Selesai + DP)", f"Rp {omset:,}")
    st.metric("Total Pengeluaran", f"Rp {exp:,}")
    st.metric("NETT PROFIT", f"Rp {omset-exp:,}")
    
    st.divider()
    with st.expander("Input Pengeluaran Baru"):
        ket = st.text_input("Keterangan")
        nom = st.number_input("Nominal", min_value=0)
        if st.button("Tambah Pengeluaran"):
            st.session_state.db['pengeluaran'].append({"ket": ket, "nominal": nom, "bulan": bln, "tahun": thn})
            save_data(); st.rerun()

# --- PROFIL ---
elif menu == "Profil & Setting":
    st.title("⚙️ Pengaturan")
    st.session_state.db['profile']['nama'] = st.text_input("Nama MUA", st.session_state.db['profile']['nama'])
    st.session_state.db['profile']['hp'] = st.text_input("No HP", st.session_state.db['profile']['hp'])
    st.session_state.db['faktur_settings']['no_rek'] = st.text_input("No Rekening", st.session_state.db['faktur_settings']['no_rek'])
    if st.button("SIMPAN PERUBAHAN"):
        save_data(); st.success("Tersimpan!")

# --- LAYANAN ---
elif menu == "Layanan":
    st.title("💄 Master Layanan")
    n_pkt = st.text_input("Nama Paket Baru")
    h_pkt = st.number_input("Harga", min_value=0)
    if st.button("Tambah Paket"):
        st.session_state.db['master_layanan'][n_pkt] = h_pkt
        save_data(); st.rerun()
    st.table(pd.DataFrame(list(st.session_state.db['master_layanan'].items()), columns=['Paket', 'Harga']))
