from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components


BASE_DIR = Path(__file__).resolve().parent
MODEL_CSV_PATH = BASE_DIR / "wb_2026_model_input.csv"
HTML_SOURCE_PATH = BASE_DIR / "wb2021_results.html"

# --- Constants & Styling ---
PARTY_COLORS = {
    "AITC Bloc": "#2E7D32",
    "BJP": "#FF9933",
    "Left-Cong-ISF Bloc": "#D32F2F",
    "Others": "#757575",
    "AITC": "#2E7D32",
    "Opposition Bloc": "#D32F2F",
}

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Metric Card */
    .metric-container {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        transition: transform 0.3s ease, background 0.3s ease;
        backdrop-filter: blur(10px);
    }
    .metric-container:hover {
        transform: translateY(-4px);
        background: rgba(255, 255, 255, 0.09);
    }
    .metric-label {
        font-size: 0.78rem;
        color: #a3a8b4;
        margin-bottom: 8px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 700;
        color: #ffffff;
    }
    .metric-subvalue {
        font-size: 0.82rem;
        color: #00ffcc;
        margin-top: 5px;
    }

    /* Section header divider */
    .section-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #e0e0e0;
        border-left: 4px solid #667eea;
        padding-left: 10px;
        margin: 1.5rem 0 0.8rem 0;
    }

    /* Vulnerability badge */
    .badge-hot   { background: #c62828; color: #fff; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
    .badge-watch { background: #f57c00; color: #fff; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
    .badge-safe  { background: #2e7d32; color: #fff; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }

    /* Stacked donut legend */
    .legend-dot {
        display: inline-block;
        width: 12px; height: 12px;
        border-radius: 50%;
        margin-right: 6px;
        vertical-align: middle;
    }

    /* Button */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        padding: 10px 20px;
        transition: all 0.25s ease;
    }
    .stButton>button:hover {
        opacity: 0.88;
        transform: scale(1.02);
    }
</style>
"""


# ── helpers ─────────────────────────────────────────────────────────────────

def bloc_columns() -> dict[str, str]:
    return {
        "AITC Bloc": "base_aitc_bloc_pct",
        "BJP": "base_bjp_pct",
        "Left-Cong-ISF Bloc": "base_left_cong_isf_bloc_pct",
        "Others": "base_others_pct",
    }


def scenario_presets() -> dict[str, dict[str, object]]:
    return {
        "BJP Phase 1 Lead Scenario": {
            "aitc_swing": -1.5,
            "bjp_swing": 1.5,
            "opposition_swing": 0.0,
            "default_phases": [1],
            "summary": (
                "Modeled Phase 1 scenario where BJP moves slightly ahead on seats "
                "within the first phase only."
            ),
        },
        "BJP Statewide Lead Scenario": {
            "aitc_swing": -4.5,
            "bjp_swing": 4.5,
            "opposition_swing": 0.0,
            "default_phases": [1, 2],
            "summary": (
                "Modeled statewide scenario where BJP narrowly moves ahead in the full 294-seat map."
            ),
        },
        "Baseline 2021 Carry Forward": {
            "aitc_swing": 0.0,
            "bjp_swing": 0.0,
            "opposition_swing": 0.0,
            "default_phases": [1, 2],
            "summary": "No swing applied. This mostly carries forward the 2021 result structure.",
        },
        "Custom": {
            "aitc_swing": 0.0,
            "bjp_swing": 0.0,
            "opposition_swing": 0.0,
            "default_phases": [1, 2],
            "summary": "Manual scenario. Use the sliders to set your own swing assumptions.",
        },
    }


def projected_party(row: pd.Series, projected_bloc: str) -> str:
    if projected_bloc == row["winner_bloc"]:
        return row["winner_party"]
    if projected_bloc == row["runner_bloc"]:
        return row["runner_party"]
    fallback = {
        "AITC Bloc": "AITC",
        "BJP": "BJP",
        "Left-Cong-ISF Bloc": "Opposition Bloc",
        "Others": "Others",
    }
    return fallback[projected_bloc]


def apply_swing(
    df: pd.DataFrame,
    aitc_swing: float,
    bjp_swing: float,
    opposition_swing: float,
) -> pd.DataFrame:
    projected = df.copy()
    shares = bloc_columns()
    projected["proj_aitc"] = (projected[shares["AITC Bloc"]] + aitc_swing).clip(lower=0)
    projected["proj_bjp"] = (projected[shares["BJP"]] + bjp_swing).clip(lower=0)
    projected["proj_opposition"] = (
        projected[shares["Left-Cong-ISF Bloc"]] + opposition_swing
    ).clip(lower=0)
    projected["proj_others"] = projected[shares["Others"]].clip(lower=0)

    total = (
        projected["proj_aitc"]
        + projected["proj_bjp"]
        + projected["proj_opposition"]
        + projected["proj_others"]
    )
    projected["proj_aitc"] = projected["proj_aitc"] / total * 100
    projected["proj_bjp"] = projected["proj_bjp"] / total * 100
    projected["proj_opposition"] = projected["proj_opposition"] / total * 100
    projected["proj_others"] = projected["proj_others"] / total * 100

    bloc_map = {
        "proj_aitc": "AITC Bloc",
        "proj_bjp": "BJP",
        "proj_opposition": "Left-Cong-ISF Bloc",
        "proj_others": "Others",
    }
    projected["projected_bloc"] = (
        projected[["proj_aitc", "proj_bjp", "proj_opposition", "proj_others"]]
        .idxmax(axis=1)
        .map(bloc_map)
    )
    projected["projected_party"] = projected.apply(
        lambda row: projected_party(row, row["projected_bloc"]), axis=1
    )
    projected["projected_margin_vs_runner_2021"] = projected.apply(
        lambda row: row["proj_aitc"] - row["proj_bjp"]
        if row["projected_bloc"] in {"AITC Bloc", "BJP"}
        else row["margin_pct_points"],
        axis=1,
    )
    projected["is_flip"] = projected["winner_party"] != projected["projected_party"]
    projected["vulnerability"] = pd.cut(
        projected["margin_pct_points"],
        bins=[-1, 5, 10, 100],
        labels=["Hot (<5%)", "Watch (5-10%)", "Safe (>10%)"],
    )
    return projected


def render_hero_metric(label: str, value: str, subvalue: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-container">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-subvalue">{subvalue}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def transparent_layout(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#e0e0e0",
    )
    return fig


# ── tabs ────────────────────────────────────────────────────────────────────

def tab_overview(projected: pd.DataFrame, preset_name: str, preset: dict) -> None:
    """Summary metrics, Scenario Story, and top charts."""
    seat_projection = (
        projected.groupby("projected_party", as_index=False)
        .size()
        .rename(columns={"size": "seats"})
        .sort_values("seats", ascending=False)
    )
    baseline_projection = (
        projected.groupby("winner_party", as_index=False)
        .size()
        .rename(columns={"size": "baseline_seats", "winner_party": "projected_party"})
    )
    gain_loss_df = (
        pd.merge(seat_projection, baseline_projection, on="projected_party", how="outer")
        .fillna(0)
    )
    gain_loss_df["gain_loss"] = (gain_loss_df["seats"] - gain_loss_df["baseline_seats"]).astype(int)
    gain_loss_df = gain_loss_df.sort_values("seats", ascending=False)

    total_flips = int(projected["is_flip"].sum())
    leader = seat_projection.iloc[0]
    runner = seat_projection.iloc[1] if len(seat_projection) > 1 else None
    total_electors = int(projected["total_electors"].sum())
    female_share = projected["female_electors"].sum() / total_electors
    close_seats = int(projected["is_close_seat"].sum())

    # Scenario Story
    summary = f"**Scenario: {preset_name}** — {preset['summary']} "
    if runner is not None:
        summary += (
            f"**{leader['projected_party']}** leads with **{int(leader['seats'])}** seats "
            f"vs **{int(runner['seats'])}** for **{runner['projected_party']}**."
        )
    if total_flips > 15:
        summary += f" Major volatility: **{total_flips} seat flips**."
    elif total_flips > 0:
        summary += f" **{total_flips} seat flips** from 2021."
    else:
        summary += " Status quo from 2021."
    st.info(summary)

    # Hero metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: render_hero_metric("Projected Leader", leader["projected_party"], "Top party")
    with m2: render_hero_metric("Projected Seats", str(int(leader["seats"])), "of total")
    with m3: render_hero_metric("Total Electors", f"{total_electors:,}", "2026 data")
    with m4: render_hero_metric("Female Share", f"{female_share:.1%}", "voter base")
    with m5: render_hero_metric("Close Seats (2021)", str(close_seats), "margin < 5 pp")

    st.write("---")

    # Majority banner
    if leader["seats"] >= 148:
        st.success(
            f"**{leader['projected_party']}** is projected to cross the majority mark "
            f"(148 seats) in this scenario."
        )
    else:
        st.warning("**Hung Assembly Scenario** — No party crosses the 148-seat majority mark.")

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(
            seat_projection,
            x="projected_party", y="seats",
            color="projected_party",
            color_discrete_map=PARTY_COLORS,
            title="Projected Seats by Party",
            text="seats",
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(transparent_layout(fig).update_layout(showlegend=False), use_container_width=True)

    with c2:
        fig_gl = px.bar(
            gain_loss_df,
            x="projected_party", y="gain_loss",
            color="gain_loss",
            color_continuous_scale="RdYlGn",
            title="Seat Gain / Loss vs 2021",
            text="gain_loss",
        )
        fig_gl.update_traces(textposition="outside")
        st.plotly_chart(transparent_layout(fig_gl), use_container_width=True)

    # Donut bloc view
    bloc_projection = (
        projected.groupby("projected_bloc", as_index=False)
        .size()
        .rename(columns={"size": "seats"})
    )
    fig_donut = px.pie(
        bloc_projection,
        names="projected_bloc", values="seats",
        color="projected_bloc",
        color_discrete_map=PARTY_COLORS,
        hole=0.5,
        title="Projected Bloc Share",
    )
    fig_donut.update_traces(textinfo="label+percent+value")
    st.plotly_chart(transparent_layout(fig_donut), use_container_width=True)


def tab_district_flips(projected: pd.DataFrame) -> None:
    """District heatmap + flip list."""
    total_flips = int(projected["is_flip"].sum())

    flip_col, dist_col = st.columns([1, 2])

    with flip_col:
        st.metric("Projected Flips", total_flips, delta=total_flips, delta_color="inverse")
        st.caption("Seats changing hands from 2021.")
        if total_flips > 0:
            flips_df = (
                projected[projected["is_flip"]]
                [["ac_name", "district", "winner_party", "projected_party", "margin_pct_points"]]
                .rename(columns={
                    "ac_name": "Seat",
                    "district": "District",
                    "winner_party": "2021 Winner",
                    "projected_party": "2026 Projected",
                    "margin_pct_points": "2021 Margin (pp)",
                })
                .sort_values("2021 Margin (pp)")
            )
            st.dataframe(flips_df, hide_index=True, use_container_width=True)

    with dist_col:
        district_summary = (
            projected.groupby("district", as_index=False)
            .agg(seats=("ac_no", "count"), flips=("is_flip", "sum"))
            .sort_values("flips", ascending=False)
        )
        fig_dist = px.bar(
            district_summary, x="district", y="seats",
            color="flips",
            title="Seats by District (Color intensity = Flips)",
            color_continuous_scale="OrRd",
        )
        st.plotly_chart(transparent_layout(fig_dist), use_container_width=True)


def tab_elector_breakdown(projected: pd.DataFrame) -> None:
    """Gender + seat-size elector distribution charts."""
    st.markdown('<div class="section-header">Elector Gender Breakdown by District</div>', unsafe_allow_html=True)

    by_district = (
        projected.groupby("district", as_index=False)
        .agg(male=("male_electors", "sum"), female=("female_electors", "sum"))
    )
    fig_gender = go.Figure()
    fig_gender.add_bar(name="Male", x=by_district["district"], y=by_district["male"], marker_color="#1565C0")
    fig_gender.add_bar(name="Female", x=by_district["district"], y=by_district["female"], marker_color="#AD1457")
    fig_gender.update_layout(barmode="group", title="Male vs Female Electors by District")
    st.plotly_chart(transparent_layout(fig_gender), use_container_width=True)

    st.markdown('<div class="section-header">Seat-Size Distribution</div>', unsafe_allow_html=True)
    size_counts = projected["seat_size_band"].value_counts().reset_index()
    size_counts.columns = ["Band", "Count"]
    fig_size = px.pie(size_counts, names="Band", values="Count", hole=0.45,
                      title="Constituencies by Elector Size Band")
    st.plotly_chart(transparent_layout(fig_size), use_container_width=True)

    st.markdown('<div class="section-header">Top 15 Constituencies by Total Electors</div>', unsafe_allow_html=True)
    top15 = projected.nlargest(15, "total_electors")[["ac_name", "district", "total_electors", "female_share"]]
    top15["female_share"] = (top15["female_share"] * 100).round(1).astype(str) + "%"
    fig_top = px.bar(top15, x="total_electors", y="ac_name", orientation="h",
                     color="district", title="Top 15 Constituencies by Elector Count")
    fig_top.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(transparent_layout(fig_top), use_container_width=True)


def tab_vulnerability(projected: pd.DataFrame) -> None:
    """Seat vulnerability analysis based on 2021 margins."""
    st.markdown('<div class="section-header">Seat Vulnerability (based on 2021 winning margin)</div>', unsafe_allow_html=True)

    vuln = projected.groupby(["vulnerability", "projected_party"], as_index=False).size()
    vuln.columns = ["Vulnerability", "Party", "Seats"]

    fig_vuln = px.bar(
        vuln, x="Vulnerability", y="Seats", color="Party",
        color_discrete_map=PARTY_COLORS,
        barmode="group",
        title="Projected Seats by Vulnerability Tier",
    )
    st.plotly_chart(transparent_layout(fig_vuln), use_container_width=True)

    st.markdown('<div class="section-header">Hot Seats (2021 margin < 5 percentage points)</div>', unsafe_allow_html=True)
    hot = (
        projected[projected["margin_pct_points"] < 5]
        [["ac_name", "district", "phase", "winner_party", "projected_party", "margin_pct_points", "is_flip"]]
        .rename(columns={
            "ac_name": "Seat", "district": "District", "phase": "Phase",
            "winner_party": "2021 Winner", "projected_party": "2026 Proj.",
            "margin_pct_points": "Margin (pp)", "is_flip": "Flip?",
        })
        .sort_values("Margin (pp)")
    )
    st.dataframe(hot, hide_index=True, use_container_width=True)

    st.markdown('<div class="section-header">Phase-wise Vulnerability Summary</div>', unsafe_allow_html=True)
    phase_vuln = (
        projected.groupby(["phase", "vulnerability"], as_index=False)
        .size()
        .rename(columns={"size": "seats"})
    )
    fig_pv = px.bar(
        phase_vuln, x="phase", y="seats", color="vulnerability",
        color_discrete_map={
            "Hot (<5%)": "#c62828",
            "Watch (5-10%)": "#f57c00",
            "Safe (>10%)": "#2e7d32",
        },
        title="Phase-wise Seat Vulnerability",
        barmode="stack",
    )
    st.plotly_chart(transparent_layout(fig_pv), use_container_width=True)


def tab_seat_table(projected: pd.DataFrame, preset_name: str) -> None:
    """Full seat-level table with download."""
    search = st.text_input("Search constituency or district", "")
    display = projected.copy()
    if search:
        mask = (
            display["ac_name"].str.contains(search, case=False, na=False) |
            display["district"].str.contains(search, case=False, na=False)
        )
        display = display[mask]

    seat_table = display[[
        "ac_no", "ac_name", "district", "phase",
        "total_electors", "winner_party", "projected_party",
        "is_flip", "margin_pct_points", "vulnerability",
    ]].sort_values(["district", "ac_no"])

    st.dataframe(
        seat_table.style.map(
            lambda x: "color: #ff4b4b; font-weight:600" if x is True
            else "color: #00ffcc;" if x is False else "",
            subset=["is_flip"],
        ),
        use_container_width=True,
        hide_index=True,
    )

    csv = seat_table.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Projection Data (CSV)",
        data=csv,
        file_name=f"wb_2026_projection_{preset_name.lower().replace(' ', '_')}.csv",
        mime="text/csv",
    )


def tab_source_html() -> None:
    """Embed the raw 2021 Wikipedia results HTML file."""
    if not HTML_SOURCE_PATH.exists():
        st.error(f"Source HTML not found at: {HTML_SOURCE_PATH}")
        return
    html_content = HTML_SOURCE_PATH.read_text(encoding="utf-8", errors="replace")
    st.markdown(
        "Displaying the saved Wikipedia page used as the 2021 election results source. "
        "External links and images may not load (offline snapshot)."
    )
    components.html(html_content, height=800, scrolling=True)


# ── main ────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="WB 2026 Election Forecast",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    st.title("West Bengal 2026 Election Forecast")
    st.markdown(
        "<p style='font-size:1.05rem;color:#a3a8b4;margin-bottom:1.5rem;'>"
        "Advanced scenario modeling — 2026 elector data + 2021 constituency results."
        "</p>",
        unsafe_allow_html=True,
    )

    df = pd.read_csv(MODEL_CSV_PATH)
    presets = scenario_presets()

    # ── Sidebar ────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Scenario Controls")

        preset_name = st.selectbox("Scenario preset", list(presets.keys()), index=0)
        preset = presets[preset_name]

        phase_options = sorted(df["phase"].unique())
        selected_phases = st.multiselect("Phases", phase_options, default=preset["default_phases"])

        if preset_name == "Custom":
            aitc_swing = st.slider("AITC bloc swing (pp)", -15.0, 15.0, 0.0, 0.5)
            bjp_swing = st.slider("BJP swing (pp)", -15.0, 15.0, 0.0, 0.5)
            opposition_swing = st.slider("Left-Cong-ISF swing (pp)", -15.0, 15.0, 0.0, 0.5)
        else:
            aitc_swing = float(preset["aitc_swing"])
            bjp_swing = float(preset["bjp_swing"])
            opposition_swing = float(preset["opposition_swing"])
            st.caption(
                f"AITC {aitc_swing:+.1f} pp  |  BJP {bjp_swing:+.1f} pp  |  "
                f"Left-Cong-ISF {opposition_swing:+.1f} pp"
            )

        districts = sorted(df["district"].unique())
        district_filter = st.multiselect("Filter districts", districts, default=districts)

        st.divider()
        st.info(f"**Scenario note:** {preset['summary']}")
        if st.button("Reset View"):
            st.rerun()

    # ── Data ───────────────────────────────────────────────────────────────
    projected = apply_swing(df, aitc_swing, bjp_swing, opposition_swing)
    projected = projected[
        projected["district"].isin(district_filter) & projected["phase"].isin(selected_phases)
    ].copy()

    if projected.empty:
        st.warning("No constituencies match the selected filters.")
        return

    # ── Tabs ───────────────────────────────────────────────────────────────
    tabs = st.tabs([
        "Overview",
        "District & Flips",
        "Elector Breakdown",
        "Vulnerability",
        "All Seats",
        "2021 Source Data",
    ])

    with tabs[0]:
        tab_overview(projected, preset_name, preset)

    with tabs[1]:
        tab_district_flips(projected)

    with tabs[2]:
        tab_elector_breakdown(projected)

    with tabs[3]:
        tab_vulnerability(projected)

    with tabs[4]:
        tab_seat_table(projected, preset_name)

    with tabs[5]:
        tab_source_html()


if __name__ == "__main__":
    main()
