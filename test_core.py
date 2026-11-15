from datetime import datetime, timedelta
from bot.candles import Candle, Aggregator
from bot.indicators import ema, sma, bollinger


def test_sma_ema():
    assert sma([1, 2, 3, 4], 2) == [None, 1.5, 2.5, 3.5]
    e = ema([1, 2, 3, 4, 5], 3)
    assert e[:2] == [None, None] and e[2] == 2 and abs(e[3] - 3) < 1e-9


def test_bollinger_flat():
    up, mid, lo = bollinger([5.0] * 25, 20, 2)
    assert up[-1] == mid[-1] == lo[-1] == 5.0 and up[18] is None


def test_aggregator_3m():
    t0, agg, out = datetime(2026, 11, 16, 9, 15), Aggregator(3), []
    for i in range(6):
        r = agg.push(Candle(t0 + timedelta(minutes=i), 10 + i, 20 + i, i, 11 + i, 100))
        if r: out.append(r)
    assert len(out) == 2
    assert (out[0].open, out[0].high, out[0].low, out[0].close, out[0].volume) == (10, 22, 0, 13, 300)
    assert out[1].ts.minute == 18
