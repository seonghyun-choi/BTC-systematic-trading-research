# 📈 BTC Systematic Trading Research

A systematic research and backtesting project for evaluating rule-based Bitcoin trading hypotheses using historical spot and futures market data.

Rather than optimizing a strategy until it appears profitable, this project follows a **hypothesis → frozen plan → backtest → robustness check → accept/reject** workflow.

> **Current Status:** Research / Experimental  
> **Dataset:** BTCUSDT Spot + USD-M Futures, 1-minute candles  
> **Research Period:** 2020-01-01 → 2022-12-31 UTC  
> **Validation 2023–2024:** Sealed / Not Used  
> **OOS 2025+:** Sealed / Not Used  
> **Current Qualified Strategies:** **0**

---

## 🎯 Research Objective

The broader goal is to investigate whether systematic BTC trading rules can produce repeatable positive expectancy after realistic transaction-cost assumptions.

The experiment currently documented in this repository is **CF1: Spot + Futures Flow Confirmation**.

The research question was:

> Does requiring spot-market order-flow confirmation improve the persistence of futures order-flow signals?

The experiment was intentionally designed as a falsifiable hypothesis rather than a strategy optimization exercise.

The result was negative.

**No tested CF1 configuration produced positive average returns after transaction costs.**

The hypothesis was therefore rejected in its frozen form rather than retuned after observing the results.

---

## 🧪 CF1 Hypothesis

For every completed one-minute candle, quote-volume imbalance is calculated as:

```text
imbalance =
2 × taker_buy_quote_volume / quote_volume - 1
```

A value of `+0.2` corresponds to approximately 60% taker-buy quote-volume share.

### LONG candidate

The three most recently completed futures candles must all satisfy:

```text
imbalance >= +0.2
```

### SHORT candidate

The three most recently completed futures candles must all satisfy:

```text
imbalance <= -0.2
```

A candidate event occurs only when the futures condition transitions:

```text
FALSE → TRUE
```

CF1 then requires the **same three spot candles** to satisfy the same directional threshold.

The control arm, `FUTURES_ONLY`, does not require this additional spot confirmation.

CF1 events therefore form a subset of the futures-only candidate population.

---

## 🔒 Pre-Frozen Research Design

The experimental plan was frozen before performance calculation and its SHA-256 digest was preserved.

The experiment tested:

```text
2 directions
× 2 confirmation groups
× 3 holding periods
= 12 configurations
```

Holding periods:

```text
5 minutes
15 minutes
30 minutes
```

The primary holding period was **15 minutes**.

After observing results, the experiment did **not**:

- Search for a better threshold
- Reverse the signal
- Select the best holding period retrospectively
- Rescue the strategy with additional filters
- Tune parameters to recover profitability

This was intended to reduce post-hoc optimization and research overfitting.

---

## ⏱️ Execution Model

A signal is confirmed at time `t`.

Entry is modeled at:

```text
t + 60 seconds
```

using the futures open price.

The one-minute delay acts as a conservative processing-latency proxy because actual real-time data-delivery latency was not measured.

Exit occurs at the open price corresponding to:

```text
entry time + holding period
```

Signals occurring while an existing position for the same direction/configuration remains open are ignored.

LONG and SHORT are evaluated independently.

This experiment does **not** claim to reproduce actual exchange fills.

---

## 💰 Transaction-Cost Model

Three round-trip cost scenarios were evaluated:

| Scenario | Interpretation |
|---|---|
| `net6` | 6 bp modeled round-trip cost |
| `net8` | 8 bp modeled round-trip cost |
| `net10` | 10 bp modeled round-trip cost |

`net6` uses an assumed fee model based on a provisional 50% rebate assumption.

The additional costs in `net8` and `net10` are sensitivity assumptions, not measured Bitget slippage or spread.

Therefore, the results should be interpreted as **research estimates rather than live-trading performance**.

---

## 📊 Main Results

### CF1 results

| Side | Hold | Trades | Gross (bp) | Net 6bp | Net 8bp | Net 10bp | Trades/day |
|---|---:|---:|---:|---:|---:|---:|---:|
| LONG | 5m | 2,738 | +0.784 | -5.217 | -7.217 | -9.217 | 2.50 |
| LONG | 15m | 2,650 | +0.201 | -5.799 | -7.799 | -9.799 | 2.42 |
| LONG | 30m | 2,515 | -0.754 | -6.754 | -8.754 | -10.754 | 2.29 |
| SHORT | 5m | 3,753 | -0.893 | -6.893 | -8.893 | -10.893 | 3.42 |
| SHORT | 15m | 3,612 | -1.476 | -7.476 | -9.476 | -11.476 | 3.30 |
| SHORT | 30m | 3,417 | -1.205 | -7.205 | -9.205 | -11.205 | 3.12 |

### Result

**All 12 configurations produced negative average returns under the 6bp, 8bp, and 10bp cost assumptions.**

No configuration qualified as a viable strategy.

---

## 📅 Year-by-Year Robustness Check

The primary 15-minute configuration was also evaluated separately across 2020, 2021, and 2022.

### LONG

| Year | Trades | Gross (bp) | Net 6bp | Net 8bp |
|---|---:|---:|---:|---:|
| 2020 | 1,355 | -0.104 | -6.104 | -8.104 |
| 2021 | 645 | +1.493 | -4.508 | -6.508 |
| 2022 | 650 | -0.443 | -6.443 | -8.443 |

### SHORT

| Year | Trades | Gross (bp) | Net 6bp | Net 8bp |
|---|---:|---:|---:|---:|
| 2020 | 1,825 | -1.792 | -7.793 | -9.793 |
| 2021 | 891 | -2.570 | -8.570 | -10.570 |
| 2022 | 896 | +0.257 | -5.743 | -7.743 |

Across the full experiment:

> **All 36 year × configuration cells had negative average `net6` returns.**

Because the predefined economic and robustness gates failed, the experiment did not proceed to bootstrap/FDR significance testing.

---

## 🔍 Spot Confirmation vs. Futures-Only Control

For the primary 15-minute configuration:

### LONG

Spot confirmation improved `net8` by approximately:

```text
+0.539 bp
```

relative to the futures-only control.

However, CF1 remained:

```text
-7.799 bp
```

after modeled costs.

### SHORT

Spot confirmation worsened performance by approximately:

```text
-1.023 bp
```

relative to the control.

These are observational mean differences.

They are **not interpreted as statistically established improvements or causal effects**.

---

## 🧹 Data Quality

The research dataset covers:

```text
2020-01-01 → 2022-12-31 UTC
```

and contains official Binance BTCUSDT data for:

- 36 months of Spot data
- 36 months of USD-M Futures data
- 72 monthly ZIP archives in total

Official SHA-256 checksums were validated.

### Futures

```text
Rows:             1,578,240
Missing minutes:  0
```

### Spot

```text
Rows:             1,575,995
Missing minutes:  2,245
Missing segments: 14
Longest gap:      354 minutes
```

Missing candles were **not imputed**.

Additional checks covered:

- Duplicate timestamps
- Out-of-order observations
- Invalid OHLC relationships
- Negative/inconsistent volume
- Zero quote-volume candles
- Non-standard close timestamps
- Missing entries
- Delayed exits
- Unresolved exits
- Funding-window crossings

Seven spot rows with non-standard close timestamps were excluded from signal windows and preserved separately for audit.

---

## 🧪 Validation & Audit

The engine passed synthetic tests covering:

1. Signal causality and subset behavior
2. Entry delay, position locking, and fees
3. Missing exits and SHORT behavior
4. Common funding-window exclusion

Three intermediate prefix checks were also used to verify that signals generated on partial datasets remained consistent with the corresponding prefix of the full dataset.

Trade ledgers were checked for:

- Position overlap
- Signal-to-entry timing
- Expected holding duration

---

## 💸 Funding Handling

A common entry filter excludes trades whose maximum planned 30-minute holding period would reach the next scheduled UTC funding time:

```text
00:00
08:00
16:00
```

Entries occurring exactly at funding time are also excluded.

No accepted trade subsequently crossed a funding boundary due to delayed exit.

Funding was therefore not separately deducted from the resulting trade set.

---

## 🧠 Research Philosophy

A major goal of this project is to distinguish:

```text
finding a profitable-looking backtest
```

from:

```text
testing whether a predefined hypothesis survives realistic constraints
```

CF1 did not survive those constraints.

Instead of modifying the threshold or reversing the signal after seeing the results, the hypothesis was archived as a failed experiment.

That negative result is retained as part of the research record.

---

## 🗂️ Repository Contents

Key files include:

```text
run.py
test_engine.py
audit_detail.py
report.py
download.py

plan.json
frozen_plan.sha256
execution_audit.json
prefix_checks.json

performance.csv
attribution.csv
data_audit.csv

spot_missing_intervals.csv
spot_bad_close_times.csv

REPORT.md
00_PROJECT_STATUS.md
HANDOFF.md

figures/
```

### Important files

`plan.json`  
Frozen experimental configuration.

`frozen_plan.sha256`  
Digest used to preserve the predefined research plan.

`performance.csv`  
Performance results across direction, holding period, cost scenario, and year.

`attribution.csv`  
Supplementary spot-confirmation analysis.

`data_audit.csv`  
Dataset validation results.

`REPORT.md`  
Full research report and methodological details.

---

## ⚙️ Reproduction

The original research workflow was executed in this order:

```bash
python test_engine.py
python run.py
python audit_detail.py
python report.py
```

The original research package used Python 3 with:

```text
NumPy
pandas
matplotlib
```

Raw historical market archives are intentionally not included in this public repository.

Source metadata and dataset provenance are retained separately.

---

## 🚧 Current Limitations

This repository is a **research/backtesting project**, not a production trading bot.

It does not currently implement:

- Live order execution
- Exchange account API integration
- Wallet management
- Leverage execution
- Liquidation modeling
- Real measured Bitget slippage
- Real-time market-data collection
- Portfolio-level LONG/SHORT combination

Binance historical prices are used as a research proxy and should not be interpreted as guaranteed Bitget execution prices.

---

## 🔐 Holdout Discipline

The research period is limited to:

```text
Research:   2020–2022
Validation: 2023–2024 — SEALED
Final OOS:  2025+      — SEALED
```

The sealed periods were intentionally not used to rescue the failed CF1 hypothesis.

A future strategy would require independent validation before any live-trading consideration.

---

## 🤖 AI-Assisted Research & Development

AI coding tools were used throughout the project to assist with:

- Research architecture
- Python implementation
- Backtesting logic
- Test generation
- Data-quality auditing
- Experiment documentation
- Result analysis
- Iterative debugging

AI-generated code and research suggestions were treated as hypotheses and implementation inputs rather than accepted conclusions.

The final experiment was evaluated against predefined rules and retained even though the result was negative.

---

## 📌 Conclusion

CF1 tested whether simultaneous spot order-flow confirmation could strengthen a three-minute futures imbalance signal.

It did not.

Although the 15-minute LONG configuration showed a small gross improvement relative to the futures-only control, the effect was far below modeled transaction costs.

**Qualified strategies: 0**

CF1 is therefore closed in its current frozen form.

The broader systematic BTC research project remains experimental and requires a new independently defined hypothesis before further testing.
