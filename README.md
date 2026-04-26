# West Bengal 2026 Election Forecast Dashboard

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://west-bengal-2026-election-winner.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Live App →** [https://west-bengal-2026-election-winner.streamlit.app/](https://west-bengal-2026-election-winner.streamlit.app/)

An advanced scenario-modeling dashboard for the **2026 West Bengal Legislative Assembly Election**, built from the official 2026 constituency-wise elector PDF and 2021 election results.

---

## Screenshots

| Overview | Vulnerability Analysis |
|---|---|
| Hero metrics, Scenario Story, Party seat chart, Bloc donut | Hot/Watch/Safe seat tiers, phase-wise breakdown |

---

## Features

- **6 Analytical Tabs**
  - **Overview** — Hero metrics, Scenario Story, Projected Seats by Party, Gain/Loss vs 2021, Bloc donut chart
  - **District & Flips** — Seat flip list with 2021 margins, district intensity heatmap
  - **Elector Breakdown** — Male/Female split by district, seat-size distribution, Top-15 constituencies
  - **Vulnerability** — Hot (<5 pp margin), Watch (5–10 pp), Safe (>10 pp) tiers
  - **All Seats** — Live search, full seat-level table, CSV export
  - **2021 Source Data** — Searchable 2021 Wikipedia results table, CSV download

- **Scenario Presets**
  - BJP Phase 1 Lead Scenario
  - BJP Statewide Lead Scenario
  - Baseline 2021 Carry Forward
  - Custom (free sliders for AITC, BJP, Left-Cong-ISF swing)

- **Party-branded color palette** (AITC Green, BJP Saffron, Left-Cong-ISF Red)
- **Premium dark UI** with glassmorphism cards, Inter typography, hover animations

---

## Data Sources

| Dataset | Source |
|---|---|
| 2026 Elector Data | `Elector_WBLA2026.pdf` — Official ECI publication |
| 2021 Results | Wikipedia: *Results of the 2021 West Bengal Legislative Assembly election* |

> **Important caveat:** Elector counts alone cannot reliably predict the 2026 winner. This dashboard is useful for seat sizing, district comparison, close-seat analysis, and scenario testing with uniform swing assumptions. It is **not** a substitute for polling, candidate-level data, alliance data, or turnout forecasts.

---

## Project Structure

```
.
├── app.py                    # Streamlit dashboard (main entry point)
├── build_data.py             # Data pipeline: PDF + HTML → CSVs
├── wb2021_results.html       # Saved Wikipedia source page
├── wb_2021_results.csv       # Parsed 2021 constituency results
├── wb_2026_electors.csv      # Parsed 2026 elector counts
├── wb_2026_model_input.csv   # Merged model input (used by dashboard)
├── requirements.txt          # Python dependencies
└── README.md
```

---

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/chandril-mallick/West-Bengal-2026-Election-Forecast.git
cd West-Bengal-2026-Election-Forecast
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. (Optional) Rebuild data from PDF

Place `Elector_WBLA2026.pdf` in your `~/Downloads/` folder, then run:

```bash
python build_data.py
```

This regenerates `wb_2026_electors.csv`, `wb_2021_results.csv`, and `wb_2026_model_input.csv`.

### 4. Launch the dashboard

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## How the Swing Model Works

For each constituency, the model:

1. Takes the **2021 vote shares** for each political bloc as the baseline.
2. Applies a **uniform swing** (in percentage points) to the AITC Bloc, BJP, and Left-Cong-ISF Bloc.
3. **Re-normalises** shares to sum to 100%.
4. The bloc with the highest projected share **wins the seat**.
5. Party-level winner is inferred from the 2021 winner/runner-up data within each winning bloc.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Dashboard | [Streamlit](https://streamlit.io/) |
| Data Processing | [pandas](https://pandas.pydata.org/), [pypdf](https://pypdf.readthedocs.io/) |
| Visualisation | [Plotly Express](https://plotly.com/python/plotly-express/) / [Graph Objects](https://plotly.com/python/) |
| HTML Parsing | [lxml](https://lxml.de/) |
| Language | Python 3.9+ |

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## Author

**Chandril Mallick**  
[GitHub](https://github.com/chandril-mallick)

---

*This is a research/educational tool. Projections are based on a simplified uniform-swing model and should not be interpreted as election predictions or official forecasts.*
