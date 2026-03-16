import streamlit as st
import json
import os
from datetime import datetime

# --- SETTING DASAR ---
st.set_page_config(page_title="E-Admin MUA - Elisabeth", layout="centered")

# --- WARNA PINK KHAS ELIS ---
st.markdown("""
    <style>
    .stApp { background-color: #F8C8DC; }
    div.stButton > button {
        background-color: #F19CBB; color: white;
        border-radius: 10px; height: 3em; width: 100%;
        border: none; font-weight: bold;
    }
    .job-card {
        background-color: white; padding: 15px;
        border-radius: 15px; margin-bottom: 10px;
        border-left: 5px solid #F19CBB;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ---
DATA_FILE = "mua_master_pro.json"
def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: return json.load(f)
    return {"profile": {"nama": "Elisabeth MUA"}, "master_layanan": {}, "bookings": [], "faktur_settings": {"next_inv": 1}}

if 'db' not in st.session_state:
    st.session_state.db = load_db()

def save_db():
    with open(DATA_FILE, "w") as f: json.dump(st.session_state.db, f, indent=4)

# --- LOGIN ---
if 'login' not in st.session_state: st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 LOGIN E-ADMIN")
    user = st.text_input("Email", "elisabeth@mua.id")
    pw = st.text_input("Password", type="password")
    if st.button("MASUK"):
        if user == "elisabeth@mua.id" and pw == "Elis5173":
            st.session_state.login = True
            st.rerun()
        else: st.error("Salah!")
    st.stop()

# --- NAVIGASI ---
menu = st.sidebar.selectbox("MENU", ["BERANDA", "INPUT JADWAL", "LAYANAN", "PROFIL", "PENGHASILAN"])

if menu == "BERANDA":
    st.header(f"🌸 Dashboard: {st.session_state.db['profile']['nama']}")
    
    col1, col2 = st.columns(2)
    d1 = col1.date_input("Dari", datetime.now())
    d2 = col2.date_input("Sampai", datetime.now())
    
    st.divider()
    
    for idx, b in enumerate(st.session_state.db['bookings']):
        tgl_b = datetime.strptime(b['tgl'], "%d/%m/%Y").date()
        if d1 <= tgl_b <= d2:
            with st.container():
                st.markdown(f"""
                <div class="job-card">
                    <b style="color:blue; font-size:18px;">{b['jam_ready']}</b><br>
                    <b>{b['nama']}</b> {'[LUNAS]' if b.get('status') == 'SELESAI' else ''}<br>
                    <small>{b['tgl']} | {b['paket_list'][0]['nama']}</small><br>
                    <i style="color:grey; font-size:12px;">--- [ OTW ] {b['otw']} ---</i>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                if b.get('status') != "SELESAI":
                    if c1.button("LUNAS", key=f"l{idx}"):
                        st.session_state.db['bookings'][idx]['status'] = "SELESAI"
                        save_db(); st.rerun()
                if c2.button("FAKTUR", key=f"f{idx}"):
                    st.info(f"Faktur {b['inv_no']} siap cetak (Fitur ini akan muncul di update selanjutnya)")
                if c3.button("HAPUS", key=f"h{idx}"):
                    st.session_state.db['bookings'].pop(idx)
                    save_db(); st.rerun()

elif menu == "INPUT JADWAL":
    st.header("📝 Tambah Jadwal")
    with st.form("in"):
        nama = st.text_input("Nama Klien")
        lokasi = st.text_input("Lokasi")
        tgl = st.date_input("Tanggal")
        jam = st.text_input("Jam (Mulai-Selesai)", "08:00-10:00")
        otw = st.text_input("OTW", "07:00 (30m)")
        dp = st.number_input("DP", 0)
        layanan = st.selectbox("Paket", list(st.session_state.db['master_layanan'].keys()) if st.session_state.db['master_layanan'] else ["Default"])
        if st.form_submit_button("SIMPAN JADWAL"):
            new = {"inv_no": f"INV{st.session_state.db['faktur_settings'].get('next_inv', 1):04d}", "nama": nama, "alamat_mu": lokasi, "tgl": tgl.strftime("%d/%m/%Y"), "jam_ready": jam, "otw": otw, "dp": dp, "paket_list": [{"nama": layanan, "price": st.session_state.db['master_layanan'].get(layanan, 0)}], "status": "PENDING"}
            st.session_state.db['bookings'].append(new)
            st.session_state.db['faktur_settings']['next_inv'] = st.session_state.db['faktur_settings'].get('next_inv', 1) + 1
            save_db(); st.success("Tersimpan!"); st.rerun()

# --- BAGIAN LAINNYA ---
elif menu == "LAYANAN":
    st.header("💄 Master Layanan")
    n = st.text_input("Nama Paket")
    h = st.number_input("Harga", 0)
    if st.button("TAMBAH"):
        st.session_state.db['master_layanan'][n] = h
        save_db(); st.rerun()
    st.write(st.session_state.db['master_layanan'])

elif menu == "PROFIL":
    st.header("👤 Profil MUA")
    st.session_state.db['profile']['nama'] = st.text_input("Nama Bisnis", st.session_state.db['profile']['nama'])
    if st.button("SIMPAN"): save_db(); st.success("Ok!")
