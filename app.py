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
        margin-bottom: 15px; border-left: 10px solid #F19CBB; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .faktur-box {
        background-color: white; padding: 30px; border: 1px solid #eee; border-radius: 10px;
        color: black; line-height: 1.5; font-family: 'Arial', sans-serif; position: relative;
    }
    .stempel-lunas {
        position: absolute; top: 40%; left: 50%; transform: translate(-50%, -50%) rotate(-20deg);
        border: 5px solid red; color: red; font-size: 45px; font-weight: bold;
        padding: 10px 20px; border-radius: 10px; opacity: 0.5; pointer-events: none; z-index: 99;
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
        {"inv_no": "INV0005", "nama": "Kak Angel", "tgl": "17/03/2026", "wa": "0857xxxx", "alamat_mu": "Tembalang", "jam_ready": "14:00-16:00", "jam_otw": "16:15", "durasi_otw": 15, "paket_list": [], "manual_list": [], "hire_tim": True, "tim_type": "Hairdo", "tim_nama": "Selly", "dp": 0, "status": "PENDING"},
        {"inv_no": "INV0006", "nama": "Kak Reyki", "tgl": "17/03/2026", "wa": "0812xxxx", "alamat_mu": "Hotel Aruman", "jam_ready": "13:00-15:00", "jam_otw": "12:15", "durasi_otw": 30, "paket_list": [], "manual_list": [], "hire_tim": True, "tim_type": "Hairdo", "tim_nama": "Ovie", "dp": 0, "status": "PENDING"}
    ]
    defaults = {
        "profile": {"nama": "Elisabeth MUA", "alamat": "", "hp": "", "ig": "", "bank": "", "no_rek": "", "an": "", "logo_base64": ""},
        "faktur_settings": {"tnc": "", "signature": "", "salam": "", "next_inv": 7},
        "master_layanan": {}, "bookings": initial_bookings, "pengeluaran": [], "pemasukan_lain": []
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

# --- MENU SIDEBAR ---
menu = st.sidebar.radio("MENU", ["BERANDA", "INPUT JADWAL", "LAYANAN", "PROFIL & SETTING", "KEUANGAN"])
# --- 1. BERANDA ---
if menu == "BERANDA":
    st.header("🌸 Jadwal Elisabeth MUA")
    selected_date = st.date_input("Pilih Tanggal", value=date(2026, 3, 17))
    st.divider()
    
    selected_str = selected_date.strftime("%d/%m/%Y")
    list_job = [b for b in st.session_state.db['bookings'] if b.get('tgl') == selected_str]
    list_job = sorted(list_job, key=lambda x: x.get('jam_ready', '00:00').split('-')[0])
    
    if not list_job:
        st.info("Tidak ada jadwal untuk tanggal ini.")
    else:
        for i, b in enumerate(list_job):
            with st.container():
                st.markdown(f"""
                <div class="job-card">
                    <h3 style="margin:0; color:#F19CBB;">{b.get('nama','-')} - {b.get('inv_no','-')}</h3>
                    <p style="margin:5px 0;"><b>Jam Kerja:</b> {b.get('jam_ready','-')} | <b>Lokasi:</b> {b.get('alamat_mu','-')}</p>
                    <p style="margin:5px 0;"><b>Status:</b> {b.get('status','PENDING')}</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f'<p class="otw-info">🚗 Jam OTW: {b.get("jam_otw","-")} ({b.get("durasi_otw","-")}m)</p>', unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                if c1.button("EDIT", key=f"ed_{i}"):
                    st.session_state.edit_data = b
                    st.session_state.input_pakets = b.get('paket_list', [])
                    st.session_state.input_manuals = b.get('manual_list', [])
                    st.warning("Data siap diedit! Silakan klik menu 'INPUT JADWAL'")
                
                if c2.button("✅ SELESAI", key=f"dn_{i}"):
                    b['status'] = "SELESAI (LUNAS)"
                    save_data(); st.rerun()
                
                if c3.button("📄 FAKTUR", key=f"fkt_{i}"):
                    st.session_state.current_faktur = b

   # --- TAMPILAN FAKTUR ---
    if 'current_faktur' in st.session_state:
        f = st.session_state.current_faktur
        p = st.session_state.db['profile']
        s = st.session_state.db['faktur_settings']
        
        # 1. LOGIKA PERHITUNGAN
        total_p = sum([float(item.get('price', 0)) * int(item.get('qty', 1)) for item in f.get('paket_list', [])])
        total_m = sum([float(item.get('harga', 0)) * int(item.get('qty', 1)) for item in f.get('manual_list', [])])
        total_semua = total_p + total_m
        dp_val = float(f.get('dp', 0))
        
        logo_html = f'<img src="data:image/png;base64,{p["logo_base64"]}" style="width:75px; position: absolute; left: 10px; top: 10px;">' if p.get('logo_base64') else ""
        stempel = '<div class="stempel-lunas">LUNAS</div>' if f.get('status') == "SELESAI (LUNAS)" else ""
        sisa_teks = f"<span style='color:green;'>LUNAS</span>" if f.get('status') == "SELESAI (LUNAS)" else f"Rp {total_semua - dp_val:,.0f}"

        # 2. RAKIT NOTA_HTML (Satu variabel untuk Layar & Download)
        nota_html = f"""
        <div class="faktur-box">
            {stempel}
            <div style="position: relative; height: 100px; width: 100%;">
                {logo_html}
                <center>
                    <h2 style="margin:0; color:#F19CBB;">{p.get('nama','Elisabeth MUA')}</h2>
                    <p style="margin:0; font-size:12px;">{p.get('alamat','')}<br>WA: {p.get('hp','')} | IG: {p.get('ig','')}</p>
                </center>
            </div>
            <hr style="border: 1px solid #eee;">
            <p><b>INVOICE #{f.get('inv_no','')}</b></p>
            <table style="width:100%; font-size: 14px; border-collapse: collapse;">
                <tr><td style="width:35%; padding: 4px 0;">Nama Klien</td><td>: {f.get('nama','')}</td></tr>
                <tr><td style="padding: 4px 0;">WhatsApp</td><td>: {f.get('wa','-')}</td></tr>
                <tr><td style="padding: 4px 0;">Tanggal</td><td>: {f.get('tgl','')}</td></tr>
                <tr><td style="padding: 4px 0;">Lokasi</td><td>: {f.get('alamat_mu','')}</td></tr>
                <tr><td style="padding: 4px 0;">Jam Kerja</td><td>: {f.get('jam_ready','')}</td></tr>
            </table>
            <br><p style="border-bottom: 1px solid #eee; padding-bottom: 5px;"><b>RINCIAN LAYANAN:</b></p>
            <div style="font-size: 13px;">"""
        
        for item in f.get('paket_list', []):
            nota_html += f"<div style='display:flex; justify-content:space-between; padding: 2px 0;'><span>• {item.get('nama','')} (x{item.get('qty',1)})</span><span>Rp {float(item.get('price',0))*int(item.get('qty',1)):,.0f}</span></div>"
        for item_m in f.get('manual_list', []):
            nota_html += f"<div style='display:flex; justify-content:space-between; padding: 2px 0;'><span>• {item_m.get('nama','')} (x{item_m.get('qty',1)})</span><span>Rp {float(item_m.get('harga',0))*int(item_m.get('qty',1)):,.0f}</span></div>"
        
        nota_html += f"""</div>
            <hr style="border: 1px dashed #eee; margin: 15px 0;">
            <table style="width:100%; font-weight: bold; font-size: 15px;">
                <tr><td>TOTAL TAGIHAN</td><td style="text-align:right;">Rp {total_semua:,.0f}</td></tr>
                <tr><td>DP DITERIMA</td><td style="text-align:right;">Rp {dp_val:,.0f}</td></tr>
                <tr><td>SISA PELUNASAN</td><td style="text-align:right;">{sisa_teks}</td></tr>
            </table>
            <br><div style="background-color: #f9f9f9; padding: 10px; border-radius: 5px; font-size: 12px;">
            <b>REKENING PEMBAYARAN:</b><br>{p.get('bank','')} {p.get('no_rek','')} a/n {p.get('an','')}</div>
            <p style="font-size:11px; color: #555; margin-top:15px;"><b>SYARAT & KETENTUAN:</b><br>{s.get('tnc','').replace('\\n','<br>').replace('\n','<br>')}</p>
            <center><p style="margin-top:20px; font-weight: bold;">{s.get('salam','')}</p></center>
            <div style="text-align:right; margin-top:10px;"><p>Ttd,<br><br><b>{s.get('signature','')}</b></p></div>
        </div>"""
        
        # 3. OUTPUT (Hanya muncul satu kali)
        st.divider()
        st.markdown(nota_html, unsafe_allow_html=True)
        st.download_button(
            label="💾 DOWNLOAD NOTA", 
            data=f"<html><head><meta charset='UTF-8'></head><body style='padding:20px;'>{nota_html}</body></html>", 
            file_name=f"Invoice_{f.get('nama','klien')}.html", 
            mime="text/html"
        )
        if st.button("Tutup Preview"): 
            del st.session_state.current_faktur
            st.rerun()
            # --- 2. INPUT JADWAL ---
elif menu == "INPUT JADWAL":
    st.header("📝 Tambah / Edit Jadwal")
    
    # Ambil data dari tombol EDIT jika ada
    edit_data = st.session_state.get('edit_data', {})
    
    with st.container():
        nama_klien = st.text_input("1. Nama Klien", value=edit_data.get('nama', ""))
        
        # Penanganan Tanggal
        tgl_awal = datetime.now()
        if edit_data.get('tgl'):
            try: tgl_awal = datetime.strptime(edit_data['tgl'], "%d/%m/%Y")
            except: pass
        tgl_makeup = st.date_input("2. Tanggal Makeup", tgl_awal)
        
        wa_klien = st.text_input("3. Nomor WhatsApp", value=edit_data.get('wa', ""))
        alamat_makeup = st.text_area("4. Alamat Makeup", value=edit_data.get('alamat_mu', ""))
        
        # Pilihan Jam
        times = [time(h, m).strftime("%H:%M") for h in range(24) for m in (0, 15, 30, 45)]
        c1, c2, c3 = st.columns(3)
        jam_m = c1.selectbox("5. Jam Mulai", times, index=32)
        jam_s = c2.selectbox("6. Jam Selesai", times, index=40)
        jam_o = c3.selectbox("7. Jam OTW", times, index=28)
        
        durasi_otw = st.number_input("8. Durasi OTW (Menit)", min_value=0, value=edit_data.get('durasi_otw', 30))
        
        st.write("---")
        st.write("**9. Pilih Paket Master**")
        master_list = list(st.session_state.db['master_layanan'].keys())
        col_sel, col_add = st.columns([3, 1])
        selected_p = col_sel.selectbox("Cari Paket", ["-- Pilih Paket --"] + master_list)
        
        if 'input_pakets' not in st.session_state: st.session_state.input_pakets = []
        if col_add.button("PILIH PAKET"):
            if selected_p != "-- Pilih Paket --":
                st.session_state.input_pakets.append({
                    "nama": selected_p, 
                    "qty": 1, 
                    "price": st.session_state.db['master_layanan'][selected_p]
                })
        
        for i, item in enumerate(st.session_state.input_pakets):
            cp1, cp2, cp3 = st.columns([3, 1, 0.5])
            cp1.markdown(f"**{item.get('nama','')}**")
            item['qty'] = cp2.number_input("Qty", min_value=1, key=f"qty_p_{i}", value=item.get('qty', 1))
            if cp3.button("❌", key=f"del_p_{i}"):
                st.session_state.input_pakets.pop(i)
                st.rerun()

        st.write("---")
        st.write("**10. Layanan Tambahan Manual**")
        if 'input_manuals' not in st.session_state: st.session_state.input_manuals = []
        if st.button("TAMBAH LAYANAN MANUAL"):
            st.session_state.input_manuals.append({"nama": "", "harga": 0, "qty": 1})
            
        for j, item_m in enumerate(st.session_state.input_manuals):
            cm1, cm2, cm3, cm4 = st.columns([2, 1, 1, 0.5])
            item_m['nama'] = cm1.text_input("Keterangan", key=f"m_nama_{j}", value=item_m.get('nama',''))
            item_m['harga'] = cm2.number_input("Harga", min_value=0, key=f"m_harga_{j}", value=item_m.get('harga', 0))
            item_m['qty'] = cm3.number_input("Qty", min_value=1, key=f"m_qty_{j}", value=item_m.get('qty', 1))
            if cm4.button("❌", key=f"del_m_{j}"):
                st.session_state.input_manuals.pop(j)
                st.rerun()

        st.write("---")
        dp_value = st.number_input("11. DP (Down Payment)", min_value=0, value=int(edit_data.get('dp', 0)))
        
        st.write("---")
        hire_tim = st.checkbox("Gunakan Tim Tambahan?", value=edit_data.get('hire_tim', False))
        if hire_tim:
            ct1, ct2 = st.columns(2)
            tim_type = ct1.selectbox("Jenis Tim", ["Hairdo", "Hijabdo", "Hairdo + Hijabdo"])
            tim_nama = ct2.text_input("Nama Anggota Tim", value=edit_data.get('tim_nama', ""))
        else:
            tim_type, tim_nama = "-", "-"

        st.divider()
        if st.button("💾 SIMPAN JADWAL KE DATABASE"):
            if not nama_klien:
                st.error("Nama Klien wajib diisi!")
            else:
                # Jika edit, hapus data lama berdasarkan Invoice No
                if edit_data:
                    st.session_state.db['bookings'] = [b for b in st.session_state.db['bookings'] if b.get('inv_no') != edit_data.get('inv_no')]
                
                new_booking = {
                    "inv_no": edit_data.get('inv_no', f"INV{st.session_state.db['faktur_settings'].get('next_inv', 1):04d}"),
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
                    "status": edit_data.get('status', 'PENDING')
                }
                
                st.session_state.db['bookings'].append(new_booking)
                if not edit_data:
                    st.session_state.db['faktur_settings']['next_inv'] += 1
                
                # Reset State
                if 'edit_data' in st.session_state: del st.session_state.edit_data
                st.session_state.input_pakets = []
                st.session_state.input_manuals = []
                
                save_data()
                st.success("Jadwal Berhasil Disimpan!")
                st.rerun()
                # --- 3. LAYANAN ---
elif menu == "LAYANAN":
    st.header("💄 Master Layanan Utama")
    st.info("Tambahkan paket yang sering digunakan di sini agar bisa dipilih cepat saat input jadwal.")
    
    with st.form("master_form"):
        nl = st.text_input("Nama Paket Baru (Contoh: Makeup Wisuda)")
        hl = st.number_input("Harga Master (Rp)", min_value=0)
        if st.form_submit_button("Tambah ke Master"):
            if nl:
                st.session_state.db['master_layanan'][nl] = hl
                save_data()
                st.success(f"Paket {nl} berhasil ditambahkan!")
                st.rerun()
            else:
                st.error("Nama paket tidak boleh kosong.")
    
    st.divider()
    st.subheader("Daftar Paket Master")
    if st.session_state.db['master_layanan']:
        df_layanan = pd.DataFrame(list(st.session_state.db['master_layanan'].items()), columns=['Nama Paket', 'Harga'])
        st.table(df_layanan)
        if st.button("Hapus Semua Master (Hati-hati)"):
            st.session_state.db['master_layanan'] = {}
            save_data()
            st.rerun()
    else:
        st.write("Belum ada paket master.")

# --- 4. PROFIL & SETTING ---
elif menu == "PROFIL & SETTING":
    st.header("👤 Profil & Setting Faktur")
    
    tab_profil, tab_faktur = st.tabs(["PROFIL BISNIS", "SETTING FAKTUR"])
    
    with tab_profil:
        st.subheader("Informasi Bisnis")
        st.session_state.db['profile']['nama'] = st.text_input("Nama MUA / Studio", st.session_state.db['profile'].get('nama', ''))
        st.session_state.db['profile']['alamat'] = st.text_area("Alamat Studio", st.session_state.db['profile'].get('alamat', ''))
        st.session_state.db['profile']['hp'] = st.text_input("Nomor WA (untuk Faktur)", st.session_state.db['profile'].get('hp', ''))
        st.session_state.db['profile']['ig'] = st.text_input("Akun Instagram", st.session_state.db['profile'].get('ig', ''))
        
        st.divider()
        st.subheader("Logo Bisnis")
        logo_file = st.file_uploader("Upload Logo Baru (.png)", type=["png"])
        if logo_file:
            # Konversi gambar ke Base64 agar tersimpan di JSON
            img_base64 = base64.b64encode(logo_file.read()).decode()
            st.session_state.db['profile']['logo_base64'] = img_base64
            st.success("Logo berhasil diunggah!")
            st.image(logo_file, width=100)
            
        st.divider()
        st.subheader("Informasi Rekening")
        st.session_state.db['profile']['bank'] = st.text_input("Nama Bank", st.session_state.db['profile'].get('bank', ''))
        st.session_state.db['profile']['no_rek'] = st.text_input("Nomor Rekening", st.session_state.db['profile'].get('no_rek', ''))
        st.session_state.db['profile']['an'] = st.text_input("Atas Nama (A/N)", st.session_state.db['profile'].get('an', ''))
        
        if st.button("💾 SIMPAN SEMUA PROFIL"):
            save_data()
            st.success("Profil Bisnis Berhasil Diperbarui!")

    with tab_faktur:
        st.subheader("Pengaturan Tampilan Nota")
        st.session_state.db['faktur_settings']['tnc'] = st.text_area("Syarat & Ketentuan (TnC)", st.session_state.db['faktur_settings'].get('tnc', ''), help="Gunakan Enter untuk baris baru")
        st.session_state.db['faktur_settings']['salam'] = st.text_area("Salam Penutup (Contoh: Terima kasih sudah mempercayai kami)", st.session_state.db['faktur_settings'].get('salam', ''))
        st.session_state.db['faktur_settings']['signature'] = st.text_input("Nama Tanda Tangan (Contoh: Elisabeth MUA)", st.session_state.db['faktur_settings'].get('signature', ''))
        
        st.divider()
        st.session_state.db['faktur_settings']['next_inv'] = st.number_input("Nomor Invoice Berikutnya", min_value=1, value=st.session_state.db['faktur_settings'].get('next_inv', 1))
        
        if st.button("💾 SIMPAN SETTING FAKTUR"):
            save_data()
            st.success("Pengaturan Faktur Berhasil Disimpan!")
            # --- 5. KEUANGAN ---
elif menu == "KEUANGAN":
    st.header("💰 Laporan Keuangan Bulanan")
    
    # Filter Bulan dan Tahun
    c1, c2 = st.columns(2)
    sel_month = c1.selectbox("Pilih Bulan", ["01","02","03","04","05","06","07","08","09","10","11","12"], index=datetime.now().month-1)
    sel_year = c2.selectbox("Pilih Tahun", ["2025","2026","2027"], index=1)
    
    # 1. PERHITUNGAN OTOMATIS DARI JADWAL (DP & PELUNASAN)
    omset_jadwal = 0
    st.subheader("📊 Pemasukan Otomatis (Jadwal)")
    
    list_pemasukan_jadwal = []
    for j in st.session_state.db['bookings']:
        tgl_parts = j.get('tgl','').split('/')
        if len(tgl_parts) == 3 and tgl_parts[1] == sel_month and tgl_parts[2] == sel_year:
            # Jika status SELESAI, maka Omset = Full Payment
            if j.get('status') == "SELESAI (LUNAS)":
                total_klien = sum([float(p['price'])*int(p['qty']) for p in j['paket_list']]) + sum([float(m['harga'])*int(m['qty']) for m in j['manual_list']])
                list_pemasukan_jadwal.append({"tgl": j['tgl'], "ket": f"Lunas: {j['nama']}", "nom": total_klien})
                omset_jadwal += total_klien
            # Jika masih PENDING, ambil DP-nya saja sebagai pemasukan masuk
            else:
                dp_klien = float(j.get('dp', 0))
                if dp_klien > 0:
                    list_pemasukan_jadwal.append({"tgl": j['tgl'], "ket": f"DP: {j['nama']}", "nom": dp_klien})
                    omset_jadwal += dp_klien
    
    if list_pemasukan_jadwal:
        st.table(pd.DataFrame(list_pemasukan_jadwal))
    else:
        st.write("Tidak ada aktivitas jadwal di bulan ini.")

    st.divider()

    # 2. PEMASUKAN LAIN & PENGELUARAN (MANUAL)
    col_in, col_out = st.columns(2)
    
    with col_in:
        st.subheader("➕ Penghasilan Lain")
        with st.form("pemasukan_lain_form"):
            ket_in = st.text_input("Keterangan (Misal: Jual Thrift)")
            nom_in = st.number_input("Nominal (Rp)", min_value=0)
            if st.form_submit_button("Simpan Pemasukan"):
                st.session_state.db['pemasukan_lain'].append({
                    "tgl": date.today().strftime("%d/%m/%Y"), 
                    "ket": ket_in, 
                    "nom": nom_in
                })
                save_data(); st.rerun()
    
    with col_out:
        st.subheader("💸 Pengeluaran")
        with st.form("pengeluaran_form"):
            ket_out = st.text_input("Keterangan (Misal: Beli Foundation)")
            nom_out = st.number_input("Nominal (Rp)", min_value=0)
            if st.form_submit_button("Simpan Pengeluaran"):
                st.session_state.db['pengeluaran'].append({
                    "tgl": date.today().strftime("%d/%m/%Y"), 
                    "ket": ket_out, 
                    "nom": nom_out
                })
                save_data(); st.rerun()

    # Hitung Total Manual
    total_in_lain = sum([float(p['nom']) for p in st.session_state.db.get('pemasukan_lain', []) if p['tgl'].split('/')[1] == sel_month and p['tgl'].split('/')[2] == sel_year])
    total_out = sum([float(p['nom']) for p in st.session_state.db.get('pengeluaran', []) if p['tgl'].split('/')[1] == sel_month and p['tgl'].split('/')[2] == sel_year])
    
    # 3. RINGKASAN AKHIR
    st.divider()
    final_omset = omset_jadwal + total_in_lain
    res1, res2, res3 = st.columns(3)
    
    res1.metric("OMSET (Bruto)", f"Rp {final_omset:,.0f}")
    res2.metric("PENGELUARAN", f"Rp {total_out:,.0f}")
    res3.metric("NETT (Bersih)", f"Rp {final_omset - total_out:,.0f}")

    # Tampilkan Detail Jika Ada
    if total_in_lain > 0 or total_out > 0:
        with st.expander("Lihat Rincian Manual Bulan Ini"):
            if total_in_lain > 0:
                st.write("**Pemasukan Tambahan:**")
                st.json([p for p in st.session_state.db['pemasukan_lain'] if p['tgl'].split('/')[1] == sel_month])
            if total_out > 0:
                st.write("**Pengeluaran:**")
                st.json([p for p in st.session_state.db['pengeluaran'] if p['tgl'].split('/')[1] == sel_month])
                
