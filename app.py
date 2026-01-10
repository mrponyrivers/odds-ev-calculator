import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

# --- Make imports work on Streamlit Cloud (and locally) ---
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from odds_ev_tool.core import (  # noqa: E402
    american_to_decimal,
    compute_row,
    kelly_fraction,
    parse_american_odds,
)


def build_report_md(args, rows_out, plus_rows, errors, avg_ev, avg_edge, total_stake):
    valid = rows_out[rows_out["edge"].apply(lambda x: isinstance(x, float))].copy()
    top = valid.sort_values("edge", ascending=False).head(5)

    lines = []
    lines.append("# Odds EV Tool Report")
    lines.append(f"- Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Run settings")
    for k, v in args.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Rows kept: {len(rows_out)}")
    lines.append(f"- Errors: {errors}")
    lines.append(f"- +EV rows (ev >= {args['min_ev']}): {len(plus_rows)}")
    lines.append(f"- Avg EV per $1: {avg_ev:.4f}")
    lines.append(f"- Avg edge: {avg_edge:.4f}")
    lines.append(f"- Total recommended stake (sum): {total_stake:.2f}")
    lines.append("")
    lines.append("## Top bets by edge (up to 5)")
    if top.empty:
        lines.append("- (none)")
    else:
        for _, r in top.iterrows():
            lines.append(
                f"- {r['bet_name']}: edge={r['edge']:.4f}, ev={r['ev_per_1']:.4f}, stake={float(r['rec_stake']):.2f}"
            )
    return "\n".join(lines) + "\n"


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


st.set_page_config(page_title="Odds EV Tool", page_icon="📈", layout="wide")

st.title("📈 Odds EV Tool — Web App")
st.caption("Upload bets.csv → get results + plus_ev + report. (Built from your CLI tool.)")

uploaded = st.file_uploader("Upload bets.csv", type=["csv"])

with st.sidebar:
    st.header("Settings")
    bankroll = st.number_input("Bankroll", min_value=0.0, value=500.0, step=50.0)
    kelly_scale = st.number_input("Kelly scale", min_value=0.0, value=0.25, step=0.05)
    max_stake_pct = st.number_input("Max stake % of bankroll", min_value=0.0, value=0.05, step=0.01)
    min_ev = st.number_input("Min EV for +EV file", value=0.02, step=0.01)
    min_edge = st.number_input("Min edge filter (optional)", value=0.0, step=0.01)
    apply_min_edge = st.checkbox("Apply min edge filter", value=False)

st.divider()

if not uploaded:
    st.info("Upload a CSV with headers: bet_name, american_odds, win_prob")
    st.code("bet_name,american_odds,win_prob\nGame1,-110,0.55\nGame2,150,0.42\nGame3,-200,0.70")
    st.stop()

# Read CSV
try:
    df_in = pd.read_csv(uploaded)
except Exception as e:
    st.error(f"Could not read CSV: {e}")
    st.stop()

# --- DEBUG (temporary): proves what file Streamlit received ---
st.info(f"DEBUG: uploaded file name = {uploaded.name}")
st.info(f"DEBUG: uploaded file size (bytes) = {uploaded.size}")
st.info(f"DEBUG: rows read = {len(df_in)}")
if "bet_name" in df_in.columns:
    st.write("DEBUG: bet_name values:", list(df_in["bet_name"].astype(str)))
# ------------------------------------------------------------

required = {"bet_name", "american_odds", "win_prob"}
if not required.issubset(set(df_in.columns)):
    st.error(f"CSV must contain columns: {sorted(required)}. Found: {list(df_in.columns)}")
    st.stop()

rows = []
errors = 0

for _, r in df_in.iterrows():
    try:
        bet_name = str(r["bet_name"]).strip() if pd.notna(r["bet_name"]) else "Unnamed"
        american = parse_american_odds(str(r["american_odds"]))
        win_prob = float(r["win_prob"])

        base = compute_row(bet_name, american, win_prob)

        if apply_min_edge and base["edge"] < float(min_edge):
            continue

        dec = american_to_decimal(american)
        kf = kelly_fraction(win_prob, dec)

        rec_stake = bankroll * kf * kelly_scale
        rec_stake = min(rec_stake, bankroll * max_stake_pct)
        rec_stake = max(0.0, rec_stake)

        base["kelly_fraction"] = round(kf, 4)
        base["rec_stake"] = round(rec_stake, 2)
        base["decision"] = "+EV" if base["ev_per_1"] > 0 else ("-EV" if base["ev_per_1"] < 0 else "EV=0")

        rows.append(base)

    except Exception as e:
        errors += 1
        rows.append({
            "bet_name": r.get("bet_name", ""),
            "american_odds": r.get("american_odds", ""),
            "win_prob": r.get("win_prob", ""),
            "decimal_odds": "",
            "implied_prob": "",
            "edge": "",
            "ev_per_1": "",
            "kelly_fraction": "",
            "rec_stake": "",
            "decision": f"ERROR: {e}",
        })

df_out = pd.DataFrame(rows)

# Ensure column order
cols = [
    "bet_name", "american_odds", "win_prob",
    "decimal_odds", "implied_prob", "edge", "ev_per_1",
    "kelly_fraction", "rec_stake", "decision"
]
df_out = df_out.reindex(columns=[c for c in cols if c in df_out.columns])

df_plus = df_out[
    df_out["ev_per_1"].apply(lambda x: isinstance(x, float)) &
    (df_out["ev_per_1"] >= float(min_ev))
].copy()

# Summary stats
valid_ev = df_out["ev_per_1"].dropna()
valid_ev = valid_ev[valid_ev.apply(lambda x: isinstance(x, float))]
valid_edge = df_out["edge"].dropna()
valid_edge = valid_edge[valid_edge.apply(lambda x: isinstance(x, float))]

avg_ev = float(valid_ev.mean()) if len(valid_ev) else 0.0
avg_edge = float(valid_edge.mean()) if len(valid_edge) else 0.0
total_stake = float(df_out["rec_stake"].dropna().sum()) if "rec_stake" in df_out.columns else 0.0

args = {
    "bankroll": bankroll,
    "kelly_scale": kelly_scale,
    "max_stake_pct": max_stake_pct,
    "min_ev": float(min_ev),
    "min_edge": float(min_edge) if apply_min_edge else None,
}

report_md = build_report_md(args, df_out, df_plus, errors, avg_ev, avg_edge, total_stake)

# Layout
col1, col2 = st.columns([2, 1], gap="large")

with col1:
    st.subheader("Results (all kept rows)")
    st.dataframe(df_out, use_container_width=True)

with col2:
    st.subheader("Summary")
    st.write(f"Rows kept: **{len(df_out)}**")
    st.write(f"Errors: **{errors}**")
    st.write(f"+EV rows (ev ≥ {float(min_ev):.2f}): **{len(df_plus)}**")
    if apply_min_edge:
        st.write(f"Edge filter: **edge ≥ {float(min_edge):.2f}**")
    st.write(f"Avg EV per $1: **{avg_ev:.4f}**")
    st.write(f"Avg edge: **{avg_edge:.4f}**")
    st.write(f"Total recommended stake: **{total_stake:.2f}**")

st.subheader("+EV (filtered)")
st.dataframe(df_plus, use_container_width=True)

st.subheader("Downloads")
c1, c2, c3 = st.columns(3)
with c1:
    st.download_button("Download results.csv", data=df_to_csv_bytes(df_out), file_name="results.csv", mime="text/csv")
with c2:
    st.download_button("Download plus_ev.csv", data=df_to_csv_bytes(df_plus), file_name="plus_ev.csv", mime="text/csv")
with c3:
    st.download_button("Download report.md", data=report_md.encode("utf-8"), file_name="report.md", mime="text/markdown")

st.subheader("Report preview")
st.code(report_md, language="markdown")
