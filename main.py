"""Android dashboard (Kivy). Runs both paper engines on a DEMO feed until the
Angel One feed is connected. No real orders are ever placed."""
import random
from datetime import datetime, timedelta

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from bot.candles import Candle
from bot.config import INDICES, S1, S2, ATM_DELTA
from bot.paper import PaperBook
from bot.strategy1 import Strategy1
from bot.strategy2 import Strategy2

DEMO = INDICES[:4]


class BotApp(App):
    def build(self):
        self.px = {i: 20000.0 + 1000 * n for n, i in enumerate(DEMO)}
        self.start = dict(self.px)
        self.t, self.k = datetime(2026, 11, 16, 9, 15), 0
        prem = self.premium
        self.b1, self.b2 = PaperBook("S1", 3), PaperBook("S2", 3)
        self.e1 = Strategy1(S1, self.b1, prem, ATM_DELTA)
        self.e2 = Strategy2(S2, self.b2, prem)
        self.label = Label(text="starting...", size_hint_y=None, halign="left", valign="top")
        self.label.bind(texture_size=lambda w, s: setattr(w, "height", s[1]))
        self.label.bind(width=lambda w, s: setattr(w, "text_size", (s, None)))
        root = BoxLayout(orientation="vertical")
        sv = ScrollView(); sv.add_widget(self.label); root.add_widget(sv)
        Clock.schedule_interval(self.tick, 0.5)
        return root

    def premium(self, index, side, ts):
        d = (self.px[index] - self.start[index]) * ATM_DELTA
        return max(5.0, 150 + (d if side == "CE" else -d))

    def tick(self, dt):
        self.k += 1
        ts = self.t + timedelta(days=self.k // 375, minutes=self.k % 375)
        for i in DEMO:
            self.px[i] += random.gauss(0, 6) + (4 if (self.k // 120) % 2 else -4)
            p = self.px[i]
            c = Candle(ts, p, p + 5, p - 5, p + random.gauss(0, 3), random.randint(1, 100))
            self.e1.on_candle(i, c); self.e2.on_candle(i, c)
        self.label.text = self.report()

    def report(self):
        out = ["DEMO FEED - paper trades only\n"]
        for b in (self.b1, self.b2):
            pnl = sum(t.pnl for t in b.closed)
            out.append(f"[{b.engine}] open {len(b.open)}/3  closed {len(b.closed)}  P&L {pnl:.1f} pts")
            out += [f"  OPEN {t.index} {t.side} @ {t.entry_prem:.1f}" for t in b.open.values()]
            out += [f"  {t.index} {t.side} {t.pnl:+.1f}  {t.reason}" for t in b.closed[-5:]]
            out.append("")
        return "\n".join(out)


if __name__ == "__main__":
    BotApp().run()
