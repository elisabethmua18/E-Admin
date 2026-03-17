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
        padding: 10px 20px; border-radius: 10px; opacity: 0.4; pointer-events: none;
    }
    .otw-info {
        color: #777; font-style: italic; font-size: 0.9em; margin: 5px 0 20px 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEM DATABASE ---
DATA_FILE = "mua_master_pro.json"

def load_data():
    initial_bookings = [
        {"inv_no": "INV0005", "nama": "Kak Angel", "tgl": "17/03/2026", "wa": "08xxxx", "alamat_mu": "Tembalang", "jam_ready": "14:00-16:00", "jam_otw": "16:15", "durasi_otw": 15, "paket_list": [], "manual_list": [], "hire_tim": True, "tim_type": "Hairdo", "tim_nama": "Selly", "dp": 0, "status": "PENDING"},
        {"inv_no": "INV0006", "nama": "Kak Reyki", "tgl": "17/03/2026", "wa": "08xxxx", "alamat_mu": "Hotel Aruman", "jam_ready": "13:00-15:00", "jam_otw": "12:15", "durasi_otw": 30, "paket_list": [], "manual_list": [], "hire_tim": True, "tim_type": "Hairdo", "tim_nama": "Ovie", "dp": 0, "status": "PENDING"}
    ]
    defaults = {
        "profile": {"nama": "Elisabeth MUA", "alamat": "", "hp": "", "ig": "", "bank": "", "no_rek": "", "an": ""},
        "faktur_settings": {"tnc": "", "signature": "", "salam": "", "next_inv": 7},
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

# --- 1. BERANDA (REVISI LOGO & EDIT & LUNAS) ---
if menu == "BERANDA":
    st.header("🌸 Jadwal Elisabeth MUA")
    selected_date = st.date_input("Pilih Tanggal", value=date(2026, 3, 17))
    st.divider()
    
    selected_str = selected_date.strftime("%d/%m/%Y")
    list_job = [b for b in st.session_state.db['bookings'] if b['tgl'] == selected_str]
    list_job = sorted(list_job, key=lambda x: x.get('jam_ready', '00:00').split('-')[0])
    
    if not list_job:
        st.info(f"Tidak ada jadwal.")
    else:
        for i, b in enumerate(list_job):
            with st.container():
                st.markdown(f"""
                <div class="job-card">
                    <h3 style="margin:0; color:#F19CBB;">{b['nama']} - {b['inv_no']}</h3>
                    <p style="margin:5px 0;"><b>Jam Kerja:</b> {b['jam_ready']} | <b>Lokasi:</b> {b['alamat_mu']}</p>
                    <p style="margin:5px 0;"><b>Tim:</b> {b['tim_type']} ({b['tim_nama']})</p>
                    <p style="margin:5px 0;"><b>Status:</b> {b.get('status','PENDING')}</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f'<p class="otw-info">🚗 Jam OTW: {b["jam_otw"]} ({b["durasi_otw"]}m)</p>', unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                # EDIT MENGARAH KE INPUT JADWAL
                if c1.button("EDIT", key=f"ed_{i}"):
                    st.info("Alihkan ke menu INPUT JADWAL...")
                    # Simulasikan pindah menu di Streamlit
                    st.session_state.edit_mode = b
                    st.warning("Silakan klik 'INPUT JADWAL' di menu samping.")
                
                # TOMBOL SELESAI (UBAH STATUS & SIMPAN KE KEUANGAN)
                if c2.button("✅ SELESAI", key=f"dn_{i}"):
                    b['status'] = "SELESAI (LUNAS)"
                    save_data()
                    st.success(f"Status {b['nama']} diperbarui ke LUNAS!")
                    st.rerun()
                
                if c3.button("📄 FAKTUR", key=f"fkt_{i}"):
                    st.session_state.current_faktur = b

    if 'current_faktur' in st.session_state:
        f = st.session_state.current_faktur
        p = st.session_state.db['profile']
        s = st.session_state.db['faktur_settings']
        
        # LOGIKA LOGO
        logo_html = '<div style="width:60px; height:60px; border:1px dashed #F19CBB;">LOGO</div>'
        if 'logo_img' in st.session_state:
            logo_html = f'<img src="data:image/png;base64,{st.session_state.logo_img}" style="width:80px;">'
        
        # STEMPEL LUNAS
        stempel = '<div class="stempel-lunas">LUNAS</div>' if f.get('status') == "SELESAI (LUNAS)" else ""
        
        total_p = sum([item['price'] * item['qty'] for item in f.get('paket_list', [])])
        total_m = sum([item['harga'] * item['qty'] for item in f.get('manual_list', [])])
        total_semua = total_p + total_m
        kurang_bayar = total_semua - f.get('dp', 0)
        tnc_formatted = s['tnc'].replace('\n', '<br>')
        
        st.divider()
        nota_html = f"""
        <div class="faktur-box">
            {stempel}
            <div style="position: absolute; top: 20px; left: 20px;">{logo_html}</div>
            <center>
                <h2 style="margin:0; color:#F19CBB;">{p['nama']}</h2>
                <p style="margin:0;">{p['alamat']}<br>WA: {p['hp']} | IG: {p['ig']}</p>
            </center>
            <hr style="border: 1px solid #eee; margin-top: 20px;">
            <p><b>INVOICE #{f['inv_no']}</b></p>
            <table style="width:100%; font-size: 14px;">
                <tr><td style="width:35%;">Nama Klien</td><td>: {f['nama']}</td></tr>
                <tr><td>No. WhatsApp</td><td>: {f.get('wa','-')}</td></tr>
                <tr><td>Tanggal Acara</td><td>: {f['tgl']}</td></tr>
                <tr><td>Lokasi Makeup</td><td>: {f['alamat_mu']}</td></tr>
                <tr><td>Jam Kerja</td><td>: {f['jam_ready']}</td></tr>
            </table>
            <br>
            <p style="border-bottom: 1px solid #eee; padding-bottom: 5px;"><b>RINCIAN LAYANAN:</b></p>
            <div style="font-size: 13px;">
        """
        for item in f.get('paket_list', []):
            nota_html += f"<div style='display:flex; justify-content:space-between;'><span>• {item['nama']} (x{item['qty']})</span><span>Rp {item['price']*item['qty']:,}</span></div>"
        for item_m in f.get('manual_list', []):
            nota_html += f"<div style='display:flex; justify-content:space-between;'><span>• {item_m['nama']} (x{item_m['qty']})</span><span>Rp {item_m['harga']*item_m['qty']:,}</span></div>"
        
        nota_html += f"""
            </div>
            <hr style="border: 1px dashed #eee; margin: 15px 0;">
            <table style="width:100%; font-weight: bold; font-size: 15px;">
                <tr><td>TOTAL TAGIHAN</td><td style="text-align:right;">Rp {total_semua:,}</td></tr>
                <tr><td>DP DITERIMA</td><td style="text-align:right;">Rp {f.get('dp',0):,}</td></tr>
                <tr style="color: #d9534f;"><td>SISA PELUNASAN</td><td style="text-align:right;">Rp {kurang_bayar if f.get('status') != 'SELESAI (LUNAS)' else 0:,}</td></tr>
            </table>
            <br>
            <div style="background-color: #f9f9f9; padding: 10px; border-radius: 5px; font-size: 13px;">
                <b>REKENING PEMBAYARAN:</b><br>{p['bank']} {p['no_rek']}<br>a/n {p['an']}
            </div>
            <br>
            <p style="font-size:11px; color: #555;"><b>SYARAT & KETENTUAN:</b><br>{tnc_formatted}</p>
            <center><p style="margin-top:20px; font-weight: bold;">{s['salam']}</p></center>
            <div style="text-align:right; margin-top:10px;"><p>Ttd,<br><br><br><b>{s['signature']}</b></p></div>
        </div>
        """
        st.markdown(nota_html, unsafe_allow_html=True)
        st.download_button(label=f"💾 DOWNLOAD IMAGE-NOTA ({f['nama']})", data=f"<html><body style='display:flex; justify-content:center; padding:20px;'>{nota_html}</body></html>", file_name=f"Invoice_{f['nama']}.html", mime="text/html")
        if st.button("Tutup Preview"): del st.session_state.current_faktur; st.rerun()

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
        if 'input_pakets' not in st.session_state: st.session_state.input_pakets = []
        if col_add.button("PILIH PAKET"):
            if selected_p != "-- Pilih Paket --":
                st.session_state.input_pakets.append({"nama": selected_p, "qty": 1, "price": st.session_state.db['master_layanan'][selected_p]})
        for i, item in enumerate(st.session_state.input_pakets):
            cp1, cp2, cp3 = st.columns([3, 1, 0.5])
            cp1.markdown(f"**{item['nama']}**")
            item['qty'] = cp2.number_input("Qty", min_value=1, key=f"qty_p_{i}", value=item['qty'])
            if cp3.button("❌", key=f"del_p_{i}"): st.session_state.input_pakets.pop(i); st.rerun()
        st.write("---")
        st.write("**10. Layanan Tambahan Manual**")
        if 'input_manuals' not in st.session_state: st.session_state.input_manuals = []
        if st.button("TAMBAH LAYANAN MANUAL"):
            st.session_state.input_manuals.append({"nama": "", "harga": 0, "qty": 1})
        for j, item_m in enumerate(st.session_state.input_manuals):
            cm1, cm2, cm3, cm4 = st.columns([2, 1, 1, 0.5])
            item_m['nama'] = cm1.text_input("Keterangan", key=f"m_nama_{j}", value=item_m['nama'])
            item_m['harga'] = cm2.number_input("Harga", min_value=0, key=f"m_harga_{j}", value=item_m['harga'])
            item_m['qty'] = cm3.number_input("Qty", min_value=1, key=f"m_qty_{j}", value=item_m['qty'])
            if cm4.button("❌", key=f"del_m_{j}"): st.session_state.input_manuals.pop(j); st.rerun()
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
        logo_file = st.file_uploader("Upload Logo MUA (.png)", type=["png"])
        if logo_file:
            st.session_state.logo_img = base64.b64encode(logo_file.read()).decode()
            st.success("Logo terupload!")
        st.divider()
        st.session_state.db['profile']['bank'] = st.text_input("Nama Bank", st.session_state.db['profile'].get('bank', ''))
        st.session_state.db['profile']['no_rek'] = st.text_input("No Rekening", st.session_state.db['profile'].get('no_rek', ''))
        st.session_state.db['profile']['an'] = st.text_input("Nama Pemilik Rekening", st.session_state.db['profile'].get('an', ''))
        if st.button("💾 SIMPAN PROFIL"): save_data(); st.success("Profil Berhasil Disimpan!")
    with t_set:
        st.subheader("⚙️ Aturan Faktur")
        st.session_state.db['faktur_settings']['tnc'] = st.text_area("Terms & Conditions (TnC)", st.session_state.db['faktur_settings'].get('tnc', ''), height=200)
        st.session_state.db['faktur_settings']['salam'] = st.text_area("Salam Penutup", st.session_state.db['faktur_settings'].get('salam', ''), height=100)
        st.session_state.db['faktur_settings']['signature'] = st.text_input("Signature (Nama Tanda Tangan)", st.session_state.db['faktur_settings'].get('signature', ''))
        if st.button("💾 SIMPAN SETTING"): save_data(); st.success("Setting Berhasil Disimpan!")

# --- 5. KEUANGAN (INTEGRASI LUNAS) ---
elif menu == "KEUANGAN":
    st.header("💰 Laporan Keuangan")
    lunas_jobs = [b for b in st.session_state.db['bookings'] if b.get('status') == "SELESAI (LUNAS)"]
    total_pendapatan = 0
    st.subheader("📈 Daftar Job Lunas")
    for j in lunas_jobs:
        price_p = sum([p['price'] * p['qty'] for p in j.get('paket_list', [])])
        price_m = sum([m['harga'] * m['qty'] for m in j.get('manual_list', [])])
        total_j = price_p + price_m
        st.write(f"✅ {j['tgl']} - {j['nama']} : **Rp {total_j:,}**")
        total_pendapatan += total_j
    st.divider()
    st.metric("TOTAL PENGHASILAN BERSIH", f"Rp {total_pendapatan:,}")
