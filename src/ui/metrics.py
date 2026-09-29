"""Dashboard metrics derived from the existing SIF pipeline outputs."""

from __future__ import annotations

import pandas as pd


def _rate(part: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return float(part) / float(total) * 100.0


def _filled(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().ne("")


def compute_metrics(df: pd.DataFrame) -> dict:
    total = int(len(df))
    sif_yes = int((df["predicted_sif"] == "YES").sum()) if "predicted_sif" in df.columns else 0
    critical = int((df["risk_level"] == "CRITICAL").sum()) if "risk_level" in df.columns else 0
    high = int((df["risk_level"] == "HIGH").sum()) if "risk_level" in df.columns else 0
    medium = int((df["risk_level"] == "MEDIUM").sum()) if "risk_level" in df.columns else 0
    low = int((df["risk_level"] == "LOW").sum()) if "risk_level" in df.columns else 0

    required = [c for c in ["report_id", "site", "location", "activity", "free_text"] if c in df.columns]
    if required:
        completeness = float(df[required].notna().all(axis=1).mean() * 100.0)
        complete_n = int(df[required].notna().all(axis=1).sum())
    else:
        completeness = 0.0
        complete_n = 0

    extraction_hit = 0.0
    if "extracted_hazard" in df.columns:
        extraction_hit = float(
            (
                _filled(df["extracted_hazard"])
                | _filled(df.get("extracted_energy", pd.Series("", index=df.index)))
                | _filled(df.get("extracted_barrier", pd.Series("", index=df.index)))
            ).mean()
            * 100.0
        )

    no_barrier = 100.0
    barrier_n = 0
    if "barrier_failures" in df.columns:
        barrier_n = int(_filled(df["barrier_failures"]).sum())
        no_barrier = 100.0 - _rate(barrier_n, total)

    sif_rate = _rate(sif_yes, total)
    crit_rate = _rate(critical, total)

    intelligence = max(
        0.0,
        min(
            100.0,
            0.30 * completeness
            + 0.25 * no_barrier
            + 0.25 * (100.0 - crit_rate)
            + 0.20 * (100.0 - sif_rate),
        ),
    )

    if crit_rate >= 15:
        hazard_tier, hazard_label = "L3", "HIGH"
    elif crit_rate >= 6 or high + critical >= max(3, int(total * 0.12)):
        hazard_tier, hazard_label = "L2", "MODERATE"
    else:
        hazard_tier, hazard_label = "L1", "LOW"

    mismatches = 0
    if "ground_truth_sif" in df.columns:
        mismatches = int((df["predicted_sif"] != df["ground_truth_sif"]).sum())

    indicator_set = set()
    if "sif_indicators" in df.columns:
        for raw in df["sif_indicators"].fillna(""):
            for token in str(raw).split(","):
                token = token.strip()
                if token:
                    indicator_set.add(token)

    sites = sorted(df["site"].dropna().unique().tolist()) if "site" in df.columns else []
    date_min = date_max = None
    if "date" in df.columns:
        dates = pd.to_datetime(df["date"], errors="coerce")
        if dates.notna().any():
            date_min = dates.min().strftime("%Y-%m-%d")
            date_max = dates.max().strftime("%Y-%m-%d")

    mean_sif = float(df["sif_score"].mean()) if "sif_score" in df.columns and total else 0.0
    mean_risk = float(df["risk_score"].mean()) if "risk_score" in df.columns and total else 0.0

    return {
        "total": total,
        "sif_yes": sif_yes,
        "sif_rate": sif_rate,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "high_or_critical": high + critical,
        "completeness": completeness,
        "complete_n": complete_n,
        "extraction_hit": extraction_hit,
        "compliance": no_barrier,
        "barrier_n": barrier_n,
        "intelligence": intelligence,
        "hazard_tier": hazard_tier,
        "hazard_label": hazard_label,
        "mismatches": mismatches,
        "indicator_count": len(indicator_set),
        "sites": sites,
        "site_count": len(sites),
        "date_min": date_min,
        "date_max": date_max,
        "mean_sif": mean_sif,
        "mean_risk": mean_risk,
        "has_ground_truth": "ground_truth_sif" in df.columns,
    }


def risk_counts(df: pd.DataFrame) -> pd.Series:
    if "risk_level" not in df.columns or df.empty:
        return pd.Series({"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0})
    return (
        df["risk_level"]
        .value_counts()
        .reindex(["LOW", "MEDIUM", "HIGH", "CRITICAL"], fill_value=0)
    )


def recommendations(df: pd.DataFrame, patterns: dict) -> list[str]:
    recs = []
    site_patterns = patterns.get("site_patterns", pd.DataFrame())
    if not site_patterns.empty:
        top = site_patterns.sort_values("sif_rate", ascending=False).iloc[0]
        recs.append(
            f"Concentrate barrier restoration at {top['site']} "
            f"(SIF rate {top['sif_rate']:.1f}%, avg risk {top['average_risk']:.1f})."
        )

    barrier_patterns = patterns.get("barrier_patterns", pd.DataFrame())
    if barrier_patterns is not None and not barrier_patterns.empty:
        top_b = barrier_patterns.iloc[0]
        recs.append(
            f"Most frequent control-gap language: “{top_b['barrier_failure']}” "
            f"({int(top_b['count'])} reports)."
        )

    indicator_patterns = patterns.get("indicator_patterns", pd.DataFrame())
    if indicator_patterns is not None and not indicator_patterns.empty:
        top_i = indicator_patterns.iloc[0]
        recs.append(
            f"Leading SIF precursor family: {top_i['indicator']} "
            f"({int(top_i['count'])} detections)."
        )

    if "activity" in df.columns and "predicted_sif" in df.columns:
        confined = df[df["activity"].astype(str).str.contains("Confined", case=False, na=False)]
        if not confined.empty:
            rate = _rate((confined["predicted_sif"] == "YES").sum(), len(confined))
            if rate >= 40:
                recs.append(
                    f"Confined-space observations are SIF-positive in {rate:.0f}% of cases — "
                    "enforce atmospheric testing before entry."
                )

    if not recs:
        recs.append("No high-priority operational recommendation could be derived from the current corpus.")
    return recs[:5]


def top_critical_rows(df: pd.DataFrame, n: int = 4) -> pd.DataFrame:
    if df.empty:
        return df
    work = df.copy()
    if "risk_score" in work.columns:
        work = work.sort_values(["risk_score", "sif_score"], ascending=False)
    return work.head(n)


def location_nodes(df: pd.DataFrame, n: int = 6) -> pd.DataFrame:
    if df.empty or "location" not in df.columns:
        return pd.DataFrame()
    grouped = (
        df.groupby(["site", "location"], dropna=False)
        .agg(
            reports=("report_id", "count"),
            sif=("predicted_sif", lambda x: (x == "YES").sum()),
            avg_risk=("risk_score", "mean"),
            critical=("risk_level", lambda x: (x == "CRITICAL").sum()),
        )
        .reset_index()
        .sort_values("reports", ascending=False)
    )
    return grouped.head(n)


def verified_row(df: pd.DataFrame) -> pd.Series | None:
    if df.empty:
        return None
    mask = (df.get("predicted_sif") == "NO") & (df.get("risk_level").isin(["LOW", "MEDIUM"]))
    subset = df[mask]
    if subset.empty:
        subset = df[df.get("risk_level") == "LOW"]
    if subset.empty:
        return None
    return subset.iloc[0]


def variance_site(patterns: dict) -> dict | None:
    site_patterns = patterns.get("site_patterns", pd.DataFrame())
    if site_patterns is None or site_patterns.empty:
        return None
    mean_risk = float(site_patterns["average_risk"].mean())
    row = site_patterns.assign(delta=(site_patterns["average_risk"] - mean_risk).abs())
    row = row.sort_values("delta", ascending=False).iloc[0]
    return {
        "site": row["site"],
        "average_risk": float(row["average_risk"]),
        "mean_risk": mean_risk,
        "delta": float(row["average_risk"] - mean_risk),
        "sif_rate": float(row["sif_rate"]),
        "total": int(row["total_reports"]),
    }
