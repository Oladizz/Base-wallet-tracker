
const API_KEY = 'B93PFHQ33YHX6KXUS8DMPYIY6YZ1MB67BJ';

const input = document.getElementById('walletInput');
const btn = document.getElementById('fetchBtn');
const clearBtn = document.getElementById('clearBtn');
const output = document.getElementById('output');

function shortenAddress(address) {
  if (!address || address.length < 12) return address;
  return address.substring(0, 6) + '...' + address.substring(address.length - 6);
}

function formatEth(bigint) {
  return (Number(bigint) / 1e18).toFixed(6);
}

function formatGwei(bigint) {
  return (Number(bigint) / 1e9).toFixed(2);
}

function formatDate(timestamp) {
  return new Date(timestamp * 1000).toLocaleString();
}

async function fetchEthPrice() {
  try {
    const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usdt');
    const json = await res.json();
    return json.ethereum.usdt || 0;
  } catch {
    return 0;
  }
}

function copyToClipboard(text, button) {
  if (!navigator.clipboard) {
    alert('Clipboard not supported');
    return;
  }
  navigator.clipboard.writeText(text).then(() => {
    button.textContent = 'Copied!';
    setTimeout(() => button.textContent = 'Copy', 1500);
  });
}

async function fetchGasData(wallet) {
  output.textContent = 'Fetching data, please wait...';

  const url = `https://api.basescan.org/api?module=account&action=txlist&address=${wallet}&startblock=0&endblock=99999999&sort=asc&apikey=${API_KEY}`;

  try {
    const response = await fetch(url);
    const json = await response.json();

    if (json.status !== '1') {
      output.textContent = `API error: ${json.message}`;
      return;
    }

    const txs = json.result;
    const txCount = txs.length;

    if (txCount === 0) {
      output.textContent = 'No transactions found.';
      return;
    }

    let totalGas = 0n;
    for (const tx of txs) {
      totalGas += BigInt(tx.gasUsed) * BigInt(tx.gasPrice);
    }

    const ethPrice = await fetchEthPrice();
    const totalGasEth = Number(totalGas) / 1e18;
    const totalGasUSDT = (totalGasEth * ethPrice).toFixed(2);

    // Last 5 transactions (latest)
    const last5 = txs.slice(-5).reverse();

    let txHTML = `
      <h3>Last 5 Transactions</h3>
      <div style="overflow-x:auto;">
      <table>
        <thead>
          <tr>
            <th>Hash</th>
            <th>Date</th>
            <th>Gas Used</th>
            <th>Gas Price (Gwei)</th>
            <th>Copy</th>
          </tr>
        </thead>
        <tbody>
    `;

    for (const tx of last5) {
      const shortHash = shortenAddress(tx.hash);
      txHTML += `
        <tr>
          <td title="${tx.hash}" style="font-family: monospace;">${shortHash}</td>
          <td>${formatDate(Number(tx.timeStamp))}</td>
          <td>${tx.gasUsed}</td>
          <td>${formatGwei(tx.gasPrice)}</td>
          <td><button class="copy-btn" data-hash="${tx.hash}">Copy</button></td>
        </tr>
      `;
    }

    txHTML += `</tbody></table></div>`;

    output.innerHTML = `
      <div style="margin-bottom:1rem;">
        <strong>Wallet:</strong> ${shortenAddress(wallet)}<br />
        <strong>Transactions:</strong> ${txCount}<br />
        <strong style="color:#0ff; text-shadow: 0 0 6px #0ff;">Total Gas Used:</strong> 
        <span style="background: #012; padding: 0.2rem 0.5rem; border-radius: 8px; box-shadow: 0 0 8px #0ff;">
          ${formatEth(totalGas)} ETH
        </span><br />
        <strong>Total Gas Cost in USDT:</strong> $${totalGasUSDT}
      </div>
      ${txHTML}
    `;

    // Add event listeners to copy buttons
    document.querySelectorAll('.copy-btn').forEach(btn => {
      btn.addEventListener('click', () => copyToClipboard(btn.dataset.hash, btn));
    });

  } catch (err) {
    output.textContent = `Request failed: ${err.message}`;
  }
}

btn.addEventListener('click', () => {
  const wallet = input.value.trim();
  if (!wallet) {
    output.textContent = 'Please enter a valid wallet address.';
    return;
  }
  fetchGasData(wallet);
});

clearBtn.addEventListener('click', () => {
  input.value = '';
  output.textContent = '';
});
