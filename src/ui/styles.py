COMMAND_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

:root {
  --bg: #070b10;
  --panel: #101820;
  --panel-2: #0c131b;
  --line: rgba(232, 148, 42, 0.28);
  --line-dim: rgba(140, 170, 190, 0.16);
  --amber: #e8942a;
  --amber-2: #f0b35a;
  --cyan: #3ee6d6;
  --teal: #2ec4b6;
  --green: #4ade80;
  --red: #ff5a5a;
  --warn: #f5c542;
  --text: #d8e4ee;
  --muted: #8ea0b0;
  --dim: #6b7d8c;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
  background: var(--bg) !important;
  color: var(--text);
  font-family: "IBM Plex Sans", sans-serif;
}

.stApp {
  background-image:
    radial-gradient(rgba(180, 210, 230, 0.045) 1px, transparent 1px);
  background-size: 18px 18px;
}

[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu,
footer, [data-testid="stDecoration"] {
  visibility: hidden;
  height: 0;
}

[data-testid="stSidebar"] {
  background: #0a1016 !important;
  border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] > div:first-child {
  background: #0a1016;
}

[data-testid="stSidebar"] * {
  font-family: "IBM Plex Sans", sans-serif;
}

.block-container {
  padding-top: 1.1rem !important;
  padding-bottom: 2rem !important;
  max-width: 1600px;
}

.pc-kicker {
  font-family: "IBM Plex Mono", monospace;
  font-size: 11px;
  letter-spacing: 0.16em;
  color: var(--amber);
  text-transform: uppercase;
}

.pc-title {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.04em;
  margin: 0;
  color: var(--text);
}

.pc-sub {
  color: var(--muted);
  font-size: 12px;
  margin-top: 2px;
}

.pc-brand {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.pc-mark {
  width: 28px;
  height: 28px;
  border: 1px solid var(--amber);
  color: var(--amber);
  display: grid;
  place-items: center;
  font-family: "IBM Plex Mono", monospace;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 0 12px rgba(232, 148, 42, 0.25);
}

.pc-status {
  border: 1px solid rgba(74, 222, 128, 0.35);
  background: rgba(74, 222, 128, 0.08);
  color: var(--green);
  padding: 8px 10px;
  font-size: 11px;
  font-family: "IBM Plex Mono", monospace;
  margin: 8px 0 16px 0;
}

.pc-status strong { color: var(--green); }

.kpi-card {
  background: linear-gradient(180deg, #121b24 0%, #0d141c 100%);
  border: 1px solid var(--line-dim);
  border-top: 2px solid var(--amber);
  padding: 12px 14px 14px 14px;
  min-height: 118px;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02);
}

.kpi-card.cyan { border-top-color: var(--cyan); }
.kpi-card.green { border-top-color: var(--green); }
.kpi-card.warn { border-top-color: var(--warn); }
.kpi-card.crit { border-top-color: var(--red); }

.kpi-label {
  font-family: "IBM Plex Mono", monospace;
  font-size: 10px;
  letter-spacing: 0.12em;
  color: var(--muted);
  text-transform: uppercase;
}

.kpi-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.1;
  margin-top: 8px;
  color: var(--text);
}

.kpi-card.cyan .kpi-value { color: var(--cyan); }
.kpi-card.green .kpi-value { color: var(--green); }
.kpi-card.warn .kpi-value { color: var(--warn); }
.kpi-card.crit .kpi-value { color: var(--red); }

.kpi-meta {
  margin-top: 6px;
  color: var(--dim);
  font-size: 11px;
  font-family: "IBM Plex Mono", monospace;
}

.panel {
  background: #0e151d;
  border: 1px solid var(--line-dim);
  padding: 12px 14px;
  margin-bottom: 12px;
}

.panel-h {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 10px;
}

.panel-title {
  font-family: "IBM Plex Mono", monospace;
  font-size: 12px;
  letter-spacing: 0.12em;
  color: var(--amber-2);
  text-transform: uppercase;
}

.panel-note {
  color: var(--dim);
  font-size: 11px;
  font-family: "IBM Plex Mono", monospace;
}

.twin-wrap {
  position: relative;
  min-height: 430px;
  background:
    linear-gradient(180deg, rgba(10,18,26,0.92), rgba(8,12,18,0.96)),
    radial-gradient(ellipse at 30% 40%, rgba(46, 196, 182, 0.08), transparent 50%);
  border: 1px solid rgba(232, 148, 42, 0.22);
  overflow: hidden;
}

.twin-gridline {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(90,140,160,0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(90,140,160,0.07) 1px, transparent 1px);
  background-size: 42px 42px;
}

.node {
  position: absolute;
  min-width: 160px;
  max-width: 230px;
  background: rgba(12, 20, 28, 0.92);
  border: 1px solid rgba(62, 230, 214, 0.35);
  padding: 8px 10px;
  font-size: 11px;
}

.node.crit { border-color: rgba(255, 90, 90, 0.7); box-shadow: 0 0 16px rgba(255,90,90,0.15); }
.node.warn { border-color: rgba(245, 197, 66, 0.55); }
.node.ok { border-color: rgba(74, 222, 128, 0.45); }
.node .n-k {
  font-family: "IBM Plex Mono", monospace;
  font-size: 9px;
  letter-spacing: 0.12em;
  color: var(--muted);
}
.node .n-t { font-weight: 600; margin-top: 2px; }
.node .n-m { color: var(--dim); font-family: "IBM Plex Mono", monospace; margin-top: 4px; }

.callout {
  background: rgba(18, 12, 12, 0.94);
  border: 1px solid rgba(255, 90, 90, 0.55);
  padding: 10px 12px;
  font-size: 12px;
}

.callout.warn {
  border-color: rgba(232, 148, 42, 0.55);
  background: rgba(22, 16, 10, 0.94);
}

.callout.ok {
  border-color: rgba(62, 230, 214, 0.45);
  background: rgba(8, 18, 18, 0.94);
}

.callout .c-k {
  font-family: "IBM Plex Mono", monospace;
  font-size: 10px;
  letter-spacing: 0.1em;
  color: var(--red);
  margin-bottom: 4px;
}
.callout.warn .c-k { color: var(--amber); }
.callout.ok .c-k { color: var(--cyan); }

.stage-row { display: flex; gap: 8px; }
.stage {
  flex: 1;
  border: 1px solid var(--line-dim);
  background: #0b1218;
  padding: 8px;
  min-height: 78px;
}
.stage.active {
  border-color: rgba(232, 148, 42, 0.55);
  background: rgba(232, 148, 42, 0.08);
}
.stage .s-k {
  font-family: "IBM Plex Mono", monospace;
  font-size: 9px;
  letter-spacing: 0.12em;
  color: var(--muted);
}
.stage .s-t { font-size: 12px; font-weight: 600; margin-top: 4px; }
.stage .s-m { font-size: 11px; color: var(--dim); margin-top: 4px; font-family: "IBM Plex Mono", monospace; }

.term {
  background: #070b0e;
  border: 1px solid var(--line-dim);
  padding: 10px 12px;
  font-family: "IBM Plex Mono", monospace;
  font-size: 11px;
  color: #9fd0c4;
  max-height: 180px;
  overflow: auto;
}

.badge {
  display: inline-block;
  padding: 2px 7px;
  border: 1px solid;
  font-family: "IBM Plex Mono", monospace;
  font-size: 10px;
  letter-spacing: 0.08em;
}
.badge.crit { color: var(--red); border-color: rgba(255,90,90,0.5); }
.badge.warn { color: var(--warn); border-color: rgba(245,197,66,0.45); }
.badge.ok { color: var(--green); border-color: rgba(74,222,128,0.4); }
.badge.info { color: var(--cyan); border-color: rgba(62,230,214,0.4); }

.sev-card {
  border: 1px solid rgba(255,90,90,0.4);
  background: linear-gradient(90deg, rgba(255,90,90,0.12), rgba(14,21,29,0.9));
  padding: 12px;
  margin-bottom: 10px;
}
.sev-card.warn {
  border-color: rgba(232,148,42,0.4);
  background: linear-gradient(90deg, rgba(232,148,42,0.1), rgba(14,21,29,0.9));
}
.sev-k {
  font-family: "IBM Plex Mono", monospace;
  font-size: 10px;
  letter-spacing: 0.12em;
  color: var(--red);
}
.sev-t { font-weight: 700; margin: 4px 0; }
.sev-b { color: var(--muted); font-size: 12px; }

.bar-row { display: flex; align-items: center; gap: 8px; margin: 6px 0; font-size: 12px; }
.bar-lab { width: 84px; color: var(--muted); font-family: "IBM Plex Mono", monospace; font-size: 10px; }
.bar-track { flex: 1; height: 8px; background: #18222c; }
.bar-fill { height: 8px; background: var(--amber); }
.bar-fill.crit { background: var(--red); }
.bar-fill.warn { background: var(--warn); }
.bar-fill.ok { background: var(--green); }
.bar-n { width: 36px; text-align: right; font-family: "IBM Plex Mono", monospace; font-size: 11px; }

.placeholder {
  border: 1px dashed rgba(142, 160, 176, 0.35);
  padding: 16px;
  color: var(--muted);
  font-size: 13px;
  background: rgba(10,16,22,0.6);
}

div.stButton > button {
  border-radius: 2px;
  border: 1px solid rgba(232,148,42,0.45);
  background: #151c24;
  color: var(--text);
  font-family: "IBM Plex Sans", sans-serif;
}

div.stButton > button:hover {
  border-color: var(--amber);
  color: var(--amber-2);
}

div.stButton > button[kind="primary"] {
  background: linear-gradient(180deg, #f0a33a, #d07a16);
  color: #1a1208;
  border: 0;
  font-weight: 700;
}

[data-testid="stMetricValue"] { font-family: "IBM Plex Sans", sans-serif; }
[data-testid="stDataFrame"] { border: 1px solid var(--line-dim); }

.hdr-chip {
  font-family: "IBM Plex Mono", monospace;
  font-size: 11px;
  color: var(--muted);
  border: 1px solid var(--line-dim);
  padding: 8px 10px;
  background: #0c131a;
}

.hdr-chip b { color: var(--cyan); font-weight: 600; }
</style>
"""
