document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('stock-grid');
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modal-title');
    const closeBtn = document.querySelector('.close-btn');

    // Tab Logic
    window.switchTab = function (tabName) {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        const activeBtn = document.querySelector(`.tab-btn[onclick="switchTab('${tabName}')"]`);
        if (activeBtn) activeBtn.classList.add('active');

        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.getElementById(`tab-${tabName}`).classList.add('active');

        if (tabName === 'chart' && window.currentSymbol) {
            renderMainChart(window.currentSymbol);
        }
    };

    // Chart Instance
    let chartInstance = null;

    let chartPollInterval = null;
    let currentRange = '1d';

    // --- Sniper Mode State ---
    let isSniperMode = false;

    window.toggleSniperMode = function () {
        const toggle = document.getElementById('sniper-mode-toggle');
        isSniperMode = toggle.checked;
        if (isSniperMode) alert("🎯 SNIPER MODE ACTIVE\n\n- Showing only stocks with >80% Confidence.\n- Hiding weak signals.");
        renderSlice();
    };

    window.updateChartRange = function (range) {
        currentRange = range;

        // Update Buttons
        document.querySelectorAll('.btn-range').forEach(btn => btn.classList.remove('active'));
        const activeBtn = document.querySelector(`.btn-range[onclick="updateChartRange('${range}')"]`);
        if (activeBtn) activeBtn.classList.add('active');

        if (window.currentSymbol) renderMainChart(window.currentSymbol);
    };

    function renderMainChart(symbol) {
        const chartDiv = document.querySelector("#main-chart");
        if (!chartDiv) return;

        // Stop any existing poll when switching context
        if (chartPollInterval) clearInterval(chartPollInterval);

        function updateChart() {
            let url = '';

            if (currentRange === '1d') {
                url = `/api/chart/intraday/${symbol}?t=${new Date().getTime()}`;
            } else {
                // Map range to interval
                let interval = '1d';
                if (currentRange === '5d') interval = '15m'; // or 30m
                if (currentRange === '1mo') interval = '1d';
                if (currentRange === '6mo') interval = '1d';
                if (currentRange === 'ytd') interval = '1d';
                if (currentRange === '1y') interval = '1d';
                if (currentRange === '5y') interval = '1wk';
                if (currentRange === 'max') interval = '1mo';

                url = `/api/history/${symbol}?period=${currentRange}&interval=${interval}&t=${new Date().getTime()}`;
            }

            fetch(url)
                .then(res => res.json())
                .then(data => {
                    // Handle error or empty
                    if (data.error || !Array.isArray(data) && !data.data) {
                        if (!chartInstance) chartDiv.innerHTML = `<div class="error-msg">${data.error || "No Data"}</div>`;
                        return;
                    }

                    let seriesData = [];
                    let currentPrice = 0;
                    let prevClose = 0;

                    if (currentRange === '1d') {
                        // Intraday
                        seriesData = data.data.map(d => ({ x: new Date(d.t).getTime(), y: d.y }));
                        currentPrice = data.current_price;
                        prevClose = data.prev_close;
                    } else {
                        // History
                        seriesData = data.map(d => ({ x: new Date(d.x).getTime(), y: d.y }));
                        currentPrice = seriesData[seriesData.length - 1].y;
                        prevClose = seriesData[0].y; // Approx change over period
                    }

                    // --- Dynamic Coloring & Header ---
                    const change = currentPrice - prevClose;
                    const changeP = (change / prevClose) * 100;
                    const isPositive = change >= 0;
                    const color = isPositive ? '#00e676' : '#ef4444'; // Green : Red

                    // Update Header
                    const symbolEl = document.getElementById('chart-symbol');
                    const priceEl = document.getElementById('chart-price');
                    const changeEl = document.getElementById('chart-change');

                    if (symbolEl) symbolEl.innerText = symbol;
                    if (priceEl) priceEl.innerText = "₹" + currentPrice.toLocaleString('en-IN', { minimumFractionDigits: 2 });
                    if (changeEl) {
                        const sign = isPositive ? '+' : '';
                        changeEl.innerText = `${sign}${change.toFixed(2)} (${sign}${changeP.toFixed(2)}%)`;
                        changeEl.style.color = color;
                    }

                    if (!chartInstance) {
                        chartDiv.innerHTML = ""; // Clear loader
                        const options = {
                            series: [{
                                name: 'Price',
                                data: seriesData
                            }],
                            chart: {
                                type: 'area',
                                height: 350,
                                background: 'transparent',
                                toolbar: { show: false },
                                animations: { enabled: false }
                            },
                            dataLabels: { enabled: false },
                            stroke: { curve: 'straight', width: 2, colors: [color] },
                            fill: {
                                type: 'gradient',
                                gradient: {
                                    shadeIntensity: 1,
                                    opacityFrom: 0.7,
                                    opacityTo: 0.1,
                                    stops: [0, 100]
                                },
                                colors: [color]
                            },
                            theme: { mode: 'dark' },
                            xaxis: {
                                type: 'datetime',
                                tooltip: { enabled: true },
                                labels: { datetimeUTC: false }
                            },
                            yaxis: {
                                tooltip: { enabled: true },
                                labels: {
                                    formatter: function (value) { return "₹" + value.toFixed(2); }
                                }
                            },
                            colors: [color] // Main series color
                        };

                        const chart = new ApexCharts(chartDiv, options);
                        chart.render();
                        chartInstance = chart;
                    } else {
                        // Efficient Update with Color Change
                        chartInstance.updateOptions({
                            colors: [color],
                            stroke: { colors: [color] },
                            fill: { colors: [color] }
                        });
                        chartInstance.updateSeries([{
                            data: seriesData
                        }]);
                    }
                })
                .catch(err => console.error("Chart Poll Error:", err));
        }

        // Initial Call
        if (!chartInstance) chartDiv.innerHTML = '<div class="loading">Loading Chart...</div>';
        updateChart();

        // Poll ONLY if 1d
        if (currentRange === '1d') {
            chartPollInterval = setInterval(updateChart, 5000);
        }
    }

    window.refreshChart = function () {
        if (window.currentSymbol) {
            renderMainChart(window.currentSymbol);
        }
    };

    // Add Stock Logic
    const stockInput = document.getElementById('stock-input');
    const addBtn = document.getElementById('add-btn');
    const stockList = document.getElementById('stock-list');

    // Fetch Symbols for Autocomplete
    fetch('/api/symbols')
        .then(res => res.json())
        .then(data => {
            if (stockList && data.length > 0) {
                stockList.innerHTML = '';
                data.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item.symbol;
                    option.textContent = item.name;
                    stockList.appendChild(option);
                });
            }
        });

    if (addBtn) addBtn.onclick = addStock;
    if (stockInput) {
        stockInput.addEventListener("keypress", function (event) {
            if (event.key === "Enter") addStock();
        });
    }

    function addStock() {
        const symbol = stockInput.value.trim();
        if (!symbol) return;
        addBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        fetch('/api/stocks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: symbol })
        })
            .then(res => res.json())
            .then(data => {
                if (data.error) alert(data.error);
                else {
                    stockInput.value = '';
                    fetchStockData();
                }
            })
            .catch(err => alert("Error adding stock: " + err))
            .finally(() => {
                addBtn.innerHTML = '<i class="fa-solid fa-plus"></i> Add';
            });
    }

    window.removeStock = function (event, symbol) {
        event.stopPropagation();
        if (!confirm(`Remove ${symbol}?`)) return;
        fetch(`/api/stocks/${symbol}`, { method: 'DELETE' })
            .then(() => fetchStockData());
    }

    // --- Pagination Logic ---
    let currentData = [];
    let itemsToShow = 100; // Show all (Nifty 50 is < 100)
    const PAGE_SIZE = 50;

    const loadMoreBtn = document.getElementById('load-more-btn');

    const paginationControls = document.getElementById('pagination-controls');

    if (loadMoreBtn) {
        loadMoreBtn.onclick = () => {
            itemsToShow += PAGE_SIZE;
            renderSlice();
        };
    }

    function fetchStockData() {
        return fetch('/api/data')
            .then(response => response.json())
            .then(data => {
                currentData = data;
                renderSlice();
                return data;
            })
            .catch(error => {
                console.error('Error:', error);
                const loading = document.querySelector('.loading');
                if (loading) loading.innerText = "Error loading data. Server might be down.";
            });
    }

    function renderSlice() {
        const loading = document.querySelector('.loading');
        if (loading) loading.remove();

        if (!currentData || currentData.length === 0) {
            grid.innerHTML = '<div class="loading">No stocks tracked. Add some!</div>';
            return;
        }

        const visibleData = currentData.slice(0, itemsToShow);
        renderCards(visibleData);

        // Update Controls
        if (paginationControls) {
            paginationControls.style.display = currentData.length > 0 ? 'block' : 'none';
        }

        // Hide Load More if all shown
        if (loadMoreBtn) {
            loadMoreBtn.style.display = (visibleData.length >= currentData.length) ? 'none' : 'inline-block';
        }
    }

    function renderCards(data) {
        grid.innerHTML = '';
        data.forEach(stock => {
            const card = document.createElement('div');
            card.className = 'card';
            card.onclick = (e) => {
                if (!e.target.closest('.remove-btn') && !e.target.closest('button')) openModal(stock.symbol);
            };

            const changeClass = stock.change >= 0 ? 'positive' : 'negative';
            const sign = stock.change >= 0 ? '+' : '';

            // Confidence is 0-1. Convert to %
            // DEFENSIVE: Handle case where backend sends 0-1 OR 0-100
            let score = stock.confidence;
            if (score <= 1.0) {
                score = Math.round(score * 100);
            } else {
                score = Math.round(score);
            }

            // --- SNIPER MODE FILTER ---
            if (isSniperMode && score < 80) {
                return; // Skip this card
            }

            // Color scale: Red (High Risk) -> Yellow (Moderate) -> Green (Low Risk)
            let scoreColor = '#ef4444';
            let scoreLabel = 'High Risk';

            if (score >= 36) {
                scoreColor = '#f59e0b';
                scoreLabel = 'Moderate Risk';
            }
            if (score >= 76) {
                scoreColor = '#10b981';
                scoreLabel = 'Low Risk';
            }

            card.innerHTML = `
                <div class="remove-btn" onclick="removeStock(event, '${stock.symbol}')"><i class="fa-solid fa-trash"></i></div>
                <div class="card-header">
                    <div class="symbol">${stock.symbol}</div>
                    <div class="change ${changeClass}">${sign}${stock.change}%</div>
                </div>
                <div class="price">₹${stock.price}</div>
                
                <div class="decision-box" style="text-align: left; padding: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                        <span class="label" style="font-size: 0.8rem; opacity: 0.8;">${scoreLabel}</span>
                        <span class="score-val" style="font-size: 1rem; font-weight: 700; color: ${scoreColor}">${score}%</span>
                    </div>
                    <div class="progress-bar-bg" style="width: 100%; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">
                        <div class="progress-bar-fill" style="width: ${score}%; height: 100%; background: ${scoreColor}; transition: width 0.5s;"></div>
                    </div>
                </div>
                
                <div class="metrics">
                    <div class="metric">RSI: <span>${stock.rsi}</span></div>
                    <div class="metric">Sent: <span>${stock.sentiment}</span></div>
                </div>

                <div style="margin-top: 15px; display: flex; gap: 10px;">
                     <button class="btn-primary trade-btn" style="flex: 1; padding: 6px; font-size: 0.9rem; background: var(--accent-green); border: none;">
                        <i class="fa-solid fa-money-bill"></i> Trade
                     </button>
                </div>
            `;

            // Attach Trade Handler Correctly
            const tradeBtn = card.querySelector('.trade-btn');
            if (tradeBtn) {
                tradeBtn.onclick = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log("Opening Trade Modal for " + stock.symbol);
                    openTradeModal(stock.symbol, stock.price);
                };
            }

            grid.appendChild(card);
        });
    }

    // --- Trade Logic ---
    let tradeAction = 'BUY';
    let tradeSymbol = '';
    let tradePrice = 0.0;

    window.openTradeModal = function (symbol, price) {
        try {
            tradeSymbol = symbol;
            tradePrice = price;

            // 1. Check if Dynamic Modal Exists, else Create it
            let modal = document.getElementById('trade-modal-v3');

            if (!modal) {
                console.log("Creating Trade Modal v3...");
                modal = document.createElement('div');
                modal.id = 'trade-modal-v3';
                modal.className = 'modal active'; // Use existing CSS too

                // FORCE STYLES (The 'Nuclear' Option)
                Object.assign(modal.style, {
                    display: 'flex',
                    position: 'fixed',
                    zIndex: '2147483647',
                    left: '0',
                    top: '0',
                    width: '100vw',
                    height: '100vh',
                    backgroundColor: 'rgba(0,0,0,0.85)', // Dark overlay
                    backdropFilter: 'blur(5px)',
                    alignItems: 'center',
                    justifyContent: 'center',
                    opacity: '1'
                });

                // Inner Content
                modal.innerHTML = `
                    <div class="modal-content glass" style="max-width: 400px; height: auto; position: relative; background: #1e1e24; padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1);">
                        <span class="close-btn" style="position: absolute; top: 15px; right: 20px; font-size: 2rem; cursor: pointer; color: #fff;">&times;</span>
                        <div class="modal-header" style="margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px;">
                            <h2 style="margin: 0; color: #fff;">Trade Stock</h2>
                        </div>
                        <div class="modal-body">
                            <div style="margin-bottom: 20px; text-align: center;">
                                <div id="trd-price" style="font-size: 2rem; font-weight: bold; color: #fff;">₹0.00</div>
                                <div id="trd-symbol" style="color: #aaa;">SYMBOL</div>
                            </div>
        
                            <div style="margin-bottom: 15px;">
                                <label style="display: block; margin-bottom: 5px; color: #ccc;">Action</label>
                                <div style="display: flex; gap: 10px;">
                                    <button id="btn-buy-dyn" style="flex: 1; padding: 10px; border-radius: 5px; border: none; font-weight: bold; cursor: pointer;">BUY</button>
                                    <button id="btn-sell-dyn" style="flex: 1; padding: 10px; border-radius: 5px; border: none; font-weight: bold; cursor: pointer;">SELL</button>
                                </div>
                            </div>
        
                            <div style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 5px; color: #ccc;">Quantity</label>
                                <input type="number" id="trd-qty" value="1" min="1" style="width: 100%; padding: 10px; background: rgba(0,0,0,0.2); border: 1px solid #444; color: white; border-radius: 5px;">
                            </div>
                            
                            <div style="display: flex; justify-content: space-between; margin-bottom: 20px; font-size: 0.9rem; color: #aaa;">
                                <span>Total Cost:</span>
                                <span id="trd-total" style="color: white; font-weight: bold;">₹0.00</span>
                            </div>
        
                            <button id="confirm-dyn" style="width: 100%; padding: 12px; border-radius: 8px; border: none; font-weight: bold; font-size: 1rem; cursor: pointer; background: #00e676; color: #000;">Confirm Trade</button>
                        </div>
                    </div>
                `;

                document.body.appendChild(modal);

                // Attach Event Listeners (Since HTML is new)
                modal.querySelector('.close-btn').onclick = () => { modal.remove(); }; // Destroy on close

                // Dynamic Action Handlers
                const btnBuy = document.getElementById('btn-buy-dyn');
                const btnSell = document.getElementById('btn-sell-dyn');
                const btnConfirm = document.getElementById('confirm-dyn');
                const inputQty = document.getElementById('trd-qty');

                const updateCalc = () => {
                    const q = parseInt(inputQty.value) || 1;
                    const tot = (q * tradePrice).toFixed(2);
                    document.getElementById('trd-total').innerText = "₹" + tot;
                };

                inputQty.oninput = updateCalc;

                const setAction = (act) => {
                    tradeAction = act;
                    btnBuy.style.background = act === 'BUY' ? '#00e676' : '#333';
                    btnBuy.style.color = act === 'BUY' ? '#000' : '#fff';

                    btnSell.style.background = act === 'SELL' ? '#ef4444' : '#333';
                    btnSell.style.color = act === 'SELL' ? '#fff' : '#fff';

                    btnConfirm.style.background = act === 'BUY' ? '#00e676' : '#ef4444';
                    btnConfirm.style.color = '#fff';
                    btnConfirm.innerText = act + " STOCK";
                };

                btnBuy.onclick = () => setAction('BUY');
                btnSell.onclick = () => setAction('SELL');

                btnConfirm.onclick = () => {
                    const qty = parseInt(inputQty.value);
                    btnConfirm.disabled = true;
                    btnConfirm.innerHTML = "Processing...";

                    const endpoint = tradeAction === 'BUY' ? '/api/paper/buy' : '/api/paper/sell';
                    fetch(endpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ symbol: tradeSymbol, quantity: qty, price: tradePrice })
                    })
                        .then(r => r.json())
                        .then(d => {
                            if (d.error) alert(d.error);
                            else {
                                alert("Success! Cash: ₹" + d.new_cash);
                                modal.remove(); // Close
                            }
                        })
                        .catch(e => alert(e))
                        .finally(() => { btnConfirm.disabled = false; btnConfirm.innerText = tradeAction; });
                };

                // Init State
                setAction('BUY');

            } else {
                // Even if it exists, ensure it's visible (case of re-open)
                modal.style.display = 'flex';
                // Re-attach close handler just in case
                modal.querySelector('.close-btn').onclick = () => { modal.remove(); };
            }

            // Fill Data
            document.getElementById('trd-symbol').innerText = symbol;
            document.getElementById('trd-price').innerText = "₹" + price;
            // Recalc total
            const q = document.getElementById('trd-qty').value;
            document.getElementById('trd-total').innerText = "₹" + (q * price).toFixed(2);

            // Force close other modal
            const analysisModal = document.getElementById('modal');
            if (analysisModal) analysisModal.classList.remove('active');

        } catch (e) {
            alert("Injection Error: " + e.message);
        }
    };

    window.closeTradeModal = function () {
        if (modal) {
            modal.classList.remove('active');
            modal.style.display = ''; // Clear inline style to revert to CSS
        }
    };

    window.setTradeAction = function (action) {
        tradeAction = action;
        document.getElementById('btn-buy').classList.toggle('active', action === 'BUY');
        document.getElementById('btn-sell').classList.toggle('active', action === 'SELL');

        const btn = document.getElementById('confirm-trade-btn');
        if (action === 'BUY') {
            btn.style.background = 'var(--accent-green)';
            btn.innerText = "BUY STOCK";
        } else {
            btn.style.background = 'var(--accent-red)';
            btn.innerText = "SELL STOCK";
        }
    };

    function updateTradeTotal() {
        const qty = document.getElementById('trade-qty').value;
        const total = (qty * tradePrice).toFixed(2);
        document.getElementById('trade-total').innerText = "₹" + total;
    }

    // --- Safe Initialization of Trade Listeners ---
    function initTradeListeners() {
        const qtyInput = document.getElementById('trade-qty');
        const confirmBtn = document.getElementById('confirm-trade-btn');

        if (qtyInput) {
            qtyInput.addEventListener('input', updateTradeTotal);
        }

        if (confirmBtn) {
            confirmBtn.onclick = function () {
                const qty = document.getElementById('trade-qty').value;
                const btn = this;

                btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
                btn.disabled = true;

                const endpoint = tradeAction === 'BUY' ? '/api/paper/buy' : '/api/paper/sell';

                fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ symbol: tradeSymbol, quantity: parseInt(qty), price: tradePrice })
                })
                    .then(res => res.json())
                    .then(data => {
                        if (data.error) alert(data.error);
                        else {
                            alert("Trade Successful! \nNew Cash: ₹" + data.new_cash.toLocaleString());
                            closeTradeModal();
                        }
                    })
                    .catch(e => alert(e))
                    .finally(() => {
                        btn.innerHTML = tradeAction + ' STOCK';
                        btn.disabled = false;
                    });
            };
        }
    }

    // Call init immediately if DOM is ready, or wait
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTradeListeners);
    } else {
        initTradeListeners();
    }

    function generateSparkline(data, color) {
        if (!data || data.length < 2) return '';
        const width = 120;
        const height = 40;
        const min = Math.min(...data);
        const max = Math.max(...data);
        const range = max - min || 1;

        // Points
        const points = data.map((val, i) => {
            const x = (i / (data.length - 1)) * width;
            const y = height - ((val - min) / range) * height;
            return `${x},${y} `;
        }).join(' ');

        return `
            <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
                <polyline fill="none" stroke="${color}" stroke-width="2" points="${points}" />
            </svg>
        `;
    }

    function openModal(symbol) {
        // Force close Trade Modal
        const tradeModal = document.getElementById('trade-modal');
        if (tradeModal) {
            tradeModal.classList.remove('active');
            tradeModal.style.display = ''; // Reset display style
        }

        window.currentSymbol = symbol; // Store for chart
        modalTitle.textContent = `Analysis: ${symbol}`;
        modal.classList.add('active');
        switchTab('analysis');

        // Loader Logic
        // Loader Logic
        const aiText = document.getElementById('ai-text');
        const loader = document.getElementById('analysis-loader');

        if (loader) loader.style.display = 'block';
        if (aiText) aiText.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing market data...';

        // Fetch Explanation Text
        fetch(`/api/explanation/${symbol}`)
            .then(r => r.json())
            .then(data => {
                let html = data.explanation;
                // Simple markdown-ish parser for bold
                html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                if (aiText) aiText.innerHTML = html;
            })
            .catch(e => {
                if (aiText) aiText.innerText = "Failed to load explanation.";
            })
            .finally(() => {
                if (loader) loader.style.display = 'none';
            });

        // Trigger Load (Image still supported if needed, but text is priority)
        const shapImg = document.getElementById('shap-image');
        if (shapImg) {
            shapImg.src = `/explanation/${symbol}?t=${new Date().getTime()}`;
            shapImg.style.display = 'block'; // Ensure visible on refresh
        }

        fetchDetails(symbol);
    }

    function fetchDetails(symbol) {
        const funGrid = document.getElementById('fundamentals-grid');
        const newsList = document.getElementById('news-list');

        // Explicitly clear content
        funGrid.innerHTML = '<div class="loading">Loading Fundamentals...</div>';
        newsList.innerHTML = '<div class="loading">Loading News...</div>';
        console.log("Fetching details for:", symbol);

        // Add cache buster
        fetch(`/api/details/${symbol}?t=${new Date().getTime()}`)
            .then(res => {
                if (!res.ok) throw new Error("API Request Failed");
                return res.json();
            })
            .then(data => {
                console.log("Received data for:", symbol);
                // Fundamentals
                funGrid.innerHTML = '';
                const fData = data.fundamentals || {};
                if (Object.keys(fData).length === 0) funGrid.innerHTML = "<div>No data available.</div>";
                else {
                    for (const [key, val] of Object.entries(fData)) {
                        let displayVal = val;
                        if (typeof val === 'number') {
                            if (val > 10000000) displayVal = (val / 10000000).toFixed(2) + ' Cr';
                            else displayVal = val.toLocaleString();
                        }
                        // Formatting keys
                        const label = key.replace(/([A-Z])/g, ' $1').trim(); // CamelCase to Space

                        funGrid.innerHTML += `
                            <div class="info-item">
                                <div class="info-label">${label}</div>
                                <div class="info-value">${displayVal}</div>
                            </div>
                        `;
                    }
                }
                // News
                newsList.innerHTML = '';
                const nData = data.news || [];
                if (nData.length === 0) newsList.innerHTML = "<div>No news available.</div>";
                else {
                    nData.forEach(news => {
                        const sentClass = news.sentiment_score > 0.1 ? 'pos' : (news.sentiment_score < -0.1 ? 'neg' : 'neu');
                        const sentLabel = news.sentiment_score > 0.1 ? 'Pos' : (news.sentiment_score < -0.1 ? 'Neg' : 'Neu');
                        newsList.innerHTML += `
                            <div class="news-item">
                                <a href="${news.link}" target="_blank">${news.title} <i class="fa-solid fa-external-link-alt"></i></a>
                                <div class="news-meta">
                                    <span>${new Date(news.published).toLocaleDateString()}</span>
                                    <span class="sentiment-badge ${sentClass}">${sentLabel}</span>
                                </div>
                            </div>
                        `;
                    });
                }
            })
            .catch(err => {
                console.error("Fetch Details Error:", err);
                funGrid.innerHTML = `<div class="error-msg">Failed to load data. <br> <small>${err.message}</small></div>`;
                newsList.innerHTML = `<div class="error-msg">Failed to load news. <br> <small>${err.message}</small></div>`;
            });
    }

    function formatLabel(str) {
        return str.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    closeBtn.onclick = () => {
        modal.classList.remove('active');
        document.getElementById('shap-image').src = '';
        if (chartPollInterval) clearInterval(chartPollInterval);
        if (chartInstance) { chartInstance.destroy(); chartInstance = null; }
    };
    window.onclick = (event) => {
        if (event.target == modal) {
            modal.classList.remove('active');
            document.getElementById('shap-image').src = '';
            if (chartPollInterval) clearInterval(chartPollInterval);
            if (chartInstance) { chartInstance.destroy(); chartInstance = null; }
        }
    };

    // Initial Fetch
    fetchStockData();
    setInterval(fetchStockData, 10000);

    // Uptime Fetch
    function updateStatus() {
        const uptimeEl = document.getElementById('uptime-display');
        if (uptimeEl) {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    uptimeEl.innerText = data.uptime;
                })
                .catch(e => console.error(e));
        }
    }
    setInterval(updateStatus, 1000);
    updateStatus();

    // Auto-Refresh Grid (Dynamic)
    let refreshRate = 5000;
    fetch('/api/settings').then(r => r.json()).then(s => {
        if (s.refresh_rate) {
            refreshRate = s.refresh_rate * 1000;
            console.log("Refresh Rate set to:", refreshRate);
        }
        setInterval(fetchStockData, refreshRate);
    }).catch(e => setInterval(fetchStockData, 5000));

    // New Refresh Logic
    window.refreshThisStock = function () {
        if (!window.currentSymbol) return;

        const btn = document.querySelector('button[onclick="refreshThisStock()"]');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Refreshing...';
        btn.disabled = true;

        fetch(`/api/refresh/${window.currentSymbol}`, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.error) alert("Refresh Failed: " + data.error);
                else {
                    // Success - Reload details
                    openModal(window.currentSymbol); // Re-opens/refreshes modal content
                    // Also refresh main grid in background
                    fetchStockData();
                }
            })
            .catch(err => alert("Network Error: " + err))
            .finally(() => {
                btn.innerHTML = originalText;
                btn.disabled = false;
            });
    };

    // --- Market Indices Logic ---
    function renderIndices() {
        const container = document.getElementById('indices-container');
        if (!container) return;

        fetch('/api/indices')
            .then(res => res.json())
            .then(data => {
                if (data.error) return; // Silent fail

                container.innerHTML = data.map(idx => {
                    const colorClass = idx.change >= 0 ? 'text-green' : 'text-red';
                    const icon = idx.change >= 0 ? '▲' : '▼';

                    return `
                        <div style="flex: 0 0 auto; width: 200px; padding: 15px; border-radius: 12px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 0.8rem; opacity: 0.7; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">${idx.name}</div>
                                <div style="font-size: 1.2rem; font-weight: 700; margin-top: 4px;">${idx.price.toLocaleString()}</div>
                            </div>
                            <div class="${colorClass}" style="text-align: right;">
                                <div style="font-size: 1rem; font-weight: 700;">${Math.abs(idx.change).toFixed(2)}</div>
                                <div style="font-size: 0.75rem; font-weight: 600;">${icon} ${Math.abs(idx.percent).toFixed(2)}%</div>
                            </div>
                        </div>
                    `;
                }).join('');
            })
            .catch(err => console.error("Indices Error:", err));
    }

    // Init Indices
    renderIndices();
    setInterval(renderIndices, 5000); // Update every 5 seconds (was 60s)

    // --- Heatmap Logic ---
    function renderHeatmap() {
        const heatmapDiv = document.querySelector("#sentiment-heatmap");
        if (!heatmapDiv) return;

        fetch('/api/market/sentiment')
            .then(res => res.json())
            .then(data => {
                // ApexCharts Treemap Format:
                // [{ x: 'Infosys', y: 0.8 }, { x: 'TCS', y: -0.2 }]
                // We want color based on y value.

                const seriesData = data.map(item => ({
                    x: item.x,
                    y: item.y, // Sentiment Score
                    fillColor: item.y > 0.2 ? '#00e676' : (item.y < -0.2 ? '#ef4444' : '#fbbf24') // Green/Red/Yellow
                }));

                const options = {
                    series: [
                        {
                            data: seriesData
                        }
                    ],
                    chart: {
                        height: 300,
                        type: 'treemap',
                        background: 'transparent',
                        toolbar: { show: false }
                    },
                    theme: { mode: 'dark' },
                    title: {
                        text: 'Fear & Greed Map',
                        align: 'center',
                        style: { color: '#e0e0e0' }
                    },
                    dataLabels: {
                        enabled: true,
                        style: {
                            fontSize: '12px',
                        },
                        formatter: function (text, op) {
                            return [text, op.value.toFixed(2)];
                        },
                        offsetY: -4
                    },
                    plotOptions: {
                        treemap: {
                            distributed: true,
                            enableShades: false
                        }
                    },
                    tooltip: {
                        theme: 'dark',
                        y: {
                            formatter: function (val) {
                                return val + " (Sentiment)";
                            }
                        }
                    }
                };

                heatmapDiv.innerHTML = "";
                const chart = new ApexCharts(heatmapDiv, options);
                chart.render();
            })
            .catch(err => console.error("Heatmap Error:", err));
    }

    // Call Heatmap on load
    renderHeatmap();
    // Refresh Heatmap every minute
    setInterval(renderHeatmap, 60000);

    // --- Global Refresh Logic ---
    window.refreshAllData = function () {
        const btn = document.getElementById('global-refresh-btn');
        const icon = btn.querySelector('i');

        btn.disabled = true;
        icon.classList.add('fa-spin');

        // Call backend to force update
        fetch('/api/market/refresh', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                console.log(data.message);
                // Reload Grid
                fetchStockData().then(() => {
                    // small delay for visual feedback
                    setTimeout(() => {
                        btn.disabled = false;
                        icon.classList.remove('fa-spin');
                    }, 500);
                });
            })
            .catch(err => {
                alert("Refresh Error: " + err);
                btn.disabled = false;
                icon.classList.remove('fa-spin');
            });
    }

});
