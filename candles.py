"""1m candles -> 3m / 5m / 15m, aligned to the NSE session open (09:15)."""
from dataclasses import dataclass
from datetime import datetime

SESSION_OPEN_MIN = 9 * 60 + 15


@dataclass
class Candle:
    ts: datetime  # start time of the candle
    open: float
    high: float
    low: float
    close: float
    volume: float


def _bucket(ts, minutes):
    mod = ts.hour * 60 + ts.minute - SESSION_OPEN_MIN
    return mod // minutes, mod % minutes


class Aggregator:
    """Feed closed 1m candles with push(); returns a completed N-min candle or None."""

    def __init__(self, minutes):
        self.n, self.cur, self.cur_bucket = minutes, None, None

    def push(self, c):
        b, pos = _bucket(c.ts, self.n)
        done = None
        if self.cur is not None and b != self.cur_bucket:
            done, self.cur = self.cur, None  # missed last minute: flush
        if self.cur is None:
            start = c.ts.replace(minute=c.ts.minute - pos, second=0, microsecond=0)
            self.cur = Candle(start, c.open, c.high, c.low, c.close, c.volume)
            self.cur_bucket = b
        else:
            k = self.cur
            k.high, k.low = max(k.high, c.high), min(k.low, c.low)
            k.close, k.volume = c.close, k.volume + c.volume
        if pos == self.n - 1 and done is None:
            done, self.cur = self.cur, None
        return done
