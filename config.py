"""All tunable rules in one place (both engines are independent)."""
INDICES = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]
EXPIRY_PRIORITY = ["weekly", "monthly"]
STRIKE = "ATM"
PAPER_TRADING = True

S1 = dict(  # 1m engine
    timeframe=1, bb_period=20, bb_dev=0.618, ema_period=21,
    ema_timeframes=[3, 5, 15], volume_lookback=5,
    max_sl_points=15,          # option premium, when 15m EMA is crossed
    sl_gap_limit=20,           # option premium; beyond this use 1m lower BB
    target_bb=dict(timeframe=15, period=20, dev=2.0),
    cross_mode="all",          # price + upper/middle/lower must all cross
    max_open_trades=3,         # one per index
)
S2 = dict(  # 3m engine
    timeframe=3, bb_period=20, bb_devs=(1.0, 2.0),
    confirm_candles=3, max_open_trades=3,
)

# Futures-gap -> option-premium conversion for the "20 point gap" rule (approx ATM delta)
ATM_DELTA = 0.5
