# Retail Sales Dashboard — Live Web Version

By Abatar Bhattarai

## Business question

How can the retail sales numbers be shared so anyone can open them in a browser and slice them their own way — no downloads, no software to install, no waiting for someone to send an updated file?

## Data

The same cleaned dataset of 1,200 retail orders from 2024 as my Power BI dashboard (practice data from my Retail Sales Analysis project).

## What I did

- Wrote `build_dashboard.py`, which reads the order data (`retail_orders_clean.csv`), computes all the aggregates, and checks them against the verified headline numbers before generating the page
- Generated `index.html` — a single self-contained page with the data embedded and charts drawn with Chart.js
- Built KPI cards (total revenue, number of orders, average order value, units sold, top category), a monthly revenue trend, revenue by category and region, an online vs. in-store split, and orders by category
- Added filters for category, region, and channel that recalculate every KPI and chart on the page
- Hosted it as a static page with GitHub Pages, so it can be shared as one link

## Key finding

The dashboard's numbers are verified against the source data: total revenue of **$118,568.75 across 1,200 orders**, average order value **$98.81**, Clothing the top category at **31.2% of revenue**, and a peak month of **November 2024 ($14,948.60)**.

## Recommendation

Share one live link instead of passing around static screenshots or spreadsheet copies — everyone then looks at the same numbers, and each person can filter to the category, region, or channel they care about without asking for a new report.

---

I built this as a live, interactive version of my retail sales dashboard so anyone can open it in a browser and explore the data — no downloads, no software to install. It uses the same cleaned dataset of 1,200 retail orders from 2024 as my Power BI dashboard.

## What it shows

- **KPI cards:** total revenue, number of orders, average order value, units sold, and the top category
- **Monthly revenue trend** for January–December 2024
- **Revenue by category** and **revenue by region**
- **Online vs. in-store** revenue split
- **Orders by category**

Filters at the top — category, region, and channel — recalculate every KPI and chart on the page, so the data can be sliced any way you want.

## Headline numbers (verified against the source data)

- Total revenue: **$118,568.75** across 1,200 orders
- Average order value: **$98.81**
- Top category: **Clothing, 31.2%** of revenue
- Peak month: **November 2024** ($14,948.60)

## How it's built

`build_dashboard.py` reads the order data (`retail_orders_clean.csv`), computes all the aggregates, checks them against the verified headline numbers above, and generates `index.html` — a single self-contained page with the data embedded and charts drawn with Chart.js. To rebuild it after updating the data:

```
python3 build_dashboard.py
```

The page is a single static file, so I can host it free with GitHub Pages — just push this folder to a repository and enable Pages.

— Abatar Bhattarai
