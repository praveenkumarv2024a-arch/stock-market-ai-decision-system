document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('portfolio-table-body');
    const totalValueEl = document.getElementById('total-value');
    const totalPdlEl = document.getElementById('total-pnl');
    const totalInvestedEl = document.getElementById('total-invested');

    // Add Modal Logic
    const addBtn = document.getElementById('add-holding-btn');
    const modal = document.getElementById('add-modal');
    const closeBtn = document.querySelector('.close-modal');
    const saveBtn = document.getElementById('save-holding-btn');

    // Inputs
    const symbolInput = document.getElementById('p-symbol');
    const qtyInput = document.getElementById('p-qty');
    const priceInput = document.getElementById('p-price');

    // Autocomplete for symbol
    const stockList = document.getElementById('stock-list');
    if (stockList) {
        fetch('/api/symbols')
            .then(res => res.json())
            .then(data => {
                stockList.innerHTML = '';
                data.forEach(item => {
                    const opt = document.createElement('option');
                    opt.value = item.symbol;
                    opt.textContent = item.name;
                    stockList.appendChild(opt);
                });
            });
    }

    if (addBtn) addBtn.onclick = () => modal.classList.add('active');
    if (closeBtn) closeBtn.onclick = () => modal.classList.remove('active');
    window.onclick = (e) => { if (e.target == modal) modal.classList.remove('active'); };

    if (saveBtn) {
        saveBtn.onclick = () => {
            const sym = symbolInput.value.trim();
            const qty = parseInt(qtyInput.value);
            const price = parseFloat(priceInput.value);

            if (!sym || qty <= 0 || price < 0) {
                alert("Please enter valid details.");
                return;
            }

            saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
            fetch('/api/paper/buy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol: sym, quantity: qty, price: price })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.error) alert(data.error);
                    else {
                        modal.classList.remove('active');
                        symbolInput.value = '';
                        qtyInput.value = '';
                        priceInput.value = '';
                        fetchPortfolio(); // Refresh
                    }
                })
                .catch(err => alert("Error: " + err))
                .finally(() => saveBtn.innerHTML = 'Buy Stock');
        };
    }

    window.liquidateHolding = function (symbol, qty) {
        if (!confirm(`Sell all ${qty} shares of ${symbol} at market price?`)) return;
        fetch(`/api/paper/sell`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: symbol, quantity: qty, price: 0 }) // 0 = Market Price
        })
            .then(res => res.json())
            .then(data => {
                if (data.error) alert(data.error);
                else fetchPortfolio();
            });
    };

    window.manageFunds = function (action) {
        const verb = action === 'deposit' ? 'Deposit' : 'Withdraw';
        const input = prompt(`Enter amount to ${verb}:`);

        if (!input) return;
        let amount = parseFloat(input);

        if (isNaN(amount) || amount <= 0) {
            alert("Please enter a valid positive number.");
            return;
        }

        if (action === 'withdraw') {
            amount = -amount;
        }

        fetch('/api/paper/funds', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: amount })
        })
            .then(async res => {
                const isJson = res.headers.get('content-type')?.includes('application/json');
                if (!res.ok) {
                    const text = await res.text();
                    throw new Error(isJson ? JSON.parse(text).error : text.substring(0, 100)); // Show HTTP error
                }
                if (!isJson) throw new Error("Server returned non-JSON response");
                return res.json();
            })
            .then(data => {
                if (data.error) alert(data.error);
                else {
                    alert(`${verb} Successful!\nNew Balance: ₹${data.new_cash.toLocaleString()}`);
                    fetchPortfolio();
                }
            })
            .catch(err => {
                console.error(err);
                alert("Error: " + err.message);
            });
    };

    function fetchPortfolio() {
        tableBody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Loading...</td></tr>';

        fetch('/api/paper/portfolio')
            .then(res => res.json())
            .then(data => {
                renderPortfolio(data);
            })
            .catch(err => {
                console.error(err);
                tableBody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Error loading data</td></tr>';
            });
    }

    function renderPortfolio(data) {
        const holdings = data.holdings || [];
        tableBody.innerHTML = '';

        if (holdings.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" style="text-align:center;">No holdings. Buy some stocks!</td></tr>';
        } else {
            holdings.forEach(item => {
                const pnlClass = item.pnl >= 0 ? 'text-green' : 'text-red';
                const sign = item.pnl >= 0 ? '+' : '';

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${item.symbol}</td>
                    <td>${item.quantity}</td>
                    <td>₹${item.avg_price.toLocaleString()}</td>
                    <td>₹${item.current_price.toLocaleString()}</td>
                    <td>₹${item.market_value.toLocaleString()}</td>
                    <td class="${pnlClass}">${sign}₹${item.pnl.toLocaleString()} <br> <small>(${sign}${item.pnl_pct}%)</small></td>
                    <td>
                        <button class="btn-icon delete-btn" onclick="liquidateHolding('${item.symbol}', ${item.quantity})" title="Sell All"><i class="fa-solid fa-money-bill-wave"></i></button>
                    </td>
                `;
                tableBody.appendChild(tr);
            });
        }

        // Update Totals
        document.getElementById('cash-balance').innerText = "₹" + data.cash.toLocaleString();
        totalValueEl.innerText = "₹" + data.current_value.toLocaleString(); // Holdings Value
        totalInvestedEl.innerText = "₹" + data.total_invested.toLocaleString();
        document.getElementById('total-combined-value').innerText = "₹" + data.total_portfolio_value.toLocaleString();

        // Calculate Total PnL (Combined Value - (Initial 1L? No, purely based on invested vs current))
        // Better: Total PnL = Current Holdings Value - Total Invested
        const totPnl = data.current_value - data.total_invested;
        const totPnlPct = (data.total_invested > 0) ? (totPnl / data.total_invested * 100) : 0.0;

        const totPnlClass = totPnl >= 0 ? 'text-green' : 'text-red';
        const totSign = totPnl >= 0 ? '+' : '';
        totalPdlEl.innerHTML = `<span class="${totPnlClass}">${totSign}₹${totPnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} (${totSign}${totPnlPct.toFixed(2)}%)</span>`;
    }

    // Initial Load
    fetchPortfolio();

    // Auto Refresh every 5s
    setInterval(fetchPortfolio, 5000);
});
