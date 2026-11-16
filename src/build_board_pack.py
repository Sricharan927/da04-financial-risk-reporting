"""Build the Excel board pack from the database."""
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd

conn = sqlite3.connect("data/processed/finance.db")
pnl = pd.read_sql_query(Path("sql/pnl.sql").read_text(encoding="utf-8-sig"), conn)
bva = pd.read_sql_query(Path("sql/budget_vs_actual.sql").read_text(encoding="utf-8-sig"), conn)
scores = pd.read_sql_query("SELECT * FROM credit_scores", conn)
conn.close()

pnl["month"] = pd.to_datetime(pnl["month"])
bva["month"] = pd.to_datetime(bva["month"])

# Revenue: above budget is good. Costs: below budget is good.
is_rev = bva.category == "Revenue"
bva["status"] = np.where((is_rev & (bva.variance >= 0)) | (~is_rev & (bva.variance <= 0)),
                         "Favorable", "Unfavorable")

out = Path("reports/board_pack.xlsx")
with pd.ExcelWriter(out, engine="xlsxwriter", datetime_format="mmm-yy") as writer:
    wb = writer.book
    money = wb.add_format({"num_format": "#,##0"})
    pct = wb.add_format({"num_format": "0.0%"})
    pct1 = wb.add_format({"num_format": "0.0"})
    title = wb.add_format({"bold": True, "font_size": 16})
    bold = wb.add_format({"bold": True})
    hdr = wb.add_format({"bold": True, "bg_color": "#1F3864", "font_color": "white"})
    red = wb.add_format({"bg_color": "#F8CBAD"})
    green = wb.add_format({"bg_color": "#C6E0B4"})

    # ---- Summary (created first so it is the first tab) ----
    ws = wb.add_worksheet("Summary")
    rev, net = pnl.revenue.sum(), pnl.net_profit.sum()
    high = int((scores.risk_band == "High").sum())
    ws.write("A1", "Monthly Board Pack - Financial and Risk Summary", title)
    ws.write("A2", f"Period: {pnl.month.min():%b %Y} to {pnl.month.max():%b %Y} (amounts in INR)")
    kpis = [
        ("Total revenue", rev, money),
        ("Total net profit", net, money),
        ("Net profit margin", net / rev, pct),
        ("Latest month revenue", pnl.revenue.iloc[-1], money),
        ("Latest month net profit", pnl.net_profit.iloc[-1], money),
        ("Customers scored", len(scores), money),
        ("High-risk customers", high, money),
        ("Overall default rate", scores.defaulted.mean(), pct),
    ]
    for i, (label, value, fmt) in enumerate(kpis, start=4):
        ws.write(i, 0, label, bold)
        ws.write(i, 1, value, fmt)
    ws.set_column(0, 0, 28)
    ws.set_column(1, 1, 18)

    # ---- Monthly P&L with chart ----
    pnl.to_excel(writer, sheet_name="Monthly PnL", index=False)
    ws = writer.sheets["Monthly PnL"]
    ws.set_column(0, 0, 10)
    ws.set_column(1, 6, 16, money)
    ws.freeze_panes(1, 1)
    n = len(pnl)
    col = wb.add_chart({"type": "column"})
    col.add_series({"name": "Revenue",
                    "categories": ["Monthly PnL", 1, 0, n, 0],
                    "values": ["Monthly PnL", 1, 1, n, 1]})
    line = wb.add_chart({"type": "line"})
    line.add_series({"name": "Net profit",
                     "categories": ["Monthly PnL", 1, 0, n, 0],
                     "values": ["Monthly PnL", 1, 6, n, 6],
                     "y2_axis": True})
    col.combine(line)
    col.set_title({"name": "Revenue vs Net Profit"})
    col.set_size({"width": 760, "height": 380})
    ws.insert_chart("I2", col)

    # ---- Budget vs Actual ----
    bva.to_excel(writer, sheet_name="Budget vs Actual", index=False)
    ws = writer.sheets["Budget vs Actual"]
    last = len(bva)
    ws.set_column(0, 0, 10)
    ws.set_column(1, 2, 20)
    ws.set_column(3, 5, 14, money)
    ws.set_column(6, 6, 13, pct1)
    ws.set_column(7, 7, 13)
    ws.freeze_panes(1, 0)
    ws.autofilter(0, 0, last, 7)
    ws.conditional_format(1, 0, last, 7, {"type": "formula",
                          "criteria": '=$H2="Unfavorable"', "format": red})
    ws.conditional_format(1, 0, last, 7, {"type": "formula",
                          "criteria": '=$H2="Favorable"', "format": green})

    # ---- Credit Risk ----
    summ = (scores.groupby("risk_band")
            .agg(customers=("customer_id", "count"),
                 avg_default_probability=("default_probability", "mean"),
                 actual_default_rate=("defaulted", "mean"))
            .reindex(["Low", "Medium", "High"]).reset_index())
    top = (scores.sort_values("default_probability", ascending=False).head(20)
           [["customer_id", "name", "credit_score", "default_probability",
             "risk_band", "loan_amount"]])
    summ.to_excel(writer, sheet_name="Credit Risk", index=False, startrow=1)
    top.to_excel(writer, sheet_name="Credit Risk", index=False, startrow=8)
    ws = writer.sheets["Credit Risk"]
    ws.write(0, 0, "Risk band summary", title)
    ws.write(7, 0, "Top 20 highest-risk customers", title)
    ws.set_column(0, 0, 14)
    ws.set_column(1, 1, 26)
    ws.set_column(2, 5, 22)
    ws.conditional_format("C3:D5", {"type": "no_blanks", "format": pct})
    ws.conditional_format("D10:D29", {"type": "no_blanks", "format": pct})
    ws.conditional_format("F10:F29", {"type": "no_blanks", "format": money})

print("Board pack saved to", out.resolve())
