from datetime import datetime, timedelta
from bot.candles import Candle
from bot.config import S2
from bot.paper import PaperBook
from bot.strategy2 import Strategy2


def run(closes, side_prem=lambda i, s, ts: 100.0):
    book = PaperBook("S2", 3)
    eng = Strategy2(S2, book, side_prem)
    t = datetime(2026, 11, 16, 9, 15)
    for k, px in enumerate(closes):          # each value = one 3m candle (3 x 1m)
        for m in range(3):
            eng.on_candle("NIFTY", Candle(t, px, px, px, px, 1)); t += timedelta(minutes=1)
    return book


def base(): return [100 + (0.1 if i % 2 else -0.1) for i in range(20)]


def test_ride_then_exit():
    up = [103 + 3 * i for i in range(8)]
    book = run(base() + up + [100])
    assert len(book.closed) == 1 and book.closed[0].side == "CE"
    assert book.closed[0].reason == "BB1 ride exit"


def test_middle_line_sl():
    book = run(base() + [110, 100])
    assert book.closed[0].reason == "Middle-line SL"


def test_pe_mirror():
    book = run(base() + [90, 100])
    assert book.closed[0].side == "PE" and book.closed[0].reason == "Middle-line SL"
