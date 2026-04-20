"""
WRF ÇIKTISI → PDF RAPOR
========================
Tüm zaman adımları için 4 değişken haritası + zaman serileri + basınç sayfası
Çıktı: 12 sayfalık PDF

Gereksinimler:
    pip install netCDF4 matplotlib numpy

Kullanım:
    python wrf_pdf_rapor.py
"""

import netCDF4 as nc
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# ⚙️  AYARLAR
# =============================================================================
WRF_FILE = "wrfout_d01_2025-05-08_00_00_00"   # ← WRF çıktı dosyası
PDF_OUTPUT   = "wrf_rapor_istanbul.pdf"             # ← Çıktı PDF adı
DPI         = 150                                  # Çözünürlük (100-200)

# =============================================================================
# 📖  VERİ OKUMA
# =============================================================================
ds = nc.Dataset(WRF_FILE)

lat  = ds.variables['XLAT'][0]
lon  = ds.variables['XLONG'][0]
times_raw = nc.chartostring(ds.variables['Times'][:])
times = [datetime.strptime(str(t), '%Y-%m-%d_%H:%M:%S') for t in times_raw]
N    = len(times)
LAND = ds.variables['LANDMASK'][0]   # 1=kara, 0=deniz

# ── Değişkenler ──────────────────────────────────────────────────────────────
# ▼ Buraya başka değişken ekleyebilirsin
T2     = ds.variables['T2'][:] - 273.15      # 2m sıcaklık [°C]
U10    = ds.variables['U10'][:]               # 10m rüzgar U [m/s]
V10    = ds.variables['V10'][:]               # 10m rüzgar V [m/s]
WS     = np.sqrt(U10**2 + V10**2)            # Hız büyüklüğü
RAINNC = ds.variables['RAINNC'][:]            # Büyük ölçekli yağış [mm]
RAINC  = ds.variables['RAINC'][:]             # Konvektif yağış [mm]
RAIN   = RAINNC + RAINC                       # Toplam yağış [mm]
PBLH   = ds.variables['PBLH'][:]             # PBL yüksekliği [m]
SWDOWN = ds.variables['SWDOWN'][:]            # Kısa dalga radyasyon [W/m²]
PSFC   = ds.variables['PSFC'][:] / 100.0     # Yüzey basıncı [hPa]
# ▲

# =============================================================================
# 🎨  TEMA & YARDIMCI FONKSİYONLAR
# =============================================================================
BG = '#0f1117'   # Arkaplan rengi
AX = '#111827'   # Eksen rengi
GR = '#aaaaaa'   # Gri metin

def stil(ax, baslik, fontsize=10):
    """Harita eksenine koyu tema uygular."""
    ax.set_facecolor(AX)
    ax.set_title(baslik, color='white', fontsize=fontsize, fontweight='bold', pad=5)
    ax.tick_params(colors=GR, labelsize=7)
    for sp in ax.spines.values(): sp.set_edgecolor('#444')
    ax.set_xlabel('Boylam (°E)', color=GR, fontsize=7)
    ax.set_ylabel('Enlem (°N)',  color=GR, fontsize=7)
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f°'))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f°'))

def cbar(fig, ax, cf, lbl):
    """Renk çubuğu ekler."""
    cb = fig.colorbar(cf, ax=ax, shrink=0.85, pad=0.02, aspect=18)
    cb.set_label(lbl, color='white', fontsize=8)
    cb.ax.yaxis.set_tick_params(color=GR, labelcolor=GR, labelsize=6)

def sea(ax):
    """Deniz/göl piksellerini koyulaştırır."""
    m = np.ma.masked_where(LAND == 1, np.ones_like(LAND))
    ax.contourf(lon, lat, m, levels=[0.5, 1.5], colors=['#0a1628'], alpha=0.65)

def tlabel(t):
    return times[t].strftime('%d %b %Y  %H:%M UTC')


# =============================================================================
# 📄  SAYFA 1: KAPAK
# =============================================================================
def kapak(pdf):
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=BG)
    ax  = fig.add_subplot(111)
    ax.set_facecolor(BG)
    ax.axis('off')

    fig.text(0.5, 0.72, 'WRF V4.6 MODEL RAPORU',
             ha='center', color='white', fontsize=28, fontweight='bold')
    fig.text(0.5, 0.62, 'İstanbul Bölgesi  ·  12 km Çözünürlük  ·  Lambert Conformal',
             ha='center', color='#90caf9', fontsize=14)
    fig.text(0.5, 0.54,
             f'Simülasyon: {tlabel(0)}  →  {tlabel(-1)}',
             ha='center', color=GR, fontsize=12)

    icerik = [
        '● Kapak ve domain özeti',
        f'● {N} × 4-panelli anlık harita  (T2 / Rüzgar / Yağış / PBLH)',
        '● Zaman serisi grafikleri (domain kara ortalaması)',
        '● Yüzey basıncı haritaları (3×3 grid)',
    ]
    for i, satir in enumerate(icerik):
        fig.text(0.18, 0.43 - i*0.055, satir, color='#e0e0e0', fontsize=11)

    fig.text(0.5, 0.06,
             f'Oluşturuldu: {datetime.now().strftime("%d %B %Y")}  ·  WRF-ARW V4.6.0',
             ha='center', color='#555', fontsize=9)

    # Domain mini-haritası
    ax2 = fig.add_axes([0.63, 0.36, 0.24, 0.27])
    ax2.set_facecolor('#0d1b2a')
    ax2.contourf(lon, lat, LAND, levels=[0.5,1.5], colors=['#2d4a22'], alpha=0.8)
    ax2.contour(lon, lat, LAND, levels=[0.5], colors=['#aaa'], linewidths=0.7)
    ax2.set_title('Domain', color='white', fontsize=9)
    ax2.tick_params(colors=GR, labelsize=6)
    ax2.set_xlabel('°E', color=GR, fontsize=7)
    ax2.set_ylabel('°N', color=GR, fontsize=7)
    for sp in ax2.spines.values(): sp.set_edgecolor('#444')

    pdf.savefig(fig, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    print("  ✓ Kapak sayfası")


# =============================================================================
# 📄  SAYFALAR 2-10: Her zaman adımı için 4-panelli harita
# =============================================================================
def harita_sayfalari(pdf):
    for t in range(N):
        tl = tlabel(t)
        fig, axes = plt.subplots(2, 2, figsize=(16.54, 11.69), facecolor=BG)
        fig.patch.set_facecolor(BG)

        # ── Panel 1: 2m Sıcaklık ──────────────────────────────────────────
        # ▼ DEĞİŞTİRİLEBİLİR: data1, cmap1, seviye1, unit1
        ax = axes[0, 0]
        data1  = T2[t]
        cmap1  = 'RdYlBu_r'
        unit1 = '°C'
        # ▲
        cf = ax.contourf(lon, lat, data1, levels=20, cmap=cmap1, alpha=0.9)
        sea(ax)
        cs = ax.contour(lon, lat, data1, levels=8, colors='white', linewidths=0.25, alpha=0.35)
        ax.clabel(cs, inline=True, fontsize=5.5, colors='white', fmt='%.1f')
        cbar(fig, ax, cf, unit1)
        stil(ax, f'2m Sıcaklık (T2)  —  {tl}')

        # ── Panel 2: Rüzgar ───────────────────────────────────────────────
        # ▼ DEĞİŞTİRİLEBİLİR: arrow_step, arrow_scale
        ax = axes[0, 1]
        arrow_step = 2   # Her kaç gridde bir ok (1=sık, 3=seyrek)
        arrow_scale  = 45  # Ok boyu (büyük=küçük oklar)
        # ▲
        cf = ax.contourf(lon, lat, WS[t], levels=15, cmap='YlOrRd', alpha=0.9)
        sea(ax)
        sk = arrow_step
        ax.quiver(lon[::sk,::sk], lat[::sk,::sk],
                  U10[t,::sk,::sk], V10[t,::sk,::sk],
                  scale=arrow_scale, width=0.004, color='white', alpha=0.85, zorder=5)
        cbar(fig, ax, cf, 'm/s')
        stil(ax, f'10m Rüzgar Hızı & Yönü  —  {tl}')

        # ── Panel 3: Artımlı Yağış ────────────────────────────────────────
        # ▼ DEĞİŞTİRİLEBİLİR: seviyeler yağış eşikleri
        ax = axes[1, 0]
        rain_inc = RAIN[t] - RAIN[t-1] if t > 0 else RAIN[0]
        rain_inc = np.where(rain_inc < 0, 0, rain_inc)
        lvls = [0.1, 0.5, 1, 2, 5, 10, 20, 30, 50]   # ← değiştir
        # ▲
        if rain_inc.max() > 0.1:
            cf = ax.contourf(lon, lat, rain_inc, levels=lvls,
                             cmap='Blues', extend='max', alpha=0.92)
            cbar(fig, ax, cf, 'mm / 3 sa')
        else:
            ax.contourf(lon, lat, LAND, levels=[0.5,1.5], colors=['#1a2a1a'], alpha=0.5)
            ax.text(0.5, 0.5, 'Bu adımda yağış yok', transform=ax.transAxes,
                    ha='center', va='center', color='#aaa', fontsize=12)
        sea(ax)
        stil(ax, f'Artımlı Yağış (RAINNC + RAINC)  —  {tl}')

        # ── Panel 4: PBL Yüksekliği ───────────────────────────────────────
        # ▼ DEĞİŞTİRİLEBİLİR: data4, cmap4, unit4
        ax = axes[1, 1]
        data4  = PBLH[t]
        cmap4  = 'plasma'
        unit4 = 'm'
        # ▲
        cf = ax.contourf(lon, lat, data4, levels=20, cmap=cmap4, alpha=0.9)
        sea(ax)
        cs = ax.contour(lon, lat, data4, levels=6, colors='white', linewidths=0.25, alpha=0.4)
        ax.clabel(cs, inline=True, fontsize=5.5, colors='white', fmt='%.0f')
        cbar(fig, ax, cf, unit4)
        stil(ax, f'PBL Yüksekliği (PBLH)  —  {tl}')

        fig.suptitle(
            f'Zaman Adımı {t+1}/{N}  ·  {tl}  ·  WRF İstanbul Bölgesi',
            color='white', fontsize=13, fontweight='bold', y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.993])
        pdf.savefig(fig, facecolor=BG, bbox_inches='tight')
        plt.close(fig)
        print(f"  ✓ Harita adım {t+1}/{N}  ({tl})")


# =============================================================================
# 📄  SAYFA 11: ZAMAn SERİLERİ
# =============================================================================
def zaman_serisi_sayfasi(pdf):
    lm = LAND == 1

    T2m   = [T2[t][lm].mean()     for t in range(N)]
    T2mx  = [T2[t][lm].max()      for t in range(N)]
    T2mn  = [T2[t][lm].min()      for t in range(N)]
    WSm   = [WS[t][lm].mean()     for t in range(N)]
    WSmx  = [WS[t][lm].max()      for t in range(N)]
    PBLm  = [PBLH[t][lm].mean()   for t in range(N)]
    SWm   = [SWDOWN[t][lm].mean() for t in range(N)]
    Pm    = [PSFC[t][lm].mean()   for t in range(N)]
    Rinc  = [0] + [max(0,(RAIN[t]-RAIN[t-1])[lm].mean()) for t in range(1, N)]
    Rcum  = [max(0,(RAIN[t]-RAIN[0])[lm].mean())         for t in range(N)]

    fig, axes = plt.subplots(3, 2, figsize=(16.54, 11.69), facecolor=BG)
    fig.patch.set_facecolor(BG)

    def sax(ax, ylabel, title):
        ax.set_facecolor(AX)
        ax.set_title(title, color='white', fontsize=10, fontweight='bold', pad=4)
        ax.set_ylabel(ylabel, color=GR, fontsize=8)
        ax.tick_params(colors=GR, labelsize=7)
        for sp in ax.spines.values(): sp.set_edgecolor('#444')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m\n%H UTC'))
        ax.grid(alpha=0.12, color='gray', ls='--')

    # T2
    ax = axes[0, 0]
    ax.fill_between(times, T2mn, T2mx, alpha=0.22, color='#ff7043')
    ax.plot(times, T2m,  'o-', color='#ff7043', lw=2, ms=5, label='Ort')
    ax.plot(times, T2mx, '--', color='#ffccbc', lw=1, alpha=0.7, label='Maks')
    ax.plot(times, T2mn, '--', color='#b71c1c', lw=1, alpha=0.7, label='Min')
    ax.legend(fontsize=7, facecolor='#1a1a2e', labelcolor='white', framealpha=0.7)
    sax(ax, '°C', '2m Sıcaklık — Ort / Min / Maks')

    # Rüzgar
    ax = axes[0, 1]
    ax.plot(times, WSmx, '--', color='#b3e5fc', lw=1.2, alpha=0.7, label='Maks')
    ax.plot(times, WSm,  's-', color='#4fc3f7', lw=2,   ms=5,      label='Ort')
    ax.fill_between(times, 0, WSm, alpha=0.18, color='#4fc3f7')
    ax.legend(fontsize=7, facecolor='#1a1a2e', labelcolor='white', framealpha=0.7)
    sax(ax, 'm/s', '10m Rüzgar Hızı — Ort / Maks')

    # Artımlı yağış
    ax = axes[1, 0]
    ax.bar(times, Rinc, width=0.09, color='#42a5f5', edgecolor='#1565c0', alpha=0.85)
    ax.set_facecolor(AX)
    sax(ax, 'mm / 3 saat', 'Artımlı Yağış (3 saatlik adım)')

    # Kümülatif yağış
    ax = axes[1, 1]
    ax.plot(times, Rcum, 'o-', color='#29b6f6', lw=2, ms=5)
    ax.fill_between(times, 0, Rcum, alpha=0.2, color='#29b6f6')
    sax(ax, 'mm', 'Kümülatif Yağış (00 UTC bazlı)')

    # PBLH + SWDOWN
    ax = axes[2, 0]
    ax.plot(times, PBLm, 'D-', color='#ce93d8', lw=2, ms=5)
    ax.fill_between(times, 0, PBLm, alpha=0.18, color='#ce93d8')
    ax2b = ax.twinx()
    ax2b.plot(times, SWm, '--', color='#ffd54f', lw=1.8, alpha=0.85)
    ax2b.set_ylabel('W/m²', color='#ffd54f', fontsize=8)
    ax2b.tick_params(colors='#ffd54f', labelsize=7)
    for sp in ax2b.spines.values(): sp.set_edgecolor('#444')
    sax(ax, 'm', 'PBL Yüksekliği (mor) + SWDOWN (sarı)')

    # Basınç
    ax = axes[2, 1]
    ax.plot(times, Pm, '^-', color='#a5d6a7', lw=2, ms=5)
    ax.fill_between(times, min(Pm)-0.5, Pm, alpha=0.18, color='#a5d6a7')
    sax(ax, 'hPa', 'Yüzey Basıncı (PSFC) — Kara Ort')

    fig.suptitle('WRF Zaman Serileri  ·  Kara Noktaları Ortalaması  ·  8–9 Mayıs 2025',
                 color='white', fontsize=13, fontweight='bold', y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.993])
    pdf.savefig(fig, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    print("  ✓ Zaman serileri sayfası")


# =============================================================================
# 📄  SAYFA 12: YÜZEY BASINCI 3×3 GRID
# =============================================================================
def basinc_sayfasi(pdf):
    fig, axes = plt.subplots(3, 3, figsize=(16.54, 11.69), facecolor=BG)
    fig.patch.set_facecolor(BG)

    for t in range(N):
        ax = axes[t // 3, t % 3]
        cf = ax.contourf(lon, lat, PSFC[t], levels=15, cmap='coolwarm', alpha=0.9)
        sea(ax)
        cs = ax.contour(lon, lat, PSFC[t], levels=8, colors='white',
                        linewidths=0.25, alpha=0.4)
        ax.clabel(cs, inline=True, fontsize=5, colors='white', fmt='%.0f')
        cb = fig.colorbar(cf, ax=ax, shrink=0.8, pad=0.02)
        cb.ax.yaxis.set_tick_params(labelsize=5, labelcolor=GR)
        ax.set_title(times[t].strftime('%d/%m  %H UTC'),
                     color='white', fontsize=8, fontweight='bold', pad=3)
        ax.tick_params(colors=GR, labelsize=5)
        ax.set_facecolor(AX)
        for sp in ax.spines.values(): sp.set_edgecolor('#444')

    fig.suptitle('Yüzey Basıncı (PSFC)  ·  Tüm Zaman Adımları  ·  hPa',
                 color='white', fontsize=13, fontweight='bold', y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.993])
    pdf.savefig(fig, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    print("  ✓ Yüzey basıncı sayfası (3×3 grid)")


# =============================================================================
# 🚀  ÇALIŞTIR
# =============================================================================
print(f"PDF oluşturuluyor → {PDF_OUTPUT}")
print(f"  {N} zaman adımı okundu: {tlabel(0)} → {tlabel(-1)}\n")

with PdfPages(PDF_OUTPUT) as pdf:
    meta = pdf.infodict()
    meta['Title']   = 'WRF Model Raporu — İstanbul'
    meta['Author']  = 'WRF V4.6.0'
    meta['Subject'] = '8-9 Mayıs 2025 Simülasyonu'

    kapak(pdf)
    harita_sayfalari(pdf)
    zaman_serisi_sayfasi(pdf)
    basinc_sayfasi(pdf)

import os
size = os.path.getsize(PDF_OUTPUT) / (1024 * 1024)
print(f"\n✅ Tamamlandı!  {PDF_OUTPUT}  ({size:.1f} MB)")
ds.close()
