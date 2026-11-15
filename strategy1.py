"""Strategy 1 (1m engine). Feed closed 1m futures candles per index via on_candle()."""
from .candles import Aggregator
from .indicators import bollinger, ema
from .paper import Trade

KEEP = 300  # candles kept per series


def rejection(c, band, side):
    """Candle touches the band and closes back inside, wick bigger than body."""
    body = abs(c.close - c.open)
    if side == "CE":
        return c.high >= band and c.close < band and (c.high - max(c.open, c.close)) > body
    return c.low <= band and c.close > band and (min(c.open, c.close) - c.low) > body


class _State:
    def __init__(self, tfs):
        self.c1, self.v1 = [], []
        self.aggs = {tf: Aggregator(tf) for tf in tfs}
        self.closes = {tf: [] for tf in tfs}
        self.prev = {}   # tf -> "up" / "down" / None, set once first evaluated


class Strategy1:
    name = "S1"

    def __init__(self, cfg, book, premium_fn, delta=0.5):
        self.cfg, self.book, self.prem, self.delta = cfg, book, premium_fn, delta
        self.states = {}

    # ---- helpers
    def _cross_states(self, price_lines, emas):
        out = {}
        for tf, e in emas.items():
            if e is None:
                out[tf] = None
            elif all(x > e for x in price_lines):
                out[tf] = "up"
            elif all(x < e for x in price_lines):
                out[tf] = "down"
            else:
                out[tf] = None
        return out

    def _stop(self, side, crossed_tf, c, emas, bb):
        up, _, lo = bb
        stop_tf = {3: 5, 5: 15}.get(crossed_tf)
        if stop_tf is None:  # 15m EMA crossed -> fixed premium stop
            return "premium", self.cfg["max_sl_points"]
        lvl = emas.get(stop_tf)
        fallback = lo if side == "CE" else up
        if lvl is None:
            return "level", fallback
        valid = lvl < c.close if side == "CE" else lvl > c.close
        gap_prem = abs(c.close - lvl) * self.delta
        if not valid or gap_prem > self.cfg["sl_gap_limit"]:
            return "level", fallback
        return "level", lvl

    # ---- main entry point
    def on_candle(self, index, c):
        cfg = self.cfg
        st = self.states.setdefault(index, _State(cfg["ema_timeframes"]))
        st.c1.append(c.close); st.v1.append(c.volume)
        for tf, agg in st.aggs.items():
            done = agg.push(c)
            if done:
                st.closes[tf].append(done.close)
        for s in (st.c1, st.v1, *st.closes.values()):
            del s[:-KEEP]
        if len(st.c1) < cfg["bb_period"]:
            return
        bb = tuple(x[-1] for x in bollinger(st.c1, cfg["bb_period"], cfg["bb_dev"]))
        emas = {tf: ema(st.closes[tf], cfg["ema_period"])[-1] if st.closes[tf] else None
                for tf in st.closes}
        tb = cfg["target_bb"]
        bb15 = bollinger(st.closes[tb["timeframe"]], tb["period"], tb["dev"]) \
            if len(st.closes[tb["timeframe"]]) >= tb["period"] else None
        bb15 = tuple(x[-1] for x in bb15) if bb15 else None

        if index in self.book.open:
            self._manage(index, c, bb, bb15)
        elif self.book.can_open(index):
            self._maybe_enter(index, st, c, bb, emas)
        # update cross states last so events compare against the previous candle
        st.prev = self._cross_states([c.close, *bb], emas)

    def _maybe_enter(self, index, st, c, bb, emas):
        now = self._cross_states([c.close, *bb], emas)
        look = self.cfg["volume_lookback"]
        if len(st.v1) <= look or not all(c.volume > v for v in st.v1[-look - 1:-1]):
            return
        for side, want in (("CE", "up"), ("PE", "down")):
            tfs = [tf for tf, s in now.items()
                   if s == want and tf in st.prev and st.prev[tf] != want]
            if not tfs:
                continue
            kind, level = self._stop(side, max(tfs), c, emas, bb)
            prem = self.prem(index, side, c.ts)
            sl = prem - level if kind == "premium" else level
            self.book.open_trade(Trade(self.name, index, side, c.ts, c.close, prem, kind, sl))
            return

    def _manage(self, index, c, bb, bb15):
        t = self.book.open[index]
        up, _, lo = bb
        ce = t.side == "CE"
        prem = self.prem(index, t.side, c.ts)
        reason = None
        if t.sl_kind == "premium" and prem <= t.sl_level:
            reason = "SL (premium)"
        elif t.sl_kind == "level" and (c.close < t.sl_level if ce else c.close > t.sl_level):
            reason = "SL (level)"
        elif c.close < lo if ce else c.close > up:
            reason = "1m BB exit"
        elif bb15 and rejection(c, bb15[0] if ce else bb15[2], t.side):
            reason = "15m BB target rejection"
        if reason:
            self.book.close_trade(index, c.ts, c.close, prem, reason)
