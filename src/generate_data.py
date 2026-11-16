import numpy as np
import pandas as pd
from faker import Faker
from pathlib import Path

SEED = 42
rng = np.random.default_rng(SEED)
fake = Faker("en_IN")
Faker.seed(SEED)

OUT = Path("data/raw")
OUT.mkdir(parents=True, exist_ok=True)

# ---------- 1. Chart of accounts ----------
accounts = pd.DataFrame([
    (4000, "Product Sales",        "Revenue"),
    (4100, "Service Revenue",      "Revenue"),
    (5000, "Cost of Goods Sold",   "COGS"),
    (6000, "Salaries",             "Opex"),
    (6100, "Marketing",            "Opex"),
    (6200, "Rent and Utilities",   "Opex"),
    (6300, "Software and IT",      "Opex"),
    (6400, "Travel",               "Opex"),
    (7000, "Interest Expense",     "Other"),
], columns=["account_id", "account_name", "category"])

departments = ["Sales", "Operations", "Marketing", "IT", "Finance"]
months = pd.date_range("2024-11-01", periods=24, freq="MS")

# Base monthly amount per account (in INR)
base = {4000: 9_000_000, 4100: 3_000_000, 5000: 5_500_000, 6000: 2_800_000,
        6100: 700_000, 6200: 450_000, 6300: 350_000, 6400: 150_000, 7000: 120_000}

# ---------- 2. Budgets and actuals ----------
rows = []
for i, m in enumerate(months):
    growth = 1 + 0.012 * i                                  # steady growth
    season = 1 + 0.10 * np.sin(2 * np.pi * (m.month - 1) / 12)  # seasonality
    for _, acc in accounts.iterrows():
        for dept in departments:
            share = 1 / len(departments)
            budget = base[acc.account_id] * growth * share
            noise = rng.normal(1.0, 0.07)                   # actual vs budget variance
            if acc.category in ("Revenue", "COGS"):
                actual = budget * season * noise
            else:
                actual = budget * noise
            rows.append((m, acc.account_id, dept, round(budget, 2), round(actual, 2)))

fin = pd.DataFrame(rows, columns=["month", "account_id", "department", "budget", "actual"])
fin[["month", "account_id", "department", "budget"]].to_csv(OUT / "budgets.csv", index=False)
fin[["month", "account_id", "department", "actual"]].rename(
    columns={"actual": "amount"}).to_csv(OUT / "transactions.csv", index=False)
accounts.to_csv(OUT / "chart_of_accounts.csv", index=False)

# ---------- 3. Customers and loans (credit risk) ----------
n_customers = 1000
customers = pd.DataFrame({
    "customer_id": range(1, n_customers + 1),
    "name": [fake.name() for _ in range(n_customers)],
    "age": rng.integers(21, 70, n_customers),
    "annual_income": rng.lognormal(13.2, 0.5, n_customers).round(0),
    "employment_years": rng.integers(0, 30, n_customers),
})

loan_amount = (customers.annual_income * rng.uniform(0.3, 2.5, n_customers)).round(0)
credit_utilization = rng.beta(2, 3, n_customers).round(3)       # 0 to 1
late_payments = rng.poisson(1.2, n_customers)
existing_debt_ratio = rng.beta(2, 4, n_customers).round(3)

# Default probability is driven by the risk factors, so a model can learn it
logit = (-4.8
         + 2.0 * credit_utilization
         + 0.45 * late_payments
         + 2.5 * existing_debt_ratio
         + 0.8 * (loan_amount / customers.annual_income)
         - 0.03 * customers.employment_years)
p_default = 1 / (1 + np.exp(-logit))
defaulted = rng.binomial(1, p_default)

loans = pd.DataFrame({
    "loan_id": range(1, n_customers + 1),
    "customer_id": customers.customer_id,
    "loan_amount": loan_amount,
    "credit_utilization": credit_utilization,
    "late_payments": late_payments,
    "existing_debt_ratio": existing_debt_ratio,
    "defaulted": defaulted,
})

customers.to_csv(OUT / "customers.csv", index=False)
loans.to_csv(OUT / "loans.csv", index=False)

print("Done. Files written to", OUT.resolve())
print(f"Financial rows: {len(fin)} | Customers: {len(customers)} | Default rate: {defaulted.mean():.1%}")