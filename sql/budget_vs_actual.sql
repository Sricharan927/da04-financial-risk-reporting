-- Budget vs actual by account and month
-- Revenue: positive variance = good. Costs: positive variance = overspend.
SELECT
    b.month,
    a.category,
    a.account_name,
    ROUND(SUM(b.budget), 0) AS budget,
    ROUND(SUM(t.amount), 0) AS actual,
    ROUND(SUM(t.amount) - SUM(b.budget), 0) AS variance,
    ROUND(100.0 * (SUM(t.amount) - SUM(b.budget)) / SUM(b.budget), 1) AS variance_pct
FROM budgets b
JOIN transactions t
  ON t.month = b.month AND t.account_id = b.account_id AND t.department = b.department
JOIN chart_of_accounts a ON a.account_id = b.account_id
GROUP BY b.month, a.category, a.account_name
ORDER BY b.month, a.category, a.account_name;
