"""Renderer-local style for the notebook landing view.

Rules are prefixed with ``.pytics-report`` so they do not style the
notebook page. There is no external font, image, or script.
"""

NOTEBOOK_CSS = """
.pytics-report {
  --pytics-ink: #1c1917;
  --pytics-muted: #5e5852;
  --pytics-line: #e6e1da;
  --pytics-warning: #6b4423;
  --pytics-notable: #3c4a3d;
  --pytics-info: #5e5852;
  --pytics-font: "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif;
  color: var(--pytics-ink);
  font-family: var(--pytics-font);
  font-size: 14px;
  line-height: 1.45;
  background: transparent;
  max-width: 100%;
  overflow-wrap: anywhere;
  border-top: 2px solid var(--pytics-ink);
  padding-top: 0.75rem;
  text-align: left;
}
.pytics-report,
.pytics-report * {
  box-sizing: border-box;
}
.pytics-report h1,
.pytics-report h2,
.pytics-report p,
.pytics-report ol,
.pytics-report dl,
.pytics-report dd,
.pytics-report dt {
  margin: 0;
  padding: 0;
  font-family: var(--pytics-font);
  color: var(--pytics-ink);
  background: transparent;
  border: 0;
  text-align: left;
  font-weight: 400;
  letter-spacing: normal;
  text-transform: none;
  box-shadow: none;
  float: none;
}
.pytics-report .pytics-mark {
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--pytics-muted);
  margin: 0 0 0.15rem;
}
.pytics-report h1 {
  font-size: 20px;
  line-height: 1.3;
  font-weight: 600;
}
.pytics-report section {
  margin-top: 1.05rem;
  padding-top: 0.8rem;
  border-top: 1px solid var(--pytics-line);
}
.pytics-report h2 {
  font-size: 15px;
  line-height: 1.35;
  font-weight: 600;
}
.pytics-report .pytics-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1.75rem;
  margin-top: 0.15rem;
}
.pytics-report .pytics-metric {
  min-width: 5.5rem;
}
.pytics-report .pytics-metric dt {
  font-size: 13px;
  color: var(--pytics-muted);
}
.pytics-report .pytics-metric dd {
  margin-top: 0.1rem;
  font-size: 18px;
  line-height: 1.3;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.pytics-report table {
  width: 100%;
  max-width: 100%;
  margin: 0.45rem 0 0;
  border-collapse: collapse;
  table-layout: fixed;
  background: transparent;
  font-family: var(--pytics-font);
  font-size: 14px;
  color: var(--pytics-ink);
}
.pytics-report table.pytics-facts {
  table-layout: auto;
}
.pytics-report col.pytics-col-label { width: 46%; }
.pytics-report col.pytics-col-value { width: 27%; }
.pytics-report .pytics-facts col.pytics-col-label { width: 42%; }
.pytics-report .pytics-facts col.pytics-col-value { width: 58%; }
.pytics-report th,
.pytics-report td {
  padding: 0.32rem 0.6rem 0.32rem 0;
  border: 0;
  border-bottom: 1px solid var(--pytics-line);
  vertical-align: top;
  text-align: left;
  font-weight: 400;
  color: var(--pytics-ink);
  background: transparent;
  overflow-wrap: anywhere;
  font-variant-numeric: tabular-nums;
  box-shadow: none;
}
.pytics-report thead th {
  font-size: 13px;
  font-weight: 600;
  color: var(--pytics-muted);
}
.pytics-report tbody th {
  font-weight: 600;
}
.pytics-report .pytics-sides td {
  text-align: right;
}
.pytics-report .pytics-counts {
  margin-top: 0.35rem;
  font-variant-numeric: tabular-nums;
}
.pytics-report .pytics-finding-list {
  list-style: none;
  margin: 0.35rem 0 0;
  padding: 0;
}
.pytics-report .pytics-finding {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  column-gap: 0.75rem;
  row-gap: 0.12rem;
  padding: 0.42rem 0;
  border-bottom: 1px solid var(--pytics-line);
}
.pytics-report .pytics-severity {
  flex: 0 0 5.6rem;
  font-size: 14px;
  font-weight: 600;
}
.pytics-report .pytics-severity-warning { color: var(--pytics-warning); }
.pytics-report .pytics-severity-notable { color: var(--pytics-notable); }
.pytics-report .pytics-severity-info { color: var(--pytics-info); }
.pytics-report .pytics-finding-body {
  display: flex;
  flex-wrap: wrap;
  gap: 0.15rem 0.7rem;
  min-width: 0;
  flex: 1 1 12rem;
}
.pytics-report .pytics-finding-title { font-weight: 600; }
.pytics-report .pytics-finding-subject,
.pytics-report .pytics-finding-detail,
.pytics-report .pytics-muted {
  color: var(--pytics-muted);
}
.pytics-report .pytics-note {
  margin-top: 0.45rem;
  color: var(--pytics-muted);
}
.pytics-report .pytics-subhead {
  margin-top: 0.75rem;
  font-weight: 600;
}
""".strip()
