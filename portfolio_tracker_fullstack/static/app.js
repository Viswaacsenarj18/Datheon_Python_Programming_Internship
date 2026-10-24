const $ = (id) => document.getElementById(id);
const money = (value) => new Intl.NumberFormat('en-US', {style:'currency', currency:'USD'}).format(Number(value || 0));
const signedMoney = (value) => `${Number(value) > 0 ? '+' : ''}${money(value)}`;
const pctClass = (value) => Number(value) >= 0 ? 'positive' : 'negative';

async function loadPortfolio() {
  const response = await fetch('/api/portfolio');
  const data = await response.json();
  const summary = data.summary;
  $('investedValue').textContent = money(summary.invested);
  $('marketValue').textContent = money(summary.market_value);
  $('pnlValue').textContent = signedMoney(summary.pnl);
  $('pnlValue').className = `metric-value ${pctClass(summary.pnl)}`;
  $('pnlPercent').textContent = `${summary.pnl_pct > 0 ? '+' : ''}${Number(summary.pnl_pct).toFixed(2)}%`;
  $('pnlPercent').className = `mini-badge ${pctClass(summary.pnl_pct)}`;
  $('holdingCount').textContent = summary.total_holdings;
  $('tableCount').textContent = `${summary.total_holdings} holding${summary.total_holdings === 1 ? '' : 's'}`;
  $('tableFootText').textContent = summary.total_holdings
    ? `${summary.total_holdings} purchase record(s) · ${money(summary.invested)} invested`
    : 'Add holdings to see your portfolio breakdown.';

  const body = $('holdingsBody');
  if (!data.holdings.length) {
    body.innerHTML = '<tr><td colspan="7" class="empty-state">Your portfolio is empty. Add your first holding to get started.</td></tr>';
    return;
  }
  body.innerHTML = data.holdings.map(item => {
    const initials = (item.ticker || '?').slice(0, 2);
    const pnlClass = pctClass(item.pnl);
    return `<tr>
      <td><div class="asset-cell"><div class="asset-logo">${escapeHtml(initials)}</div><div class="asset-name"><strong>${escapeHtml(item.ticker)}</strong><small>${escapeHtml(item.company || item.ticker)}</small></div></div></td>
      <td>${item.quantity}</td><td>${money(item.buy_price)}</td><td>${money(item.current_price)}</td>
      <td><strong>${money(item.market_value)}</strong></td>
      <td class="return-cell ${pnlClass}">${signedMoney(item.pnl)}<small>${item.pnl_pct > 0 ? '+' : ''}${Number(item.pnl_pct).toFixed(2)}%</small></td>
      <td><button class="delete-btn" title="Delete holding" aria-label="Delete ${escapeHtml(item.ticker)}" data-delete="${escapeHtml(item.id)}">×</button></td>
    </tr>`;
  }).join('');
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
}

function message(text, type='success') {
  $('formMessage').textContent = text;
  $('formMessage').className = `form-message ${type}`;
}

$('lookupBtn').addEventListener('click', async () => {
  const ticker = $('ticker').value.trim().toUpperCase();
  if (!ticker) { message('Enter a ticker symbol first.', 'error'); return; }
  $('lookupBtn').disabled = true;
  $('lookupBtn').textContent = '...';
  try {
    const response = await fetch(`/api/quote/${encodeURIComponent(ticker)}`);
    const data = await response.json();
    if (data.price) {
      $('currentPrice').value = data.price;
      $('tickerHelper').textContent = `${data.company || ticker} · Price source: ${data.source}`;
      message(`Price found for ${ticker}: ${money(data.price)}.`, 'success');
    } else {
      $('tickerHelper').textContent = data.message || 'Price unavailable. Enter it manually below.';
      message('Automatic price unavailable. Enter the current price manually.', 'error');
    }
  } catch (error) {
    message('Could not look up price. Check that the backend is running.', 'error');
  } finally {
    $('lookupBtn').disabled = false;
    $('lookupBtn').textContent = 'Lookup';
  }
});

$('holdingForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    ticker: $('ticker').value.trim().toUpperCase(),
    buy_price: $('buyPrice').value,
    quantity: $('quantity').value,
    current_price: $('currentPrice').value || null
  };
  $('submitBtn').disabled = true;
  $('submitBtn').textContent = 'Saving...';
  try {
    const response = await fetch('/api/holdings', {
      method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Could not save holding.');
    message(data.message, 'success');
    $('holdingForm').reset();
    $('tickerHelper').textContent = 'Use a ticker symbol such as AAPL or MSFT.';
    await loadPortfolio();
  } catch (error) {
    message(error.message, 'error');
  } finally {
    $('submitBtn').disabled = false;
    $('submitBtn').textContent = '＋ Add to portfolio';
  }
});

$('holdingsBody').addEventListener('click', async (event) => {
  const button = event.target.closest('[data-delete]');
  if (!button) return;
  if (!confirm('Delete this holding from your portfolio?')) return;
  const response = await fetch(`/api/holdings/${encodeURIComponent(button.dataset.delete)}`, {method:'DELETE'});
  const data = await response.json();
  if (!response.ok) alert(data.error || 'Could not delete holding.');
  await loadPortfolio();
});

$('refreshBtn').addEventListener('click', async () => {
  const button = $('refreshBtn');
  button.disabled = true;
  button.textContent = '↻ Refreshing...';
  try {
    const response = await fetch('/api/refresh-prices', {method:'POST'});
    const data = await response.json();
    await loadPortfolio();
    alert(data.message || 'Price refresh finished.');
  } catch (error) {
    alert('Could not refresh prices. Check that the backend is running.');
  } finally {
    button.disabled = false;
    button.textContent = '↻ Refresh prices';
  }
});

loadPortfolio().catch(() => {
  $('holdingsBody').innerHTML = '<tr><td colspan="7" class="empty-state">Could not connect to the backend. Start the Flask server and reload.</td></tr>';
});
