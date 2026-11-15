import random
from datetime import datetime, timedelta
from bot.candles import Candle
from bot.config import S1
from bot.paper import PaperBook
from bot.strategy1 import Strategy1, rejection


def C(o, h, l, c): return Candle(datetime(2026, 11, 16, 9, 15), o, h, l, c, 1)


def test_rejection():
    assert rejection(C(100, 112, 99, 101), 110, "CE")        # long upper wick, closes inside
    assert not rejection(C(100, 112, 99, 111), 110, "CE")    # closes above band
    assert rejection(C(100, 101, 88, 99), 90, "PE")


def test_limits_and_smoke():
    random.seed(7)
    book = PaperBook("S1", 3)
    eng = Strategy1(S1, book, lambda i, s, ts: 100.0)
    t, px = datetime(2026, 11, 16, 9, 15), 20000.0
    for i in range(375 * 3):
        d = t + timedelta(days=i // 375, minutes=i % 375)
        px += random.gauss(0, 6) + (4 if (i // 120) % 2 else -4)
        for idx in ("NIFTY", "BANKNIFTY", "SENSEX", "FINNIFTY"):
            eng.on_candle(idx, Candle(d, px, px + 5, px - 5, px + random.gauss(0, 3), random.randint(1, 100)))
            assert len(book.open) <= 3
    assert len(book.closed) + len(book.open) > 0
    print("trades:", len(book.closed), {t.reason for t in book.closed})
