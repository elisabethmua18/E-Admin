import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# --- CONFIG HALAMAN ---
st.set_page_config(page_title="E-Admin MUA - Elisabeth", page_icon="💄")

# --- STYLE CSS (Agar Mirip Nuansa Pink Flet) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8C8DC; }
    div.stButton > button {
        background-color: #F19CBB; color: white;
        border-radius: 10px; font-weight: bold; width: 100%;
    }
    .faktur-box {
        background-color: white; padding: 20px;
        border-radius: 10px; color: black; border: 1px solid #ddd;
    }
    .job-card {
        background-color: white; padding: 15px;
        border-radius: 10px; margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEM DATABASE ---
DATA_FILE = "mua_master_pro.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if "pengeluaran" not in data: data["pengeluaran"] = []
            return data
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

# --- LOGIN LOGIC ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("💄 E-ADMIN LOGIN")
    email = st.text_input("Email", value="elisabeth@mua.id")
    pw = st.text_input("Password", type="password", value="Elis5173")
    if st.button("MASUK"):
        if email == "elisabeth@mua.id" and pw == "Elis5173":
            st.session_state.auth = True
            st.rerun()
        else: st.error("Email/Password salah!")
    st.stop()

# --- NAVIGASI ---
menu = st.sidebar.radio("MENU", ["BERANDA", "INPUT JADWAL", "LAYANAN", "PROFIL & SETTING", "PENGHASILAN"])

# --- 1. BERANDA ---
if menu == "BERANDA":
    st.header(f"🌸 Dashboard: {st.session_state.db['profile']['nama']}")
    
    col_t1, col_t2 = st.columns(2)
    f_start = col_t1.text_input("Dari (DD/MM/YYYY)", datetime.now().strftime("%d/%m/%Y"))
    f_end = col_t2.text_input("Sampai (DD/MM/YYYY)", datetime.now().strftime("%d/%m/%Y"))

    if st.button("🗑️ HAPUS RENTANG TANGGAL", type="secondary"):
        try:
            d1 = datetime.strptime(f_start, "%d/%m/%Y")
            d2 = datetime.strptime(f_end, "%d/%m/%Y")
            st.session_state.db['bookings'] = [b for b in st.session_state.db['bookings'] if not (d1 <= datetime.strptime(b['tgl'], "%d/%m/%Y") <= d2)]
            save_data(); st.success("Data dibersihkan!"); st.rerun()
        except: st.error("Format Tanggal Salah!")

    st.divider()

    for idx, b in enumerate(st.session_state.db['bookings']):
        try:
            bt = datetime.strptime(b['tgl'], "%d/%m/%Y")
            d1 = datetime.strptime(f_start, "%d/%m/%Y")
            d2 = datetime.strptime(f_end, "%d/%m/%Y")
            
            if d1 <= bt <= d2:
                st.markdown(f"""
                <div class="job-card">
                    <b style="color:blue;">{b['jam_ready']}</b> | <b>{b['nama']}</b> {'<span style="color:green;">[LUNAS]</span>' if b.get('status') == 'SELESAI' else ''}<br>
                    <small>{b['tgl']} | {b['paket_list'][0]['nama']}</small><br>
                    <i style="color:grey; font-size:11px;">--- [ OTW ] {b['otw']} ---</i>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                if b.get('status') != "SELESAI":
                    if c1.button("LUNAS", key=f"lns_{idx}"):
                        st.session_state.db['bookings'][idx]['status'] = "SELESAI"
                        save_data(); st.rerun()
                if c2.button("FAKTUR", key=f"fkt_{idx}"):
                    st.session_state.view_faktur = b
                if c3.button("HAPUS", key=f"del_{idx}"):
                    st.session_state.db['bookings'].pop(idx)
                    save_data(); st.rerun()
        except: pass

    # --- TAMPILAN FAKTUR ---
    if 'view_faktur' in st.session_state:
        k = st.session_state.view_faktur
        st.divider()
        st.subheader("📄 Preview Faktur")
        tp = sum([p.get('price', 0) * p.get('qty', 1) for p in k['paket_list']])
        tm = sum([m.get('harga', 0) for m in k.get('manual_list', [])])
        gt = tp + tm
        terutang = gt - k.get('dp', 0)
        
        st.markdown(f"""
        <div class="faktur-box">
            <h2 style="text-align:center;">{st.session_state.db['profile']['nama']}</h2>
            <p style="text-align:center; font-size:12px;">{st.session_state.db['profile']['alamat']}<br>HP: {st.session_state.db['profile']['hp']}</p>
            <hr>
            <b>No Inv: #{k['inv_no']}</b><br>Tgl: {k['tgl']}<br>Klien: {k['nama']} ({k.get('wa', '-')})
            <hr>
            <b>Rincian:</b><br>
            {k['paket_list'][0]['nama']} x{k['paket_list'][0].get('qty',1)} : Rp {tp:,}<br>
            TOTAL TAGIHAN: <b>Rp {gt:,}</b><br>
            DP / SUDAH DIBAYAR: <b style="color:green;">Rp {k.get('dp',0):,}</b><br>
            <h3 style="color:red;">SALDO TERUTANG: Rp {terutang:,}</h3>
            <hr>
            <p style="font-size:10px;">Bank: {st.session_state.db['faktur_settings']['bank']} - {st.session_state.db['faktur_settings']['no_rek']} (a/n {st.session_state.db['faktur_settings']['an']})</p>
            <p>Hormat Kami,<br><br><b>{st.session_state.db['faktur_settings']['signature']}</b></p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Tutup Faktur"): del st.session_state.view_faktur; st.rerun()

# --- 2. INPUT JADWAL ---
elif menu == "INPUT JADWAL":
    st.header("📝 Tambah Jadwal Baru")
    with st.form("form_job"):
        nama = st.text_input("Nama Klien")
        wa = st.text_input("WhatsApp")
        lokasi = st.text_input("Lokasi Gmaps / Alamat")
        tgl = st.text_input("Tanggal (DD/MM/YYYY)", datetime.now().strftime("%d/%m/%Y"))
        c1, c2, c3, c4 = st.columns(4)
        jam_m = c1.text_input("Mulai", "08:00")
        jam_s = c2.text_input("Selesai", "10:00")
        otw_j = c3.text_input("Jam OTW", "07:00")
        otw_m = c4.text_input("Menit", "30")
        
        dp = st.number_input("DP (Down Payment)", value=0)
        paket_opt = list(st.session_state.db['master_layanan'].keys())
        paket_sel = st.selectbox("Pilih Paket", paket_opt if paket_opt else ["Belum Ada Paket"])
        qty = st.number_input("Jumlah Orang (Qty)", value=1)
        
        st.write("---")
        man_n = st.text_input("Item Manual (Jika Ada)")
        man_h = st.number_input("Harga Manual", value=0)
        
        if st.form_submit_button("SIMPAN JADWAL"):
            manual = [{"nama": man_n, "harga": man_h}] if man_n else []
            price_paket = st.session_state.db['master_layanan'].get(paket_sel, 0)
            
            new_booking = {
                "inv_no": f"INV{st.session_state.db['faktur_settings']['next_inv']:04d}",
                "nama": nama, "wa": wa, "alamat_mu": lokasi, "tgl": tgl,
                "jam_ready": f"{jam_m}-{jam_s}", "otw": f"{otw_j}({otw_m}m)",
                "dp": dp, "paket_list": [{"nama": paket_sel, "qty": int(qty), "price": price_paket}],
                "manual_list": manual, "status": "PENDING"
            }
            st.session_state.db['bookings'].append(new_booking)
            st.session_state.db['faktur_settings']['next_inv'] += 1
            save_data()
            st.success("Jadwal Berhasil Disimpan!")

# --- 3. LAYANAN ---
elif menu == "LAYANAN":
    st.header("💄 Master Layanan")
    c1, c2 = st.columns([2, 1])
    n_lay = c1.text_input("Nama Paket")
    h_lay = c2.number_input("Harga (Rp)", value=0)
    if st.button("TAMBAH PAKET"):
        st.session_state.db['master_layanan'][n_lay] = h_lay
        save_data(); st.rerun()
    
    st.write("---")
    for n, h in st.session_state.db['master_layanan'].items():
        st.write(f"✅ {n} - Rp {h:,}")

# --- 4. PROFIL & SETTING ---
elif menu == "PROFIL & SETTING":
    st.header("👤 Profil & Faktur")
    with st.expander("Edit Profil MUA"):
        st.session_state.db['profile']['nama'] = st.text_input("Nama MUA", st.session_state.db['profile']['nama'])
        st.session_state.db['profile']['alamat'] = st.text_input("Alamat", st.session_state.db['profile']['alamat'])
        st.session_state.db['profile']['hp'] = st.text_input("HP", st.session_state.db['profile']['hp'])
        if st.button("Simpan Profil"): save_data(); st.success("Profil Tersimpan")
        
    with st.expander("Setting Faktur & Bank"):
        st.session_state.db['faktur_settings']['bank'] = st.text_input("Bank", st.session_state.db['faktur_settings']['bank'])
        st.session_state.db['faktur_settings']['no_rek'] = st.text_input("No Rekening", st.session_state.db['faktur_settings']['no_rek'])
        st.session_state.db['faktur_settings']['an'] = st.text_input("Atas Nama", st.session_state.db['faktur_settings']['an'])
        st.session_state.db['faktur_settings']['signature'] = st.text_input("Tanda Tangan", st.session_state.db['faktur_settings']['signature'])
        if st.button("Simpan Setting"): save_data(); st.success("Setting Tersimpan")

# --- 5. PENGHASILAN ---
elif menu == "PENGHASILAN":
    st.header("💰 Laporan Keuangan (NETT)")
    c1, c2 = st.columns(2)
    bln = c1.selectbox("Bulan", [f"{i:02d}" for i in range(1, 13)], index=int(datetime.now().month)-1)
    thn = c2.selectbox("Tahun", ["2025", "2026"], index=1)
    
    omset = 0
    for b in st.session_state.db['bookings']:
        try:
            dt = datetime.strptime(b['tgl'], "%d/%m/%Y")
            if f"{dt.month:02d}" == bln and str(dt.year) == thn:
                total_inv = sum([p['price'] * p.get('qty', 1) for p in b['paket_list']]) + sum([m['harga'] for m in b.get('manual_list', [])])
                omset += total_inv if b.get('status') == "SELESAI" else b.get('dp', 0)
        except: pass
    
    exp = sum([x['nominal'] for x in st.session_state.db['pengeluaran'] if x['bulan'] == bln and x['tahun'] == thn])
    
    st.metric("Total Omset", f"Rp {omset:,}")
    st.metric("Total Pengeluaran", f"Rp {exp:,}")
    st.metric("NETT PROFIT", f"Rp {omset-exp:,}", delta_color="normal")
    
    st.divider()
    with st.form("exp_input"):
        st.write("Tambah Pengeluaran")
        ket = st.text_input("Keterangan")
        nom = st.number_input("Nominal", value=0)
        if st.form_submit_button("TAMBAH"):
            st.session_state.db['pengeluaran'].append({"ket": ket, "nominal": nom, "bulan": bln, "tahun": thn})
            save_data(); st.rerun()
