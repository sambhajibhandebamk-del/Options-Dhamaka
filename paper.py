"""Paper-trade book: one per engine, so the engines stay independent."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Trade:
    engine: str
    index: str
    side: str              # "CE" or "PE"
    entry_ts: object
    entry_fut: float
    entry_prem: float
    sl_kind: str           # "level" (futures price level) or "premium"
    sl_level: float        # futures level, or premium level when sl_kind == "premium"
    exit_ts: object = None
    exit_fut: Optional[float] = None
    exit_prem: Optional[float] = None
    reason: str = ""

    @property
    def pnl(self):  # premium points per unit (options are bought, so exit - entry)
        return None if self.exit_prem is None else self.exit_prem - self.entry_prem


class PaperBook:
    def __init__(self, engine, max_open=3):
        self.engine, self.max_open = engine, max_open
        self.open, self.closed = {}, []   # open keyed by index

    def can_open(self, index):
        return index not in self.open and len(self.open) < self.max_open

    def open_trade(self, trade):
        assert self.can_open(trade.index)
        self.open[trade.index] = trade

    def close_trade(self, index, ts, fut, prem, reason):
        t = self.open.pop(index)
        t.exit_ts, t.exit_fut, t.exit_prem, t.reason = ts, fut, prem, reason
        self.closed.append(t)
        return t
