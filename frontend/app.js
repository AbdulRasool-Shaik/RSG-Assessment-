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

    // API Key Panel Elements
    const apiKeyBtn = document.getElementById('api-key-btn');
    const apiKeyPanel = document.getElementById('api-key-panel');
    const closeApiPanel = document.getElementById('close-api-panel');
    const geminiKeyInput = document.getElementById('gemini-key-input');
    const toggleKeyVisibility = document.getElementById('toggle-key-visibility');
    const geminiModelSelect = document.getElementById('gemini-model-select');
    const verifyKeyBtn = document.getElementById('verify-key-btn');
    const clearKeyBtn = document.getElementById('clear-key-btn');
    const keyVerificationMsg = document.getElementById('key-verification-msg');
    const apiKeyStatusText = document.getElementById('api-key-status-text');
    const keyDot = document.getElementById('key-dot');

    // 1. Initialize API Key from localStorage
    initApiKey();

    function initApiKey() {
        const savedKey = localStorage.getItem('gemini_api_key');
        const savedModel = localStorage.getItem('gemini_model');
        if (savedModel && geminiModelSelect) {
            geminiModelSelect.value = savedModel;
        }

        if (savedKey) {
            geminiKeyInput.value = savedKey;
            setKeyStatus(true, `🟢 Gemini Live (${savedModel || '1.5 Flash'})`);
        } else {
            setKeyStatus(false, 'Connect Gemini AI');
        }
    }

    function setKeyStatus(isOnline, text) {
        apiKeyStatusText.textContent = text;
        if (isOnline) {
            keyDot.className = 'key-status-dot online';
            apiKeyBtn.style.borderColor = 'rgba(16, 185, 129, 0.4)';
            apiKeyBtn.style.background = 'rgba(16, 185, 129, 0.1)';
            apiKeyBtn.style.color = '#6ee7b7';
        } else {
            keyDot.className = 'key-status-dot offline';
            apiKeyBtn.style.borderColor = 'rgba(59, 130, 246, 0.25)';
            apiKeyBtn.style.background = 'rgba(59, 130, 246, 0.1)';
            apiKeyBtn.style.color = '#93c5fd';
        }
    }

    // Toggle API Key Panel
    apiKeyBtn.addEventListener('click', () => {
        apiKeyPanel.classList.toggle('hidden');
    });

    closeApiPanel.addEventListener('click', () => {
        apiKeyPanel.classList.add('hidden');
    });

    // Toggle Password Visibility
    toggleKeyVisibility.addEventListener('click', () => {
        if (geminiKeyInput.type === 'password') {
            geminiKeyInput.type = 'text';
            toggleKeyVisibility.textContent = '🔒';
        } else {
            geminiKeyInput.type = 'password';
            toggleKeyVisibility.textContent = '👁️';
        }
    });

    // Verify & Connect API Key
    verifyKeyBtn.addEventListener('click', async () => {
        const key = geminiKeyInput.value.trim();
        const model = geminiModelSelect.value;
        if (!key) {
            keyVerificationMsg.textContent = 'Please paste a valid Google AI Studio key.';
            keyVerificationMsg.className = 'verification-msg error';
            return;
        }

        verifyKeyBtn.disabled = true;
        keyVerificationMsg.textContent = 'Verifying key with Google AI Studio...';
        keyVerificationMsg.className = 'verification-msg';

        try {
            const res = await fetch('/api/verify-key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: key })
            });
            const data = await res.json();

            if (data.valid) {
                localStorage.setItem('gemini_api_key', key);
                localStorage.setItem('gemini_model', model);
                keyVerificationMsg.textContent = `✓ ${data.message}`;
                keyVerificationMsg.className = 'verification-msg success';
                setKeyStatus(true, `🟢 Gemini Live (${model})`);
                setTimeout(() => { apiKeyPanel.classList.add('hidden'); }, 1500);
            } else {
                keyVerificationMsg.textContent = `✗ ${data.message}`;
                keyVerificationMsg.className = 'verification-msg error';
                setKeyStatus(false, 'Invalid Key');
            }
        } catch (err) {
            keyVerificationMsg.textContent = `Connection error: ${err.message}`;
            keyVerificationMsg.className = 'verification-msg error';
        } finally {
            verifyKeyBtn.disabled = false;
        }
    });

    // Clear Stored Key
    clearKeyBtn.addEventListener('click', () => {
        localStorage.removeItem('gemini_api_key');
        localStorage.removeItem('gemini_model');
        geminiKeyInput.value = '';
        keyVerificationMsg.textContent = 'API key removed. Running in offline fallback mode.';
        keyVerificationMsg.className = 'verification-msg';
        setKeyStatus(false, 'Connect Gemini AI');
    });

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

        const activeKey = localStorage.getItem('gemini_api_key') || geminiKeyInput.value.trim();
        const selectedModel = geminiModelSelect ? geminiModelSelect.value : 'gemini-1.5-flash';

        try {
            const res = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    use_llm: true,
                    api_key: activeKey || null,
                    model: selectedModel
                })
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
        const engineBadge = document.getElementById('engine-badge');
        const liveModelBadge = document.getElementById('live-model-badge');

        // Check if processed by Live Gemini or Fallback
        const isLive = data.live_model && !data.live_model.includes('None') && !data.live_model.includes('Failed');

        if (isLive) {
            engineBadge.textContent = 'AGENTIC VECTORLESS RAG';
            engineBadge.style.background = 'rgba(59, 130, 246, 0.15)';
            engineBadge.style.borderColor = 'rgba(59, 130, 246, 0.35)';
            engineBadge.style.color = '#93c5fd';

            liveModelBadge.textContent = `🟢 LIVE: ${data.live_model.replace('(Live)', '').trim()}`;
            liveModelBadge.classList.remove('hidden');
        } else {
            engineBadge.textContent = 'DETERMINISTIC FALLBACK ENGINE';
            engineBadge.style.background = 'rgba(245, 158, 11, 0.15)';
            engineBadge.style.borderColor = 'rgba(245, 158, 11, 0.35)';
            engineBadge.style.color = '#fcd34d';

            liveModelBadge.textContent = 'OFFLINE (NO API KEY)';
            liveModelBadge.style.background = 'rgba(107, 114, 128, 0.15)';
            liveModelBadge.style.borderColor = 'rgba(107, 114, 128, 0.3)';
            liveModelBadge.style.color = '#9ca3af';
            liveModelBadge.classList.remove('hidden');
        }

        if (data.status === 'refused') {
            engineBadge.textContent = 'GUARDRAIL BLOCKED';
            engineBadge.style.background = 'rgba(239, 68, 68, 0.2)';
            engineBadge.style.borderColor = 'rgba(239, 68, 68, 0.4)';
            engineBadge.style.color = '#fca5a5';
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
        document.getElementById('explanation-box').innerHTML = `<strong>Reasoning & Logic:</strong> ${escapeHtml(data.explanation || 'Processed deterministically.')}`;

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

        // Ensure datasets have nice background colors
        const defaultColors = [
            'rgba(59, 130, 246, 0.75)',
            'rgba(16, 185, 129, 0.75)',
            'rgba(245, 158, 11, 0.75)',
            'rgba(139, 92, 246, 0.75)',
            'rgba(239, 68, 68, 0.75)',
            'rgba(14, 165, 233, 0.75)'
        ];

        const preparedDatasets = chartData.datasets.map((ds, idx) => {
            if (!ds.backgroundColor) {
                ds.backgroundColor = chartData.chart_type === 'doughnut' ? defaultColors : defaultColors[idx % defaultColors.length];
            }
            if (!ds.borderColor && chartData.chart_type !== 'doughnut') {
                ds.borderColor = 'rgba(255, 255, 255, 0.2)';
                ds.borderWidth = 1;
            }
            return ds;
        });

        currentChart = new Chart(ctx, {
            type: chartData.chart_type || 'bar',
            data: {
                labels: chartData.labels,
                datasets: preparedDatasets
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
        html = html.replace(/<\/ul>\s*<ul>/gim, '');
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
