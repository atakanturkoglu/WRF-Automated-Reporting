"""
WRF İstanbul — Otomatik Meteoroloji Panosu
============================================
Altay HPC üzerinde günlük olarak üretilen WRF-ARW çıktılarını gösteren
Streamlit dashboard'u. Her simülasyon tarihi `data/archive/YYYY-MM-DD/`
altında arşivlenir; Altay'daki otomasyon her gün yeni bir tarih klasörü ekler
(bkz. WRF/slurm/08_yayinla.slurm).
"""
import json
from datetime import datetime
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="WRF İstanbul", page_icon="🌦️", layout="wide")

ARCHIVE_ROOT = Path(__file__).parent / "data" / "archive"

st.markdown(
    """
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 16px; }
    h1, h2, h3 { color: #90caf9; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)
def list_archive_dates():
    if not ARCHIVE_ROOT.exists():
        return []
    return sorted([p.name for p in ARCHIVE_ROOT.iterdir() if p.is_dir()], reverse=True)


@st.cache_data(ttl=300)
def load_manifest(date_str: str):
    path = ARCHIVE_ROOT / date_str / "manifest.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def fmt_parts(iso_time: str):
    dt = datetime.strptime(iso_time, "%Y-%m-%dT%H:%M:%S")
    return dt.strftime("%Y%m%d"), dt.strftime("%H"), dt


def img(data_dir: Path, name: str, caption: str | None = None):
    path = data_dir / name
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=True)
    else:
        st.info(f"Görsel henüz üretilmemiş: {name}")


st.title("🌦️ WRF İstanbul — Otomatik Meteoroloji Panosu")

available_dates = list_archive_dates()

if not available_dates:
    st.warning(
        "Henüz veri yayınlanmamış. Altay HPC'deki otomasyon ilk günlük koşuyu "
        "tamamladığında burası dolacak."
    )
    st.stop()

selected_date = st.sidebar.selectbox(
    "📅 Arşiv Tarihi (simülasyon başlangıcı)", available_dates, index=0
)
DATA_DIR = ARCHIVE_ROOT / selected_date
manifest = load_manifest(selected_date)

if manifest is None:
    st.error(f"{selected_date} için manifest.json bulunamadı.")
    st.stop()

st.sidebar.caption(f"Arşivde {len(available_dates)} tarih mevcut.")

run_start = datetime.strptime(manifest["run_start"], "%Y-%m-%dT%H:%M:%S")
run_end = datetime.strptime(manifest["run_end"], "%Y-%m-%dT%H:%M:%S")
generated_at = manifest.get("generated_at", "—")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Bölge", manifest.get("domain", "İstanbul/Marmara"))
c2.metric("Çözünürlük", f'{manifest.get("resolution_km", "—")} km')
c3.metric("Simülasyon Aralığı", f'{run_start:%d %b} → {run_end:%d %b %Y}')
c4.metric("Son Güncelleme", generated_at[:16].replace("T", " "))

st.caption(
    "Sınır koşulu: ERA5 (Copernicus CDS)  ·  Model: WRF-ARW 4.4, Lambert projeksiyonu  ·  "
    "Otomatik olarak İTÜ UHeM Altay HPC üzerinde üretilir."
)

yorum_path = DATA_DIR / "yorum.json"
if yorum_path.exists():
    yorum_data = json.loads(yorum_path.read_text())
    st.markdown(
        f"""
        <div style="background-color:#111827; border-left:4px solid #90caf9;
                    border-radius:6px; padding:16px 20px; margin:12px 0 20px 0;">
            <div style="color:#90caf9; font-weight:600; font-size:0.85em;
                        text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">
                🤖 Yapay Zeka Meteorolojik Yorumu
            </div>
            <div style="color:#e0e0e0; font-size:1.02em; line-height:1.6;">
                {yorum_data['yorum']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

times = manifest["times"]
time_labels = [datetime.strptime(t, "%Y-%m-%dT%H:%M:%S").strftime("%d %b %H:%M UTC") for t in times]
selected_label = st.sidebar.selectbox("Zaman Adımı", time_labels, index=len(time_labels) // 2)
selected_time = times[time_labels.index(selected_label)]
date_part, hour_part, _ = fmt_parts(selected_time)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Hakkında**\n\n"
    "Bu panel, İstanbul/Marmara bölgesi için Altay HPC üzerinde her gün otomatik "
    "olarak çalıştırılan WRF-ARW simülasyonunun çıktılarını gösterir: sıcaklık, "
    "rüzgar, nem, yağış, CAPE, sinoptik 500hPa durumu ve Skew-T sondajları."
)

tab_dash, tab_synop, tab_skewt, tab_summary, tab_precip, tab_meteo = st.tabs(
    ["📊 Genel Bakış", "🛰️ Sinoptik / Radar / Nem", "📈 Skew-T Sondaj",
     "🗓️ 24 Saatlik Özet", "🌧️ Yağış Animasyonu", "📉 Meteogram"]
)

with tab_dash:
    st.subheader(f"2m Sıcaklık · 10m Rüzgar · MSLP · Nem · Yağış · CAPE — {selected_label}")
    img(DATA_DIR, f"dashboard_{date_part}_{hour_part}UTC.png")

with tab_synop:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Simüle Radar Yansıtırlığı**")
        img(DATA_DIR, f"dbz_{date_part}_{hour_part}UTC.png")
    with col2:
        st.markdown("**500 hPa Sinoptik**")
        img(DATA_DIR, f"synoptic500_{date_part}_{hour_part}UTC.png")
    with col3:
        st.markdown("**Toplam Kolon Su Buharı (PWAT)**")
        img(DATA_DIR, f"pwat_{date_part}_{hour_part}UTC.png")

with tab_skewt:
    st.subheader(f"İstanbul — Skew-T Log-P Sondajı — {selected_label}")
    _, sk_col, _ = st.columns([1, 2, 1])
    with sk_col:
        img(DATA_DIR, f"skewt_istanbul_{date_part}_{hour_part}UTC.png")

with tab_summary:
    st.subheader("24 Saatlik Özet Haritaları")
    col1, col2 = st.columns(2)
    with col1:
        img(DATA_DIR, "max_sicaklik_24saat.png")
        img(DATA_DIR, "max_ruzgar_24saat.png")
    with col2:
        img(DATA_DIR, "min_sicaklik_24saat.png")
        img(DATA_DIR, "toplam_yagis_24saat.png")

with tab_precip:
    st.subheader("6 Saatlik Yağış Animasyonu")
    img(DATA_DIR, "yagis_animasyon.gif")

with tab_meteo:
    st.subheader("İstanbul — 24 Saatlik Meteogram")
    _, m_col, _ = st.columns([1, 3, 1])
    with m_col:
        img(DATA_DIR, "meteogram_istanbul.png")

st.markdown("---")
st.caption(
    "Bu panel [WRF-Automated-Reporting](https://github.com/atakanturkoglu/WRF-Automated-Reporting) "
    "reposundan otomatik dağıtılır. Kaynak: İTÜ UHeM Altay HPC."
)
