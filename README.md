# WB 2026 Election Forecast Dashboard

This project turns the PDF dataset at `/Users/chandrilmallick/Downloads/Elector_WBLA2026.pdf` into a constituency-level dashboard and joins it with 2021 West Bengal Assembly results for a baseline forecast.

## What the model does

- Extracts 2026 elector counts for all 294 assembly constituencies.
- Joins them with 2021 constituency winners and runners-up.
- Uses a simple swing-based scenario model to project seat changes.

## Important caveat

Elector counts alone cannot reliably predict the 2026 winner. The dashboard is useful for:

- seat sizing
- district comparison
- close-seat analysis
- scenario testing with uniform swing assumptions

It is not a substitute for polling, candidate-level data, alliances, or turnout forecasts.

## Files

- `build_data.py`: extracts and joins the raw data
- `app.py`: Streamlit dashboard
- `wb2021_results.html`: downloaded 2021 results source page

## Run

```bash
python3 build_data.py
streamlit run app.py
```
