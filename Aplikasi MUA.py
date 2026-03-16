import flet as ft
import json
import os
import re
from datetime import datetime, timedelta

def main(page: ft.Page):
    page.title = "E-Admin MUA - Elisabeth"
    page.bgcolor = "#F8C8DC"
    page.scroll = "always"
    page.window_width = 600

    # --- 1. SISTEM DATABASE ---
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

    db = load_data()

    def save_data():
        with open(DATA_FILE, "w") as f:
            json.dump(db, f, indent=4)

    # --- 2. LOGIKA NAVIGASI & PESAN ---
    def navigasi(target):
        login_view.visible = beranda_view.visible = profil_view.visible = False
        lay_view.visible = faktur_set_view.visible = input_j_view.visible = False
        finance_view.visible = faktur_page_view.visible = False
        target.visible = True
        page.update()

    def tampil_pesan(teks):
        page.dialog = ft.AlertDialog(content=ft.Text(teks), actions=[ft.TextButton("OK", on_click=lambda _: (setattr(page.dialog, "open", False), page.update()))])
        page.dialog.open = True
        page.update()

    def clean_num(val):
        if not val or val == "": return 0
        return int(str(val).replace(".", "").replace(",", ""))

    def str_to_time(t_str):
        return datetime.strptime(t_str.strip(), "%H:%M")

    # --- 3. HALAMAN KEUANGAN ---
    def refresh_finance_ui(bln, thn):
        omset = 0
        for b in db['bookings']:
            try:
                dt = datetime.strptime(b['tgl'], "%d/%m/%Y")
                if f"{dt.month:02d}" == bln and str(dt.year) == thn:
                    total_inv = sum([(p.get('price') or p.get('harga', 0)) * p.get('qty', 1) for p in b['paket_list']]) + sum([m.get('harga', 0) for m in b.get('manual_list', [])])
                    omset += total_inv if b.get('status') == "SELESAI" else b.get('dp', 0)
            except: pass
        exp = sum([x['nominal'] for x in db['pengeluaran'] if x['bulan'] == bln and x['tahun'] == thn])
        txt_omset.value = f"Rp {omset:,}"; txt_exp.value = f"Rp {exp:,}"; txt_nett.value = f"Rp {(omset - exp):,}"
        list_exp_ui.controls.clear()
        for i, x in enumerate(db['pengeluaran']):
            if x['bulan'] == bln and x['tahun'] == thn:
                list_exp_ui.controls.append(ft.Row([ft.Text(x['ket'], expand=True), ft.Text(f"Rp {x['nominal']:,}"), ft.ElevatedButton("X", on_click=lambda e, idx=i: (db['pengeluaran'].pop(idx), save_data(), refresh_finance_ui(bln, thn)), color="red")]))
        page.update()

    txt_omset = ft.Text(); txt_exp = ft.Text(); txt_nett = ft.Text(size=20, weight="bold", color="blue")
    in_exp_ket = ft.TextField(label="Ket Pengeluaran"); in_exp_nom = ft.TextField(label="Nominal", width=120)
    list_exp_ui = ft.Column()
    drop_bln = ft.Dropdown(value=datetime.now().strftime("%m"), options=[ft.dropdown.Option(f"{i:02d}") for i in range(1, 13)], width=80)
    drop_thn = ft.Dropdown(value=datetime.now().strftime("%Y"), options=[ft.dropdown.Option("2025"), ft.dropdown.Option("2026")], width=100)
    finance_view = ft.Column([ft.ElevatedButton("[ KEMBALI ]", on_click=lambda _: navigasi(beranda_view)), ft.Row([drop_bln, drop_thn, ft.ElevatedButton("CEK", on_click=lambda _: refresh_finance_ui(drop_bln.value, drop_thn.value))]), ft.Text("Total Omset:"), txt_omset, ft.Text("Total Pengeluaran:"), txt_exp, ft.Text("NETT PROFIT:", weight="bold"), txt_nett, ft.Row([in_exp_ket, in_exp_nom, ft.ElevatedButton("TAMBAH", on_click=lambda _: (db['pengeluaran'].append({"ket":in_exp_ket.value, "nominal":clean_num(in_exp_nom.value), "bulan":drop_bln.value, "tahun":drop_thn.value}), save_data(), refresh_finance_ui(drop_bln.value, drop_thn.value)))]), list_exp_ui], visible=False, scroll="always")

    # --- 4. HALAMAN FAKTUR (DENGAN DP) ---
    def generate_faktur(k):
        tp = sum([(p.get('price') or p.get('harga', 0)) * p.get('qty', 1) for p in k['paket_list']])
        tm = sum([m.get('harga', 0) for m in k.get('manual_list', [])])
        gt = tp + tm; terutang = gt - k.get('dp', 0)
        f_logo.src = db['profile']['logo_url'] if db['profile']['logo_url'] else "https://via.placeholder.com/150"
        f_mua_nama.value = db['profile']['nama']
        f_mua_detail.value = f"{db['profile']['alamat']}\nHP: {db['profile']['hp']} | IG: {db['profile']['ig']}"
        f_inv_no.value = f"#{k['inv_no']}"; f_inv_tgl.value = k['tgl']
        f_klien_nama.value = k['nama']; f_klien_wa.value = f"WA: {k.get('wa','-')}"; f_klien_lok.value = k['alamat_mu']
        f_items.controls.clear()
        for p in k['paket_list']:
            f_items.controls.append(ft.Row([ft.Text(f"{p['nama']} ({p.get('qty',1)}x)"), ft.Text(f"Rp {(p.get('price') or p.get('harga',0))*p.get('qty',1):,}")], alignment="spaceBetween"))
        for m in k.get('manual_list', []):
            f_items.controls.append(ft.Row([ft.Text(f"+ {m['nama']}"), ft.Text(f"Rp {m['harga']:,}")], alignment="spaceBetween"))
        f_total.value = f"Rp {gt:,}"; f_dp.value = f"Rp {k.get('dp',0):,}"; f_terutang.value = f"Rp {terutang:,}"
        f_bank.value = f"Bank: {db['faktur_settings']['bank']} - {db['faktur_settings']['no_rek']} (a/n {db['faktur_settings']['an']})"
        f_tnc.value = f"S&K: {db['faktur_settings']['tnc']}"; f_sig.value = db['faktur_settings']['signature']
        navigasi(faktur_page_view)

    f_logo = ft.Image(src="https://via.placeholder.com/150", width=70, height=70); f_mua_nama = ft.Text(weight="bold", size=18); f_mua_detail = ft.Text(size=10)
    f_inv_no = ft.Text(color="blue", weight="bold"); f_inv_tgl = ft.Text(size=10); f_klien_nama = ft.Text(weight="bold"); f_klien_wa = ft.Text(); f_klien_lok = ft.Text()
    f_items = ft.Column(); f_total = ft.Text(); f_dp = ft.Text(); f_terutang = ft.Text(color="red", weight="bold", size=18); f_bank = ft.Text(size=10); f_tnc = ft.Text(size=9); f_sig = ft.Text(weight="bold")
    faktur_page_view = ft.Column([ft.ElevatedButton("[ KEMBALI ]", on_click=lambda _: navigasi(beranda_view)), ft.Container(content=ft.Column([ft.Row([f_logo, ft.Column([f_mua_nama, f_mua_detail], expand=True), ft.Column([f_inv_no, f_inv_tgl], horizontal_alignment="right")], alignment="spaceBetween"), ft.Divider(), ft.Row([ft.Column([f_klien_nama, f_klien_wa]), f_klien_lok], alignment="spaceBetween"), ft.Divider(), f_items, ft.Divider(), ft.Row([ft.Text("TOTAL TAGIHAN:"), f_total], alignment="spaceBetween"), ft.Row([ft.Text("DP / SUDAH DIBAYAR:"), f_dp], alignment="spaceBetween"), ft.Row([ft.Text("SALDO TERUTANG:", weight="bold"), f_terutang], alignment="spaceBetween"), ft.Divider(), f_bank, f_tnc, ft.Text("\nHormat Kami,"), f_sig], tight=True), bgcolor="white", padding=20, border_radius=10)], visible=False, scroll="always")

    # --- 5. BERANDA ---
    def hapus_massal(e):
        try:
            d1 = datetime.strptime(f_start.value, "%d/%m/%Y"); d2 = datetime.strptime(f_end.value, "%d/%m/%Y")
            db['bookings'] = [b for b in db['bookings'] if not (d1 <= datetime.strptime(b['tgl'], "%d/%m/%Y") <= d2)]
            save_data(); refresh_beranda(); tampil_pesan("Dibersihkan.")
        except: tampil_pesan("Format Tgl Salah.")
    def set_selesai(b): b['status'] = "SELESAI"; save_data(); refresh_beranda()
    display_j = ft.Column(); f_start = ft.TextField(label="Dari", value=datetime.now().strftime("%d/%m/%Y"), width=120); f_end = ft.TextField(label="Sampai", value=datetime.now().strftime("%d/%m/%Y"), width=120)
    def refresh_beranda(e=None):
        display_j.controls.clear()
        try:
            d1 = datetime.strptime(f_start.value, "%d/%m/%Y"); d2 = datetime.strptime(f_end.value, "%d/%m/%Y")
            sorted_b = sorted(db['bookings'], key=lambda x: str_to_time(x['jam_ready'].split("-")[0]))
            for b in sorted_b:
                bt = datetime.strptime(b['tgl'], "%d/%m/%Y")
                if d1 <= bt <= d2:
                    st = " [LUNAS]" if b.get('status') == "SELESAI" else ""
                    display_j.controls.append(ft.Container(content=ft.Row([ft.Column([ft.Text(b['jam_ready'].split('-')[0], weight="bold", color="blue"), ft.Text(b['jam_ready'].split('-')[1], size=10)], width=50), ft.Column([ft.Text(f"{b['nama']}{st}", weight="bold"), ft.Text(f"{b['tgl']} | {b['paket_list'][0]['nama']}", size=11)], expand=True), ft.ElevatedButton("LUNAS", on_click=lambda e, x=b: set_selesai(x), bgcolor="green", color="white", visible=b.get('status')!="SELESAI", height=30), ft.ElevatedButton("EDIT", on_click=lambda e, x=b: buka_edit_x(x), bgcolor="orange", height=30), ft.ElevatedButton("FAKTUR", on_click=lambda e, x=b: generate_faktur(x), height=30)]), padding=10, bgcolor="white", border_radius=10))
                    display_j.controls.append(ft.Text(f"   --- [ OTW ] {b['otw']} ---", size=10, italic=True, color="grey"))
        except: pass
        page.update()

    # --- 6. FORM PROFIL & SETTING (FIXED) ---
    def simpan_profil_action(e):
        db['profile'].update({"nama":set_mua_n.value,"alamat":set_mua_a.value,"hp":set_mua_h.value,"ig":set_mua_ig.value,"logo_url":set_mua_l.value})
        save_data(); tampil_pesan("Profil Tersimpan"); navigasi(beranda_view)
    set_mua_n = ft.TextField(label="Nama MUA", value=db['profile']['nama']); set_mua_a = ft.TextField(label="Alamat MUA", value=db['profile']['alamat']); set_mua_h = ft.TextField(label="No HP", value=db['profile']['hp']); set_mua_ig = ft.TextField(label="IG", value=db['profile']['ig']); set_mua_l = ft.TextField(label="Link Logo", value=db['profile']['logo_url'])
    profil_view = ft.Column([ft.ElevatedButton("[ KEMBALI ]", on_click=lambda _: navigasi(beranda_view)), ft.Text("EDIT PROFIL", size=20, weight="bold"), set_mua_n, set_mua_a, set_mua_h, set_mua_ig, set_mua_l, ft.ElevatedButton("SIMPAN PROFIL", on_click=simpan_profil_action, bgcolor="green", color="white")], visible=False, scroll="always")

    def simpan_faktur_action(e):
        db['faktur_settings'].update({"tnc":set_tnc.value, "bank":set_bank.value, "no_rek":set_norek.value, "an":set_an.value, "signature":set_sig.value})
        save_data(); tampil_pesan("Setting Faktur Tersimpan"); navigasi(beranda_view)
    set_tnc = ft.TextField(label="TnC", multiline=True, value=db['faktur_settings']['tnc']); set_bank = ft.TextField(label="Bank", value=db['faktur_settings']['bank']); set_norek = ft.TextField(label="No Rekening", value=db['faktur_settings']['no_rek']); set_an = ft.TextField(label="Atas Nama", value=db['faktur_settings']['an']); set_sig = ft.TextField(label="Signature", value=db['faktur_settings']['signature'])
    faktur_set_view = ft.Column([ft.ElevatedButton("[ KEMBALI ]", on_click=lambda _: navigasi(beranda_view)), ft.Text("SETTING FAKTUR", size=20, weight="bold"), set_tnc, set_bank, set_norek, set_an, set_sig, ft.ElevatedButton("SIMPAN SETTING", on_click=simpan_faktur_action, bgcolor="green", color="white")], visible=False, scroll="always")

    # --- 7. LAYANAN & JADWAL ---
    list_lay_m = ft.Column()
    def refresh_lay_ui():
        list_lay_m.controls.clear()
        for n, h in db['master_layanan'].items():
            list_lay_m.controls.append(ft.Row([ft.Text(f"{n} (Rp {h:,})", expand=True), ft.ElevatedButton("X", on_click=lambda e, x=n: (db['master_layanan'].pop(x), save_data(), refresh_lay_ui(), page.update()))]))
    set_lay_n = ft.TextField(label="Nama Paket"); set_lay_h = ft.TextField(label="Harga")
    lay_view = ft.Column([ft.ElevatedButton("[ KEMBALI ]", on_click=lambda _: navigasi(beranda_view)), ft.Row([set_lay_n, set_lay_h, ft.ElevatedButton("TAMBAH", on_click=lambda _: (db['master_layanan'].update({set_lay_n.value: clean_num(set_lay_h.value)}), save_data(), refresh_lay_ui(), page.update()))]), list_lay_m], visible=False)

    is_editing = {"active": False, "index": None}
    in_klien = ft.TextField(label="Nama"); in_wa = ft.TextField(label="WA"); in_mu_a = ft.TextField(label="Lokasi"); in_tgl = ft.TextField(label="Tgl")
    in_m = ft.TextField(label="Mulai", width=70); in_s = ft.TextField(label="Selesai", width=70); in_otw_j = ft.TextField(label="OTW", width=70); in_otw_d = ft.TextField(label="Mnt", width=70); in_dp = ft.TextField(label="DP", value="0"); in_pkt = ft.Dropdown(expand=True); in_qty = ft.TextField(label="Qty", value="1", width=60); in_tim_check = ft.Checkbox(label="Tim?"); in_tim_type = ft.Dropdown(options=[ft.dropdown.Option("Hairdo"), ft.dropdown.Option("Hijabdo")], width=100); in_tim_nama = ft.TextField(label="Nama Tim"); in_man_n = ft.TextField(label="Manual", expand=True); in_man_h = ft.TextField(label="Harga", width=100)
    def simpan_jadwal(e):
        manual = [{"nama": in_man_n.value, "harga": clean_num(in_man_h.value)}] if in_man_n.value else []
        booking = {"inv_no": f"INV{db['faktur_settings']['next_inv']:04d}" if not is_editing["active"] else db['bookings'][is_editing["index"]]['inv_no'], "nama": in_klien.value, "wa": in_wa.value, "alamat_mu": in_mu_a.value, "tgl": in_tgl.value, "jam_ready": f"{in_m.value}-{in_s.value}", "otw": f"{in_otw_j.value}({in_otw_d.value}m)", "dp": clean_num(in_dp.value), "paket_list": [{"nama": in_pkt.value, "qty": int(in_qty.value), "price": db['master_layanan'][in_pkt.value]}], "manual_list": manual, "hire_tim": in_tim_check.value, "tim_type": in_tim_type.value, "tim_nama": in_tim_nama.value, "status": "PENDING"}
        if is_editing["active"]: db['bookings'][is_editing["index"]] = booking
        else: db['bookings'].append(booking); db['faktur_settings']['next_inv'] += 1
        save_data(); navigasi(beranda_view); refresh_beranda()
    def buka_edit_x(k):
        is_editing.update({"active": True, "index": db['bookings'].index(k)})
        in_klien.value = k['nama']; in_wa.value = k.get('wa', ''); in_mu_a.value = k['alamat_mu']; in_tgl.value = k['tgl']
        m, s = k['jam_ready'].split("-"); in_m.value = m; in_s.value = s
        oj, od = k['otw'].split("("); in_otw_j.value = oj; in_otw_d.value = od.replace("m)", "")
        in_dp.value = str(k['dp']); in_pkt.value = k['paket_list'][0]['nama']; in_qty.value = str(k['paket_list'][0].get('qty', 1))
        in_tim_check.value = k['hire_tim']; in_tim_type.value = k['tim_type']; in_tim_nama.value = k['tim_nama']
        in_man_n.value = k['manual_list'][0]['nama'] if k['manual_list'] else ""; in_man_h.value = str(k['manual_list'][0]['harga']) if k['manual_list'] else "0"
        navigasi(input_j_view)
    input_j_view = ft.Column([ft.ElevatedButton("[ BATAL ]", on_click=lambda _: navigasi(beranda_view)), in_klien, in_wa, in_mu_a, in_tgl, ft.Row([in_m, in_s, in_otw_j, in_otw_d]), in_dp, ft.Row([in_pkt, in_qty]), ft.Row([in_tim_check, in_tim_type, in_tim_nama]), ft.Row([in_man_n, in_man_h]), ft.ElevatedButton("SIMPAN JADWAL", on_click=simpan_jadwal, bgcolor="#F19CBB", color="white")], visible=False, scroll="always")

    # --- 8. LOGIN & BERANDA ---
    def login_check(e):
        if login_email.value == "elisabeth@mua.id" and login_pass.value == "Elis5173": navigasi(beranda_view); refresh_beranda()
        else: tampil_pesan("Email/Password salah!")
    login_email = ft.TextField(label="Email", value="elisabeth@mua.id"); login_pass = ft.TextField(label="Pass", password=True, can_reveal_password=True, value="Elis5173")
    login_view = ft.Column([ft.Text("LOGIN", size=25, weight="bold"), login_email, login_pass, ft.ElevatedButton("MASUK", on_click=login_check, width=300)], horizontal_alignment="center")

    beranda_view = ft.Column([
        ft.Text(f"Dashboard: {db['profile']['nama']}", size=22, weight="bold"),
        ft.Row([ft.ElevatedButton("JADWAL", on_click=lambda _: (is_editing.update({"active":False}), in_pkt.options.clear(), in_pkt.options.extend([ft.dropdown.Option(k) for k in db['master_layanan'].keys()]), navigasi(input_j_view))), ft.ElevatedButton("LAYANAN", on_click=lambda _: (navigasi(lay_view), refresh_lay_ui()))]),
        ft.Row([ft.ElevatedButton("PROFIL", on_click=lambda _: navigasi(profil_view)), ft.ElevatedButton("SETTING", on_click=lambda _: navigasi(faktur_set_view))]),
        ft.ElevatedButton("PENGHASILAN (NETT)", on_click=lambda _: (navigasi(finance_view), refresh_finance_ui(drop_bln.value, drop_thn.value)), bgcolor="blue", color="white", width=400),
        ft.Divider(), ft.Row([f_start, f_end, ft.ElevatedButton("CARI", on_click=refresh_beranda)]),
        ft.ElevatedButton("HAPUS RENTANG TANGGAL", on_click=hapus_massal, bgcolor="red", color="white", width=400),
        display_j
    ], visible=False)

    page.add(login_view, beranda_view, profil_view, lay_view, faktur_set_view, input_j_view, finance_view, faktur_page_view)

ft.app(target=main)