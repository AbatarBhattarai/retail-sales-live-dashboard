#!/usr/bin/env python3
"""
Build a live, interactive HTML version of the Retail Sales Dashboard.

Reads retail_orders_clean.csv (1,200 orders), computes every aggregate the
dashboard shows, verifies the headline numbers against the known-good values
from the Power BI build, then writes a single self-contained index.html with
the order data embedded as JSON. Category / region / channel filters in the
page recalculate all KPIs and charts in the browser.

Usage:
    python3 build_dashboard.py

Output:
    index.html  (in this folder)
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE.parent / "power-bi-retail-dashboard" / "retail_orders_clean.csv"
OUT_PATH = HERE / "index.html"

# Known verified numbers from the Power BI dashboard build (Nov 12, 2026).
KNOWN = {
    "total_revenue": 118568.75,
    "aov": 98.81,
    "top_category": "Clothing",
    "top_category_share": 31.2,   # percent, 1 decimal
    "peak_month": "2024-11",      # November 2024
    "orders": 1200,
}


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["revenue"] = float(r["revenue"])
        r["quantity"] = int(r["quantity"])
        r["month"] = r["order_date"][:7]  # YYYY-MM
    return rows


def aggregate(rows):
    total_revenue = round(sum(r["revenue"] for r in rows), 2)
    orders = len(rows)
    units = sum(r["quantity"] for r in rows)
    aov = round(total_revenue / orders, 2) if orders else 0.0

    by_category = defaultdict(float)
    by_region = defaultdict(float)
    by_month = defaultdict(float)
    by_channel = defaultdict(float)
    for r in rows:
        by_category[r["category"]] += r["revenue"]
        by_region[r["region"]] += r["revenue"]
        by_month[r["month"]] += r["revenue"]
        by_channel[r["channel"]] += r["revenue"]

    by_category = {k: round(v, 2) for k, v in sorted(by_category.items(), key=lambda kv: -kv[1])}
    by_region = {k: round(v, 2) for k, v in sorted(by_region.items(), key=lambda kv: -kv[1])}
    by_month = {k: round(v, 2) for k, v in sorted(by_month.items())}
    by_channel = {k: round(v, 2) for k, v in sorted(by_channel.items(), key=lambda kv: -kv[1])}

    top_category = max(by_category, key=by_category.get)
    top_share = round(by_category[top_category] / total_revenue * 100, 1) if total_revenue else 0.0
    peak_month = max(by_month, key=by_month.get)

    return {
        "total_revenue": total_revenue,
        "orders": orders,
        "units": units,
        "aov": aov,
        "by_category": by_category,
        "by_region": by_region,
        "by_month": by_month,
        "by_channel": by_channel,
        "top_category": top_category,
        "top_category_share": top_share,
        "peak_month": peak_month,
        "peak_month_revenue": by_month[peak_month],
    }


def verify(agg):
    """Check computed aggregates against the known verified numbers."""
    checks = [
        ("orders == 1200", agg["orders"] == KNOWN["orders"], f'{agg["orders"]} vs {KNOWN["orders"]}'),
        ("total revenue == $118,568.75", abs(agg["total_revenue"] - KNOWN["total_revenue"]) < 0.01,
         f'${agg["total_revenue"]:,.2f} vs ${KNOWN["total_revenue"]:,.2f}'),
        ("AOV == $98.81", abs(agg["aov"] - KNOWN["aov"]) < 0.005, f'${agg["aov"]:.2f} vs ${KNOWN["aov"]:.2f}'),
        ("top category == Clothing", agg["top_category"] == KNOWN["top_category"],
         f'{agg["top_category"]} vs {KNOWN["top_category"]}'),
        ("Clothing share == 31.2%", abs(agg["top_category_share"] - KNOWN["top_category_share"]) < 0.05,
         f'{agg["top_category_share"]:.1f}% vs {KNOWN["top_category_share"]:.1f}%'),
        ("peak month == Nov 2024", agg["peak_month"] == KNOWN["peak_month"],
         f'{agg["peak_month"]} vs {KNOWN["peak_month"]}'),
    ]
    print("Verification against known verified numbers:")
    ok = True
    for name, passed, detail in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}  ({detail})")
        ok = ok and passed
    return ok


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Retail Sales Dashboard — Abatar Bhattarai</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #0f172a; --panel: #ffffff; --ink: #0f172a; --muted: #64748b;
    --accent: #2563eb; --accent2: #16a34a; --line: #e2e8f0;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: "Segoe UI", system-ui, -apple-system, Arial, sans-serif; background: #f1f5f9; color: var(--ink); }
  header { background: var(--bg); color: #fff; padding: 28px 20px 22px; }
  header .wrap, main { max-width: 1180px; margin: 0 auto; }
  header h1 { font-size: 1.65rem; font-weight: 700; letter-spacing: .2px; }
  header p { color: #cbd5e1; margin-top: 6px; font-size: .95rem; max-width: 760px; line-height: 1.45; }
  main { padding: 22px 20px 40px; }
  .filters { display: flex; flex-wrap: wrap; gap: 14px; background: var(--panel); border: 1px solid var(--line);
             border-radius: 12px; padding: 14px 16px; margin-bottom: 18px; align-items: end; }
  .filters label { display: block; font-size: .75rem; font-weight: 600; text-transform: uppercase;
                   letter-spacing: .06em; color: var(--muted); margin-bottom: 5px; }
  .filters select { padding: 8px 10px; border: 1px solid var(--line); border-radius: 8px; font-size: .95rem;
                    background: #fff; min-width: 170px; color: var(--ink); }
  .filters button { padding: 9px 16px; border: 0; border-radius: 8px; background: var(--accent); color: #fff;
                    font-size: .9rem; font-weight: 600; cursor: pointer; }
  .filters button:hover { background: #1d4ed8; }
  .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-bottom: 18px; }
  .kpi { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 16px 18px; }
  .kpi .label { font-size: .75rem; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
  .kpi .value { font-size: 1.7rem; font-weight: 700; margin-top: 6px; }
  .kpi .sub { font-size: .82rem; color: var(--muted); margin-top: 3px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap: 14px; }
  .card { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 16px 18px 10px; }
  .card h2 { font-size: 1rem; font-weight: 650; margin-bottom: 10px; }
  .card .chartbox { position: relative; height: 260px; }
  .wide { grid-column: 1 / -1; }
  .wide .chartbox { height: 300px; }
  footer { max-width: 1180px; margin: 0 auto; padding: 0 20px 30px; color: var(--muted); font-size: .85rem; line-height: 1.5; }
</style>
</head>
<body>
<header>
  <div class="wrap">
    <h1>Retail Sales Dashboard</h1>
    <p>Analysis of 1,200 retail orders (2024): revenue by category, region, month, and sales channel.
       Use the filters to slice the data — every KPI and chart recalculates. Built by Abatar Bhattarai.</p>
  </div>
</header>
<main>
  <div class="filters">
    <div>
      <label for="f-category">Category</label>
      <select id="f-category"><option value="">All categories</option></select>
    </div>
    <div>
      <label for="f-region">Region</label>
      <select id="f-region"><option value="">All regions</option></select>
    </div>
    <div>
      <label for="f-channel">Channel</label>
      <select id="f-channel"><option value="">All channels</option></select>
    </div>
    <button id="reset" type="button">Reset filters</button>
  </div>

  <section class="kpis">
    <div class="kpi"><div class="label">Total Revenue</div><div class="value" id="k-revenue">–</div><div class="sub">Filtered selection</div></div>
    <div class="kpi"><div class="label">Orders</div><div class="value" id="k-orders">–</div><div class="sub">Transactions in selection</div></div>
    <div class="kpi"><div class="label">Avg Order Value</div><div class="value" id="k-aov">–</div><div class="sub">Revenue per order</div></div>
    <div class="kpi"><div class="label">Units Sold</div><div class="value" id="k-units">–</div><div class="sub">Total quantity</div></div>
    <div class="kpi"><div class="label">Top Category</div><div class="value" id="k-topcat">–</div><div class="sub" id="k-topcat-sub"></div></div>
  </section>

  <section class="grid">
    <div class="card wide"><h2>Monthly Revenue Trend</h2><div class="chartbox"><canvas id="ch-month"></canvas></div></div>
    <div class="card"><h2>Revenue by Category</h2><div class="chartbox"><canvas id="ch-category"></canvas></div></div>
    <div class="card"><h2>Revenue by Region</h2><div class="chartbox"><canvas id="ch-region"></canvas></div></div>
    <div class="card"><h2>Online vs In-Store</h2><div class="chartbox"><canvas id="ch-channel"></canvas></div></div>
    <div class="card"><h2>Orders by Category</h2><div class="chartbox"><canvas id="ch-catorders"></canvas></div></div>
  </section>
</main>
<footer>
  Data: 1,200 cleaned retail orders, January–December 2024. Headline figures (all filters cleared):
  total revenue $118,568.75, average order value $98.81, top category Clothing at 31.2% of revenue,
  peak month November 2024. The same dataset and measures power my Power BI version of this dashboard.
</footer>

<script>
const ORDERS = __DATA_JSON__;
const money = v => "$" + v.toLocaleString("en-US", {minimumFractionDigits: 2, maximumFractionDigits: 2});
const money0 = v => "$" + Math.round(v).toLocaleString("en-US");
const PALETTE = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed", "#0891b2"];

function fillSelect(id, values) {
  const sel = document.getElementById(id);
  values.forEach(v => {
    const o = document.createElement("option");
    o.value = v; o.textContent = v; sel.appendChild(o);
  });
}
fillSelect("f-category", [...new Set(ORDERS.map(r => r.category))].sort());
fillSelect("f-region",   [...new Set(ORDERS.map(r => r.region))].sort());
fillSelect("f-channel",  [...new Set(ORDERS.map(r => r.channel))].sort());

const charts = {};
function makeChart(id, cfg) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart(document.getElementById(id), cfg);
}
const tooltipMoney = { callbacks: { label: c => " " + (c.dataset.label || "") + " " + money(c.parsed.y ?? c.parsed) } };

function sumBy(rows, key) {
  const m = new Map();
  rows.forEach(r => m.set(r[key], (m.get(r[key]) || 0) + r.revenue));
  return [...m.entries()].sort((a, b) => b[1] - a[1]);
}

function render() {
  const cat = document.getElementById("f-category").value;
  const reg = document.getElementById("f-region").value;
  const chn = document.getElementById("f-channel").value;
  const rows = ORDERS.filter(r =>
    (!cat || r.category === cat) && (!reg || r.region === reg) && (!chn || r.channel === chn));

  const revenue = rows.reduce((s, r) => s + r.revenue, 0);
  const units = rows.reduce((s, r) => s + r.quantity, 0);
  document.getElementById("k-revenue").textContent = money(revenue);
  document.getElementById("k-orders").textContent = rows.length.toLocaleString("en-US");
  document.getElementById("k-aov").textContent = rows.length ? money(revenue / rows.length) : "$0.00";
  document.getElementById("k-units").textContent = units.toLocaleString("en-US");

  const catData = sumBy(rows, "category");
  if (catData.length && revenue > 0) {
    document.getElementById("k-topcat").textContent = catData[0][0];
    document.getElementById("k-topcat-sub").textContent =
      (catData[0][1] / revenue * 100).toFixed(1) + "% of revenue in selection";
  } else {
    document.getElementById("k-topcat").textContent = "–";
    document.getElementById("k-topcat-sub").textContent = "";
  }

  const months = [...new Set(ORDERS.map(r => r.month))].sort();
  const monthRev = months.map(m => rows.filter(r => r.month === m).reduce((s, r) => s + r.revenue, 0));
  const monthLabels = months.map(m => {
    const [y, mo] = m.split("-");
    return new Date(y, mo - 1).toLocaleString("en-US", {month: "short"}) + " " + y.slice(2);
  });
  makeChart("ch-month", {
    type: "line",
    data: { labels: monthLabels, datasets: [{ label: "Revenue", data: monthRev,
      borderColor: "#2563eb", backgroundColor: "rgba(37,99,235,.12)", fill: true, tension: .3, pointRadius: 3 }] },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: tooltipMoney },
      scales: { y: { ticks: { callback: v => money0(v) } } } }
  });

  makeChart("ch-category", {
    type: "bar",
    data: { labels: catData.map(d => d[0]), datasets: [{ label: "Revenue", data: catData.map(d => d[1]),
      backgroundColor: PALETTE }] },
    options: { responsive: true, maintainAspectRatio: false, indexAxis: "y",
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => " " + money(c.parsed.x) } } },
      scales: { x: { ticks: { callback: v => money0(v) } } } }
  });

  const regData = sumBy(rows, "region");
  makeChart("ch-region", {
    type: "bar",
    data: { labels: regData.map(d => d[0]), datasets: [{ label: "Revenue", data: regData.map(d => d[1]),
      backgroundColor: "#16a34a" }] },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: tooltipMoney },
      scales: { y: { ticks: { callback: v => money0(v) } } } }
  });

  const chnData = sumBy(rows, "channel");
  makeChart("ch-channel", {
    type: "doughnut",
    data: { labels: chnData.map(d => d[0]), datasets: [{ data: chnData.map(d => d[1]),
      backgroundColor: ["#2563eb", "#f59e0b", "#16a34a"] }] },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { tooltip: { callbacks: { label: c => " " + c.label + ": " + money(c.parsed) +
        " (" + (revenue ? (c.parsed / revenue * 100).toFixed(1) : "0.0") + "%)" } } } }
  });

  const catOrders = [...new Set(ORDERS.map(r => r.category))].sort()
    .map(c => [c, rows.filter(r => r.category === c).length]).sort((a, b) => b[1] - a[1]);
  makeChart("ch-catorders", {
    type: "bar",
    data: { labels: catOrders.map(d => d[0]), datasets: [{ label: "Orders", data: catOrders.map(d => d[1]),
      backgroundColor: "#7c3aed" }] },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
  });
}

["f-category", "f-region", "f-channel"].forEach(id =>
  document.getElementById(id).addEventListener("change", render));
document.getElementById("reset").addEventListener("click", () => {
  ["f-category", "f-region", "f-channel"].forEach(id => document.getElementById(id).value = "");
  render();
});
render();
</script>
</body>
</html>
"""


def main():
    if not CSV_PATH.exists():
        print(f"ERROR: CSV not found at {CSV_PATH}", file=sys.stderr)
        return 1
    rows = load_rows(CSV_PATH)
    agg = aggregate(rows)

    if not verify(agg):
        print("\nVERIFICATION FAILED — CSV disagrees with the known verified numbers. "
              "index.html was NOT regenerated.", file=sys.stderr)
        return 1
    print("\nAll checks passed.")

    # Compact per-order records for the in-browser filters.
    records = [
        {
            "month": r["month"],
            "category": r["category"],
            "region": r["region"],
            "channel": r["channel"],
            "revenue": r["revenue"],
            "quantity": r["quantity"],
        }
        for r in rows
    ]
    html = HTML_TEMPLATE.replace("__DATA_JSON__", json.dumps(records, separators=(",", ":")))
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size:,} bytes, {len(records)} orders embedded)")
    print(f"Aggregates: revenue ${agg['total_revenue']:,.2f} | orders {agg['orders']} | "
          f"AOV ${agg['aov']:.2f} | units {agg['units']} | top {agg['top_category']} "
          f"{agg['top_category_share']:.1f}% | peak {agg['peak_month']} ${agg['peak_month_revenue']:,.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
