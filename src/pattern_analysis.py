import pandas as pd

# ============================================================
# SIF PRECURSOR PATTERN ANALYSIS
# ============================================================

def analyze_patterns(df):

    df = df.copy()

    # --------------------------------------------------------
    # Convert date
    # --------------------------------------------------------

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # --------------------------------------------------------
    # 1. SIF patterns by site
    # --------------------------------------------------------

    site_patterns = (
        df.groupby("site")
        .agg(
            total_reports=("report_id", "count"),
            sif_reports=("predicted_sif", lambda x: (x == "YES").sum()),
            average_risk=("risk_score", "mean")
        )
        .reset_index()
    )

    site_patterns["sif_rate"] = (
        site_patterns["sif_reports"]
        / site_patterns["total_reports"]
        * 100
    ).round(2)

    # --------------------------------------------------------
    # 2. SIF patterns by location
    # --------------------------------------------------------

    location_patterns = (
        df.groupby("location")
        .agg(
            total_reports=("report_id", "count"),
            sif_reports=("predicted_sif", lambda x: (x == "YES").sum()),
            average_risk=("risk_score", "mean")
        )
        .reset_index()
    )

    location_patterns["sif_rate"] = (
        location_patterns["sif_reports"]
        / location_patterns["total_reports"]
        * 100
    ).round(2)

    # --------------------------------------------------------
    # 3. SIF patterns by activity
    # --------------------------------------------------------

    activity_patterns = (
        df.groupby("activity")
        .agg(
            total_reports=("report_id", "count"),
            sif_reports=("predicted_sif", lambda x: (x == "YES").sum()),
            average_risk=("risk_score", "mean")
        )
        .reset_index()
    )

    activity_patterns["sif_rate"] = (
        activity_patterns["sif_reports"]
        / activity_patterns["total_reports"]
        * 100
    ).round(2)

    # --------------------------------------------------------
    # 4. Risk-level distribution
    # --------------------------------------------------------

    risk_distribution = (
        df["risk_level"]
        .value_counts()
        .reset_index()
    )

    risk_distribution.columns = ["risk_level", "report_count"]

    # --------------------------------------------------------
    # 5. Precursor indicator frequency
    # --------------------------------------------------------

    indicator_counts = {}

    for indicators in df["sif_indicators"].fillna(""):

        if not indicators:
            continue

        for indicator in indicators.split(", "):

            if indicator:
                indicator_counts[indicator] = (
                    indicator_counts.get(indicator, 0) + 1
                )

    indicator_patterns = pd.DataFrame(
        list(indicator_counts.items()),
        columns=["indicator", "count"]
    )

    if not indicator_patterns.empty:
        indicator_patterns = indicator_patterns.sort_values(
            "count",
            ascending=False
        )

    # --------------------------------------------------------
    # 6. Primary risk frequency
    # --------------------------------------------------------

    primary_risk_patterns = (
        df["primary_risk"]
        .value_counts()
        .reset_index()
    )

    primary_risk_patterns.columns = [
        "primary_risk",
        "count"
    ]

    # --------------------------------------------------------
    # 7. Barrier failure frequency
    # --------------------------------------------------------

    barrier_counts = {}

    for barriers in df["barrier_failures"].fillna(""):

        if not barriers:
            continue

        for barrier in barriers.split(", "):

            if barrier:
                barrier_counts[barrier] = (
                    barrier_counts.get(barrier, 0) + 1
                )

    barrier_patterns = pd.DataFrame(
        list(barrier_counts.items()),
        columns=["barrier_failure", "count"]
    )

    if not barrier_patterns.empty:
        barrier_patterns = barrier_patterns.sort_values(
            "count",
            ascending=False
        )

    return {
        "site_patterns": site_patterns,
        "location_patterns": location_patterns,
        "activity_patterns": activity_patterns,
        "risk_distribution": risk_distribution,
        "indicator_patterns": indicator_patterns,
        "primary_risk_patterns": primary_risk_patterns,
        "barrier_patterns": barrier_patterns
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    from sif_detector import load_and_detect
    from risk_scoring import apply_risk_scoring

    file_path = "data/synthetic_reports.csv"

    print("=" * 70)
    print("SIF PRECURSOR PATTERN ANALYSIS")
    print("=" * 70)

    # --------------------------------------------------------
    # Load complete pipeline
    # --------------------------------------------------------

    print()
    print("Loading reports...")

    df = load_and_detect(file_path)

    print("Reports loaded:", len(df))

    # --------------------------------------------------------
    # Apply risk scoring
    # --------------------------------------------------------

    df = apply_risk_scoring(df)

    # --------------------------------------------------------
    # Analyze patterns
    # --------------------------------------------------------

    results = analyze_patterns(df)

    # --------------------------------------------------------
    # Site patterns
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("SIF PATTERNS BY SITE")
    print("=" * 70)

    print(
        results["site_patterns"]
        .sort_values("sif_rate", ascending=False)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Location patterns
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("SIF PATTERNS BY LOCATION")
    print("=" * 70)

    print(
        results["location_patterns"]
        .sort_values("sif_rate", ascending=False)
        .head(10)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Activity patterns
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("SIF PATTERNS BY ACTIVITY")
    print("=" * 70)

    print(
        results["activity_patterns"]
        .sort_values("sif_rate", ascending=False)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Risk distribution
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("RISK LEVEL DISTRIBUTION")
    print("=" * 70)

    print(
        results["risk_distribution"]
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Precursor indicators
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("TOP SIF PRECURSOR INDICATORS")
    print("=" * 70)

    if results["indicator_patterns"].empty:
        print("No indicators found.")
    else:
        print(
            results["indicator_patterns"]
            .head(10)
            .to_string(index=False)
        )

    # --------------------------------------------------------
    # Primary risks
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("PRIMARY RISK DISTRIBUTION")
    print("=" * 70)

    print(
        results["primary_risk_patterns"]
        .head(10)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Barrier failures
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("BARRIER FAILURE PATTERNS")
    print("=" * 70)

    if results["barrier_patterns"].empty:
        print("No barrier failures found.")
    else:
        print(
            results["barrier_patterns"]
            .head(10)
            .to_string(index=False)
        )

    print()
    print("=" * 70)
    print("PATTERN ANALYSIS COMPLETE")
    print("=" * 70)