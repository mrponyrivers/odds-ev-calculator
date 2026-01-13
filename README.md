cd ~/ai-journey/odds-ev-calculator

cat > README.md <<'MD'
# Odds + EV Calculator (CLI + Web App)

A small Python tool that:
- Converts **American odds** (e.g., `-110` / `+150`) to **decimal odds**
- Computes **implied probability**, **edge**, and **EV per $1 staked**
- Suggests a **Kelly-scaled recommended stake** (with a max stake cap)
- Works as both:
  - a **CSV CLI tool** (input CSV → output CSV + report)
  - a **Streamlit web app** (upload CSV → download results)

## Live Demo (Web App)
https://odds-ev-calculator-ponyrivers.streamlit.app/

---

## CSV Input Format

Your input CSV must have these headers:

```csv
bet_name,american_odds,win_prob
Game1,-110,0.55
Game2,150,0.42
Game3,-200,0.70

