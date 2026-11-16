"""Train a credit risk model and score every customer."""
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

conn = sqlite3.connect("data/processed/finance.db")
df = pd.read_sql_query(
    """SELECT c.customer_id, c.name, c.age, c.annual_income, c.employment_years,
              l.loan_amount, l.credit_utilization, l.late_payments,
              l.existing_debt_ratio, l.defaulted
       FROM customers c JOIN loans l ON l.customer_id = c.customer_id""", conn)

df["loan_to_income"] = df.loan_amount / df.annual_income
features = ["credit_utilization", "late_payments", "existing_debt_ratio",
            "loan_to_income", "employment_years", "age"]

X_train, X_test, y_train, y_test = train_test_split(
    df[features], df.defaulted, test_size=0.25, random_state=42, stratify=df.defaulted)

model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
model.fit(X_train, y_train)

proba_test = model.predict_proba(X_test)[:, 1]
print(f"ROC AUC on test set: {roc_auc_score(y_test, proba_test):.3f}")
print(classification_report(y_test, (proba_test > 0.5).astype(int), zero_division=0))

# Score everyone
df["default_probability"] = model.predict_proba(df[features])[:, 1].round(4)
df["credit_score"] = (850 - df.default_probability * 550).round(0).astype(int)
df["risk_band"] = pd.cut(df.default_probability, bins=[-0.01, 0.10, 0.25, 1.0],
                         labels=["Low", "Medium", "High"])

df.to_sql("credit_scores", conn, if_exists="replace", index=False)
df.to_csv(Path("reports") / "credit_scores.csv", index=False)
print("\nRisk band counts:")
print(df.risk_band.value_counts().to_string())
conn.close()
