"""Strategy 2 (3m engine). Feed closed 1m futures candles; it builds 3m candles itself.

CE: 3m close breaks above BB1 upper (fresh breakout) -> enter.
  Initial SL: 3m close below the BB middle line.
  After `confirm_candles` candles, if the trade is in favour (close above entry close),
  switch to ride mode: hold while close stays above BB1 upper (between BB1 and BB2, or beyond),
  exit when a close comes back inside BB1.
PE is the mirror image with the lower bands.
"""
from .candles import Aggregator
from .indicators import bollinger
from .paper import Trade

KEEP = 300


class _State:
    def __init__(self, tf):
        self.agg, self.closes, self.n = Aggregator(tf), [], {}  # n: bars since entry per trade


class Strategy2:
    name = "S2"

    def __init__(self, cfg, book, premium_fn):
        self.cfg, self.book, self.prem = cfg, book, premium_fn
        self.states, self.ride = {}, {}

    def on_candle(self, index, c1):
        st = self.states.setdefault(index, _State(self.cfg["timeframe"]))
        c = st.agg.push(c1)
        if c is None:
            return
        st.closes.append(c.close)
        del st.closes[:-KEEP]
        p, (d1, d2) = self.cfg["bb_period"], self.cfg["bb_devs"]
        if len(st.closes) < p + 1:
            return
        up1, mid, lo1 = (x for x in bollinger(st.closes, p, d1))
        if index in self.book.open:
            self._manage(index, c, up1[-1], mid[-1], lo1[-1])
            return
        if not self.book.can_open(index):
            return
        prev, cur = st.closes[-2], c.close
        side = None
        if cur > up1[-1] and prev <= up1[-2]:
            side = "CE"
        elif cur < lo1[-1] and prev >= lo1[-2]:
            side = "PE"
        if side:
            prem = self.prem(index, side, c.ts)
            self.book.open_trade(Trade(self.name, index, side, c.ts, cur, prem, "level", mid[-1]))
            self.ride[index] = {"bars": 0, "riding": False}

    def _manage(self, index, c, up1, mid, lo1):
        t, r = self.book.open[index], self.ride[index]
        ce = t.side == "CE"
        r["bars"] += 1
        if not r["riding"] and r["bars"] >= self.cfg["confirm_candles"]:
            in_favour = c.close > t.entry_fut if ce else c.close < t.entry_fut
            r["riding"] = in_favour
        reason = None
        if r["riding"]:
            if c.close < up1 if ce else c.close > lo1:
                reason = "BB1 ride exit"
        elif c.close < mid if ce else c.close > mid:
            reason = "Middle-line SL"
        if reason:
            self.book.close_trade(index, c.ts, c.close, self.prem(index, t.side, c.ts), reason)
            self.ride.pop(index, None)
