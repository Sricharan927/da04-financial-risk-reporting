-- Monthly Profit & Loss (actuals), amounts in INR
SELECT
    t.month,
    SUM(CASE WHEN a.category = 'Revenue' THEN t.amount ELSE 0 END) AS revenue,
    SUM(CASE WHEN a.category = 'COGS'    THEN t.amount ELSE 0 END) AS cogs,
    SUM(CASE WHEN a.category = 'Revenue' THEN t.amount ELSE 0 END)
      - SUM(CASE WHEN a.category = 'COGS' THEN t.amount ELSE 0 END) AS gross_profit,
    SUM(CASE WHEN a.category = 'Opex'    THEN t.amount ELSE 0 END) AS opex,
    SUM(CASE WHEN a.category = 'Other'   THEN t.amount ELSE 0 END) AS interest,
    SUM(CASE WHEN a.category = 'Revenue' THEN t.amount ELSE -t.amount END) AS net_profit
FROM transactions t
JOIN chart_of_accounts a ON a.account_id = t.account_id
GROUP BY t.month
ORDER BY t.month;
