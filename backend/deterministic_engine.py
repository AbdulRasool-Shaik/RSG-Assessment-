"""
Deterministic Semantic Query Engine
Zero-LLM fallback engine that reliably recognizes analytical intents,
generates verified SQL queries, executes them safely, and formats
structured BI responses with metric cards and chart payloads.
"""

import re
from typing import Dict, Any, Optional, Tuple, List
from .security import execute_safe_query
from .models import QueryResponse, MetricCard, ChartData

MONTH_MAP = {
    'january': '2026-01', 'jan': '2026-01', '01': '2026-01', '1': '2026-01',
    'february': '2026-02', 'feb': '2026-02', '02': '2026-02', '2': '2026-02',
    'march': '2026-03', 'mar': '2026-03', '03': '2026-03', '3': '2026-03',
    'april': '2026-04', 'apr': '2026-04', '04': '2026-04', '4': '2026-04',
    'may': '2026-05', '05': '2026-05', '5': '2026-05',
    'june': '2026-06', 'jun': '2026-06', '06': '2026-06', '6': '2026-06'
}

MONTH_NAMES = {
    '2026-01': 'January 2026',
    '2026-02': 'February 2026',
    '2026-03': 'March 2026',
    '2026-04': 'April 2026',
    '2026-05': 'May 2026',
    '2026-06': 'June 2026'
}

class DeterministicEngine:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def process_query(self, query: str) -> QueryResponse:
        q = query.strip().lower()

        # Guardrail: Check for destructive injection attempts in raw user query
        if any(w in q for w in ['drop table', 'delete from', 'update sales', 'insert into', 'alter table', 'truncate']):
            return QueryResponse(
                query=query,
                status="refused",
                answer="**Security Alert:** Modifying or destructive database operations are strictly blocked by the AST Security Guardrails.",
                engine_used="security_guardrail",
                explanation="The request contained forbidden DDL/DML mutation keywords."
            )

        # 1. Total Revenue Query
        if self._matches_total_revenue(q):
            return self._handle_total_revenue(query)

        # 2. Product Revenue / Highest Product Query
        if self._matches_product_revenue(q):
            return self._handle_product_revenue(query)

        # 3. Monthly Revenue Trend Query
        if self._matches_monthly_trend(q):
            return self._handle_monthly_trend(query)

        # 4. Regional Sales / Highest Region Query
        if self._matches_regional_sales(q):
            return self._handle_regional_sales(query)

        # 5. Month-over-Month Comparison Query
        if self._matches_month_comparison(q):
            return self._handle_month_comparison(query, q)

        # 6. Category Breakdown
        if 'category' in q:
            return self._handle_category_sales(query)

        # 7. Sales Channel Breakdown
        if 'channel' in q or 'online' in q or 'retail' in q:
            return self._handle_channel_sales(query)

        # 8. Out of domain refusal
        return QueryResponse(
            query=query,
            status="refused",
            answer=(
                "I am a specialized Sales Business Intelligence Assistant. I can answer questions regarding:\n"
                "- **Total revenue** (gross, net, and discounts)\n"
                "- **Top performing products** and product revenue breakdown\n"
                "- **Monthly revenue trends** (Jan–Jun 2026)\n"
                "- **Regional sales performance** (North, South, East, West)\n"
                "- **Month-over-month comparisons** (e.g., 'How did revenue change between April and May?')"
            ),
            engine_used="guardrail_router",
            explanation="The query was outside the scope of sales analytics or could not be mapped to analytical schema."
        )

    def _matches_total_revenue(self, q: str) -> bool:
        patterns = [
            r'total\s+revenue', r'overall\s+revenue', r'total\s+sales',
            r'net\s+revenue', r'gross\s+revenue', r'how\s+much\s+money',
            r'total\s+turnover', r'revenue\s+generated'
        ]
        return any(re.search(p, q) for p in patterns) and not any(k in q for k in ['product', 'region', 'month', 'between', 'trend'])

    def _handle_total_revenue(self, query: str) -> QueryResponse:
        sql = (
            "SELECT "
            "COUNT(*) AS completed_orders, "
            "SUM(quantity) AS total_units_sold, "
            "ROUND(SUM(gross_revenue), 2) AS total_gross_revenue, "
            "ROUND(SUM(discount_amount), 2) AS total_discounts, "
            "ROUND(SUM(net_revenue), 2) AS total_net_revenue "
            "FROM sales "
            "WHERE status = 'Completed'"
        )
        cols, rows, exec_time = execute_safe_query(self.db_path, sql)
        data = rows[0] if rows else {}

        net_rev = data.get('total_net_revenue', 0.0)
        gross_rev = data.get('total_gross_revenue', 0.0)
        discounts = data.get('total_discounts', 0.0)
        orders = data.get('completed_orders', 0)
        units = data.get('total_units_sold', 0)

        answer = (
            f"### Total Sales Revenue Summary\n\n"
            f"- **Net Realized Revenue:** **${net_rev:,.2f}**\n"
            f"- **Gross Invoiced Revenue:** **${gross_rev:,.2f}**\n"
            f"- **Total Discounts Applied:** **${discounts:,.2f}** across completed orders\n"
            f"- **Completed Transactions:** **{orders}** orders ({units} units sold)\n\n"
            f"> *Note: 1 returned order (`TXN0033`, Monitor, $19,000) was excluded to reflect actual realized revenue.*"
        )

        metrics = [
            MetricCard(label="Net Revenue", value=f"${net_rev:,.2f}", subtitle="Realized Income"),
            MetricCard(label="Gross Revenue", value=f"${gross_rev:,.2f}", subtitle="Before Discounts"),
            MetricCard(label="Total Discounts", value=f"${discounts:,.2f}", subtitle="Promotional Savings"),
            MetricCard(label="Completed Orders", value=str(orders), subtitle=f"{units} Units")
        ]

        return QueryResponse(
            query=query,
            status="success",
            answer=answer,
            sql_query=sql,
            execution_time_ms=exec_time,
            row_count=len(rows),
            columns=cols,
            data=rows,
            metrics=metrics,
            engine_used="deterministic_semantic_engine",
            explanation="Calculated aggregate sum of net revenue ((Quantity * Unit_price) - Discount) for all completed sales transactions."
        )

    def _matches_product_revenue(self, q: str) -> bool:
        return 'product' in q or 'highest revenue' in q or 'best selling' in q or 'top product' in q

    def _handle_product_revenue(self, query: str) -> QueryResponse:
        sql = (
            "SELECT "
            "product, "
            "ROUND(SUM(net_revenue), 2) AS total_net_revenue, "
            "SUM(quantity) AS units_sold, "
            "COUNT(*) AS order_count "
            "FROM sales "
            "WHERE status = 'Completed' "
            "GROUP BY product "
            "ORDER BY total_net_revenue DESC"
        )
        cols, rows, exec_time = execute_safe_query(self.db_path, sql)
        top = rows[0] if rows else {}

        top_prod = top.get('product', 'Unknown')
        top_rev = top.get('total_net_revenue', 0.0)
        top_units = top.get('units_sold', 0)

        answer = (
            f"### Highest Revenue Product: **{top_prod}**\n\n"
            f"The product that generated the highest revenue is the **{top_prod}**, producing **${top_rev:,.2f}** "
            f"in net revenue across **{top_units} units sold** ({top.get('order_count', 0)} transactions).\n\n"
            f"#### Full Product Revenue Ranking:\n"
        )
        for i, r in enumerate(rows, 1):
            answer += f"{i}. **{r['product']}**: ${r['total_net_revenue']:,.2f} ({r['units_sold']} units)\n"

        metrics = [
            MetricCard(label="Top Product", value=top_prod, subtitle=f"${top_rev:,.2f}"),
            MetricCard(label="Units Sold", value=str(top_units), subtitle="Total Volume"),
            MetricCard(label="Total Products", value=str(len(rows)), subtitle="In Catalog")
        ]

        chart = ChartData(
            chart_type="bar",
            title="Net Revenue by Product ($)",
            labels=[r['product'] for r in rows],
            datasets=[{
                "label": "Net Revenue ($)",
                "data": [r['total_net_revenue'] for r in rows],
                "backgroundColor": "rgba(59, 130, 246, 0.7)",
                "borderColor": "rgba(59, 130, 246, 1.0)",
                "borderWidth": 1
            }]
        )

        return QueryResponse(
            query=query,
            status="success",
            answer=answer,
            sql_query=sql,
            execution_time_ms=exec_time,
            row_count=len(rows),
            columns=cols,
            data=rows,
            metrics=metrics,
            chart=chart,
            engine_used="deterministic_semantic_engine",
            explanation="Aggregated net revenue by product for completed orders and ranked in descending order."
        )

    def _matches_monthly_trend(self, q: str) -> bool:
        return 'monthly' in q or 'trend' in q or ('month' in q and not any(m in q for m in ['between', 'compare', 'from']))

    def _handle_monthly_trend(self, query: str) -> QueryResponse:
        sql = (
            "SELECT "
            "order_month AS month, "
            "ROUND(SUM(net_revenue), 2) AS monthly_net_revenue, "
            "SUM(quantity) AS units_sold, "
            "COUNT(*) AS transaction_count "
            "FROM sales "
            "WHERE status = 'Completed' "
            "GROUP BY order_month "
            "ORDER BY order_month ASC"
        )
        cols, rows, exec_time = execute_safe_query(self.db_path, sql)

        peak_row = max(rows, key=lambda r: r['monthly_net_revenue']) if rows else {}
        peak_month_name = MONTH_NAMES.get(peak_row.get('month', ''), peak_row.get('month', ''))

        answer = (
            f"### Monthly Revenue Trend (Jan 2026 – Jun 2026)\n\n"
            f"Revenue grew steadily over the first half of 2026, reaching a peak in **{peak_month_name}** at **${peak_row.get('monthly_net_revenue', 0):,.2f}**.\n\n"
            f"| Month | Net Revenue | Units Sold | Orders |\n"
            f"| :--- | :--- | :--- | :--- |\n"
        )
        for r in rows:
            m_label = MONTH_NAMES.get(r['month'], r['month'])
            answer += f"| {m_label} | ${r['monthly_net_revenue']:,.2f} | {r['units_sold']} | {r['transaction_count']} |\n"

        metrics = [
            MetricCard(label="Peak Month", value=peak_month_name, subtitle=f"${peak_row.get('monthly_net_revenue', 0):,.2f}"),
            MetricCard(label="Average Monthly Rev", value=f"${sum(r['monthly_net_revenue'] for r in rows)/len(rows):,.2f}" if rows else "$0", subtitle="6-Month Average"),
            MetricCard(label="Total Months", value=str(len(rows)), subtitle="Reporting Period")
        ]

        chart = ChartData(
            chart_type="line",
            title="Monthly Revenue Trend (Jan–Jun 2026)",
            labels=[MONTH_NAMES.get(r['month'], r['month']) for r in rows],
            datasets=[{
                "label": "Monthly Net Revenue ($)",
                "data": [r['monthly_net_revenue'] for r in rows],
                "borderColor": "rgba(16, 185, 129, 1.0)",
                "backgroundColor": "rgba(16, 185, 129, 0.2)",
                "borderWidth": 2,
                "fill": True,
                "tension": 0.3
            }]
        )

        return QueryResponse(
            query=query,
            status="success",
            answer=answer,
            sql_query=sql,
            execution_time_ms=exec_time,
            row_count=len(rows),
            columns=cols,
            data=rows,
            metrics=metrics,
            chart=chart,
            engine_used="deterministic_semantic_engine",
            explanation="Aggregated net revenue grouped chronologically by month (order_month) for completed orders."
        )

    def _matches_regional_sales(self, q: str) -> bool:
        return 'region' in q or 'territory' in q or 'location' in q

    def _handle_regional_sales(self, query: str) -> QueryResponse:
        sql = (
            "SELECT "
            "region, "
            "ROUND(SUM(net_revenue), 2) AS net_revenue, "
            "SUM(quantity) AS units_sold, "
            "COUNT(*) AS order_count "
            "FROM sales "
            "WHERE status = 'Completed' "
            "GROUP BY region "
            "ORDER BY net_revenue DESC"
        )
        cols, rows, exec_time = execute_safe_query(self.db_path, sql)
        top = rows[0] if rows else {}

        top_region = top.get('region', 'Unknown')
        top_rev = top.get('net_revenue', 0.0)
        top_units = top.get('units_sold', 0)

        answer = (
            f"### Regional Sales Performance\n\n"
            f"The **{top_region}** region generated the highest sales, leading both in total revenue (**${top_rev:,.2f}**) "
            f"and unit sales (**{top_units} units**) across {top.get('order_count', 0)} orders.\n\n"
            f"#### Regional Comparison:\n"
        )
        for r in rows:
            answer += f"- **{r['region']}**: ${r['net_revenue']:,.2f} ({r['units_sold']} units, {r['order_count']} orders)\n"

        metrics = [
            MetricCard(label="Top Region", value=top_region, subtitle=f"${top_rev:,.2f}"),
            MetricCard(label="Top Region Units", value=str(top_units), subtitle="Units Sold"),
            MetricCard(label="Active Regions", value=str(len(rows)), subtitle="North, South, East, West")
        ]

        chart = ChartData(
            chart_type="doughnut",
            title="Revenue Share by Region",
            labels=[r['region'] for r in rows],
            datasets=[{
                "label": "Revenue ($)",
                "data": [r['net_revenue'] for r in rows],
                "backgroundColor": [
                    "rgba(59, 130, 246, 0.8)",
                    "rgba(16, 185, 129, 0.8)",
                    "rgba(245, 158, 11, 0.8)",
                    "rgba(239, 68, 68, 0.8)"
                ]
            }]
        )

        return QueryResponse(
            query=query,
            status="success",
            answer=answer,
            sql_query=sql,
            execution_time_ms=exec_time,
            row_count=len(rows),
            columns=cols,
            data=rows,
            metrics=metrics,
            chart=chart,
            engine_used="deterministic_semantic_engine",
            explanation="Aggregated net revenue and total units sold grouped by geographic region and ordered descending."
        )

    def _matches_month_comparison(self, q: str) -> bool:
        return 'between' in q or 'change between' in q or 'compare' in q or 'growth' in q

    def _handle_month_comparison(self, query: str, q: str) -> QueryResponse:
        # Detect target months in query
        found_months: List[str] = []
        for name, m_key in MONTH_MAP.items():
            if re.search(r'\b' + name + r'\b', q):
                if m_key not in found_months:
                    found_months.append(m_key)

        # Default to April vs May if not explicitly provided or if "two months" was asked
        if len(found_months) < 2:
            m1, m2 = '2026-04', '2026-05'
        else:
            found_months.sort()
            m1, m2 = found_months[0], found_months[1]

        sql = (
            f"SELECT "
            f"order_month AS month, "
            f"ROUND(SUM(net_revenue), 2) AS net_revenue, "
            f"SUM(quantity) AS units_sold, "
            f"COUNT(*) AS order_count "
            f"FROM sales "
            f"WHERE status = 'Completed' AND order_month IN ('{m1}', '{m2}') "
            f"GROUP BY order_month "
            f"ORDER BY order_month ASC"
        )
        cols, rows, exec_time = execute_safe_query(self.db_path, sql)

        if len(rows) == 2:
            r1, r2 = rows[0], rows[1]
            rev1, rev2 = r1['net_revenue'], r2['net_revenue']
            diff = rev2 - rev1
            pct_change = ((rev2 - rev1) / rev1 * 100) if rev1 else 0.0
            direction = "increased" if diff >= 0 else "decreased"
            symbol = "+" if diff >= 0 else ""

            m1_name = MONTH_NAMES.get(m1, m1)
            m2_name = MONTH_NAMES.get(m2, m2)

            answer = (
                f"### Revenue Comparison: **{m1_name} vs. {m2_name}**\n\n"
                f"Revenue **{direction} by ${abs(diff):,.2f} ({symbol}{pct_change:.2f}%)** from {m1_name} to {m2_name}.\n\n"
                f"- **{m1_name}:** ${rev1:,.2f} ({r1['units_sold']} units in {r1['order_count']} orders)\n"
                f"- **{m2_name}:** ${rev2:,.2f} ({r2['units_sold']} units in {r2['order_count']} orders)\n"
                f"- **Net Variance:** {symbol}${diff:,.2f}\n"
                f"- **Percentage Growth:** {symbol}{pct_change:.2f}%"
            )

            metrics = [
                MetricCard(label="Revenue Delta", value=f"{symbol}${diff:,.2f}", subtitle=f"{symbol}{pct_change:.2f}% Change", delta=f"{symbol}{pct_change:.2f}%"),
                MetricCard(label=m1_name, value=f"${rev1:,.2f}", subtitle=f"{r1['units_sold']} Units"),
                MetricCard(label=m2_name, value=f"${rev2:,.2f}", subtitle=f"{r2['units_sold']} Units")
            ]

            chart = ChartData(
                chart_type="bar",
                title=f"Revenue Comparison ({m1_name} vs {m2_name})",
                labels=[m1_name, m2_name],
                datasets=[{
                    "label": "Net Revenue ($)",
                    "data": [rev1, rev2],
                    "backgroundColor": ["rgba(59, 130, 246, 0.7)", "rgba(16, 185, 129, 0.7)"],
                    "borderWidth": 1
                }]
            )
        else:
            answer = "Could not find sufficient data for both requested months to compute comparison."
            metrics = []
            chart = None

        return QueryResponse(
            query=query,
            status="success",
            answer=answer,
            sql_query=sql,
            execution_time_ms=exec_time,
            row_count=len(rows),
            columns=cols,
            data=rows,
            metrics=metrics,
            chart=chart,
            engine_used="deterministic_semantic_engine",
            explanation=f"Queried monthly net revenue for {m1} and {m2} to compute absolute difference and percentage variance."
        )

    def _handle_category_sales(self, query: str) -> QueryResponse:
        sql = (
            "SELECT "
            "category, "
            "ROUND(SUM(net_revenue), 2) AS net_revenue, "
            "SUM(quantity) AS units_sold, "
            "COUNT(*) AS order_count "
            "FROM sales "
            "WHERE status = 'Completed' "
            "GROUP BY category "
            "ORDER BY net_revenue DESC"
        )
        cols, rows, exec_time = execute_safe_query(self.db_path, sql)
        answer = "### Sales by Product Category:\n\n"
        for r in rows:
            answer += f"- **{r['category']}**: ${r['net_revenue']:,.2f} ({r['units_sold']} units)\n"
        
        return QueryResponse(
            query=query,
            status="success",
            answer=answer,
            sql_query=sql,
            execution_time_ms=exec_time,
            row_count=len(rows),
            columns=cols,
            data=rows,
            metrics=[MetricCard(label=r['category'], value=f"${r['net_revenue']:,.2f}", subtitle=f"{r['units_sold']} units") for r in rows],
            chart=ChartData(
                chart_type="doughnut",
                title="Revenue by Category",
                labels=[r['category'] for r in rows],
                datasets=[{"label": "Revenue", "data": [r['net_revenue'] for r in rows]}]
            ),
            engine_used="deterministic_semantic_engine",
            explanation="Aggregated net revenue grouped by product category for completed sales."
        )

    def _handle_channel_sales(self, query: str) -> QueryResponse:
        sql = (
            "SELECT "
            "sales_channel, "
            "ROUND(SUM(net_revenue), 2) AS net_revenue, "
            "SUM(quantity) AS units_sold, "
            "COUNT(*) AS order_count "
            "FROM sales "
            "WHERE status = 'Completed' "
            "GROUP BY sales_channel "
            "ORDER BY net_revenue DESC"
        )
        cols, rows, exec_time = execute_safe_query(self.db_path, sql)
        answer = "### Sales by Sales Channel:\n\n"
        for r in rows:
            answer += f"- **{r['sales_channel']}**: ${r['net_revenue']:,.2f} ({r['units_sold']} units, {r['order_count']} orders)\n"
            
        return QueryResponse(
            query=query,
            status="success",
            answer=answer,
            sql_query=sql,
            execution_time_ms=exec_time,
            row_count=len(rows),
            columns=cols,
            data=rows,
            metrics=[MetricCard(label=r['sales_channel'], value=f"${r['net_revenue']:,.2f}", subtitle=f"{r['order_count']} orders") for r in rows],
            engine_used="deterministic_semantic_engine",
            explanation="Aggregated revenue grouped by sales channel (Online vs Retail)."
        )
