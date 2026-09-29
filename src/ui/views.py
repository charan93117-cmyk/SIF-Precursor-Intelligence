"""Streamlit views for the PETRO-CORE command center. Presentation only."""
from __future__ import annotations
import html
import pandas as pd
import streamlit as st
from ui.metrics import (
    compute_metrics,
    location_nodes,
    recommendations,
    risk_counts,
    top_critical_rows,
    variance_site,
    verified_row,
)
from ui.styles import COMMAND_CSS
NAV_ITEMS = [
    ("dashboard", "Digital Twin"),
    ("dpr_ai", "DPR Document AI"),
    ("manifolds", "Manifolds & Rigs"),
    ("pipelines", "Pipeline Vectors"),
    ("anomaly", "Anomaly Detection"),
    ("scada_logs", "SCADA Audit Logs"),
    ("diagnostics", "Diagnostics"),
    ("terminal", "Terminal SCADA"),
]
def inject_css() -> None:
    st.markdown(COMMAND_CSS, unsafe_allow_html=True)
def _esc(value) -> str:
    return html.escape("" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value))
def _state_class(level: str) -> str:
    level = (level or "").upper()
    if level == "CRITICAL":
        return "crit"
    if level == "HIGH":
        return "warn"
    if level in {"LOW", "VERIFIED"}:
        return "ok"
    return "info"
def render_sidebar(metrics: dict, data_note: str) -> str:
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"
    st.sidebar.markdown(
        """
        <div class="pc-brand">
          <div class="pc-mark">◆</div>
          <div>
            <div class="pc-kicker">Petro-Core //</div>
            <div class="pc-title" style="font-size:16px">DPR AI SYNTHESIS</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    coverage = "AWAITING DATA" if metrics["total"] == 0 else "DATA LOADED"
    st.sidebar.markdown(
        f"""
        <div class="pc-status">
          SECTOR COVERAGE<br>
          STATUS: <strong>{coverage}</strong><br>
          SITES: {metrics["site_count"]} · REPORTS: {metrics["total"]}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.caption(data_note)
    for key, label in NAV_ITEMS:
        suffix = ""
        if key == "anomaly" and metrics["critical"]:
            suffix = f" · {metrics['critical']} FLG"
        clicked = st.sidebar.button(
            f"{label}{suffix}",
            key=f"nav_{key}",
            type="primary" if st.session_state.page == key else "secondary",
            use_container_width=True,
        )
        if clicked:
            st.session_state.page = key
            st.rerun()
    st.sidebar.markdown("")
    if st.sidebar.button("RUN NEURAL AUDIT", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.session_state.page = "dashboard"
        st.rerun()
    st.sidebar.markdown("")
    st.sidebar.markdown('<div class="pc-kicker">Emergency / Interlock</div>', unsafe_allow_html=True)
    if st.sidebar.button("ESD INTERLOCK", use_container_width=True):
        st.session_state.show_esd = True
        st.session_state.page = "terminal"
        st.rerun()
    st.sidebar.caption("SYS · SIF precursor pipeline · detect → score → patterns")
    return st.session_state.page
def render_topbar(df: pd.DataFrame, metrics: dict) -> pd.DataFrame:
    left, mid, right = st.columns([2.3, 3.4, 1.3])
    with left:
        st.markdown(
            """
            <div class="pc-kicker">Petro-Core // AI DPR Command &amp; Digital Twin Center</div>
            <div class="pc-title">SIF Precursor Intelligence</div>
            <div class="pc-sub">Petroleum operations decision support · observation corpus analytics</div>
            """,
            unsafe_allow_html=True,
        )
    with mid:
        sites = ["All fields"] + metrics["sites"]
        selected = st.selectbox("Project / field", sites, label_visibility="collapsed")
        window = "—"
        if metrics["date_min"]:
            window = f"{metrics['date_min']} → {metrics['date_max']}"
        c1, c2, c3 = st.columns(3)
        c1.markdown(
            f'<div class="hdr-chip">REPORTS<br><b>{metrics["total"]}</b></div>',
            unsafe_allow_html=True,
        )
        c2.markdown(
            f'<div class="hdr-chip">SIF FLAG RATE<br><b>{metrics["sif_rate"]:.1f}%</b></div>',
            unsafe_allow_html=True,
        )
        c3.markdown(
            f'<div class="hdr-chip">WINDOW<br><b>{_esc(window)}</b></div>',
            unsafe_allow_html=True,
        )
    with right:
        if st.button("View flagged reports", type="primary", use_container_width=True):
            st.session_state.page = "anomaly"
            st.rerun()
        st.caption("Opens flagged reports for human review. No control action is taken.")
    if selected != "All fields" and "site" in df.columns:
        df = df[df["site"] == selected].copy()
    return df
def render_kpi_row(metrics: dict) -> None:
    if metrics["has_ground_truth"]:
        label_value = str(metrics["mismatches"])
        label_meta = "Compared with supplied reference labels; not real-world validation"
    else:
        label_value = "N/A"
        label_meta = "No reference labels supplied"
    kpis = [
        (
            "",
            "Reports analyzed",
            str(metrics["total"]),
            f"Current view · {metrics['site_count']} sites",
        ),
        (
            "cyan",
            "Predicted SIF flags",
            str(metrics["sif_yes"]),
            f"{metrics['sif_rate']:.1f}% flagged · human review required",
        ),
        (
            "warn",
            "Failed-barrier signals",
            str(metrics["barrier_n"]),
            "Reports with rule-detected failure language",
        ),
        (
            "crit",
            "High / critical risk",
            str(metrics["high_or_critical"]),
            "Heuristic review-priority bands, not probabilities",
        ),
        (
            "green",
            "Label mismatches",
            label_value,
            label_meta,
        ),
    ]
    cols = st.columns(5)
    for col, (klass, label, value, meta) in zip(cols, kpis):
        col.markdown(
            f"""
            <div class="kpi-card {klass}">
              <div class="kpi-label">{_esc(label)}</div>
              <div class="kpi-value">{_esc(value)}</div>
              <div class="kpi-meta">{_esc(meta)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
def render_digital_twin(df: pd.DataFrame, patterns: dict) -> None:
    st.markdown("### Report concentration by site and location")
    st.caption(
        "Rule-based grouping of reports by site and location. "
        "This is not a live digital twin or semantic clustering."
    )
    nodes = location_nodes(df, n=6)
    if nodes.empty:
        st.info("No site and location data is available for the current reports.")
        return
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("#### Where reports are concentrated")
        display_nodes = nodes.rename(
            columns={
                "site": "Site",
                "location": "Location",
                "reports": "Reports",
                "sif": "SIF flags",
                "avg_risk": "Mean heuristic risk",
                "critical": "Critical flags",
            }
        )
        st.dataframe(display_nodes, use_container_width=True, hide_index=True)
        st.markdown("#### Recurring site–activity–barrier patterns")
        st.caption(
            "Rule-based grouping by site, activity, and failed-barrier text. "
            "Locations are listed as examples; this is not semantic similarity."
        )
        required = {
            "site",
            "activity",
            "location",
            "barrier_failures",
            "report_id",
        }
        if required.issubset(df.columns):
            repeat_rows = df[
                ["site", "activity", "location", "barrier_failures", "report_id"]
            ].copy()
            repeat_rows["barrier_failure"] = (
                repeat_rows["barrier_failures"].fillna("").astype(str).str.strip()
            )
            repeat_rows = repeat_rows[
                ~repeat_rows["barrier_failure"].str.lower().isin(
                    ["", "none", "nan", "[]"]
                )
            ]
            recurring = (
                repeat_rows.groupby(
                    ["site", "activity", "barrier_failure"],
                    dropna=False,
                )
                .agg(
                    Reports=("report_id", "nunique"),
                    Locations=(
                        "location",
                        lambda values: ", ".join(
                            values.dropna().astype(str).drop_duplicates().head(3)
                        ),
                    ),
                    Example_reports=(
                        "report_id",
                        lambda ids: ", ".join(
                            ids.astype(str).drop_duplicates().head(3)
                        ),
                    ),
                )
                .reset_index()
            )
            recurring = recurring[recurring["Reports"] >= 2].sort_values(
                "Reports", ascending=False
            )
            if recurring.empty:
                st.info("No repeated site–activity–barrier patterns found in this view.")
            else:
                recurring = recurring.rename(
                    columns={
                        "site": "Site",
                        "activity": "Activity",
                        "barrier_failure": "Failed barrier",
                        "Example_reports": "Example reports",
                    }
                )
                st.dataframe(
                    recurring.head(10),
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.info("Required report, site, activity, location, or barrier fields are missing.")
    with right:
        st.markdown("#### Priority report for review")
        candidates = top_critical_rows(df, n=5)
        if candidates.empty:
            st.info("No scored reports are available.")
            return
        report_ids = candidates["report_id"].astype(str).tolist()
        selected_id = st.selectbox(
            "Choose a report",
            report_ids,
            key="dashboard_priority_report",
        )
        report = candidates[
            candidates["report_id"].astype(str) == selected_id
        ].iloc[0]
        st.metric("Heuristic risk score", report.get("risk_score", "—"))
        st.caption("This score is a review-priority heuristic, not a probability.")
        st.write("**Why it was flagged**")
        st.write(
            report.get("risk_reason")
            or report.get("primary_risk")
            or "No reason recorded."
        )
        evidence = report.get("sif_evidence")
        if isinstance(evidence, dict):
            evidence_items = [evidence]
        elif isinstance(evidence, list):
            evidence_items = evidence
        else:
            evidence_items = []
        if evidence_items:
            with st.expander(
                f"Show detector evidence ({len(evidence_items)} matches)"
            ):
                for item in evidence_items[:5]:
                    if isinstance(item, dict):
                        heading = (
                            item.get("category")
                            or item.get("barrier")
                            or "Detector match"
                        )
                        st.markdown(f"**{heading}**")
                        text = item.get("text")
                        if text:
                            st.markdown(f"> {text}")
                        rule_id = item.get("rule_id")
                        if rule_id:
                            st.caption(f"Rule: {rule_id}")
                    else:
                        st.write(item)
        elif isinstance(evidence, str) and evidence.strip():
            with st.expander("Show detector evidence"):
                st.write(evidence)
        narrative = report.get("free_text")
        if isinstance(narrative, str) and narrative.strip():
            st.write("**Report narrative**")
            st.info(narrative)
def render_pipeline_and_flags(df: pd.DataFrame, metrics: dict) -> None:
    left, right = st.columns([1.15, 1])
    with left:
        st.markdown(
            """
            <div class="panel">
              <div class="panel-h">
                <div class="panel-title">Report analysis pipeline</div>
                <div class="panel-note">MODEL: EXISTING SIF DETECTOR</div>
              </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="stage-row">
              <div class="stage">
                <div class="s-k">STAGE 01</div>
                <div class="s-t">Unstructured</div>
                <div class="s-m">{metrics['total']} reports</div>
              </div>
              <div class="stage">
                <div class="s-k">STAGE 02</div>
                <div class="s-t">Normalize</div>
                <div class="s-m">clean_text applied</div>
              </div>
              <div class="stage">
                <div class="s-k">STAGE 03</div>
                <div class="s-t">Entities</div>
                <div class="s-m">hit {metrics['extraction_hit']:.1f}%</div>
              </div>
              <div class="stage active">
                <div class="s-k">STAGE 04</div>
                <div class="s-t">SIF + Risk</div>
                <div class="s-m">{metrics['sif_yes']} SIF · {metrics['critical']} CRIT</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        recent = df.copy()
        if "date" in recent.columns:
            recent["date"] = pd.to_datetime(recent["date"], errors="coerce")
            recent = recent.sort_values("date", ascending=False)
        lines = []
        for _, row in recent.head(8).iterrows():
            lines.append(
                f"[{_esc(row.get('date', ''))}] {_esc(row.get('report_id',''))} "
                f"{_esc(row.get('site',''))} {_esc(row.get('risk_level',''))} "
                f"SIF={_esc(row.get('predicted_sif',''))} :: {_esc(str(row.get('free_text',''))[:90])}"
            )
        st.markdown(
            f'<div class="panel-note" style="margin-top:10px;">RECENT REPORT EXAMPLES / PROCESSED NARRATIVES</div>'
            f'<div class="term">{"<br>".join(lines) if lines else "No reports in view."}</div></div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"""
            <div class="panel">
              <div class="panel-h">
                <div class="panel-title">Highest-priority reports for review</div>
                <div class="panel-note">{metrics['critical']} CRITICAL · {metrics['high']} HIGH · HUMAN REVIEW REQUIRED</div>
              </div>
            """,
            unsafe_allow_html=True,
        )
        rows = top_critical_rows(df, n=3)
        if rows.empty:
            st.info("No scored reports available.")
        else:
            for _, r in rows.iterrows():
                klass = "sev-card" if r.get("risk_level") == "CRITICAL" else "sev-card warn"
                st.markdown(
                    f"""
                    <div class="{klass}">
                      <div class="sev-k">{_esc(r.get('risk_level',''))} · {_esc(r.get('report_id',''))} · {_esc(r.get('site',''))}</div>
                      <div class="sev-t">{_esc(r.get('primary_risk', 'Precursor risk'))}</div>
                      <div class="sev-b">{_esc(r.get('risk_reason', ''))}</div>
                      <div class="sev-b" style="margin-top:6px;">{_esc(str(r.get('free_text',''))[:220])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)
def render_lower_analytics(df: pd.DataFrame, patterns: dict, metrics: dict) -> None:
    recs = recommendations(df, patterns)
    counts = risk_counts(df)
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        st.markdown(
            '<div class="panel"><div class="panel-title">Review priorities</div>',
            unsafe_allow_html=True,
        )
        for rec in recs:
            rec_text = str(rec)
            if "Confined-space observations are SIF-positive" in rec_text:
                rec_text = (
                    "Review confined-space reports and check the narrative evidence "
                    "for gas-testing controls."
                )
            st.markdown(f"- {rec_text}")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(
            '<div class="panel"><div class="panel-title">Risk Distribution</div>',
            unsafe_allow_html=True,
        )
        bars = []
        fill = {"LOW": "ok", "MEDIUM": "ok", "HIGH": "warn", "CRITICAL": "crit"}
        max_n = max(int(counts.max()), 1)
        for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            n = int(counts.get(level, 0))
            pct = int(n / max_n * 100)
            bars.append(
                f'<div class="bar-row"><div class="bar-lab">{level}</div>'
                f'<div class="bar-track"><div class="bar-fill {fill[level]}" style="width:{pct}%"></div></div>'
                f'<div class="bar-n">{n}</div></div>'
            )
        st.markdown("".join(bars) + "</div>", unsafe_allow_html=True)
    with c3:
        st.markdown(
            '<div class="panel"><div class="panel-title">Control signals in reports</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            Barrier-language gap rate: <b>{100 - metrics['compliance']:.1f}%</b><br>
            SIF-positive share: <b>{metrics['sif_rate']:.1f}%</b><br>
            High+critical share: <b>{_rate_text(metrics['high_or_critical'], metrics['total'])}</b>
            """,
            unsafe_allow_html=True,
        )
        primary = patterns.get("primary_risk_patterns", pd.DataFrame())
        if primary is not None and not primary.empty:
            max_n = max(int(primary.head(6)["count"].max()), 1)
            bars = []
            for _, row in primary.head(6).iterrows():
                n = int(row["count"])
                pct = int(n / max_n * 100)
                bars.append(
                    f'<div class="bar-row"><div class="bar-lab">{_esc(row["primary_risk"])[:12]}</div>'
                    f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>'
                    f'<div class="bar-n">{n}</div></div>'
                )
            st.markdown("".join(bars), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
def _rate_text(part: int, total: int) -> str:
    if total <= 0:
        return "0%"
    return f"{part / total * 100:.1f}%"
def page_dashboard(df: pd.DataFrame, patterns: dict, metrics: dict) -> None:
    render_kpi_row(metrics)
    st.caption(
        "The bundled 250-report dataset is synthetic. Its results are development "
        "evidence, not real-world OIL accuracy."
    )
    st.markdown("")
    render_digital_twin(df, patterns)
    render_pipeline_and_flags(df, metrics)
    render_lower_analytics(df, patterns, metrics)
def _filter_explorer(df: pd.DataFrame) -> pd.DataFrame:
    c1, c2, c3 = st.columns(3)
    risk_opts = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    with c1:
        risk_filter = st.multiselect("Risk level", risk_opts, default=["HIGH", "CRITICAL"])
    with c2:
        sif_filter = st.multiselect("SIF prediction", ["NO", "YES"], default=["YES"])
    with c3:
        sites = sorted(df["site"].dropna().unique()) if "site" in df.columns else []
        site_filter = st.multiselect("Site", sites)
    work = df.copy()
    if risk_filter:
        work = work[work["risk_level"].isin(risk_filter)]
    if sif_filter:
        work = work[work["predicted_sif"].isin(sif_filter)]
    if site_filter:
        work = work[work["site"].isin(site_filter)]
    return work
DISPLAY_COLUMNS = [
    "report_id",
    "date",
    "site",
    "location",
    "activity",
    "predicted_sif",
    "sif_score",
    "sif_indicators",
    "risk_score",
    "risk_level",
    "primary_risk",
    "barrier_failures",
    "extracted_hazard",
    "extracted_energy",
]
def _show_table(df: pd.DataFrame) -> None:
    cols = [c for c in DISPLAY_COLUMNS if c in df.columns]
    st.dataframe(df[cols] if cols else df, use_container_width=True, hide_index=True)
def page_dpr_document_ai(df: pd.DataFrame, metrics: dict) -> None:
    st.markdown('<div class="panel-title">DPR Document AI</div>', unsafe_allow_html=True)
    st.caption("Entity extraction, SIF classification, and risk scoring from the existing NLP pipeline.")
    render_kpi_row(metrics)
    filtered = _filter_explorer(df)
    st.write(f"Reports matching filters: {len(filtered)}")
    _show_table(filtered)
    st.markdown('<div class="panel-title">Detailed report analysis</div>', unsafe_allow_html=True)
    if filtered.empty:
        st.info("No reports match the selected filters.")
        return
    selected_report = st.selectbox("Select report ID", filtered["report_id"].tolist())
    selected = filtered[filtered["report_id"] == selected_report].iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SIF prediction", selected["predicted_sif"])
    c2.metric("SIF score", selected["sif_score"])
    c3.metric("Risk score", selected["risk_score"])
    c4.metric("Risk level", selected["risk_level"])
    st.write("**Primary risk:**", selected["primary_risk"])
    st.write("**SIF indicators:**", selected["sif_indicators"])
    st.write("**Barrier failures:**", selected["barrier_failures"])
    st.write("**Risk factors:**", selected.get("risk_factors", ""))
    st.write("**Risk reason:**", selected["risk_reason"])
    st.write("**Extracted hazard / energy / barrier:**",
             f"{selected.get('extracted_hazard', '')} / {selected.get('extracted_energy', '')} / {selected.get('extracted_barrier', '')}")
    if "free_text" in selected.index:
        st.info(selected["free_text"])
def page_location_slice(df: pd.DataFrame, patterns: dict, title: str, needles: list[str]) -> None:
    st.markdown(f'<div class="panel-title">{_esc(title)}</div>', unsafe_allow_html=True)
    mask = pd.Series(False, index=df.index)
    if "location" in df.columns:
        for needle in needles:
            mask = mask | df["location"].astype(str).str.contains(needle, case=False, na=False)
    if "activity" in df.columns:
        for needle in needles:
            mask = mask | df["activity"].astype(str).str.contains(needle, case=False, na=False)
    subset = df[mask]
    if subset.empty:
        st.markdown(
            '<div class="placeholder">No matching location/activity rows in the current corpus. '
            "This view is a filtered slice of existing reports, not a separate CAD module.</div>",
            unsafe_allow_html=True,
        )
        return
    m = compute_metrics(subset)
    render_kpi_row(m)
    loc = patterns.get("location_patterns", pd.DataFrame())
    if loc is not None and not loc.empty:
        st.dataframe(loc.sort_values("sif_rate", ascending=False), use_container_width=True, hide_index=True)
    _show_table(subset)
def page_anomaly(df: pd.DataFrame) -> None:
    st.markdown('<div class="panel-title">Anomaly Detection</div>', unsafe_allow_html=True)
    st.caption("HIGH and CRITICAL SIF-positive observations from the risk scorer.")
    work = df.copy()
    if "risk_level" in work.columns:
        work = work[work["risk_level"].isin(["HIGH", "CRITICAL"])]
    if "predicted_sif" in work.columns:
        flagged = work[work["predicted_sif"] == "YES"]
        work = flagged if not flagged.empty else work
    st.write(f"Flagged reports: {len(work)}")
    _show_table(work)
def page_logs(df: pd.DataFrame) -> None:
    st.markdown('<div class="panel-title">SCADA Audit Logs</div>', unsafe_allow_html=True)
    st.caption(
        "Chronological observation log. Live SCADA historians are not connected; "
        "this is the processed safety-report audit trail."
    )
    work = df.copy()
    if "date" in work.columns:
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
        work = work.sort_values("date", ascending=False)
    q = st.text_input("Search report id, site, location, or text")
    if q:
        blob = work.astype(str).apply(lambda row: " ".join(row.values), axis=1)
        work = work[blob.str.contains(q, case=False, na=False)]
    _show_table(work)
def page_diagnostics(df: pd.DataFrame, metrics: dict) -> None:
    st.markdown('<div class="panel-title">Diagnostics</div>', unsafe_allow_html=True)
    st.write(
        {
            "reports": metrics["total"],
            "sites": metrics["site_count"],
            "sif_yes": metrics["sif_yes"],
            "critical": metrics["critical"],
            "pipeline": "preprocessing → entity_extraction → sif_detector → risk_scoring → pattern_analysis",
        }
    )
    if not metrics["has_ground_truth"]:
        st.markdown(
            '<div class="placeholder">Ground-truth labels are not in this file, so detector accuracy cannot be scored here. '
            "Use data/synthetic_reports.csv (includes ground_truth_sif) or run src/evaluate_detector.py.</div>",
            unsafe_allow_html=True,
        )
        return
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
    y_true = df["ground_truth_sif"].map({"NO": 0, "YES": 1})
    y_pred = df["predicted_sif"].map({"NO": 0, "YES": 1})
    valid = y_true.notna() & y_pred.notna()
    y_true, y_pred = y_true[valid], y_pred[valid]
    acc = accuracy_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    st.metric("Detector accuracy vs ground_truth_sif", f"{acc:.2%}")
    st.write("Confusion matrix [NO, YES]:")
    st.dataframe(
        pd.DataFrame(cm, index=["Actual NO", "Actual YES"], columns=["Pred NO", "Pred YES"]),
        use_container_width=True,
    )
    st.text(
        classification_report(
            y_true, y_pred, target_names=["NO SIF", "SIF"], zero_division=0
        )
    )
def page_terminal(df: pd.DataFrame, metrics: dict) -> None:
    st.markdown('<div class="panel-title">Terminal SCADA</div>', unsafe_allow_html=True)
    if st.session_state.get("show_esd"):
        st.warning(
            "ESD INTERLOCK is a reserved interface. No live emergency shutdown system is attached. "
            f"{metrics['critical']} CRITICAL observation flags are in the current corpus."
        )
    st.caption("Read-only dump of scored observations (latest first).")
    work = df.copy()
    if "date" in work.columns:
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
        work = work.sort_values("date", ascending=False)
    lines = []
    for _, row in work.head(40).iterrows():
        lines.append(
            f"{row.get('date','')}  {row.get('report_id','')}  {row.get('site','')}  "
            f"{row.get('location','')}  SIF={row.get('predicted_sif','')}  "
            f"{row.get('risk_level','')}({row.get('risk_score','')})  {row.get('primary_risk','')}"
        )
    st.code("\n".join(lines) if lines else "empty corpus", language="text")
    st.markdown(
        '<div class="placeholder">Physical SCADA tags (flow, pressure, methane, separator limits) '
        "are not present in this repository. Connect a historian here later without changing the SIF pipeline.</div>",
        unsafe_allow_html=True,
    )
def render_page(page: str, df: pd.DataFrame, patterns: dict, metrics: dict) -> None:
    if page == "dashboard":
        page_dashboard(df, patterns, metrics)
    elif page == "dpr_ai":
        page_dpr_document_ai(df, metrics)
    elif page == "manifolds":
        page_location_slice(
            df, patterns, "Manifolds & Rigs",
            ["Rig", "Well Pad", "Production", "Compressor", "Gathering", "Processing", "Tank"],
        )
    elif page == "pipelines":
        page_location_slice(df, patterns, "Pipeline Vectors", ["Pipeline"])
    elif page == "anomaly":
        page_anomaly(df)
    elif page == "scada_logs":
        page_logs(df)
    elif page == "diagnostics":
        page_diagnostics(df, metrics)
    elif page == "terminal":
        page_terminal(df, metrics)
    else:
        page_dashboard(df, patterns, metrics)
