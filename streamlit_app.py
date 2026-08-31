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


def parse_time(t: str) -> datetime:
    """WRF'in kendi zaman formatı ('_' ayraçlı) ile eski ISO formatı ('T' ayraçlı) ikisini de kabul eder."""
    for fmt in ("%Y-%m-%d_%H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            continue
    raise ValueError(f"Tanınmayan zaman formatı: {t}")


def fmt_parts(time_str: str):
    dt = parse_time(time_str)
    return dt.strftime("%Y%m%d"), dt.strftime("%H"), dt


def img(data_dir: Path, name: str, caption: str | None = None):
    path = data_dir / name
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=True)
    else:
        st.info(f"Görsel henüz üretilmemiş: {name}")


def video(data_dir: Path, name: str, caption: str | None = None):
    path = data_dir / name
    if path.exists():
        st.video(str(path))
        if caption:
            st.caption(caption)
        return True
    return False


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

run_start = parse_time(manifest["run_start"])
run_end = parse_time(manifest["run_end"])
generated_at = manifest.get("generated_at", "—")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Bölge", manifest.get("domain", "İstanbul/Marmara"))
c2.metric("Çözünürlük", f'{manifest.get("resolution_km", "—")} km')
c3.metric("Simülasyon Aralığı", f'{run_start:%d %b} → {run_end:%d %b %Y}')
c4.metric("Son Güncelleme", generated_at[:16].replace("T", " "))

st.caption(
    "Sınır koşulu: GFS (NCEP)  ·  Model: WRF-ARW 4.4, 3km, Lambert projeksiyonu  ·  "
    "Otomatik olarak İTÜ UHeM Altay HPC üzerinde üretilir."
)

durum_path = DATA_DIR / "durum.json"
if durum_path.exists():
    durum_data = json.loads(durum_path.read_text())
    saglikli = durum_data.get("genel_durum") == "sağlıklı"
    renk = "#1b3a2b" if saglikli else "#3a1b1b"
    kenar = "#2ecc71" if saglikli else "#e74c3c"
    ikon = "✅" if saglikli else "⚠️"
    detay = "Tüm ajanlar sorunsuz tamamlandı." if saglikli else \
        "; ".join(durum_data.get("sorunlar", [])) or "Detay yok."
    st.markdown(
        f"""
        <div style="background-color:{renk}; border-left:4px solid {kenar};
                    border-radius:6px; padding:10px 16px; margin:4px 0 16px 0; font-size:0.9em;">
            {ikon} <b>Sistem Durumu: {durum_data.get('genel_durum', '—').capitalize()}</b>
            — {detay}
            <span style="color:#888; float:right;">Kontrol: {durum_data.get('kontrol_zamani', '—')[:16].replace('T',' ')}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

yorum_path = DATA_DIR / "yorum.json"
if yorum_path.exists():
    yorum_data = json.loads(yorum_path.read_text())
    ilce_rozetleri = ""
    ilceler = yorum_data.get("ilce_yagis_one_cikanlar", [])
    if ilceler:
        rozetler = "".join(
            f'<span style="background-color:#0d2438; border:1px solid #2f5d7a; '
            f'border-radius:14px; padding:4px 12px; margin:3px 6px 3px 0; '
            f'display:inline-block; font-size:0.85em; color:#8ecbe6;">'
            f'📍 <b>{i["ilce"]}</b> — {i["zaman"]} ({i["mm"]} mm)</span>'
            for i in ilceler
        )
        ilce_rozetleri = f'<div style="margin-top:10px;">{rozetler}</div>'
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
            {ilce_rozetleri}
        </div>
        """,
        unsafe_allow_html=True,
    )

times = manifest.get("detay_times", manifest["times"])
ufuk_saat = manifest.get("ufuk_saat", 24)
time_labels = [parse_time(t).strftime("%d %b %H:%M UTC") for t in times]
selected_label = st.sidebar.selectbox("Zaman Adımı (detaylı görseller)", time_labels, index=0)
selected_time = times[time_labels.index(selected_label)]
date_part, hour_part, _ = fmt_parts(selected_time)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Hakkında**\n\n"
    "Bu panel, İstanbul için Altay HPC üzerinde her gün otomatik olarak "
    "çalıştırılan 3km çözünürlüklü WRF-ARW simülasyonunun çıktılarını gösterir: "
    "sıcaklık, rüzgar, nem, yağış, CAPE, sinoptik 500hPa durumu ve Skew-T sondajları."
)

tab_dash, tab_synop, tab_skewt, tab_summary, tab_precip, tab_meteo = st.tabs(
    ["📊 Genel Bakış", "🛰️ Sinoptik / Radar / Nem", "📈 Skew-T Sondaj",
     f"🗓️ {ufuk_saat} Saatlik Özet", "🌧️ Yağış Animasyonu", "📉 Meteogram"]
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
    st.subheader(f"{ufuk_saat} Saatlik Özet Haritaları")
    col1, col2 = st.columns(2)
    with col1:
        img(DATA_DIR, f"max_sicaklik_{ufuk_saat}saat.png")
        img(DATA_DIR, f"max_ruzgar_{ufuk_saat}saat.png")
    with col2:
        img(DATA_DIR, f"min_sicaklik_{ufuk_saat}saat.png")
        img(DATA_DIR, f"toplam_yagis_{ufuk_saat}saat.png")

with tab_precip:
    st.subheader("Saatlik Yağış Animasyonu")
    # MP4 (durdur/geri sar/ilerleme çubuğu) öncelikli; eski günlerde sadece
    # GIF olabilir (bu özellik eklenmeden önce üretilmiş), ona geri düşülür.
    if not video(DATA_DIR, "yagis_animasyon.mp4"):
        img(DATA_DIR, "yagis_animasyon.gif")

with tab_meteo:
    st.subheader(f"İstanbul — {ufuk_saat} Saatlik Meteogram")
    _, m_col, _ = st.columns([1, 3, 1])
    with m_col:
        img(DATA_DIR, "meteogram_istanbul.png")

st.markdown("---")
st.caption(
    "Bu panel [WRF-Automated-Reporting](https://github.com/atakanturkoglu/WRF-Automated-Reporting) "
    "reposundan otomatik dağıtılır. Kaynak: İTÜ UHeM Altay HPC."
)
