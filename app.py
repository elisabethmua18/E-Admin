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
    defaults = {
        "profile": {"nama": "Elisabeth MUA", "alamat": "", "hp": "", "ig": "", "bank": "", "no_rek": "", "an": "", "logo_base64": ""},
        "faktur_settings": {"tnc": "", "signature": "", "salam": "", "next_inv": 1},
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

# --- FUNGSI CEK BENTROK ---
def cek_jadwal_bentrok(tgl_baru, jam_mulai_baru, jam_selesai_baru, inv_sekarang=None):
    bentrok_list = []
    fmt = "%H:%M"
    start_baru = datetime.strptime(jam_mulai_baru, fmt).time()
    end_baru = datetime.strptime(jam_selesai_baru, fmt).time()
    
    for b in st.session_state.db['bookings']:
        if b['tgl'] == tgl_baru and b['inv_no'] != inv_sekarang:
            jam_ready = b['jam_ready'].split('-')
            start_lama = datetime.strptime(jam_ready[0], fmt).time()
            end_lama = datetime.strptime(jam_ready[1], fmt).time()
            
            # Logika tabrakan waktu
            if not (end_baru <= start_lama or start_baru >= end_lama):
                bentrok_list.append(f"{b['nama']} ({b['jam_ready']})")
    return bentrok_list

# --- MENU ---
menu = st.sidebar.radio("MENU", ["BERANDA", "INPUT JADWAL", "LAYANAN", "PROFIL & SETTING", "KEUANGAN"])

# --- 1. BERANDA ---
if menu == "BERANDA":
    st.header("🌸 Jadwal Elisabeth MUA")
    selected_date = st.date_input("Pilih Tanggal", value=date.today())
    st.divider()
    
    selected_str = selected_date.strftime("%d/%m/%Y")
    list_job = [b for b in st.session_state.db['bookings'] if b.get('tgl') == selected_str]
    list_job = sorted(list_job, key=lambda x: x.get('jam_ready', '00:00').split('-')[0])
    
    if not list_job:
        st.info("Tidak ada jadwal.")
    else:
        for i, b in enumerate(list_job):
            with st.container():
                edit_info = f" | 🕒 Edit: {b['last_edit']}" if 'last_edit' in b else ""
                st.markdown(f"""
                <div class="job-card">
                    <h3 style="margin:0; color:#F19CBB;">{b.get('nama','-')} - {b.get('inv_no','-')}</h3>
                    <p style="margin:5px 0;"><b>Jam Kerja:</b> {b.get('jam_ready','-')} | <b>Lokasi:</b> {b.get('alamat_mu','-')}</p>
                    <p style="margin:5px 0; font-size:0.8em; color:gray;"><b>Status:</b> {b.get('status','PENDING')}{edit_info}</p>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                if c1.button("EDIT", key=f"ed_{i}"):
                    st.session_state.edit_data = b
                    st.session_state.input_pakets = b.get('paket_list', [])
                    st.session_state.input_manuals = b.get('manual_list', [])
                    st.warning("Data dimuat! Silakan ke menu INPUT JADWAL")
                
                if c2.button("✅ SELESAI", key=f"dn_{i}"):
                    b['status'] = f"SELESAI (LUNAS HARI H: {datetime.now().strftime('%d/%m/%Y')})"
                    save_data(); st.rerun()
                
                if c3.button("📄 FAKTUR", key=f"fkt_{i}"):
                    st.session_state.current_faktur = b

    if 'current_faktur' in st.session_state:
        f = st.session_state.current_faktur
        p = st.session_state.db['profile']
        s = st.session_state.db['faktur_settings']
        
        logo_html = f'<img src="data:image/png;base64,{p["logo_base64"]}" style="width:70px; position: absolute; left: 10px; top: 10px;">' if p.get('logo_base64') else ""
        is_lunas = "SELESAI" in f.get('status', '')
        stempel = '<div class="stempel-lunas">LUNAS</div>' if is_lunas else ""
        
        total_p = sum([(item.get('price',0) * item.get('qty',1)) for item in f.get('paket_list', [])])
        total_m = sum([(item.get('harga',0) * item.get('qty',1)) for item in f.get('manual_list', [])])
        total_semua = total_p + total_m
        dp_val = f.get('dp', 0)
        sisa = total_semua - dp_val
        
        sisa_style = "color:green; font-weight:bold;" if is_lunas else "color:black;"
        sisa_label = f.get('status') if is_lunas else f"Rp {sisa:,}"

        st.divider()
        nota_html = f"""
        <div class="faktur-box">
            {stempel}
            <div style="position: relative; min-height: 100px; padding-left: 90px;">
                {logo_html}
                <div style="text-align: center;">
                    <h2 style="margin:0; color:#F19CBB;">{p.get('nama','')}</h2>
                    <p style="margin:0; font-size:12px;">{p.get('alamat','')}<br>WA: {p.get('hp','')} | IG: {p.get('ig','')}</p>
                </div>
            </div>
            <hr>
            <p><b>INVOICE #{f.get('inv_no','')}</b></p>
            <table style="width:100%; font-size: 14px;">
                <tr><td>Nama Klien</td><td>: {f.get('nama','')}</td></tr>
                <tr><td>Tanggal</td><td>: {f.get('tgl','')}</td></tr>
                <tr><td>Lokasi</td><td>: {f.get('alamat_mu','')}</td></tr>
                <tr><td>Jam Kerja</td><td>: {f.get('jam_ready','')}</td></tr>
            </table>
            <br><b>RINCIAN:</b><br>
        """
        for item in f.get('paket_list', []):
            nota_html += f"<div style='display:flex; justify-content:space-between; font-size:13px;'><span>• {item['nama']} (x{item['qty']})</span><span>Rp {item['price']*item['qty']:,}</span></div>"
        for item_m in f.get('manual_list', []):
            nota_html += f"<div style='display:flex; justify-content:space-between; font-size:13px;'><span>• {item_m['nama']} (x{item_m['qty']})</span><span>Rp {item_m['harga']*item_m['qty']:,}</span></div>"
        
        nota_html += f"""
            <hr style="border: 0.5px dashed #ccc;">
            <table style="width:100%; font-size: 14px;">
                <tr><td>TOTAL</td><td style="text-align:right;">Rp {total_semua:,}</td></tr>
                <tr><td>DP</td><td style="text-align:right;">Rp {dp_val:,}</td></tr>
                <tr style="{sisa_style}"><td>SISA</td><td style="text-align:right;">{sisa_label}</td></tr>
            </table>
            <br><div style="font-size:11px; background:#f9f9f9; padding:5px;"><b>S&K:</b><br>{s.get('tnc','').replace('\\n','<br>').replace('\n','<br>')}</div>
        </div>"""
        st.markdown(nota_html, unsafe_allow_html=True)
        if st.button("Tutup Preview"): del st.session_state.current_faktur; st.rerun()

# --- 2. INPUT JADWAL ---
elif menu == "INPUT JADWAL":
    st.header("📝 Tambah/Edit Jadwal")
    edit_data = st.session_state.get('edit_data', {})
    
    with st.form("form_input"):
        nama_klien = st.text_input("Nama Klien", value=edit_data.get('nama', ""))
        tgl_makeup = st.date_input("Tanggal", value=datetime.strptime(edit_data['tgl'], "%d/%m/%Y") if edit_data else date.today())
        
        times = [time(h, m).strftime("%H:%M") for h in range(24) for m in (0, 15, 30, 45)]
        c1, c2 = st.columns(2)
        jam_m = c1.selectbox("Jam Mulai", times, index=32)
        jam_s = c2.selectbox("Jam Selesai", times, index=40)
        
        wa_klien = st.text_input("WhatsApp", value=edit_data.get('wa', ""))
        alamat_mu = st.text_area("Alamat", value=edit_data.get('alamat_mu', ""))
        dp_value = st.number_input("DP (Down Payment)", min_value=0, value=edit_data.get('dp', 0))
        
        submit = st.form_submit_button("💾 SIMPAN KE DATABASE")
        
        if submit:
            tgl_str = tgl_makeup.strftime("%d/%m/%Y")
            bentrok = cek_jadwal_bentrok(tgl_str, jam_m, jam_s, edit_data.get('inv_no'))
            
            if not nama_klien:
                st.error("Nama Klien wajib diisi!")
            elif bentrok:
                st.error(f"⚠️ JADWAL BENTROK dengan: {', '.join(bentrok)}. Silakan atur ulang jam.")
            else:
                if edit_data:
                    st.session_state.db['bookings'] = [b for b in st.session_state.db['bookings'] if b.get('inv_no') != edit_data.get('inv_no')]
                
                new_booking = {
                    "inv_no": edit_data.get('inv_no', f"INV{st.session_state.db['faktur_settings'].get('next_inv', 1):04d}"),
                    "nama": nama_klien, "tgl": tgl_str, "wa": wa_klien, "alamat_mu": alamat_mu,
                    "jam_ready": f"{jam_m}-{jam_s}", "dp": dp_value,
                    "status": edit_data.get('status', 'PENDING'),
                    "last_edit": datetime.now().strftime("%d/%m %H:%M"),
                    "paket_list": st.session_state.get('input_pakets', []),
                    "manual_list": st.session_state.get('input_manuals', [])
                }
                st.session_state.db['bookings'].append(new_booking)
                if not edit_data: st.session_state.db['faktur_settings']['next_inv'] += 1
                save_data()
                st.success("Tersimpan!")
                if 'edit_data' in st.session_state: del st.session_state.edit_data
                st.rerun()

# --- 3. LAYANAN (KODE ASLI) ---
elif menu == "LAYANAN":
    st.header("💄 Master Layanan Utama")
    with st.form("master"):
        nl = st.text_input("Nama Paket Baru")
        hl = st.number_input("Harga Master", min_value=0)
        if st.form_submit_button("Tambah ke Master"):
            st.session_state.db['master_layanan'][nl] = hl; save_data(); st.rerun()
    st.table(pd.DataFrame(list(st.session_state.db['master_layanan'].items()), columns=['Paket', 'Harga']))

# --- 4. PROFIL & SETTING (KODE ASLI) ---
elif menu == "PROFIL & SETTING":
    st.header("👤 Profil & Setting Faktur")
    t_prof, t_set = st.tabs(["PROFIL", "SETTING"])
    with t_prof:
        st.session_state.db['profile']['nama'] = st.text_input("Nama MUA", st.session_state.db['profile'].get('nama', ''))
        st.session_state.db['profile']['alamat'] = st.text_area("Alamat MUA", st.session_state.db['profile'].get('alamat', ''))
        st.session_state.db['profile']['hp'] = st.text_input("No WA MUA", st.session_state.db['profile'].get('hp', ''))
        st.
