# Index Options Bot
Paper-trades index options (weekly ATM, monthly fallback) using two independent engines:
- **S1 (1m):** BB(20, 0.618) + price vs 21 EMA on 3m/5m/15m, volume > prior 5 candles
- **S2 (3m):** BB(20,1) / BB(20,2) band-ride
Each engine: max 3 open trades, one per index. Rules live in `bot/config.py`.
Data feed: Angel One SmartAPI. Live trading stays off (`PAPER_TRADING = True`).
Run tests: `python -m pytest -q`
APK: push to GitHub, open Actions > build-apk > download the `indexoptionsbot-apk` artifact (first build ~20-30 min).
