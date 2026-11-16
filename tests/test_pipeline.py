"""Validation tests for the DA-04 pipeline. Run: python -m pytest tests -v"""
import sqlite3
from datetime import date

import pandas as pd
import pytest

DB = "data/processed/finance.db"


@pytest.fixture(scope="module")
def conn():
    c = sqlite3.connect(DB)
    yield c
    c.close()


def test_row_counts(conn):
    counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ["chart_of_accounts", "transactions", "budgets", "customers", "loans"]}
    assert counts == {"chart_of_accounts": 9, "transactions": 1080, "budgets": 1080,
                      "customers": 1000, "loans": 1000}


def test_pnl_reconciles(conn):
    """Revenue - COGS - Opex - Interest must equal net profit every month."""
    from pathlib import Path
    pnl = pd.read_sql_query(Path("sql/pnl.sql").read_text(encoding="utf-8-sig"), conn)
    calc = pnl.revenue - pnl.cogs - pnl.opex - pnl.interest
    assert (calc - pnl.net_profit).abs().max() < 0.01


def test_no_future_months(conn):
    """Actuals must not extend past the current month."""
    last = pd.read_sql_query("SELECT MAX(month) AS m FROM transactions", conn).m[0]
    assert pd.Timestamp(last) <= pd.Timestamp(date.today().replace(day=1))


def test_budget_and_actual_align(conn):
    """Every budget line has a matching actual line."""
    missing = conn.execute("""SELECT COUNT(*) FROM budgets b LEFT JOIN transactions t
        ON t.month=b.month AND t.account_id=b.account_id AND t.department=b.department
        WHERE t.amount IS NULL""").fetchone()[0]
    assert missing == 0


def test_risk_bands_ordered(conn):
    """Actual default rate must rise from Low to Medium to High."""
    rates = pd.read_sql_query(
        "SELECT risk_band, AVG(defaulted) AS r FROM credit_scores GROUP BY risk_band", conn
    ).set_index("risk_band").r
    assert rates["Low"] < rates["Medium"] < rates["High"]


def test_scores_valid(conn):
    s = pd.read_sql_query("SELECT default_probability, credit_score FROM credit_scores", conn)
    assert s.default_probability.between(0, 1).all()
    assert s.credit_score.between(300, 850).all()
