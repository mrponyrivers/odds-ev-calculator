# Odds + EV Calculator (CLI + Web App)

**Live app:** https://odds-ev-calculator-ponyrivers.streamlit.app/

A small Python tool that:
- Converts **American odds** (e.g., `-110` / `+150`) to **decimal odds**
- Computes **implied probability**, **edge**, and **EV per $1 staked**
- Suggests a **Kelly-scaled recommended stake** (with a max stake cap)
- Works as both:
  - a **CSV CLI tool** (input CSV → output CSV + report)
  - a **Streamlit web app** (upload CSV → download results)

## Screenshot
![App screenshot](PUT_YOUR_SCREENSHOT_FILENAME_HERE)

## Architecture
- **Web App (Streamlit):** `app.py` (upload CSV → view results → download outputs)
- **Core logic:** `src/odds_ev_tool/core.py` (odds conversion, implied prob, EV, Kelly sizing)
- **CLI:** `src/odds_ev_tool/cli.py` (batch CSV processing + `report.md`)

## Tech
Python • Streamlit • pandas • CSV I/O • Git/GitHub

## CSV Input Format

```csv
bet_name,american_odds,win_prob
Game1,-110,0.55
Game2,150,0.42
Game3,-200,0.70
