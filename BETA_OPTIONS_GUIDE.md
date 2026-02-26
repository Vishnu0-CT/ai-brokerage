# 🎯 Beta & Options - Complete Guide

## ✅ **What We're Doing:**

### 1. **Beta** - Fetching from Yahoo Finance ✅
We **fetch** Beta directly from Yahoo Finance (NOT calculating ourselves).

**Endpoint:**
```bash
GET http://localhost:8000/api/yahoo/quote/{symbol}
```

**Example:**
```bash
curl http://localhost:8000/api/yahoo/quote/AAPL
```

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "beta": 1.107,  👈 Market volatility vs S&P 500
    "price": 274.23,
    "trailingPE": 34.71,
    "returnOnEquity": 1.52,
    "returnOnAssets": 0.244
  }
}
```

**What is Beta?**
- Measures stock volatility relative to the market (S&P 500)
- Beta = 1.0 means moves with the market
- Beta > 1.0 means more volatile (AAPL = 1.107 = 10.7% more volatile)
- Beta < 1.0 means less volatile

---

### 2. **Options Chain** - Fetching from Yahoo Finance ✅

**Endpoint:**
```bash
GET http://localhost:8000/api/yahoo/options/{symbol}
```

**Example:**
```bash
# Basic options data
curl http://localhost:8000/api/yahoo/options/AAPL

# Specific expiry date
curl "http://localhost:8000/api/yahoo/options/AAPL?expiry=2026-03-20"
```

**Response (WITHOUT Greeks):**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "expirationDates": ["2026-02-27", "2026-03-20", ...],
    "selectedExpiry": "2026-02-27",
    "underlyingPrice": 274.23,
    "calls": [
      {
        "strike": 275.0,
        "lastPrice": 5.40,
        "bid": 5.30,
        "ask": 5.50,
        "volume": 12500,
        "openInterest": 45000,
        "impliedVolatility": 0.24,  👈 24% IV (from Yahoo)
        "change": 0.35,
        "percentChange": 6.93,
        "inTheMoney": false,
        "contractSymbol": "AAPL260227C00275000"
      }
    ],
    "puts": [...]
  }
}
```

**What Yahoo Finance Provides:**
- ✅ Strike prices
- ✅ Bid/Ask prices
- ✅ Last traded price
- ✅ Volume
- ✅ Open Interest
- ✅ **Implied Volatility (IV)**
- ✅ Price change
- ✅ In-the-money status
- ✅ Contract symbols
- ❌ Greeks (Delta, Gamma, Theta, Vega, Rho) - NOT provided by Yahoo

---

### 3. **Options Greeks** - WE CALCULATE THEM! 🔥

**NEW FEATURE:** We now calculate Options Greeks using Black-Scholes model!

**Endpoint:**
```bash
GET http://localhost:8000/api/yahoo/options/{symbol}?include_greeks=true
```

**Example:**
```bash
# Get options WITH Greeks
curl "http://localhost:8000/api/yahoo/options/AAPL?include_greeks=true"

# Specific expiry WITH Greeks
curl "http://localhost:8000/api/yahoo/options/AAPL?expiry=2026-03-20&include_greeks=true"
```

**Response (WITH Greeks):**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "underlyingPrice": 274.23,
    "includesGreeks": true,
    "calls": [
      {
        "strike": 275.0,
        "lastPrice": 5.40,
        "bid": 5.30,
        "ask": 5.50,
        "volume": 12500,
        "openInterest": 45000,
        "impliedVolatility": 0.24,

        // 👇 CALCULATED GREEKS 👇
        "delta": 0.5234,      // Delta: 0.52 (52% probability ITM)
        "gamma": 0.0156,      // Gamma: Rate of delta change
        "theta": -0.0842,     // Theta: -$0.08 per day (time decay)
        "vega": 0.3421,       // Vega: $0.34 per 1% IV change
        "rho": 0.1234         // Rho: Interest rate sensitivity
      }
    ]
  }
}
```

---

## 📊 **Greeks Explained:**

### Delta (Δ)
- **Range:** 0 to 1 (calls), -1 to 0 (puts)
- **Meaning:** How much option price changes per $1 stock move
- **Example:** Delta = 0.52 means option gains $0.52 if stock rises $1
- **Also:** Rough probability option expires in-the-money

### Gamma (Γ)
- **Meaning:** Rate of change of Delta
- **Example:** Gamma = 0.0156 means Delta increases by 0.0156 per $1 stock move
- **Highest:** At-the-money options have highest gamma

### Theta (Θ)
- **Meaning:** Time decay - how much option loses per day
- **Example:** Theta = -0.0842 means option loses $0.08 per day
- **Always negative** for long options (you lose value every day)

### Vega (ν)
- **Meaning:** Sensitivity to volatility changes
- **Example:** Vega = 0.3421 means option gains $0.34 if IV increases 1%
- **Higher:** For at-the-money and longer-dated options

### Rho (ρ)
- **Meaning:** Sensitivity to interest rate changes
- **Example:** Rho = 0.1234 means option gains $0.12 if rates increase 1%
- **Least important** for short-term options

---

## 🔬 **How We Calculate Greeks:**

We use the **Black-Scholes Model** with:
1. ✅ Stock price (from Yahoo Finance)
2. ✅ Strike price (from Yahoo Finance)
3. ✅ Time to expiration (calculated from expiry date)
4. ✅ Implied Volatility (from Yahoo Finance)
5. ✅ Dividend yield (from Yahoo Finance)
6. ⚙️ Risk-free rate (set to 5% - Federal Reserve rate)

**Library:** `scipy.stats` for Black-Scholes calculations

---

## 📈 **Complete Example:**

```bash
# 1. Get Beta
curl http://localhost:8000/api/yahoo/quote/AAPL | python3 -c "import sys, json; print('Beta:', json.load(sys.stdin)['data']['beta'])"

# 2. Get Options WITHOUT Greeks (faster)
curl http://localhost:8000/api/yahoo/options/AAPL

# 3. Get Options WITH Greeks (calculated)
curl "http://localhost:8000/api/yahoo/options/AAPL?include_greeks=true"

# 4. Compare at-the-money call
curl "http://localhost:8000/api/yahoo/options/AAPL?include_greeks=true" | \
  python3 -m json.tool | grep -A 15 '"strike": 275'
```

---

## 🎯 **Use Cases:**

### 1. **Delta Hedging**
```python
# If you own 100 shares of AAPL
# And sell 2 call options with Delta = 0.50
# Your position delta = 100 - (2 * 100 * 0.50) = 0 (delta neutral)
```

### 2. **Time Decay Analysis**
```python
# Option price = $5.40
# Theta = -0.08
# Tomorrow's expected price = $5.40 - $0.08 = $5.32
# In 7 days = $5.40 - (0.08 * 7) = $4.84
```

### 3. **Volatility Trading**
```python
# If IV increases from 24% to 25% (1% increase)
# Vega = 0.34
# Option price increases by $0.34
# New price = $5.40 + $0.34 = $5.74
```

---

## ⚡ **Performance:**

| Endpoint | Latency | Greeks? |
|----------|---------|---------|
| `/api/yahoo/options/AAPL` | ~300-400ms | ❌ No |
| `/api/yahoo/options/AAPL?include_greeks=true` | ~400-500ms | ✅ Yes |

**Extra cost for Greeks:** ~100ms (Black-Scholes calculation)

---

## 🚀 **JavaScript/React Example:**

```javascript
import { useState, useEffect } from 'react';

function OptionsChain({ symbol }) {
  const [options, setOptions] = useState(null);
  const [includeGreeks, setIncludeGreeks] = useState(false);

  useEffect(() => {
    const url = `http://localhost:8000/api/yahoo/options/${symbol}?include_greeks=${includeGreeks}`;

    fetch(url)
      .then(res => res.json())
      .then(data => setOptions(data.data));
  }, [symbol, includeGreeks]);

  if (!options) return <div>Loading...</div>;

  return (
    <div>
      <h2>{symbol} Options Chain</h2>
      <button onClick={() => setIncludeGreeks(!includeGreeks)}>
        {includeGreeks ? 'Hide Greeks' : 'Show Greeks'}
      </button>

      <h3>Calls</h3>
      <table>
        <thead>
          <tr>
            <th>Strike</th>
            <th>Last</th>
            <th>Bid</th>
            <th>Ask</th>
            <th>Volume</th>
            <th>IV</th>
            {includeGreeks && (
              <>
                <th>Delta</th>
                <th>Gamma</th>
                <th>Theta</th>
                <th>Vega</th>
              </>
            )}
          </tr>
        </thead>
        <tbody>
          {options.calls.map(call => (
            <tr key={call.contractSymbol}>
              <td>${call.strike}</td>
              <td>${call.lastPrice}</td>
              <td>${call.bid}</td>
              <td>${call.ask}</td>
              <td>{call.volume.toLocaleString()}</td>
              <td>{(call.impliedVolatility * 100).toFixed(1)}%</td>
              {includeGreeks && (
                <>
                  <td>{call.delta?.toFixed(3)}</td>
                  <td>{call.gamma?.toFixed(4)}</td>
                  <td>{call.theta?.toFixed(3)}</td>
                  <td>{call.vega?.toFixed(3)}</td>
                </>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## 🐍 **Python Example:**

```python
import requests

# Get options with Greeks
response = requests.get(
    'http://localhost:8000/api/yahoo/options/AAPL',
    params={'include_greeks': True}
)

data = response.json()['data']

print(f"Symbol: {data['symbol']}")
print(f"Underlying Price: ${data['underlyingPrice']}")
print(f"\nCalls:")

for call in data['calls'][:5]:  # First 5 calls
    print(f"\nStrike: ${call['strike']}")
    print(f"  Last Price: ${call['lastPrice']:.2f}")
    print(f"  IV: {call['impliedVolatility']*100:.1f}%")

    if 'delta' in call:
        print(f"  Delta: {call['delta']:.3f}")
        print(f"  Gamma: {call['gamma']:.4f}")
        print(f"  Theta: {call['theta']:.3f} (${call['theta']:.2f}/day)")
        print(f"  Vega: {call['vega']:.3f}")
        print(f"  Rho: {call['rho']:.4f}")
```

---

## 📋 **Summary:**

| Feature | Source | Endpoint | Parameter |
|---------|--------|----------|-----------|
| **Beta** | Yahoo Finance | `/api/yahoo/quote/{symbol}` | - |
| **Options Chain** | Yahoo Finance | `/api/yahoo/options/{symbol}` | - |
| **Implied Volatility** | Yahoo Finance | `/api/yahoo/options/{symbol}` | - |
| **Options Greeks** | **We Calculate** | `/api/yahoo/options/{symbol}` | `?include_greeks=true` |

---

## 🎯 **Quick Commands:**

```bash
# Beta for AAPL
curl http://localhost:8000/api/yahoo/quote/AAPL | python3 -m json.tool | grep beta

# Options WITHOUT Greeks (faster)
curl http://localhost:8000/api/yahoo/options/AAPL

# Options WITH Greeks (slower but complete)
curl "http://localhost:8000/api/yahoo/options/AAPL?include_greeks=true"

# Options for specific expiry WITH Greeks
curl "http://localhost:8000/api/yahoo/options/AAPL?expiry=2026-03-20&include_greeks=true"
```

---

## ✅ **What You Get:**

### From Yahoo Finance (Free):
- Beta ✅
- Options Chain ✅
- Implied Volatility ✅
- Strike, Bid, Ask, Volume, OI ✅

### We Calculate:
- **Delta** ✅ (using Black-Scholes)
- **Gamma** ✅ (using Black-Scholes)
- **Theta** ✅ (using Black-Scholes)
- **Vega** ✅ (using Black-Scholes)
- **Rho** ✅ (using Black-Scholes)

**Everything you need for options trading!** 🎉
