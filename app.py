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
    .faktur-card {
        background-color: white; padding: 20px; border-radius: 10px; color: black;
    }
    .job-card {
        background-color: white; padding: 15px; border-radius: 10px; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ---
DATA_FILE = "mua_master_pro.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if "pengeluaran" not in data: data["pengeluaran"] = []
            return data
    return {
        "profile": {"nama": "Elisabeth MUA", "alamat": "", "hp": "", "ig": "", "logo_url": ""},
        "faktur_settings": {"tnc": "", "bank": "", "no_rek": "", "an": "", "signature": "", "thanks": "", "next_inv": 1},
        "master_layanan": {}, "bookings": [], "pengeluaran": []
    }

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
    pdf.cell(0, 10, st.session_state.db['profile']['nama'], ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"IG: {st.session_state.db['profile']['ig']} | WA: {st.session_state.db['profile']['hp']}", ln=True, align='C')
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
        pdf.cell(0, 7, f"- {p['nama']} (x{p['qty']}): Rp {sub:,}", ln=True)
        total += sub
    for m in k.get('manual_list', []):
        pdf.cell(0, 7, f"- {m['nama']}: Rp {m['harga']:,}", ln=True)
        total += m['harga']
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, f"TOTAL TAGIHAN: Rp {total:,}", ln=True)
    pdf.cell(0, 7, f"DP / DIBAYAR: Rp {k['dp']:,}", ln=True)
    pdf.set_text_color(255, 0, 0)
    pdf.cell(0, 7, f"SISA SALDO: Rp {total - k['dp']:,}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 5, f"S&K: {st.session_state.db['faktur_settings']['tnc']}")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, st.session_state.db['faktur_settings']['thanks'], ln=True, align='C')
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
    st.header("🌸 Jadwal Elisabeth MUA")
    c1, c2 = st.columns(2)
    d1 = c1.date_input("Dari Tanggal", datetime.now())
    d2 = c2.date_input("Sampai Tanggal", datetime.now())
    
    for idx, b in enumerate(st.session_state.db['bookings']):
        tgl_b = datetime.strptime(b['tgl'], "%d/%m/%Y").date()
        if d1 <= tgl_b <= d2:
            with st.container():
                st.markdown(f"""<div class="job-card"><b>{b['jam_ready']}</b> | <b>{b['nama']}</b><br>{b['tgl']}</div>""", unsafe_allow_html=True)
                col_btn = st.columns(4)
                if col_btn[0].button("LUNAS", key=f"lns{idx}"):
                    st.session_state.db['bookings'][idx]['status'] = "SELESAI"; save_data(); st.rerun()
                if col_btn[1].button("EDIT", key=f"edt{idx}"):
                    st.session_state.edit_idx = idx; st.info("Silakan ke menu Input Jadwal untuk edit.")
                if col_btn[2].button("FAKTUR", key=f"fkt{idx}"):
                    st.session_state.current_fkt = b
                if col_btn[3].button("HAPUS", key=f"del{idx}"):
                    st.session_state.db['bookings'].pop(idx); save_data(); st.rerun()

    if 'current_fkt' in st.session_state:
        k = st.session_state.current_fkt
        st.markdown(f"""<div class="faktur-card"><h3>{st.session_state.db['profile']['nama']}</h3>
        Klien: {k['nama']}<br>Sisa: Rp {sum([p['price']*p['qty'] for p in k['paket_list']]) + sum([m['harga'] for m in k.get('manual_list',[])]) - k['dp']:,}</div>""", unsafe_allow_html=True)
        pdf_data = generate_pdf(k)
        st.download_button("📩 Download PDF", data=pdf_data, file_name=f"Faktur_{k['nama']}.pdf", mime="application/pdf")

# --- 2. INPUT JADWAL ---
elif menu == "INPUT JADWAL":
    st.header("📝 Catat Jadwal")
    with st.form("job_form"):
        nama = st.text_input("Nama Klien")
        wa = st.text_input("WhatsApp")
        lokasi = st.text_input("Lokasi")
        tgl_job = st.date_input("Tanggal Acara", datetime.now())
        
        # Pilihan Jam Pop-up
        times = [time(h, m).strftime("%H:%M") for h in range(24) for m in (0, 15, 30, 45)]
        jam_m = st.selectbox("Jam Mulai", times, index=32)
        jam_s = st.selectbox("Jam Selesai", times, index=40)
        jam_otw = st.selectbox("Jam OTW", times, index=28)
        
        # Multiple Paket
        st.write("**Pilih Paket:**")
        selected_pakets = st.multiselect("Pilih satu atau lebih paket", list(st.session_state.db['master_layanan'].keys()))
        dp = st.number_input("DP (Down Payment)", 0)
        
        # Multiple Manual Item (Simulasi dengan teks dipisah koma)
        st.write("**Item Manual (Gunakan format: Nama-Harga, contoh: Transport-50000):**")
        manual_input = st.text_area("Pisahkan tiap item dengan baris baru")

        if st.form_submit_button("SIMPAN JADWAL"):
            pakets = [{"nama": p, "qty": 1, "price": st.session_state.db['master_layanan'][p]} for p in selected_pakets]
            manuals = []
            if manual_input:
                for line in manual_input.split('\n'):
                    if '-' in line:
                        n, h = line.split('-')
                        manuals.append({"nama": n.strip(), "harga": int(h.strip())})
            
            new_booking = {
                "inv_no": f"INV{st.session_state.db['faktur_settings']['next_inv']:04d}",
                "nama": nama, "wa": wa, "alamat_mu": lokasi, "tgl": tgl_job.strftime("%d/%m/%Y"),
                "jam_ready": f"{jam_m}-{jam_s}", "otw": jam_otw, "dp": dp,
                "paket_list": pakets, "manual_list": manuals, "status": "PENDING"
            }
            st.session_state.db['bookings'].append(new_booking)
            st.session_state.db['faktur_settings']['next_inv'] += 1
            save_data(); st.success("Jadwal Disimpan!")

# --- 3. PROFIL & SETTING ---
elif menu == "PROFIL & SETTING":
    st.header("👤 Profil & Faktur")
    tab1, tab2 = st.tabs(["Profil MUA", "Setting Faktur"])
    with tab1:
        st.session_state.db['profile']['nama'] = st.text_input("Nama Bisnis", st.session_state.db['profile']['nama'])
        st.session_state.db['profile']['hp'] = st.text_input("WhatsApp", st.session_state.db['profile']['hp'])
        st.session_state.db['profile']['ig'] = st.text_input("Username Instagram", st.session_state.db['profile']['ig'])
        st.file_uploader("Upload Logo (Hanya simulasi di Streamlit Cloud)")
        if st.button("Simpan Profil"): save_data(); st.success("Ok!")
    with tab2:
        st.session_state.db['faktur_settings']['tnc'] = st.text_area("Terms & Conditions (Unlimited)", st.session_state.db['faktur_settings']['tnc'])
        st.session_state.db['faktur_settings']['thanks'] = st.text_area("Ucapan Terima Kasih", st.session_state.db['faktur_settings']['thanks'])
        st.session_state.db['faktur_settings']['bank'] = st.text_input("Bank", st.session_state.db['faktur_settings']['bank'])
        st.session_state.db['faktur_settings']['no_rek'] = st.text_input("No Rek", st.session_state.db['faktur_settings']['no_rek'])
        st.session_state.db['faktur_settings']['signature'] = st.text_input("Nama Tanda Tangan", st.session_state.db['faktur_settings']['signature'])
        if st.button("Simpan Setting"): save_data(); st.success("Ok!")

# --- 4. KEUANGAN ---
elif menu == "KEUANGAN":
    st.header("💰 Laporan Keuangan")
    bln = st.selectbox("Bulan", [f"{i:02d}" for i in range(1,13)])
    thn = st.selectbox("Tahun", ["2025", "2026"])
    
    st.subheader("📊 Rincian Omset (Job Masuk)")
    total_omset = 0
    for b in st.session_state.db['bookings']:
        if b['tgl'].split("/")[1] == bln:
            sub = sum([p['price']*p['qty'] for p in b['paket_list']]) + sum([m['harga'] for m in b.get('manual_list',[])])
            st.write(f"- {b['tgl']} | {b['nama']} | Rp {sub:,}")
            total_omset += sub
    
    st.subheader("📉 Rincian Pengeluaran")
    for e in st.session_state.db['pengeluaran']:
        if e['bulan'] == bln:
            st.write(f"- {e['ket']} | Rp {e['nominal']:,}")
