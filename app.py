import streamlit as st
import streamlit.components.v1 as components
import json
import os
import requests
import base64
import pandas as pd
from io import BytesIO
from datetime import datetime, time, date
import calendar
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

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

# --- SISTEM DATABASE PERSISTEN ---
DATA_FILE = "mua_master_pro.json"
GITHUB_REPO = "elisabethmua18/E-Admin"
GITHUB_PATH = DATA_FILE
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{GITHUB_PATH}"

MONTH_NAMES_ID = MONTH_NAMES_ID
MONTH_LOOKUP_ID = {name: i + 1 for i, name in enumerate(MONTH_NAMES_ID)}


def get_default_data():
    initial_bookings = [
        {"inv_no": "INV0005", "nama": "Kak Angel", "tgl": "17/03/2026", "wa": "0857xxxx", "alamat_mu": "Tembalang", "jam_ready": "14:00-16:00", "jam_otw": "16:15", "durasi_otw": 15, "paket_list": [], "manual_list": [], "hire_tim": True, "tim_type": "Hairdo", "tim_nama": "Selly", "dp": 0, "status": "PENDING"},
        {"inv_no": "INV0006", "nama": "Kak Reyki", "tgl": "17/03/2026", "wa": "0812xxxx", "alamat_mu": "Hotel Aruman", "jam_ready": "13:00-15:00", "jam_otw": "12:15", "durasi_otw": 30, "paket_list": [], "manual_list": [], "hire_tim": True, "tim_type": "Hairdo", "tim_nama": "Ovie", "dp": 0, "status": "PENDING"}
    ]
    return {
        "profile": {"nama": "Elisabeth MUA", "alamat": "", "hp": "", "ig": "", "bank": "", "no_rek": "", "an": "", "logo_base64": "", "logo": ""},
        "faktur_settings": {"tnc": "", "signature": "", "salam": "", "next_inv": 7},
        "master_layanan": {},
        "bookings": initial_bookings,
        "pengeluaran": [],
        "pemasukan_lain": []
    }


def merge_defaults(data: dict) -> dict:
    defaults = get_default_data()
    if not isinstance(data, dict):
        return defaults

    for key, value in defaults.items():
        if key not in data:
            data[key] = value

    profile_defaults = defaults["profile"]
    for key, value in profile_defaults.items():
        if key not in data["profile"]:
            data["profile"][key] = value

    faktur_defaults = defaults["faktur_settings"]
    for key, value in faktur_defaults.items():
        if key not in data["faktur_settings"]:
            data["faktur_settings"][key] = value

    if not isinstance(data.get("master_layanan"), dict):
        data["master_layanan"] = {}
    for list_key in ["bookings", "pengeluaran", "pemasukan_lain"]:
        if not isinstance(data.get(list_key), list):
            data[list_key] = []

    for booking in data["bookings"]:
        booking.setdefault("fee_tim_tambahan", 0)

    return data


def get_github_headers():
    token = st.secrets.get("GITHUB_TOKEN", "")
    if not token:
        return None
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }


def load_data_from_github():
    headers = get_github_headers()
    if not headers:
        return None

    try:
        response = requests.get(GITHUB_API_URL, headers=headers, timeout=20)
        if response.status_code == 200:
            payload = response.json()
            content = payload.get("content", "")
            if content:
                decoded = base64.b64decode(content).decode("utf-8")
                return merge_defaults(json.loads(decoded))

        raw_response = requests.get(GITHUB_RAW_URL, timeout=20)
        if raw_response.status_code == 200 and raw_response.text.strip():
            return merge_defaults(raw_response.json())
    except Exception as exc:
        st.warning(f"Gagal membaca database online: {exc}")

    return None


def save_data_to_github(data):
    headers = get_github_headers()
    if not headers:
        raise RuntimeError("GITHUB_TOKEN belum diisi di Streamlit secrets.")

    json_content = json.dumps(data, ensure_ascii=False, indent=4)
    encoded_content = base64.b64encode(json_content.encode("utf-8")).decode("utf-8")

    sha = None
    existing = requests.get(GITHUB_API_URL, headers=headers, timeout=20)
    if existing.status_code == 200:
        sha = existing.json().get("sha")
    elif existing.status_code not in (404,):
        raise RuntimeError(f"Gagal mengambil SHA GitHub: {existing.status_code} - {existing.text}")

    payload = {
        "message": "Auto update database dari aplikasi",
        "content": encoded_content,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(GITHUB_API_URL, headers=headers, json=payload, timeout=20)
    if response.status_code not in (200, 201):
        raise RuntimeError(f"Gagal menyimpan ke GitHub: {response.status_code} - {response.text}")



def load_data_local():
    if not os.path.exists(DATA_FILE):
        return None

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return merge_defaults(json.load(f))
    except Exception:
        return None



def save_data_local(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)



def load_data():
    data = load_data_from_github()
    if data is not None:
        save_data_local(data)
        return data

    data = load_data_local()
    if data is not None:
        return data

    return get_default_data()


if 'db' not in st.session_state:
    st.session_state.db = load_data()



def save_data():
    save_data_local(st.session_state.db)
    save_data_to_github(st.session_state.db)


def format_rupiah(nominal):
    return f"Rp {float(nominal or 0):,.0f}"


def render_month_calendar(bookings, month, year, target_menu="BERANDA", calendar_key="main"):
    cal = calendar.Calendar(firstweekday=0)
    booked_days = {}
    for b in bookings:
        try:
            dt = datetime.strptime(b.get('tgl', ''), "%d/%m/%Y")
            if dt.month == month and dt.year == year:
                booked_days.setdefault(dt.day, []).append(b)
        except Exception:
            continue

    month_name = MONTH_NAMES_ID[month - 1]
    day_names = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]

    html = """
    <style>
    .compact-calendar-wrap {background:white; padding:10px; border-radius:14px; box-shadow:2px 2px 10px rgba(0,0,0,0.08); margin-bottom:10px;}
    .compact-calendar-title {font-weight:700; color:#C85A7C; font-size:16px; margin-bottom:8px; text-align:center;}
    .compact-calendar-table {width:100%; border-collapse:separate; border-spacing:4px; table-layout:fixed;}
    .compact-calendar-table th {font-size:11px; color:#8A4D62; padding:2px 0; font-weight:700;}
    .compact-calendar-day {height:38px; border-radius:10px; background:#FFF9FB; border:1px solid #F0D5E0; text-align:center; vertical-align:middle; font-size:12px; font-weight:700; color:#333;}
    .compact-calendar-empty {height:38px;}
    .compact-calendar-link {display:flex; align-items:center; justify-content:center; width:100%; height:100%; text-decoration:none; color:#2F80ED; background:#EAF3FF; border-radius:10px; position:relative; font-weight:800;}
    .compact-calendar-link::after {content:''; position:absolute; bottom:4px; width:6px; height:6px; background:#2F80ED; border-radius:50%;}
    .compact-calendar-num {display:flex; align-items:center; justify-content:center; width:100%; height:100%;}
    </style>
    """
    html += f'<div class="compact-calendar-wrap"><div class="compact-calendar-title">Kalender Jadwal {month_name} {year}</div><table class="compact-calendar-table"><thead><tr>'
    for d in day_names:
        html += f"<th>{d}</th>"
    html += "</tr></thead><tbody>"

    for week in cal.monthdayscalendar(year, month):
        html += "<tr>"
        for day in week:
            if day == 0:
                html += '<td class="compact-calendar-empty"></td>'
            else:
                items = booked_days.get(day, [])
                selected_iso = f"{year:04d}-{month:02d}-{day:02d}"
                url = f"?menu={target_menu}&selected_date={selected_iso}&beranda_cal_month={month}&beranda_cal_year={year}&hapus_cal_month={month}&hapus_cal_year={year}&calendar_click={calendar_key}"
                html += '<td class="compact-calendar-day">'
                if items:
                    html += f'<a class="compact-calendar-link" href="{url}">{day}</a>'
                else:
                    html += f'<div class="compact-calendar-num">{day}</div>'
                html += '</td>'
        html += "</tr>"
    html += "</tbody></table></div>"
    return html, booked_days


def build_finance_report_rows(sel_month, sel_year, bookings, pemasukan_lain, pengeluaran_manual):
    report_rows = []
    omset_jadwal = 0
    list_pemasukan_jadwal = []
    list_pengeluaran_tim = []
    total_out_tim = 0

    for j in bookings:
        tgl_parts = j.get('tgl', '').split('/')
        if len(tgl_parts) != 3 or tgl_parts[1] != sel_month or tgl_parts[2] != sel_year:
            continue

        total_klien = sum(float(p.get('price', 0)) * int(p.get('qty', 1)) for p in j.get('paket_list', [])) +             sum(float(m.get('harga', 0)) * int(m.get('qty', 1)) for m in j.get('manual_list', []))
        dp_klien = float(j.get('dp', 0) or 0)

        if j.get('status') == "SELESAI (LUNAS)":
            pelunasan = max(total_klien - dp_klien, 0)
            if dp_klien > 0:
                list_pemasukan_jadwal.append({"tgl": j['tgl'], "ket": f"DP: {j['nama']}", "nom": dp_klien})
                report_rows.append({
                    "Tanggal": j['tgl'],
                    "Keterangan": f"DP: {j['nama']} (ot)",
                    "Pemasukan": dp_klien,
                    "Pengeluaran": 0
                })
                omset_jadwal += dp_klien
            if pelunasan > 0:
                list_pemasukan_jadwal.append({"tgl": j['tgl'], "ket": f"Pelunasan: {j['nama']}", "nom": pelunasan})
                report_rows.append({
                    "Tanggal": j['tgl'],
                    "Keterangan": f"Pelunasan: {j['nama']} (ot)",
                    "Pemasukan": pelunasan,
                    "Pengeluaran": 0
                })
                omset_jadwal += pelunasan
        else:
            if dp_klien > 0:
                list_pemasukan_jadwal.append({"tgl": j['tgl'], "ket": f"DP: {j['nama']}", "nom": dp_klien})
                report_rows.append({
                    "Tanggal": j['tgl'],
                    "Keterangan": f"DP: {j['nama']} (ot)",
                    "Pemasukan": dp_klien,
                    "Pengeluaran": 0
                })
                omset_jadwal += dp_klien

        fee_tim = float(j.get('fee_tim_tambahan', 0) or 0)
        if fee_tim > 0:
            ket_fee = f"Fee Tim: {j['nama']} - {j.get('tim_nama', '-')}"
            list_pengeluaran_tim.append({"tgl": j['tgl'], "ket": ket_fee, "nom": fee_tim})
            report_rows.append({
                "Tanggal": j['tgl'],
                "Keterangan": f"{ket_fee} (ot)",
                "Pemasukan": 0,
                "Pengeluaran": fee_tim
            })
            total_out_tim += fee_tim

    total_in_lain = 0
    for p in pemasukan_lain:
        parts = p.get('tgl', '').split('/')
        if len(parts) == 3 and parts[1] == sel_month and parts[2] == sel_year:
            nominal = float(p.get('nom', 0) or 0)
            total_in_lain += nominal
            report_rows.append({
                "Tanggal": p.get('tgl', ''),
                "Keterangan": f"{p.get('ket', '')} (mn)",
                "Pemasukan": nominal,
                "Pengeluaran": 0
            })

    total_out_manual = 0
    for p in pengeluaran_manual:
        parts = p.get('tgl', '').split('/')
        if len(parts) == 3 and parts[1] == sel_month and parts[2] == sel_year:
            nominal = float(p.get('nom', 0) or 0)
            total_out_manual += nominal
            report_rows.append({
                "Tanggal": p.get('tgl', ''),
                "Keterangan": f"{p.get('ket', '')} (mn)",
                "Pemasukan": 0,
                "Pengeluaran": nominal
            })

    total_out = total_out_manual + total_out_tim
    final_omset = omset_jadwal + total_in_lain
    nett = final_omset - total_out

    def parse_tanggal(val):
        try:
            return datetime.strptime(val, "%d/%m/%Y")
        except Exception:
            return datetime.max

    report_rows = sorted(report_rows, key=lambda x: (parse_tanggal(x["Tanggal"]), x["Keterangan"]))

    return {
        "list_pemasukan_jadwal": list_pemasukan_jadwal,
        "omset_jadwal": omset_jadwal,
        "list_pengeluaran_tim": list_pengeluaran_tim,
        "total_out_tim": total_out_tim,
        "total_in_lain": total_in_lain,
        "total_out_manual": total_out_manual,
        "total_out": total_out,
        "final_omset": final_omset,
        "total_pemasukan": final_omset,
        "nett": nett,
        "report_rows": report_rows
    }


def make_finance_excel(df, summary_dict):
    output = BytesIO()
    export_df = df.copy()
    export_df.loc[len(export_df)] = {
        "Tanggal": "",
        "Keterangan": "TOTAL",
        "Pemasukan": summary_dict["total_pemasukan"],
        "Pengeluaran": summary_dict["total_out"]
    }

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Transaksi")
        pd.DataFrame([
            {"Keterangan": "Total Pemasukan", "Nominal": summary_dict["total_pemasukan"]},
            {"Keterangan": "Total Pengeluaran", "Nominal": summary_dict["total_out"]},
            {"Keterangan": "Nett (Bersih)", "Nominal": summary_dict["nett"]},
        ]).to_excel(writer, index=False, sheet_name="Ringkasan")

        wb = writer.book
        for ws in wb.worksheets:
            for col in ws.columns:
                max_length = 0
                col_letter = col[0].column_letter
                for cell in col:
                    val = "" if cell.value is None else str(cell.value)
                    max_length = max(max_length, len(val))
                    if cell.row == 1:
                        cell.font = cell.font.copy(bold=True)
                ws.column_dimensions[col_letter].width = min(max_length + 3, 35)

            for row in ws.iter_rows(min_row=2):
                for cell in row:
                    if isinstance(cell.value, (int, float)) and ((ws.title == "Transaksi" and cell.column in (3, 4)) or (ws.title == "Ringkasan" and cell.column == 2)):
                        cell.number_format = '"Rp" #,##0'
    output.seek(0)
    return output



def make_finance_pdf(df, summary_dict, title):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()

    title_style = styles["Title"].clone("pink_title")
    title_style.textColor = colors.HexColor("#C85A7C")
    title_style.fontSize = 18
    title_style.leading = 22
    title_style.spaceAfter = 8

    subtitle_style = styles["Normal"].clone("subtitle")
    subtitle_style.textColor = colors.HexColor("#666666")
    subtitle_style.fontSize = 9
    subtitle_style.leading = 12

    label_style = styles["Normal"].clone("label")
    label_style.fontSize = 10
    label_style.leading = 13

    elements = [
        Paragraph("Elisabeth MUA", title_style),
        Paragraph(title, subtitle_style),
        Spacer(1, 10),
    ]

    summary_data = [
        ["Ringkasan", "Nominal"],
        ["Total Pemasukan", format_rupiah(summary_dict['total_pemasukan'])],
        ["Total Pengeluaran", format_rupiah(summary_dict['total_out'])],
        ["Nett (Bersih)", format_rupiah(summary_dict['nett'])],
    ]
    summary_tbl = Table(summary_data, colWidths=[250, 220])
    summary_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F19CBB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FFF7FA")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E7B6C4")),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
    ]))
    elements.extend([summary_tbl, Spacer(1, 14), Paragraph("Rincian Transaksi", label_style), Spacer(1, 6)])

    table_data = [["Tanggal", "Keterangan", "Pemasukan", "Pengeluaran"]]
    for _, row in df.iterrows():
        table_data.append([
            str(row["Tanggal"]),
            str(row["Keterangan"]),
            format_rupiah(row["Pemasukan"]) if float(row["Pemasukan"] or 0) > 0 else "-",
            format_rupiah(row["Pengeluaran"]) if float(row["Pengeluaran"] or 0) > 0 else "-"
        ])
    table_data.append([
        "",
        "TOTAL",
        format_rupiah(summary_dict["total_pemasukan"]),
        format_rupiah(summary_dict["total_out"])
    ])

    tbl = Table(table_data, colWidths=[58, 220, 95, 100], repeatRows=1)
    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D96C92")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E7B6C4")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (2, 1), (3, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(table_data)-1):
        bg = "#FFF7FA" if i % 2 == 1 else "#FFFFFF"
        table_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor(bg)))
    table_style.extend([
        ("BACKGROUND", (0, len(table_data)-1), (-1, len(table_data)-1), colors.HexColor("#FDE3EC")),
        ("FONTNAME", (0, len(table_data)-1), (-1, len(table_data)-1), "Helvetica-Bold"),
    ])
    tbl.setStyle(TableStyle(table_style))

    elements.append(tbl)
    doc.build(elements)
    output.seek(0)
    return output

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

# --- QUERY PARAM HANDLER ---
query_params = st.query_params
if query_params.get("menu") in ["BERANDA", "INPUT JADWAL", "LAYANAN", "PROFIL & SETTING", "KEUANGAN", "HAPUS DATA"]:
    st.session_state["menu_override"] = query_params.get("menu")

selected_date_param = query_params.get("selected_date")
if selected_date_param:
    try:
        st.session_state["selected_date_override"] = datetime.strptime(selected_date_param, "%Y-%m-%d").date()
    except Exception:
        pass

for key in ["beranda_cal_month", "beranda_cal_year", "hapus_cal_month", "hapus_cal_year"]:
    if query_params.get(key):
        try:
            st.session_state[key] = int(query_params.get(key))
        except Exception:
            pass

# --- MENU SIDEBAR ---
menu_list = ["BERANDA", "INPUT JADWAL", "LAYANAN", "PROFIL & SETTING", "KEUANGAN", "HAPUS DATA"]
default_menu = st.session_state.pop("menu_override", "BERANDA")
default_index = menu_list.index(default_menu) if default_menu in menu_list else 0
menu = st.sidebar.radio("MENU", menu_list, index=default_index)
# --- 1. BERANDA ---
if menu == "BERANDA":
    st.header("🌸 Jadwal Elisabeth MUA")
    today = date.today()

    cal_col1, cal_col2 = st.columns(2)
    current_month = int(st.session_state.get("beranda_cal_month", today.month))
    current_year = int(st.session_state.get("beranda_cal_year", today.year))
    selected_month_name = cal_col1.selectbox(
        "Bulan Kalender",
        MONTH_NAMES_ID,
        index=current_month - 1,
        key="beranda_month_name"
    )
    selected_year = cal_col2.selectbox(
        "Tahun Kalender",
        list(range(today.year - 2, today.year + 6)),
        index=list(range(today.year - 2, today.year + 6)).index(current_year) if current_year in list(range(today.year - 2, today.year + 6)) else 2,
        key="beranda_year_val"
    )
    selected_month = MONTH_LOOKUP_ID[selected_month_name]
    st.session_state["beranda_cal_month"] = selected_month
    st.session_state["beranda_cal_year"] = selected_year

    calendar_html, _ = render_month_calendar(st.session_state.db.get('bookings', []), selected_month, selected_year, target_menu="BERANDA", calendar_key="beranda")
    components.html(calendar_html, height=260, scrolling=False)

    selected_default = st.session_state.pop("selected_date_override", today)
    selected_date = st.date_input("Pilih Tanggal", value=selected_default)
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
                    <h3 style="margin:0; color:#F19CBB;">
<h3 style="margin:0; color:#F19CBB;">
{b.get('nama','-')} - {b.get('inv_no','-')}
</h3>

<p style="margin:5px 0;">
<b>Tim:</b> {b.get('tim_type','-') if b.get('hire_tim') else '-'}
| <b>Anggota:</b> {b.get('tim_nama','-') if b.get('hire_tim') else '-'}
</p>

<p style="margin:5px 0;">
<b>Jam Kerja:</b> {b.get('jam_ready','-')} | <b>Lokasi:</b> {b.get('alamat_mu','-')}
</p>

<p style="margin:5px 0;">
<b>Status:</b> {b.get('status','PENDING')}
</p>
</p>
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


                if 'current_faktur' in st.session_state:
                    f = st.session_state.current_faktur
                    p = st.session_state.db['profile']
                    s = st.session_state.db['faktur_settings']
                                
                    total_p = sum([float(item.get('price', 0)) * int(item.get('qty', 1)) for item in f.get('paket_list', [])])
                    total_m = sum([float(item.get('harga', 0)) * int(item.get('qty', 1)) for item in f.get('manual_list', [])])
                    total_semua = total_p + total_m
                    dp_val = float(f.get('dp', 0))
                    sisa_val = max(total_semua - dp_val, 0)
                    
                    is_lunas = f.get('status') == "SELESAI (LUNAS)"
                    warna_tema = "#4caf50" if is_lunas else "#F19CBB"
                    stempel_text = "LUNAS" if is_lunas else "BOOKED"
                
                    logo_html = ""
                    if 'logo_img' in st.session_state:
                        logo_html = f'<img src="data:image/png;base64,{st.session_state.logo_img}" style="width:70px;">'
                
                    isi_layanan = ""
                    for item in f.get('paket_list', []):
                        qty = int(item.get('qty', 1))
                        isi_layanan += f"<div style='display:flex; justify-content:space-between; gap:12px;'><span>{qty}x {item.get('nama')}</span><span>Rp {float(item.get('price',0))*qty:,.0f}</span></div>"
                    for item_m in f.get('manual_list', []):
                        qty = int(item_m.get('qty', 1))
                        isi_layanan += f"<div style='display:flex; justify-content:space-between; gap:12px;'><span>{qty}x {item_m.get('nama')}</span><span>Rp {float(item_m.get('harga',0))*qty:,.0f}</span></div>"
                
                    tnc_html = s.get('tnc','').replace('\n','<br>')
                
                    html_final = f"""
                    <div style="background:white;padding:20px;border-radius:15px;font-family:sans-serif;position:relative;">
                       <div style="
                        position:absolute;
                        top:50%;
                        left:50%;
                        transform:translate(-50%, -50%) rotate(-15deg);
                        font-size:70px;
                        font-weight:bold;
                        color:{warna_tema};
                        border:5px solid {warna_tema};
                        padding:20px 40px;
                        opacity:0.40;
                        border-radius:10px;
                        pointer-events:none;
                    ">
                        {stempel_text}
                    </div>
                        <div style="position:absolute;top:10px;left:10px;">{logo_html}</div>
                
                        <div style="display:flex; justify-content:space-between; align-items:center;">
    
    <div>
        <h3 style="margin:0; color:#F19CBB;">{p.get('nama','Elisabeth MUA')}</h3>
        <p style="margin:0; font-size:11px; color:#888;">
            {p.get('alamat','')}<br>
            WA: {p.get('hp','')}
        </p>
    </div>

    <img src="{p.get('logo','')}" style="height:60px;">

</div>
                
                        <hr>
                
                        <b>Invoice:</b> {f.get('inv_no')}<br>
                        <b>Tanggal:</b> {f.get('tgl')}<br>
                        <b>Klien:</b> {f.get('nama')}<br>
                        <b>WA:</b> {f.get('wa')}<br>
                        <b>Lokasi:</b> {f.get('alamat_mu')}<br>
                        <b>Jam:</b> {f.get('jam_ready')}<br>
                
                        <hr>
                
                        <b>RINCIAN</b>
                        {isi_layanan}
                
                        <hr>
                
                        <b>Total:</b> Rp {total_semua:,.0f}<br>
                        <b>DP:</b> Rp {dp_val:,.0f}<br>
                        <b>Sisa:</b> Rp {sisa_val:,.0f} { '(LUNAS)' if is_lunas else '' }
                
                        <hr>
                
                        <b>Transfer:</b><br>
                        {p.get('bank')} {p.get('no_rek')}<br>
                        a/n {p.get('an')}
                
                        <br><br>
                
                        <b>Syarat & Ketentuan</b><br>
                        {tnc_html}
                
                        <br><br>
                
                        <center><i>{s.get('salam')}</i></center>
                
                        <div style="text-align:right;margin-top:40px;">
                        {s.get('signature')}
                        </div>
                    </div>
                    """
                
                    st.divider()
                    components.html(html_final, height=900, scrolling=True)
                
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.download_button("💾 DOWNLOAD", html_final, file_name=f"Invoice_{f.get('nama','')}.html")
                    with col_b:
                        if st.button("❌ TUTUP"):
                            del st.session_state.current_faktur
                            st.rerun()
            
# --- 2. MENU INPUT JADWAL ---
elif menu == "INPUT JADWAL":
    st.header("📝 Tambah / Edit Jadwal")
    # ... sisa kode input jadwal ...
    
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
        jam_ready_edit = edit_data.get('jam_ready', '08:00-10:00').split('-')
        jam_mulai_default = jam_ready_edit[0] if jam_ready_edit and jam_ready_edit[0] in times else '08:00'
        jam_selesai_default = jam_ready_edit[1] if len(jam_ready_edit) > 1 and jam_ready_edit[1] in times else '10:00'
        jam_otw_default = edit_data.get('jam_otw', '07:00') if edit_data.get('jam_otw', '07:00') in times else '07:00'
        c1, c2, c3 = st.columns(3)
        jam_m = c1.selectbox("5. Jam Mulai", times, index=times.index(jam_mulai_default))
        jam_s = c2.selectbox("6. Jam Selesai", times, index=times.index(jam_selesai_default))
        jam_o = c3.selectbox("7. Jam OTW", times, index=times.index(jam_otw_default))
        
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
            tim_type_options = ["Hairdo", "Hijabdo", "Hairdo + Hijabdo"]
            default_tim_type = edit_data.get('tim_type', 'Hairdo') if edit_data.get('tim_type', 'Hairdo') in tim_type_options else 'Hairdo'
            tim_type = ct1.selectbox("Jenis Tim", tim_type_options, index=tim_type_options.index(default_tim_type))
            tim_nama = ct2.text_input("Nama Anggota Tim", value=edit_data.get('tim_nama', ""))
            fee_tim_tambahan = st.number_input("Fee Tim Tambahan (masuk otomatis ke pengeluaran)", min_value=0, value=int(edit_data.get('fee_tim_tambahan', 0)))
        else:
            tim_type, tim_nama = "-", "-"
            fee_tim_tambahan = 0

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
                    "fee_tim_tambahan": fee_tim_tambahan,
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
        import base64

        logo_file = st.file_uploader("Upload Logo", type=["png","jpg","jpeg"])

        if logo_file is not None:
            logo_base64 = base64.b64encode(logo_file.read()).decode()

            st.session_state.db['profile']['logo'] = f"data:image/png;base64,{logo_base64}"

            save_data()

            st.success("Logo berhasil disimpan")
            
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

    c1, c2 = st.columns(2)
    sel_month = c1.selectbox("Pilih Bulan", ["01","02","03","04","05","06","07","08","09","10","11","12"], index=datetime.now().month-1)
    sel_year = c2.selectbox("Pilih Tahun", ["2025","2026","2027"], index=1)

    finance_data = build_finance_report_rows(
        sel_month,
        sel_year,
        st.session_state.db.get('bookings', []),
        st.session_state.db.get('pemasukan_lain', []),
        st.session_state.db.get('pengeluaran', [])
    )

    list_pemasukan_jadwal = finance_data["list_pemasukan_jadwal"]
    omset_jadwal = finance_data["omset_jadwal"]
    list_pengeluaran_tim = finance_data["list_pengeluaran_tim"]
    total_out_tim = finance_data["total_out_tim"]
    total_in_lain = finance_data["total_in_lain"]
    total_out_manual = finance_data["total_out_manual"]
    total_out = finance_data["total_out"]
    final_omset = finance_data["final_omset"]
    nett = finance_data["nett"]

    st.subheader("📊 Pemasukan Otomatis (Jadwal)")
    if list_pemasukan_jadwal:
        st.table(pd.DataFrame(list_pemasukan_jadwal))
    else:
        st.write("Tidak ada aktivitas jadwal di bulan ini.")

    st.divider()

    st.subheader("🤝 Pengeluaran Otomatis (Fee Tim Tambahan)")
    if list_pengeluaran_tim:
        st.table(pd.DataFrame(list_pengeluaran_tim))
    else:
        st.write("Tidak ada fee tim tambahan di bulan ini.")

    st.divider()

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

    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("OMSET (Bruto)", format_rupiah(final_omset))
    res2.metric("PENGELUARAN", format_rupiah(total_out))
    res3.metric("NETT (Bersih)", format_rupiah(nett))

    st.divider()
    st.subheader("📥 Download Laporan")
    st.caption("Format rincian: Tanggal, Keterangan, Pemasukan, Pengeluaran | (ot) = otomatis, (mn) = manual")
    laporan_df = pd.DataFrame(finance_data["report_rows"])
    if not laporan_df.empty:
        laporan_tampil = laporan_df.copy()
        laporan_tampil.loc[len(laporan_tampil)] = {
            "Tanggal": "",
            "Keterangan": "TOTAL",
            "Pemasukan": finance_data["total_pemasukan"],
            "Pengeluaran": finance_data["total_out"]
        }
        st.dataframe(laporan_tampil, use_container_width=True)

        st.write(f"**Total Pemasukan:** {format_rupiah(finance_data['total_pemasukan'])}")
        st.write(f"**Total Pengeluaran:** {format_rupiah(finance_data['total_out'])}")

        report_title = f"Laporan Keuangan {sel_month}/{sel_year}"
        excel_buffer = make_finance_excel(laporan_df, finance_data)
        pdf_buffer = make_finance_pdf(laporan_df, finance_data, report_title)

        d1, d2 = st.columns(2)
        d1.download_button(
            "📊 Download Excel",
            data=excel_buffer,
            file_name=f"laporan_keuangan_{sel_month}_{sel_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        d2.download_button(
            "📄 Download PDF",
            data=pdf_buffer,
            file_name=f"laporan_keuangan_{sel_month}_{sel_year}.pdf",
            mime="application/pdf"
        )
    else:
        st.info("Belum ada data laporan untuk bulan ini.")

    if total_in_lain > 0 or total_out > 0:
        with st.expander("Lihat Rincian Manual Bulan Ini"):
            if total_in_lain > 0:
                st.write("**Pemasukan Tambahan:**")
                st.json([p for p in st.session_state.db['pemasukan_lain'] if p.get('tgl', '').split('/')[1] == sel_month and p.get('tgl', '').split('/')[2] == sel_year])
            if total_out_tim > 0:
                st.write("**Pengeluaran Otomatis Fee Tim:**")
                st.json(list_pengeluaran_tim)
            if total_out_manual > 0:
                st.write("**Pengeluaran Manual:**")
                st.json([p for p in st.session_state.db['pengeluaran'] if p.get('tgl', '').split('/')[1] == sel_month and p.get('tgl', '').split('/')[2] == sel_year])

# --- 6. HAPUS DATA ---
elif menu == "HAPUS DATA":
    st.header("🗑️ Hapus Data")
    st.warning("Hapus data dilakukan permanen. Pastikan data yang dipilih memang benar.")

    st.subheader("📅 Kalender Jadwal Realtime")
    today = date.today()
    del_col1, del_col2 = st.columns(2)
    delete_current_month = int(st.session_state.get("hapus_cal_month", today.month))
    delete_current_year = int(st.session_state.get("hapus_cal_year", today.year))
    delete_month_name = del_col1.selectbox(
        "Bulan Kalender Realtime",
        MONTH_NAMES_ID,
        index=delete_current_month - 1,
        key="hapus_month_name"
    )
    delete_year_options = list(range(today.year - 2, today.year + 6))
    delete_year = del_col2.selectbox(
        "Tahun Kalender Realtime",
        delete_year_options,
        index=delete_year_options.index(delete_current_year) if delete_current_year in delete_year_options else 2,
        key="hapus_year_val"
    )
    month_lookup = {
        "Januari": 1, "Februari": 2, "Maret": 3, "April": 4, "Mei": 5, "Juni": 6,
        "Juli": 7, "Agustus": 8, "September": 9, "Oktober": 10, "November": 11, "Desember": 12
    }
    delete_month = month_lookup[delete_month_name]
    st.session_state["hapus_cal_month"] = delete_month
    st.session_state["hapus_cal_year"] = delete_year
    delete_calendar_html, delete_booked_days = render_month_calendar(st.session_state.db.get('bookings', []), delete_month, delete_year)
    components.html(delete_calendar_html, height=430, scrolling=False)
    if delete_booked_days:
        total_jobs = sum(len(v) for v in delete_booked_days.values())
        st.caption(f"Tanggal warna biru menandakan ada jadwal. Total job bulan ini: {total_jobs}")
    else:
        st.caption("Belum ada jadwal pada bulan ini. Semua tanggal tampil normal.")

    st.divider()
    tab_booking, tab_pemasukan, tab_pengeluaran = st.tabs(["JADWAL / KLIEN", "PEMASUKAN LAIN", "PENGELUARAN MANUAL"])

    with tab_booking:
        bookings = st.session_state.db.get('bookings', [])
        if not bookings:
            st.info("Belum ada data jadwal.")
        else:
            booking_options = {
                f"{b.get('tgl','-')} | {b.get('inv_no','-')} | {b.get('nama','-')}": idx
                for idx, b in enumerate(bookings)
            }
            selected_booking_label = st.selectbox("Pilih data jadwal yang ingin dihapus", list(booking_options.keys()))
            selected_booking = bookings[booking_options[selected_booking_label]]
            st.json(selected_booking)
            if st.button("HAPUS JADWAL TERPILIH", type="primary"):
                st.session_state.db['bookings'].pop(booking_options[selected_booking_label])
                save_data()
                st.success("Data jadwal berhasil dihapus.")
                st.rerun()

    with tab_pemasukan:
        pemasukan_lain = st.session_state.db.get('pemasukan_lain', [])
        if not pemasukan_lain:
            st.info("Belum ada pemasukan lain.")
        else:
            pemasukan_options = {
                f"{p.get('tgl','-')} | {p.get('ket','-')} | Rp {float(p.get('nom',0)):,.0f}": idx
                for idx, p in enumerate(pemasukan_lain)
            }
            selected_pemasukan_label = st.selectbox("Pilih pemasukan lain yang ingin dihapus", list(pemasukan_options.keys()))
            st.json(pemasukan_lain[pemasukan_options[selected_pemasukan_label]])
            if st.button("HAPUS PEMASUKAN LAIN", type="primary"):
                st.session_state.db['pemasukan_lain'].pop(pemasukan_options[selected_pemasukan_label])
                save_data()
                st.success("Pemasukan lain berhasil dihapus.")
                st.rerun()

    with tab_pengeluaran:
        pengeluaran = st.session_state.db.get('pengeluaran', [])
        if not pengeluaran:
            st.info("Belum ada pengeluaran manual.")
        else:
            pengeluaran_options = {
                f"{p.get('tgl','-')} | {p.get('ket','-')} | Rp {float(p.get('nom',0)):,.0f}": idx
                for idx, p in enumerate(pengeluaran)
            }
            selected_pengeluaran_label = st.selectbox("Pilih pengeluaran manual yang ingin dihapus", list(pengeluaran_options.keys()))
            st.json(pengeluaran[pengeluaran_options[selected_pengeluaran_label]])
            if st.button("HAPUS PENGELUARAN MANUAL", type="primary"):
                st.session_state.db['pengeluaran'].pop(pengeluaran_options[selected_pengeluaran_label])
                save_data()
                st.success("Pengeluaran manual berhasil dihapus.")
                st.rerun()
