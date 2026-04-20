#  WRF Istanbul — Automated PDF Report Generator

> A Python script that automatically generates beautiful, dark-themed multi-page PDF meteorology reports from WRF-ARW output files.

---

##  Sample Output

| Cover & Domain | 4-Panel Map | Time Series | Surface Pressure |
|:-:|:-:|:-:|:-:|
| Domain summary + simulation info | T2 · Wind · Precip · PBLH | Land-averaged plots | 3×3 all timesteps |

> **Simulation:** 08 May 2025 00:00 UTC → 09 May 2025 00:00 UTC  
> **Model:** WRF-ARW V4.6.0 · 12 km resolution · Lambert Conformal · d01

---

##  Project Structure

```
wrf-istanbul-pdf-report/
├── wrf_pdf_report.py             # Main script
├── wrfout_d01_2025-05-08_00_*   # WRF output file (NetCDF)
├── wrf_report_istanbul.pdf       # Generated PDF report (example)
├── requirements.txt
└── README.md
```

---

##  Quick Start

### 1. Install Requirements

```bash
pip install -r requirements.txt
```

### 2. Set Your WRF File

Edit the configuration block at the top of `wrf_pdf_report.py`:

```python
WRF_FILE   = "wrfout_d01_2025-05-08_00_00_00"   # ← your WRF output file
PDF_OUTPUT = "wrf_report_istanbul.pdf"            # ← desired PDF name
DPI        = 150                                  # ← resolution (100–200)
```

### 3. Run

```bash
python wrf_pdf_report.py
```

Expected terminal output:
```
Generating PDF → wrf_report_istanbul.pdf
  9 timesteps loaded: 08 May 2025 00:00 UTC → 09 May 2025 00:00 UTC

  ✓ Cover page
  ✓ Map timestep 1/9  (08 May 2025  00:00 UTC)
  ...
  ✓ Time series page
  ✓ Surface pressure page (3×3 grid)

✅ Done!  wrf_report_istanbul.pdf  (X.X MB)
```

---

## PDF Contents (12 Pages)

| Page | Content |
|------|---------|
| **1** | Cover — title, simulation info, domain mini-map |
| **2–10** | 4-panel map per timestep (T2 · Wind · Precip · PBLH) |
| **11** | Time series — land-averaged plots (T2, Wind, Precip, PBLH, PSFC) |
| **12** | Surface pressure (PSFC) — all timesteps in a 3×3 grid |

---

##  Maps & Variables

| Panel | Variable | Source | Unit |
|-------|----------|--------|------|
| Top left | 2m Temperature | `T2` | °C |
| Top right | 10m Wind speed & direction | `U10` / `V10` | m/s |
| Bottom left | Incremental precipitation | `RAINNC + RAINC` | mm / 3 hr |
| Bottom right | PBL height | `PBLH` | m |

---

##  Customization

Look for `# ▼ EDITABLE` comment blocks in the script to easily:

- Change the **color map** (`cmap='RdYlBu_r'` → any matplotlib cmap)
- Adjust **contour levels**
- Control **wind arrow density & scale** (`arrow_step`, `arrow_scale`)
- Set custom **precipitation thresholds** (`lvls = [0.1, 0.5, 1, ...]`)
- **Swap any variable** in the 4th panel by changing `data4 = PBLH[t]`

---

##  Requirements

- Python ≥ 3.8
- `netCDF4`
- `matplotlib`
- `numpy`

---

##  Contributing

Pull requests and suggestions are welcome. Feel free to open an issue for new panel types, projection support, or animation output.

---

##  License

MIT License — free to use and distribute.

