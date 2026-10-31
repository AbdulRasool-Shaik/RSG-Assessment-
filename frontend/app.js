// Frontend Application Logic for Sales BI Assistant
let currentChart = null;

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('query-form');
    const input = document.getElementById('query-input');
    const submitBtn = document.getElementById('submit-btn');
    const spinner = document.getElementById('loading-spinner');
    const btnText = submitBtn.querySelector('.btn-text');
    const chips = document.querySelectorAll('.chip');
    const resultsSection = document.getElementById('results-section');
    const inspectorToggle = document.getElementById('inspector-toggle');
    const inspectorContent = document.getElementById('inspector-content');
    const inspectorIcon = document.getElementById('inspector-icon');
    const copySqlBtn = document.getElementById('copy-sql-btn');
    const healthBtn = document.getElementById('health-btn');
    const healthModal = document.getElementById('health-modal');
    const modalCloseBtn = document.getElementById('modal-close-btn');
    const modalCloseOverlay = document.getElementById('modal-close-overlay');

    // Handle Form Submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = input.value.trim();
        if (!query) return;
        await executeQuery(query);
    });

    // Handle Suggestion Chips
    chips.forEach(chip => {
        chip.addEventListener('click', async () => {
            const query = chip.getAttribute('data-query');
            input.value = query;
            await executeQuery(query);
        });
    });

    // Toggle SQL Inspector
    inspectorToggle.addEventListener('click', () => {
        inspectorContent.classList.toggle('hidden');
        inspectorIcon.classList.toggle('open');
    });

    // Copy SQL Button
    copySqlBtn.addEventListener('click', () => {
        const sqlText = document.getElementById('sql-code').textContent;
        navigator.clipboard.writeText(sqlText).then(() => {
            copySqlBtn.textContent = 'Copied!';
            setTimeout(() => { copySqlBtn.textContent = 'Copy SQL'; }, 2000);
        });
    });

    // Data Health Modal
    healthBtn.addEventListener('click', openHealthModal);
    modalCloseBtn.addEventListener('click', () => healthModal.classList.add('hidden'));
    modalCloseOverlay.addEventListener('click', () => healthModal.classList.add('hidden'));

    async function executeQuery(query) {
        setLoading(true);
        resultsSection.classList.add('hidden');

        try {
            const res = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, use_llm: true })
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `Server returned error ${res.status}`);
            }

            const data = await res.json();
            renderResults(data);
            resultsSection.classList.remove('hidden');
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            setLoading(false);
        }
    }

    function renderResults(data) {
        // Engine badge
        const badge = document.getElementById('engine-badge');
        badge.textContent = data.engine_used.replace(/_/g, ' ').toUpperCase();
        if (data.status === 'refused') {
            badge.style.background = 'rgba(239, 68, 68, 0.2)';
            badge.style.borderColor = 'rgba(239, 68, 68, 0.4)';
            badge.style.color = '#fca5a5';
        } else {
            badge.style.background = 'rgba(59, 130, 246, 0.15)';
            badge.style.borderColor = 'rgba(59, 130, 246, 0.3)';
            badge.style.color = '#93c5fd';
        }

        // Meta info
        document.getElementById('exec-time').textContent = `${data.execution_time_ms} ms`;
        document.getElementById('row-count').textContent = `${data.row_count} rows`;

        // Answer
        document.getElementById('answer-content').innerHTML = parseSimpleMarkdown(data.answer);

        // Metrics Grid
        const metricsGrid = document.getElementById('metrics-grid');
        if (data.metrics && data.metrics.length > 0) {
            metricsGrid.innerHTML = data.metrics.map(m => `
                <div class="metric-card">
                    <div class="metric-label">${escapeHtml(m.label)}</div>
                    <div class="metric-value">${escapeHtml(m.value)}</div>
                    ${m.subtitle ? `<div class="metric-subtitle">${escapeHtml(m.subtitle)}</div>` : ''}
                </div>
            `).join('');
            metricsGrid.classList.remove('hidden');
        } else {
            metricsGrid.classList.add('hidden');
        }

        // Chart
        const chartCard = document.getElementById('chart-card');
        if (data.chart && data.chart.labels && data.chart.labels.length > 0) {
            renderChart(data.chart);
            chartCard.classList.remove('hidden');
        } else {
            chartCard.classList.add('hidden');
            if (currentChart) {
                currentChart.destroy();
                currentChart = null;
            }
        }

        // SQL Inspector
        document.getElementById('sql-code').textContent = data.sql_query || '-- No SQL query executed (Refused or Handled by Guardrail)';
        document.getElementById('explanation-box').innerHTML = `<strong>Execution Logic:</strong> ${escapeHtml(data.explanation || 'Processed deterministically.')}`;

        // Table
        const tableCard = document.getElementById('table-card');
        const thead = document.getElementById('table-head-row');
        const tbody = document.getElementById('table-body');

        if (data.data && data.data.length > 0) {
            const cols = data.columns || Object.keys(data.data[0]);
            thead.innerHTML = cols.map(c => `<th>${escapeHtml(c.replace(/_/g, ' '))}</th>`).join('');
            tbody.innerHTML = data.data.map(row => `
                <tr>
                    ${cols.map(c => {
                        let val = row[c];
                        if (typeof val === 'number') {
                            val = c.includes('revenue') || c.includes('price') || c.includes('discount')
                                ? `$${val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                                : val.toLocaleString('en-US');
                        }
                        return `<td>${escapeHtml(String(val !== null && val !== undefined ? val : ''))}</td>`;
                    }).join('')}
                </tr>
            `).join('');
            tableCard.classList.remove('hidden');
        } else {
            tableCard.classList.add('hidden');
        }
    }

    function renderChart(chartData) {
        const ctx = document.getElementById('analytics-chart').getContext('2d');
        if (currentChart) {
            currentChart.destroy();
        }

        document.getElementById('chart-title').textContent = chartData.title || 'Data Visualization';

        currentChart = new Chart(ctx, {
            type: chartData.chart_type,
            data: {
                labels: chartData.labels,
                datasets: chartData.datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#9ca3af', font: { family: 'Plus Jakarta Sans' } }
                    }
                },
                scales: chartData.chart_type !== 'doughnut' ? {
                    x: {
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    y: {
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    }
                } : {}
            }
        });
    }

    async function openHealthModal() {
        healthModal.classList.remove('hidden');
        const modalBody = document.getElementById('health-modal-body');
        modalBody.innerHTML = '<div class="spinner" style="margin:2rem auto;"></div>';

        try {
            const res = await fetch('/api/health');
            const data = await res.json();

            let html = `
                <div style="margin-bottom:1.25rem;">
                    <p><strong>Database:</strong> ${escapeHtml(data.database_file)} (Read-Only Mode)</p>
                    <p><strong>Total Loaded Records:</strong> ${data.total_records} rows</p>
                    <p><strong>Indexed Fields:</strong> order_date, order_month, product, region, status, category</p>
                </div>
                <h4 style="margin:1rem 0 0.5rem; color:#93c5fd;">Forensic ETL Audit Log:</h4>
            `;

            if (data.audit_log && data.audit_log.length > 0) {
                html += data.audit_log.map(item => `
                    <div class="audit-card">
                        <div class="audit-title">[${escapeHtml(item.transaction_id)}] ${escapeHtml(item.issue)}</div>
                        <div class="audit-action">${escapeHtml(item.action)}</div>
                    </div>
                `).join('');
            } else {
                html += '<p style="color:#9ca3af;">No data anomalies detected.</p>';
            }

            modalBody.innerHTML = html;
        } catch (e) {
            modalBody.innerHTML = `<p style="color:#ef4444;">Failed to load health info: ${e.message}</p>`;
        }
    }

    function setLoading(isLoading) {
        if (isLoading) {
            btnText.classList.add('hidden');
            spinner.classList.remove('hidden');
            submitBtn.disabled = true;
        } else {
            btnText.classList.remove('hidden');
            spinner.classList.add('hidden');
            submitBtn.disabled = false;
        }
    }

    function parseSimpleMarkdown(md) {
        if (!md) return '';
        let html = md
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
            .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/gim, '<em>$1</em>')
            .replace(/`([^`]+)`/gim, '<code>$1</code>')
            .replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>')
            .replace(/^\- (.*$)/gim, '<li>$1</li>');

        // Wrap list items
        html = html.replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>');
        // Clean double wraps
        html = html.replace(/<\/ul>\s*<ul>/gim, '');
        // Replace newlines with breaks if not in blocks
        html = html.replace(/\n\n/g, '<p></p>');
        return html;
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
});
