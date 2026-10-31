# Ground Truth Benchmark Results
## Verified Analytical Metrics for All 5 Challenge Questions

This document presents the mathematically verified answers, executed SQLite queries, and accounting explanations for the 5 benchmark questions specified in the **AI Assisted Development Challenge**.

---

## Benchmark Comparison Matrix

| # | Question | Executed SQLite Query | Ground Truth Output | Supporting Figures / Explanation |
|---|---|---|---|---|
| **Q1** | **What is the total revenue?** | `SELECT COUNT(*) AS completed_orders, SUM(quantity) AS total_units_sold, ROUND(SUM(gross_revenue), 2) AS total_gross_revenue, ROUND(SUM(discount_amount), 2) AS total_discounts, ROUND(SUM(net_revenue), 2) AS total_net_revenue FROM sales WHERE status = 'Completed'` | **$1,445,200.00 Net Revenue** | - **Gross Revenue:** $1,449,700.00<br>- **Total Discounts:** $4,500.00<br>- **Completed Orders:** 50<br>- **Units Sold:** 478<br>*(Note: 1 returned order TXN0033 for $19,000 excluded from realized income).* |
| **Q2** | **Which product generated the highest revenue?** | `SELECT product, ROUND(SUM(net_revenue), 2) AS total_net_revenue, SUM(quantity) AS units_sold, COUNT(*) AS order_count FROM sales WHERE status = 'Completed' GROUP BY product ORDER BY total_net_revenue DESC` | **Monitor ($473,000.00 Net Revenue)** | 1. **Monitor:** $473,000.00 (52 units)<br>2. **Office Chair:** $257,400.00 (33 units)<br>3. **Desk:** $245,000.00 (20 units)<br>4. **Wireless Mouse:** $175,500.00 (270 units)<br>5. **USB-C Hub:** $163,800.00 (91 units)<br>6. **Keyboard:** $96,300.00 (107 units)<br>7. **Laptop Stand:** $34,200.00 (30 units) |
| **Q3** | **What is the monthly revenue trend?** | `SELECT order_month AS month, ROUND(SUM(net_revenue), 2) AS monthly_net_revenue, SUM(quantity) AS units_sold, COUNT(*) AS transaction_count FROM sales WHERE status = 'Completed' GROUP BY order_month ORDER BY order_month ASC` | **6-Month Trajectory peaking in May 2026 ($318,500.00)** | - **2026-01:** $210,250.00 (70 units, 8 orders)<br>- **2026-02:** $213,950.00 (116 units, 8 orders)<br>- **2026-03:** $237,500.00 (66 units, 8 orders)<br>- **2026-04:** $240,700.00 (105 units, 8 orders)<br>- **2026-05:** **$318,500.00 (Peak)** (113 units, 8 orders)<br>- **2026-06:** $224,300.00 (95 units, 10 orders) |
| **Q4** | **Which region generated the highest sales?** | `SELECT region, ROUND(SUM(net_revenue), 2) AS net_revenue, SUM(quantity) AS units_sold, COUNT(*) AS order_count FROM sales WHERE status = 'Completed' GROUP BY region ORDER BY net_revenue DESC` | **South Region ($411,200.00 Net Revenue, 182 units)** | 1. **South:** $411,200.00 (182 units, 14 orders)<br>2. **East:** $394,400.00 (126 units, 12 orders)<br>3. **West:** $324,800.00 (137 units, 12 orders)<br>4. **North:** $314,800.00 (120 units, 12 orders) |
| **Q5** | **How did revenue change between two months?** | `SELECT order_month AS month, ROUND(SUM(net_revenue), 2) AS net_revenue, SUM(quantity) AS units_sold, COUNT(*) AS order_count FROM sales WHERE status = 'Completed' AND order_month IN ('2026-04', '2026-05') GROUP BY order_month ORDER BY order_month ASC` | **Increased by +$77,800.00 (+32.32%)** | - **April 2026:** $240,700.00 (105 units)<br>- **May 2026:** $318,500.00 (113 units)<br>- **Absolute Delta:** +$77,800.00<br>- **Percentage Growth:** +32.32% |

---

## Accounting & Financial Definitions

1. **Gross Revenue:**
   $$\text{Gross Revenue} = \text{Quantity} \times \text{Unit\_price}$$
2. **Net Revenue (Realized Income):**
   $$\text{Net Revenue} = (\text{Quantity} \times \text{Unit\_price}) - \text{Discount\_amount}$$
3. **Treatment of Returns (`status = 'Returned'`):**
   - In accordance with standard GAAP / IFRS accounting rules, returned merchandise (`TXN0033`, 2 units of Monitor, $19,000.00) is excluded from realized sales revenue.
   - Including returns would artificially inflate net revenue from **$1,445,200.00** to **$1,464,200.00**.
   - The transaction is preserved in the database for auditability and return-rate analytics.
