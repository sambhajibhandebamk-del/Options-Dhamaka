"""Indicators on plain lists of floats. Each function returns a list the same
length as the input, with None until enough data exists."""
from math import sqrt


def ema(values, period):
    out, k, prev = [], 2 / (period + 1), None
    for i, v in enumerate(values):
        if i < period - 1:
            out.append(None)
        elif i == period - 1:
            prev = sum(values[:period]) / period  # seed with SMA (TradingView style)
            out.append(prev)
        else:
            prev = v * k + prev * (1 - k)
            out.append(prev)
    return out


def sma(values, period):
    return [None if i < period - 1 else sum(values[i - period + 1:i + 1]) / period
            for i in range(len(values))]


def bollinger(values, period=20, dev=2.0):
    """Returns (upper, middle, lower). Population std dev, as in TradingView."""
    mid = sma(values, period)
    up, lo = [], []
    for i, m in enumerate(mid):
        if m is None:
            up.append(None); lo.append(None)
            continue
        w = values[i - period + 1:i + 1]
        sd = sqrt(sum((x - m) ** 2 for x in w) / period)
        up.append(m + dev * sd)
        lo.append(m - dev * sd)
    return up, mid, lo
