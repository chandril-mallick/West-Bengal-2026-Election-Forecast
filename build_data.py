from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parent
PDF_PATH = Path("/Users/chandrilmallick/Downloads/Elector_WBLA2026.pdf")
RESULTS_HTML_PATH = BASE_DIR / "wb2021_results.html"
ELECTOR_CSV_PATH = BASE_DIR / "wb_2026_electors.csv"
RESULTS_CSV_PATH = BASE_DIR / "wb_2021_results.csv"
MODEL_CSV_PATH = BASE_DIR / "wb_2026_model_input.csv"


def party_to_bloc(party: str) -> str:
    party = (party or "").strip()
    if party in {"AITC", "GJM (Tamang)"}:
        return "AITC Bloc"
    if party == "BJP":
        return "BJP"
    if party in {"INC", "CPI(M)", "ISF", "AIFB", "RSP", "CPI", "AIFB(S)"}:
        return "Left-Cong-ISF Bloc"
    return "Others"


def normalize_constituency_name(name: str) -> str:
    name = re.sub(r"\s+", " ", str(name).strip().upper())
    return name


def parse_elector_pdf(pdf_path: Path) -> pd.DataFrame:
    reader = PdfReader(str(pdf_path))
    rows: list[dict[str, object]] = []

    for page in reader.pages:
        text = page.extract_text() or ""
        for raw_line in text.splitlines():
            line = " ".join(raw_line.split())
            if not line:
                continue
            if any(
                token in line
                for token in [
                    "Male Female Third",
                    "Gender Total",
                    "Elector as on last date of nomination",
                    "Assembly Constituency-wise Elector data",
                    "AC NameAC No.District NamePhase",
                    "Phase 1 Total",
                    "Phase 2 Total",
                    "State Total",
                ]
            ):
                continue

            numeric_tail = re.search(r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$", line)
            if not numeric_tail:
                continue
            male, female, third_gender, total = numeric_tail.groups()
            head = line[: numeric_tail.start()].strip()
            phase_match = re.match(r"^(\d+)\s+(.+)$", head)
            if not phase_match:
                continue

            phase = phase_match.group(1)
            district_and_constituency = phase_match.group(2)
            ac_no_matches = list(re.finditer(r"\b\d+\b", district_and_constituency))
            if not ac_no_matches:
                continue

            ac_no_match = ac_no_matches[-1]
            ac_no = ac_no_match.group()
            district = district_and_constituency[: ac_no_match.start()].strip()
            ac_name = district_and_constituency[ac_no_match.end() :].strip()
            rows.append(
                {
                    "phase": int(phase),
                    "district": district.title(),
                    "ac_no": int(ac_no),
                    "ac_name_pdf": normalize_constituency_name(ac_name),
                    "male_electors": int(male),
                    "female_electors": int(female),
                    "third_gender_electors": int(third_gender),
                    "total_electors": int(total),
                }
            )

    df = pd.DataFrame(rows).sort_values("ac_no").reset_index(drop=True)
    df["female_share"] = df["female_electors"] / df["total_electors"]
    df["male_share"] = df["male_electors"] / df["total_electors"]
    return df


def parse_results_html(html_path: Path) -> pd.DataFrame:
    df = pd.read_html(html_path)[0]
    df.columns = [
        "ac_no",
        "ac_name",
        "winner_party_unused",
        "winner_party",
        "winner_candidate",
        "winner_votes",
        "winner_pct",
        "runner_party_unused",
        "runner_party",
        "runner_candidate",
        "runner_votes",
        "runner_pct",
        "margin_votes",
        "voting_date",
    ]

    df = df[pd.to_numeric(df["ac_no"], errors="coerce").notna()].copy()
    df["ac_no"] = df["ac_no"].astype(int)

    def clean_numeric(series: pd.Series) -> pd.Series:
        cleaned = (
            series.astype(str)
            .str.replace(r"\[.*?\]", "", regex=True)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        return pd.to_numeric(cleaned)

    df["winner_votes"] = clean_numeric(df["winner_votes"])
    df["runner_votes"] = clean_numeric(df["runner_votes"])
    df["winner_pct"] = clean_numeric(df["winner_pct"])
    df["runner_pct"] = clean_numeric(df["runner_pct"])
    df["margin_votes"] = clean_numeric(df["margin_votes"])
    df["ac_name_results"] = df["ac_name"].map(normalize_constituency_name)
    df["winner_bloc"] = df["winner_party"].map(party_to_bloc)
    df["runner_bloc"] = df["runner_party"].map(party_to_bloc)
    df["margin_pct_points"] = df["winner_pct"] - df["runner_pct"]
    return df[
        [
            "ac_no",
            "ac_name",
            "ac_name_results",
            "winner_party",
            "winner_candidate",
            "winner_votes",
            "winner_pct",
            "runner_party",
            "runner_candidate",
            "runner_votes",
            "runner_pct",
            "margin_votes",
            "margin_pct_points",
            "winner_bloc",
            "runner_bloc",
            "voting_date",
        ]
    ].sort_values("ac_no")


def build_model_frame(electors: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    merged = electors.merge(results, on="ac_no", how="left", validate="one_to_one")

    merged["other_pct"] = (100 - merged["winner_pct"] - merged["runner_pct"]).clip(lower=0)
    for bloc in ["AITC Bloc", "BJP", "Left-Cong-ISF Bloc", "Others"]:
        merged[f"base_{bloc.lower().replace('-', '_').replace(' ', '_')}_pct"] = 0.0

    winner_col = (
        "base_" + merged["winner_bloc"].str.lower().str.replace("-", "_").str.replace(" ", "_") + "_pct"
    )
    runner_col = (
        "base_" + merged["runner_bloc"].str.lower().str.replace("-", "_").str.replace(" ", "_") + "_pct"
    )

    for idx in merged.index:
        merged.loc[idx, winner_col.loc[idx]] += merged.loc[idx, "winner_pct"]
        merged.loc[idx, runner_col.loc[idx]] += merged.loc[idx, "runner_pct"]
        merged.loc[idx, "base_others_pct"] += merged.loc[idx, "other_pct"]

    merged["is_close_seat"] = merged["margin_pct_points"] < 5
    merged["seat_size_band"] = pd.qcut(
        merged["total_electors"],
        q=4,
        labels=["Small", "Medium", "Large", "Very Large"],
    )
    return merged


def main() -> None:
    electors = parse_elector_pdf(PDF_PATH)
    results = parse_results_html(RESULTS_HTML_PATH)
    model_input = build_model_frame(electors, results)

    electors.to_csv(ELECTOR_CSV_PATH, index=False)
    results.to_csv(RESULTS_CSV_PATH, index=False)
    model_input.to_csv(MODEL_CSV_PATH, index=False)

    print(f"Wrote {ELECTOR_CSV_PATH.name}: {len(electors)} rows")
    print(f"Wrote {RESULTS_CSV_PATH.name}: {len(results)} rows")
    print(f"Wrote {MODEL_CSV_PATH.name}: {len(model_input)} rows")


if __name__ == "__main__":
    main()
