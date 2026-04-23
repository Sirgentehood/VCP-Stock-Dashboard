from __future__ import annotations
import argparse
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf

DEFAULT_CONFIG = {
    "market_index": "^NSEI", "period": "24mo", "min_history": 300, "swing_order_daily": 8, "swing_order_weekly": 3,
    "max_contractions": 4, "pivot_lookback_daily": 30, "pivot_lookback_weekly": 10, "volume_short_window": 10,
    "volume_long_window": 50, "market_ma_fast": 50, "market_ma_slow": 200, "breakout_volume_ratio": 1.8,
    "near_pivot_min_pct": -5.0, "near_pivot_max_pct": 1.5, "recent_range_days": 10, "recent_range_max_pct": 8.0,
    "min_avg_turnover_inr": 5e7, "industry_boost_top": 80.0, "industry_boost_mid": 60.0, "industry_boost_low": 40.0,
    "industry_boost_top_points": 10.0, "industry_boost_mid_points": 5.0, "industry_boost_low_points": 2.0,
    "min_contraction_days_daily": 5, "min_contraction_days_weekly": 2, "min_contraction_depth_pct_daily": 4.0,
    "min_contraction_depth_pct_weekly": 5.0, "min_base_duration_days": 30, "min_base_duration_weeks": 8,
    "max_latest_contraction_pct": 10.0, "min_weekly_strength_score": 0.45,
}

@dataclass
class MarketRegime:
    index_symbol: str
    last_close: float
    ma20: float
    ma50: float
    ma200: float
    slope20_pct: float
    slope50_pct: float
    slope200_pct: float
    ret_1m_pct: float
    ret_3m_pct: float
    drawdown_52w_pct: float
    above_20: bool
    above_50: bool
    above_200: bool
    breadth_above_20_pct: float
    breadth_above_50_pct: float
    breadth_above_200_pct: float
    breadth_stage2_pct: float
    trend_score: float
    breadth_score: float
    regime_label: str

@dataclass
class VCPScoreCard:
    ticker: str
    close: float
    ma50: float
    ma150: float
    ma200: float
    stage: str
    rs_3m_pct: float
    rs_6m_pct: float
    avg_turnover_inr: float
    daily_setup_bucket: str
    daily_score: float
    daily_pivot: float
    daily_breakout_distance_pct: float
    daily_contraction_depths_pct: List[float]
    daily_contraction_durations: List[int]
    daily_contraction_score: float
    daily_base_duration_days: float
    weekly_setup_bucket: str
    weekly_score: float
    weekly_pivot: float
    weekly_breakout_distance_pct: float
    weekly_contraction_depths_pct: List[float]
    weekly_contraction_durations: List[int]
    weekly_contraction_score: float
    weekly_base_duration_weeks: float
    weekly_vcp_quality: str
    combined_bucket: str
    combined_score: float
    volume_dryup_ratio: float
    breakout_volume_ratio: float
    volume_is_drying_up: bool
    weekly_volume_is_drying_up: bool
    notes: str

def load_nifty500_universe(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, sep=None, engine="python")
    df.columns = [c.strip() for c in df.columns]
    required = ["Company Name", "Industry", "Symbol", "Series", "ISIN Code"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in universe file: {missing}")
    for col in required:
        df[col] = df[col].astype(str).str.strip()
    df = df[df["Series"].str.upper() == "EQ"].copy()
    df["Symbol"] = df["Symbol"].str.upper()
    df["Ticker"] = df["Symbol"] + ".NS"
    df = df[df["Symbol"] != ""].drop_duplicates(subset=["Symbol"]).reset_index(drop=True)
    return df[["Company Name", "Industry", "Symbol", "Series", "ISIN Code", "Ticker"]]

def fetch_prices(tickers: List[str], period: str, interval: str = "1d", batch_size: int = 40) -> Dict[str, pd.DataFrame]:
    out: Dict[str, pd.DataFrame] = {}

    def parse_download(raw: pd.DataFrame, batch: List[str]) -> Dict[str, pd.DataFrame]:
        parsed: Dict[str, pd.DataFrame] = {}
        if len(batch) == 1:
            t = batch[0]
            df = raw.copy().rename(columns=str.title).dropna(how="all")
            if not df.empty:
                parsed[t] = df
            return parsed
        level0 = raw.columns.get_level_values(0)
        for t in batch:
            if t in level0:
                df = raw[t].copy().rename(columns=str.title).dropna(how="all")
                if not df.empty:
                    parsed[t] = df
        return parsed

    failed: List[str] = []
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        try:
            raw = yf.download(batch, period=period, interval=interval, auto_adjust=True, group_by="ticker", threads=False, progress=False)
            parsed = parse_download(raw, batch)
            out.update(parsed)
            failed.extend([t for t in batch if t not in parsed])
        except Exception:
            failed.extend(batch)
    for t in failed:
        try:
            df = yf.Ticker(t).history(period=period, interval=interval, auto_adjust=True)
            df = df.rename(columns=str.title).dropna(how="all")
            if not df.empty:
                out[t] = df
        except Exception:
            pass
    return out

def resample_weekly(df: pd.DataFrame) -> pd.DataFrame:
    weekly = pd.DataFrame()
    weekly["Open"] = df["Open"].resample("W-FRI").first()
    weekly["High"] = df["High"].resample("W-FRI").max()
    weekly["Low"] = df["Low"].resample("W-FRI").min()
    weekly["Close"] = df["Close"].resample("W-FRI").last()
    weekly["Volume"] = df["Volume"].resample("W-FRI").sum()
    return weekly.dropna(how="any")

def rolling_slope(series: pd.Series, window: int = 20) -> float:
    s = series.dropna()
    if len(s) < window:
        return np.nan
    y = s.iloc[-window:].values
    x = np.arange(window)
    return float(np.polyfit(x, y, 1)[0])

def pct_return(series: pd.Series, lookback: int) -> float:
    s = series.dropna()
    if len(s) <= lookback:
        return np.nan
    return float((s.iloc[-1] / s.iloc[-lookback] - 1) * 100)

def avg_turnover(close: pd.Series, volume: pd.Series, window: int = 20) -> float:
    if len(close) < window or len(volume) < window:
        return np.nan
    return float((close.iloc[-window:] * volume.iloc[-window:]).mean())

def volume_ratio(volume: pd.Series, short: int, long: int) -> float:
    if len(volume) < long:
        return np.nan
    short_avg = volume.iloc[-short:].mean()
    long_avg = volume.iloc[-long:].mean()
    if long_avg == 0:
        return np.nan
    return float(short_avg / long_avg)

def recent_breakout_volume_ratio(volume: pd.Series, window: int = 50) -> float:
    if len(volume) < window:
        return np.nan
    baseline = volume.iloc[-window:-1].mean()
    if baseline == 0:
        return np.nan
    return float(volume.iloc[-1] / baseline)


def slope_pct(series: pd.Series, window: int = 20) -> float:
    s = series.dropna()
    if len(s) < window:
        return np.nan
    level = float(np.nanmean(s.iloc[-window:].values))
    if level == 0:
        return np.nan
    return float(rolling_slope(s, window) / level)

def local_peaks_troughs(high: pd.Series, low: pd.Series, order: int) -> Tuple[List[int], List[int]]:
    high_arr = high.values
    low_arr = low.values
    peaks: List[int] = []
    troughs: List[int] = []
    for i in range(order, len(high_arr) - order):
        high_window = high_arr[i-order:i+order+1]
        low_window = low_arr[i-order:i+order+1]
        center_high = high_arr[i]
        center_low = low_arr[i]
        if np.isfinite(center_high) and center_high == np.max(high_window) and np.sum(high_window == center_high) == 1:
            peaks.append(i)
        if np.isfinite(center_low) and center_low == np.min(low_window) and np.sum(low_window == center_low) == 1:
            troughs.append(i)
    return peaks, troughs

def _candidate_contractions(high: pd.Series, low: pd.Series, order: int, min_duration_bars: int, min_depth_pct: float) -> List[Tuple[int, int, float, int]]:
    peaks, troughs = local_peaks_troughs(high, low, order=order)
    if not peaks or not troughs:
        return []

    pairs: List[Tuple[int, int, float, int]] = []
    for peak_idx, p in enumerate(peaks):
        next_peak = peaks[peak_idx + 1] if peak_idx + 1 < len(peaks) else len(high)
        valid_troughs = [t for t in troughs if p + min_duration_bars <= t < next_peak]
        if not valid_troughs:
            valid_troughs = [t for t in troughs if t > p and (t - p) >= min_duration_bars]
        if not valid_troughs:
            continue
        t = min(valid_troughs, key=lambda idx: float(low.iloc[idx]))
        peak_price = float(high.iloc[p])
        trough_price = float(low.iloc[t])
        if peak_price <= 0 or trough_price <= 0:
            continue
        depth = (peak_price - trough_price) / peak_price * 100
        duration = t - p
        if depth >= min_depth_pct:
            pairs.append((p, t, depth, duration))

    filtered: List[Tuple[int, int, float, int]] = []
    for pair in pairs:
        if not filtered:
            filtered.append(pair)
            continue
        prev = filtered[-1]
        if pair[0] <= prev[1]:
            if pair[2] < prev[2]:
                filtered[-1] = pair
            continue
        filtered.append(pair)
    return filtered

def detect_vcp_contractions(high: pd.Series, low: pd.Series, close: pd.Series, order: int, max_pairs: int, min_duration_bars: int, min_depth_pct: float) -> Tuple[List[float], List[int], float]:
    seq = extract_vcp_contraction_pairs(high, low, order=order, max_pairs=max_pairs, min_duration_bars=min_duration_bars, min_depth_pct=min_depth_pct)
    if not seq:
        return [], [], 0.0

    depths = [round(float(x[2]), 2) for x in seq]
    durations = [int(x[3]) for x in seq]
    base_duration = float(seq[-1][1] - seq[0][0])

    if len(seq) >= 2:
        highest_peak = float(high.iloc[seq[0][0]])
        lowest_trough = float(min(float(low.iloc[t]) for _, t, _, _ in seq))
        total_depth = (highest_peak - lowest_trough) / highest_peak * 100 if highest_peak > 0 else np.nan
        if np.isfinite(total_depth) and total_depth < min_depth_pct:
            return [], [], 0.0
    return depths, durations, base_duration

def contraction_score(depths: List[float]) -> float:
    if len(depths) < 2:
        return 0.0
    wins = sum(1 for i in range(1, len(depths)) if depths[i] <= depths[i-1] * 1.05)
    size_bonus = min(1.0, len(depths) / 4)
    return round((wins / (len(depths) - 1)) * 0.8 + size_bonus * 0.2, 4)

def extract_vcp_contraction_pairs(high: pd.Series, low: pd.Series, order: int, max_pairs: int, min_duration_bars: int, min_depth_pct: float) -> List[Tuple[int, int, float, int]]:
    pairs = _candidate_contractions(high, low, order=order, min_duration_bars=min_duration_bars, min_depth_pct=min_depth_pct)
    if not pairs:
        return []

    seq: List[Tuple[int, int, float, int]] = []
    for pair in pairs:
        if not seq:
            seq.append(pair)
            continue
        prev = seq[-1]
        prev_peak = float(high.iloc[prev[0]])
        curr_peak = float(high.iloc[pair[0]])
        depth_contracting = pair[2] <= prev[2] * 1.15
        price_tightening = curr_peak <= prev_peak * 1.10
        if depth_contracting and price_tightening:
            seq.append(pair)
        else:
            seq = [pair]
    return seq[-max_pairs:]


def _local_peak_indices(series: pd.Series, order: int = 3) -> List[int]:
    vals = series.values
    peaks: List[int] = []
    for i in range(order, len(vals) - order):
        window = vals[i - order:i + order + 1]
        center = vals[i]
        if np.isfinite(center) and center == np.max(window) and np.sum(window == center) == 1:
            peaks.append(i)
    return peaks


def compute_pivot_zone(
    high: pd.Series,
    lookback: int,
    base_duration: Optional[float] = None,
    *,
    is_weekly: bool = False,
    tolerance_pct: float = 1.5,
    min_band_pct: float = 0.35,
    max_band_pct: float = 2.0,
) -> Tuple[float, float, float]:
    if high.empty:
        return np.nan, np.nan, np.nan

    dynamic_window = lookback
    if base_duration and np.isfinite(base_duration) and base_duration > 0:
        dynamic_window = max(lookback, int(np.ceil(base_duration)) + (3 if is_weekly else 5))

    s = high.iloc[-dynamic_window:-1].dropna()
    if len(s) < 3:
        return np.nan, np.nan, np.nan

    order = 2 if is_weekly else 4
    peak_idx = _local_peak_indices(s, order=min(order, max(1, len(s) // 8)))
    if peak_idx:
        peak_vals = s.iloc[peak_idx].astype(float)
    else:
        peak_vals = s.nlargest(min(3, len(s))).sort_values()

    pivot_high = float(peak_vals.max())
    cluster_cutoff = pivot_high * (1 - tolerance_pct / 100)
    cluster = peak_vals[peak_vals >= cluster_cutoff]
    if cluster.empty:
        cluster = peak_vals.nlargest(1)

    zone_low = float(cluster.min())
    zone_high = float(cluster.max())

    min_width = pivot_high * (min_band_pct / 100)
    max_width = pivot_high * (max_band_pct / 100)
    width = zone_high - zone_low
    if width < min_width:
        pad = (min_width - width) / 2
        zone_low -= pad
        zone_high += pad
    elif width > max_width:
        zone_low = zone_high - max_width

    zone_low = max(0.0, zone_low)
    return float(zone_low), float(zone_high), float(zone_high)


def compute_pivot(high: pd.Series, lookback: int, base_duration: Optional[float] = None) -> float:
    _, _, pivot = compute_pivot_zone(high, lookback, base_duration=base_duration, is_weekly=False)
    return pivot

def classify_market_regime(score: float) -> str:
    if score >= 14:
        return "strong_risk_on"
    if score >= 8:
        return "risk_on"
    if score >= 3:
        return "mixed"
    if score >= -3:
        return "risk_off"
    return "strong_risk_off"


def compute_market_breadth(
    price_data: Dict[str, pd.DataFrame],
    universe_tickers: List[str],
) -> Dict[str, float]:
    above20 = above50 = above200 = eligible20 = eligible50 = eligible200 = 0
    stage2_count = stage_eligible = 0

    for ticker in universe_tickers:
        df = price_data.get(ticker)
        if df is None or df.empty or "Close" not in df.columns:
            continue

        close = df["Close"].dropna().astype(float)
        if len(close) >= 20:
            ma20 = float(close.rolling(20).mean().iloc[-1])
            if np.isfinite(ma20):
                eligible20 += 1
                if float(close.iloc[-1]) > ma20:
                    above20 += 1

        if len(close) >= 50:
            ma50 = float(close.rolling(50).mean().iloc[-1])
            if np.isfinite(ma50):
                eligible50 += 1
                if float(close.iloc[-1]) > ma50:
                    above50 += 1

        if len(close) >= 200:
            ma200 = float(close.rolling(200).mean().iloc[-1])
            if np.isfinite(ma200):
                eligible200 += 1
                if float(close.iloc[-1]) > ma200:
                    above200 += 1

        if len(close) >= 260:
            ma50 = float(close.rolling(50).mean().iloc[-1])
            ma150 = float(close.rolling(150).mean().iloc[-1])
            ma200 = float(close.rolling(200).mean().iloc[-1])
            stage = determine_stage(close, ma50, ma150, ma200)
            stage_eligible += 1
            if stage == "Stage 2":
                stage2_count += 1

    def pct(n: int, d: int) -> float:
        return round((n / d) * 100, 2) if d else np.nan

    return {
        "breadth_above_20_pct": pct(above20, eligible20),
        "breadth_above_50_pct": pct(above50, eligible50),
        "breadth_above_200_pct": pct(above200, eligible200),
        "breadth_stage2_pct": pct(stage2_count, stage_eligible),
    }


def market_regime(
    index_df: pd.DataFrame,
    index_symbol: str,
    ma_fast: int,
    ma_slow: int,
    price_data: Optional[Dict[str, pd.DataFrame]] = None,
    universe_tickers: Optional[List[str]] = None,
) -> MarketRegime:
    close = index_df["Close"].dropna().astype(float)
    if len(close) < 260:
        raise ValueError("Not enough index history to compute market regime")

    ma20_series = close.rolling(20).mean()
    ma50_series = close.rolling(ma_fast).mean()
    ma200_series = close.rolling(ma_slow).mean()

    last_close = float(close.iloc[-1])
    ma20 = float(ma20_series.iloc[-1])
    ma50 = float(ma50_series.iloc[-1])
    ma200 = float(ma200_series.iloc[-1])

    slope20_pct = slope_pct(ma20_series, 20)
    slope50_pct = slope_pct(ma50_series, 20)
    slope200_pct = slope_pct(ma200_series, 20)

    ret_1m_pct = pct_return(close, 21)
    ret_3m_pct = pct_return(close, 63)

    high_52w = float(close.iloc[-252:].max())
    drawdown_52w_pct = (last_close / high_52w - 1) * 100 if high_52w > 0 else np.nan

    above_20 = last_close > ma20 if pd.notna(ma20) else False
    above_50 = last_close > ma50 if pd.notna(ma50) else False
    above_200 = last_close > ma200 if pd.notna(ma200) else False

    breadth = {
        "breadth_above_20_pct": np.nan,
        "breadth_above_50_pct": np.nan,
        "breadth_above_200_pct": np.nan,
        "breadth_stage2_pct": np.nan,
    }
    if price_data is not None and universe_tickers:
        breadth = compute_market_breadth(price_data, universe_tickers)

    trend_score = 0.0

    if above_20:
        trend_score += 2
    else:
        trend_score -= 2

    if above_50:
        trend_score += 3
    else:
        trend_score -= 3

    if above_200:
        trend_score += 4
    else:
        trend_score -= 4

    if pd.notna(ma20) and pd.notna(ma50) and pd.notna(ma200):
        if ma20 > ma50 > ma200:
            trend_score += 4
        elif ma50 > ma200:
            trend_score += 2
        elif ma20 < ma50 < ma200:
            trend_score -= 4
        elif ma50 < ma200:
            trend_score -= 2

    if pd.notna(slope20_pct):
        if slope20_pct > 0.0010:
            trend_score += 2
        elif slope20_pct < -0.0010:
            trend_score -= 2

    if pd.notna(slope50_pct):
        if slope50_pct > 0.0005:
            trend_score += 2
        elif slope50_pct < -0.0005:
            trend_score -= 2

    if pd.notna(slope200_pct):
        if slope200_pct > 0.0001:
            trend_score += 2
        elif slope200_pct < -0.0001:
            trend_score -= 2

    if pd.notna(ret_1m_pct):
        if ret_1m_pct > 3:
            trend_score += 1
        elif ret_1m_pct < -3:
            trend_score -= 1

    if pd.notna(ret_3m_pct):
        if ret_3m_pct > 8:
            trend_score += 2
        elif ret_3m_pct < -8:
            trend_score -= 2

    if pd.notna(drawdown_52w_pct):
        if drawdown_52w_pct >= -5:
            trend_score += 2
        elif drawdown_52w_pct >= -10:
            trend_score += 1
        elif drawdown_52w_pct <= -30:
            trend_score -= 3
        elif drawdown_52w_pct <= -20:
            trend_score -= 2

    breadth_score = 0.0
    b20 = breadth["breadth_above_20_pct"]
    b50 = breadth["breadth_above_50_pct"]
    b200 = breadth["breadth_above_200_pct"]
    bstage2 = breadth["breadth_stage2_pct"]

    if pd.notna(b20):
        if b20 >= 70:
            breadth_score += 2
        elif b20 >= 55:
            breadth_score += 1
        elif b20 <= 35:
            breadth_score -= 1
        elif b20 <= 25:
            breadth_score -= 2

    if pd.notna(b50):
        if b50 >= 65:
            breadth_score += 3
        elif b50 >= 50:
            breadth_score += 1.5
        elif b50 <= 35:
            breadth_score -= 1.5
        elif b50 <= 25:
            breadth_score -= 3

    if pd.notna(b200):
        if b200 >= 60:
            breadth_score += 3
        elif b200 >= 45:
            breadth_score += 1.5
        elif b200 <= 30:
            breadth_score -= 1.5
        elif b200 <= 20:
            breadth_score -= 3

    if pd.notna(bstage2):
        if bstage2 >= 35:
            breadth_score += 2
        elif bstage2 >= 25:
            breadth_score += 1
        elif bstage2 <= 12:
            breadth_score -= 1
        elif bstage2 <= 7:
            breadth_score -= 2

    final_score = trend_score + breadth_score
    regime_label = classify_market_regime(final_score)

    return MarketRegime(
        index_symbol=index_symbol,
        last_close=round(last_close, 2),
        ma20=round(ma20, 2) if pd.notna(ma20) else np.nan,
        ma50=round(ma50, 2) if pd.notna(ma50) else np.nan,
        ma200=round(ma200, 2) if pd.notna(ma200) else np.nan,
        slope20_pct=round(float(slope20_pct), 6) if pd.notna(slope20_pct) else np.nan,
        slope50_pct=round(float(slope50_pct), 6) if pd.notna(slope50_pct) else np.nan,
        slope200_pct=round(float(slope200_pct), 6) if pd.notna(slope200_pct) else np.nan,
        ret_1m_pct=round(float(ret_1m_pct), 2) if pd.notna(ret_1m_pct) else np.nan,
        ret_3m_pct=round(float(ret_3m_pct), 2) if pd.notna(ret_3m_pct) else np.nan,
        drawdown_52w_pct=round(float(drawdown_52w_pct), 2) if pd.notna(drawdown_52w_pct) else np.nan,
        above_20=bool(above_20),
        above_50=bool(above_50),
        above_200=bool(above_200),
        breadth_above_20_pct=round(float(b20), 2) if pd.notna(b20) else np.nan,
        breadth_above_50_pct=round(float(b50), 2) if pd.notna(b50) else np.nan,
        breadth_above_200_pct=round(float(b200), 2) if pd.notna(b200) else np.nan,
        breadth_stage2_pct=round(float(bstage2), 2) if pd.notna(bstage2) else np.nan,
        trend_score=round(float(trend_score), 2),
        breadth_score=round(float(breadth_score), 2),
        regime_label=regime_label,
    )


def determine_stage(close: pd.Series, ma50: float, ma150: float, ma200: float) -> str:
    """
    Stage classifier tuned to reduce two recurring errors:
    - too many weak names getting stuck in Stage 3 instead of Stage 4
    - too many very-early base candidates getting left in Stage 3 instead of Stage 1

    Practical intent:
    - Stage 2 = confirmed advancing trend
    - Stage 4 = persistent decline or failed-rally weakness
    - Stage 1 = early/repairing base near long-term averages with tightening behaviour
    - Stage 3 = genuine transition/topping bucket, not the default for every ambiguous name
    """
    if len(close) < 260:
        return "Unknown"

    c = close.dropna().astype(float)
    if len(c) < 260:
        return "Unknown"

    last = float(c.iloc[-1])

    ma50_series = c.rolling(50).mean()
    ma150_series = c.rolling(150).mean()
    ma200_series = c.rolling(200).mean()

    ma50_now = float(ma50_series.iloc[-1]) if pd.notna(ma50_series.iloc[-1]) else float(ma50)
    ma150_now = float(ma150_series.iloc[-1]) if pd.notna(ma150_series.iloc[-1]) else float(ma150)
    ma200_now = float(ma200_series.iloc[-1]) if pd.notna(ma200_series.iloc[-1]) else float(ma200)

    ma50_slope = slope_pct(ma50_series, 20)
    ma150_slope = slope_pct(ma150_series, 20)
    ma200_slope = slope_pct(ma200_series, 20)

    weekly_close = c.resample("W-FRI").last().dropna()
    weekly_ma10 = weekly_close.rolling(10).mean()
    weekly_ma30 = weekly_close.rolling(30).mean()
    weekly_ma10_now = float(weekly_ma10.iloc[-1]) if len(weekly_ma10) and pd.notna(weekly_ma10.iloc[-1]) else np.nan
    weekly_ma30_now = float(weekly_ma30.iloc[-1]) if len(weekly_ma30) and pd.notna(weekly_ma30.iloc[-1]) else np.nan
    weekly_ma10_slope = slope_pct(weekly_ma10, 6)
    weekly_ma30_slope = slope_pct(weekly_ma30, 6)

    high_52w = float(c.iloc[-252:].max())
    low_52w = float(c.iloc[-252:].min())
    dist_from_high = (last / high_52w - 1) * 100 if high_52w > 0 else np.nan
    advance_from_low = (last / low_52w - 1) * 100 if low_52w > 0 else np.nan

    ret_4w = pct_return(c, 21)
    ret_8w = pct_return(c, 42)
    ret_13w = pct_return(c, 63)
    ret_26w = pct_return(c, 126)

    range_4w = ((c.iloc[-20:].max() / c.iloc[-20:].min()) - 1) * 100 if c.iloc[-20:].min() > 0 else np.nan
    range_8w = ((c.iloc[-40:].max() / c.iloc[-40:].min()) - 1) * 100 if c.iloc[-40:].min() > 0 else np.nan
    range_13w = ((c.iloc[-63:].max() / c.iloc[-63:].min()) - 1) * 100 if c.iloc[-63:].min() > 0 else np.nan
    range_26w = ((c.iloc[-126:].max() / c.iloc[-126:].min()) - 1) * 100 if c.iloc[-126:].min() > 0 else np.nan

    def _turning_points(series: pd.Series, order: int = 5) -> Tuple[List[int], List[int]]:
        vals = series.values
        peaks: List[int] = []
        troughs: List[int] = []
        for i in range(order, len(vals) - order):
            window = vals[i - order:i + order + 1]
            center = vals[i]
            if not np.isfinite(center):
                continue
            if center == np.max(window) and np.sum(window == center) == 1:
                peaks.append(i)
            if center == np.min(window) and np.sum(window == center) == 1:
                troughs.append(i)
        return peaks, troughs

    def _recent_structure(series: pd.Series, lookback: int = 90, order: int = 5) -> dict:
        s = series.iloc[-lookback:].copy()
        peaks, troughs = _turning_points(s, order=order)
        recent_peaks = [float(s.iloc[i]) for i in peaks[-3:]]
        recent_troughs = [float(s.iloc[i]) for i in troughs[-3:]]
        lower_highs = len(recent_peaks) >= 2 and all(recent_peaks[i] < recent_peaks[i - 1] for i in range(1, len(recent_peaks)))
        higher_highs = len(recent_peaks) >= 2 and all(recent_peaks[i] > recent_peaks[i - 1] for i in range(1, len(recent_peaks)))
        lower_lows = len(recent_troughs) >= 2 and all(recent_troughs[i] < recent_troughs[i - 1] for i in range(1, len(recent_troughs)))
        higher_lows = len(recent_troughs) >= 2 and all(recent_troughs[i] > recent_troughs[i - 1] for i in range(1, len(recent_troughs)))
        return {
            "lower_highs": lower_highs,
            "higher_highs": higher_highs,
            "lower_lows": lower_lows,
            "higher_lows": higher_lows,
            "peak_count": len(recent_peaks),
            "trough_count": len(recent_troughs),
        }

    structure = _recent_structure(c, lookback=90, order=5)
    lower_highs = structure["lower_highs"]
    higher_highs = structure["higher_highs"]
    lower_lows = structure["lower_lows"]
    higher_lows = structure["higher_lows"]

    ma_stack_bull = last > ma50_now > ma150_now > ma200_now
    ma_stack_bear = last < ma50_now < ma150_now < ma200_now

    above_50 = pd.notna(ma50_now) and last > ma50_now
    above_150 = pd.notna(ma150_now) and last > ma150_now
    above_200 = pd.notna(ma200_now) and last > ma200_now
    below_50 = pd.notna(ma50_now) and last < ma50_now
    below_150 = pd.notna(ma150_now) and last < ma150_now
    below_200 = pd.notna(ma200_now) and last < ma200_now

    ma50_rising = pd.notna(ma50_slope) and ma50_slope > 0.00045
    ma150_rising = pd.notna(ma150_slope) and ma150_slope > 0.00012
    ma200_rising = pd.notna(ma200_slope) and ma200_slope > 0.00003
    ma50_falling = pd.notna(ma50_slope) and ma50_slope < -0.00035
    ma150_falling = pd.notna(ma150_slope) and ma150_slope < -0.00012
    ma200_falling = pd.notna(ma200_slope) and ma200_slope < -0.00003
    ma200_flat = pd.notna(ma200_slope) and -0.00018 <= ma200_slope <= 0.00018

    weekly_bull = pd.notna(weekly_ma10_now) and pd.notna(weekly_ma30_now) and last > weekly_ma10_now > weekly_ma30_now
    weekly_bear = pd.notna(weekly_ma10_now) and pd.notna(weekly_ma30_now) and last < weekly_ma10_now < weekly_ma30_now
    weekly_10_rising = pd.notna(weekly_ma10_slope) and weekly_ma10_slope > 0.0006
    weekly_30_rising = pd.notna(weekly_ma30_slope) and weekly_ma30_slope > 0.00015
    weekly_10_falling = pd.notna(weekly_ma10_slope) and weekly_ma10_slope < -0.0006
    weekly_30_falling = pd.notna(weekly_ma30_slope) and weekly_ma30_slope < -0.00015

    # --- Stage 2: confirmed advancing structure ---
    stage2_score = 0
    if ma_stack_bull:
        stage2_score += 4
    if weekly_bull:
        stage2_score += 3
    if ma50_rising:
        stage2_score += 2
    if ma150_rising:
        stage2_score += 1
    if ma200_rising or ma200_flat:
        stage2_score += 1
    if weekly_10_rising:
        stage2_score += 1
    if weekly_30_rising:
        stage2_score += 1
    if pd.notna(ret_13w) and ret_13w > 8:
        stage2_score += 2
    if pd.notna(ret_26w) and ret_26w > 15:
        stage2_score += 2
    if pd.notna(dist_from_high) and dist_from_high >= -18:
        stage2_score += 2
    if pd.notna(advance_from_low) and advance_from_low >= 30:
        stage2_score += 1
    if higher_highs:
        stage2_score += 1
    if higher_lows:
        stage2_score += 2
    if stage2_score >= 13 and ma_stack_bull and weekly_bull and not lower_lows:
        return "Stage 2"

    # --- Stage 4: broadened to catch practical declines and failed-rally weakness ---
    weak_trend_cluster = sum([
        int(below_50),
        int(below_150),
        int(below_200),
        int(ma50_falling),
        int(ma150_falling),
        int(ma200_falling),
        int(weekly_10_falling),
        int(weekly_30_falling),
        int(lower_highs),
        int(lower_lows),
    ])

    stage4_score = 0
    if ma_stack_bear:
        stage4_score += 4
    if weekly_bear:
        stage4_score += 3
    if below_150 and below_200:
        stage4_score += 3
    if below_50 and below_150:
        stage4_score += 2
    if ma50_falling:
        stage4_score += 2
    if ma150_falling:
        stage4_score += 2
    if ma200_falling:
        stage4_score += 2
    if weekly_10_falling:
        stage4_score += 1
    if weekly_30_falling:
        stage4_score += 1
    if pd.notna(ret_8w) and ret_8w < -6:
        stage4_score += 1
    if pd.notna(ret_13w) and ret_13w < -8:
        stage4_score += 2
    if pd.notna(ret_26w) and ret_26w < -12:
        stage4_score += 2
    if pd.notna(dist_from_high) and dist_from_high <= -20:
        stage4_score += 2
    if pd.notna(dist_from_high) and dist_from_high <= -30:
        stage4_score += 2
    if lower_highs:
        stage4_score += 2
    if lower_lows:
        stage4_score += 2
    if pd.notna(range_13w) and range_13w > 22 and below_150:
        stage4_score += 1

    # Classic / strong Stage 4
    if stage4_score >= 10 and (
        (below_200 and (ma150_falling or ma200_falling or weekly_30_falling) and (lower_highs or weekly_bear))
        or (ma_stack_bear and weak_trend_cluster >= 5)
    ):
        return "Stage 4"

    # Early Stage 4 override: practical decline even before all long MAs fully roll over.
    early_stage4 = (
        below_50 and below_150
        and (ma50_falling or weekly_10_falling)
        and pd.notna(ret_13w) and ret_13w <= -8
        and pd.notna(dist_from_high) and dist_from_high <= -20
        and not higher_lows
    )
    if early_stage4:
        return "Stage 4"

    failed_rally_stage4 = (
        below_150 and (below_200 or ma200_falling or weekly_30_falling)
        and lower_highs and pd.notna(ret_8w) and ret_8w <= 0
        and pd.notna(dist_from_high) and dist_from_high <= -18
    )
    if failed_rally_stage4:
        return "Stage 4"

    near_ma150 = pd.notna(ma150_now) and 0.93 * ma150_now <= last <= 1.08 * ma150_now
    near_ma200 = pd.notna(ma200_now) and 0.93 * ma200_now <= last <= 1.08 * ma200_now
    near_long_term_ma = near_ma150 or near_ma200

    # --- Stage 1: allow very-early base candidates, but only if deterioration has stopped and ranges are tightening ---
    tightening_now = (
        pd.notna(range_4w) and pd.notna(range_8w) and pd.notna(range_13w)
        and range_4w <= range_8w * 0.90
        and range_8w <= range_13w * 0.92
    )
    early_base_zone = pd.notna(dist_from_high) and -45 <= dist_from_high <= -10
    off_the_lows = pd.notna(advance_from_low) and 8 <= advance_from_low <= 55
    not_broken_now = not (below_150 and below_200 and ma50_falling and (lower_highs or lower_lows))

    stage1_score = 0
    if near_long_term_ma:
        stage1_score += 3
    if ma200_flat:
        stage1_score += 2
    if pd.notna(ma150_slope) and -0.0002 <= ma150_slope <= 0.00035:
        stage1_score += 1
    if pd.notna(ma50_slope) and -0.00025 <= ma50_slope <= 0.00045:
        stage1_score += 1
    if pd.notna(range_4w) and range_4w <= 11:
        stage1_score += 2
    if pd.notna(range_8w) and range_8w <= 16:
        stage1_score += 2
    if pd.notna(range_13w) and range_13w <= 24:
        stage1_score += 2
    if pd.notna(range_26w) and range_26w <= 45:
        stage1_score += 1
    if tightening_now:
        stage1_score += 2
    if pd.notna(ret_13w) and -7 <= ret_13w <= 12:
        stage1_score += 1
    if pd.notna(ret_26w) and -20 <= ret_26w <= 18:
        stage1_score += 1
    if early_base_zone:
        stage1_score += 1
    if off_the_lows:
        stage1_score += 1
    if higher_lows:
        stage1_score += 2
    elif not lower_lows:
        stage1_score += 1
    if not lower_highs:
        stage1_score += 1

    stage1_confirmed = (
        stage1_score >= 10
        and near_long_term_ma
        and ma200_flat
        and not (lower_highs and lower_lows)
        and not (pd.notna(ret_13w) and ret_13w < -8)
        and not early_stage4
        and not failed_rally_stage4
    )
    if stage1_confirmed:
        return "Stage 1"

    # Early Stage 1 override for names just coming out of repair.
    early_stage1 = (
        near_long_term_ma
        and not_broken_now
        and (ma200_flat or (pd.notna(ma200_slope) and ma200_slope > -0.00008))
        and (higher_lows or tightening_now)
        and pd.notna(range_8w) and range_8w <= 18
        and pd.notna(ret_13w) and -10 <= ret_13w <= 10
        and early_base_zone
    )
    if early_stage1:
        return "Stage 1"

    return "Stage 3"

def vcp_quality_label(score: float, base_bars: float, depths: List[float], min_base_bars: int) -> str:
    if len(depths) < 2 or base_bars < min_base_bars:
        return "weak"
    return "strong" if score >= 0.66 else ("moderate" if score >= 0.5 else "weak")

def score_daily(stage: str, trend_template_ok: bool, regime_label: str, liquidity_ok: bool, near_pivot_ok: bool, breakout_today: bool, contraction_score_val: float, base_duration: float, dist_from_high: float, volume_dryup_ratio: float, breakout_volume_ratio: float, rs_3m: float, rs_6m: float) -> float:
    score = 0.0
    if trend_template_ok:
        score += 18

    if regime_label == "strong_risk_on":
        score += 12
    elif regime_label == "risk_on":
        score += 8
    elif regime_label == "mixed":
        score += 3
    elif regime_label == "risk_off":
        score -= 6
    elif regime_label == "strong_risk_off":
        score -= 12
    if liquidity_ok:
        score += 8
    if near_pivot_ok:
        score += 10
    if breakout_today:
        score += 8
    if stage == "Stage 2":
        score += 10
    elif stage == "Stage 1":
        score += 3
    score += max(0, min(18, contraction_score_val * 18))
    score += max(0, min(8, base_duration / 8))
    score += max(0, min(5, 15 + dist_from_high))
    if np.isfinite(volume_dryup_ratio):
        score += max(0, min(4, (1 - volume_dryup_ratio) * 10))
    if np.isfinite(breakout_volume_ratio):
        score += max(0, min(5, (breakout_volume_ratio - 1) * 4))
    rs_combo = np.nanmean([rs_3m, rs_6m])
    if np.isfinite(rs_combo):
        score += max(0, min(6, rs_combo / 5))
    return round(float(score), 2)

def score_weekly(stage: str, contraction_score_val: float, base_duration: float, weekly_breakout_distance_pct: float, weekly_quality: str, rs_3m: float, rs_6m: float) -> float:
    score = 0.0
    if stage == "Stage 2":
        score += 12
    elif stage == "Stage 1":
        score += 4
    score += max(0, min(22, contraction_score_val * 22))
    score += max(0, min(14, base_duration * 1.2))
    if np.isfinite(weekly_breakout_distance_pct) and -8 <= weekly_breakout_distance_pct <= 3:
        score += 8
    if weekly_quality == "strong":
        score += 12
    elif weekly_quality == "moderate":
        score += 6
    rs_combo = np.nanmean([rs_3m, rs_6m])
    if np.isfinite(rs_combo):
        score += max(0, min(8, rs_combo / 5))
    return round(float(score), 2)

def classify_daily_bucket(trend_template_ok: bool, daily_vcp_ok: bool, near_pivot_ok: bool, breakout_today: bool, tight_range_ok: bool, market_regime_ok: bool) -> str:
    if breakout_today and trend_template_ok and daily_vcp_ok and market_regime_ok:
        return "breakout_today"
    if trend_template_ok and daily_vcp_ok and near_pivot_ok and tight_range_ok:
        return "near_pivot"
    if trend_template_ok and daily_vcp_ok:
        return "forming_vcp"
    return "watchlist"

def classify_weekly_bucket(stage: str, weekly_vcp_ok: bool, weekly_breakout_distance_pct: float, weekly_quality: str) -> str:
    near_weekly_pivot = pd.notna(weekly_breakout_distance_pct) and -8 <= weekly_breakout_distance_pct <= 3
    if stage == "Stage 2" and weekly_vcp_ok and weekly_quality == "strong" and pd.notna(weekly_breakout_distance_pct) and weekly_breakout_distance_pct > 0:
        return "weekly_breakout"
    if stage == "Stage 2" and weekly_vcp_ok and near_weekly_pivot:
        return "weekly_near_pivot"
    if stage == "Stage 2" and weekly_vcp_ok:
        return "weekly_forming"
    return "weekly_watchlist"

def combined_bucket(daily_bucket: str, weekly_bucket: str) -> str:
    if daily_bucket == "breakout_today" and weekly_bucket in {"weekly_breakout", "weekly_near_pivot", "weekly_forming"}:
        return "high_conviction_breakout"
    if daily_bucket == "near_pivot" and weekly_bucket in {"weekly_near_pivot", "weekly_forming"}:
        return "high_conviction_near_pivot"
    if daily_bucket == "forming_vcp" and weekly_bucket in {"weekly_near_pivot", "weekly_forming"}:
        return "building_setup"
    return "watchlist"

def analyze_symbol(ticker: str, df: pd.DataFrame, benchmark_df: pd.DataFrame, regime: MarketRegime, config: dict) -> Optional[VCPScoreCard]:
    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(df.columns):
        return None

    df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"]).copy()
    if len(df) < config["min_history"]:
        return None

    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    volume = df["Volume"].astype(float)

    weekly_df = resample_weekly(df)
    if len(weekly_df) < 60:
        return None
    weekly_close = weekly_df["Close"].astype(float)
    weekly_high = weekly_df["High"].astype(float)
    weekly_low = weekly_df["Low"].astype(float)

    close_now = float(close.iloc[-1])
    ma50 = float(close.rolling(50).mean().iloc[-1])
    ma150 = float(close.rolling(150).mean().iloc[-1])
    ma200 = float(close.rolling(200).mean().iloc[-1])
    ma50_series = close.rolling(50).mean()
    ma150_series = close.rolling(150).mean()
    ma200_series = close.rolling(200).mean()
    stage = determine_stage(close, ma50, ma150, ma200)

    high_52w = float(close.iloc[-252:].max())
    low_52w = float(close.iloc[-252:].min())
    dist_from_high = (close_now / high_52w - 1) * 100 if high_52w > 0 else np.nan
    advance_from_low = (close_now / low_52w - 1) * 100 if low_52w > 0 else np.nan

    ma50_slope_pct = slope_pct(ma50_series, 20)
    ma150_slope_pct = slope_pct(ma150_series, 20)
    ma200_slope_pct = slope_pct(ma200_series, 20)
    weekly_ma10 = float(weekly_close.rolling(10).mean().iloc[-1]) if len(weekly_close) >= 10 else np.nan
    weekly_ma30 = float(weekly_close.rolling(30).mean().iloc[-1]) if len(weekly_close) >= 30 else np.nan

    market_regime_ok = regime.regime_label in {"strong_risk_on", "risk_on", "mixed"}

    daily_window = df.iloc[-140:]
    daily_depths, daily_durations, daily_base_duration = detect_vcp_contractions(
        daily_window["High"], daily_window["Low"], daily_window["Close"],
        config["swing_order_daily"], config["max_contractions"],
        config["min_contraction_days_daily"], config["min_contraction_depth_pct_daily"]
    )
    daily_contraction_score_val = contraction_score(daily_depths)

    weekly_window = weekly_df.iloc[-52:]
    weekly_depths, weekly_durations, weekly_base_duration = detect_vcp_contractions(
        weekly_window["High"], weekly_window["Low"], weekly_window["Close"],
        config["swing_order_weekly"], config["max_contractions"],
        config["min_contraction_days_weekly"], config["min_contraction_depth_pct_weekly"]
    )
    weekly_contraction_score_val = contraction_score(weekly_depths)
    weekly_quality = vcp_quality_label(
        weekly_contraction_score_val, weekly_base_duration, weekly_depths, config["min_base_duration_weeks"]
    )

    volume_dryup_ratio = volume_ratio(volume, config["volume_short_window"], config["volume_long_window"])
    weekly_volume_dryup_ratio = volume_ratio(weekly_df["Volume"].astype(float), 4, 12) if len(weekly_df) >= 12 else np.nan
    breakout_volume_ratio = recent_breakout_volume_ratio(volume, config["volume_long_window"])
    avg_turnover_inr = avg_turnover(close, volume, 20)
    liquidity_ok = pd.notna(avg_turnover_inr) and avg_turnover_inr >= config["min_avg_turnover_inr"]

    stock_3m = pct_return(close, 63)
    stock_6m = pct_return(close, 126)
    bm_3m = pct_return(benchmark_df["Close"], 63)
    bm_6m = pct_return(benchmark_df["Close"], 126)
    rs_3m = stock_3m - bm_3m if pd.notna(stock_3m) and pd.notna(bm_3m) else np.nan
    rs_6m = stock_6m - bm_6m if pd.notna(stock_6m) and pd.notna(bm_6m) else np.nan
    rs_combo = np.nanmean([rs_3m, rs_6m])

    daily_pivot = compute_pivot(high, config["pivot_lookback_daily"], daily_base_duration)
    daily_breakout_distance = (close_now / daily_pivot - 1) * 100 if pd.notna(daily_pivot) and daily_pivot > 0 else np.nan
    weekly_pivot = compute_pivot(weekly_high, config["pivot_lookback_weekly"], weekly_base_duration)
    weekly_breakout_distance = (float(weekly_close.iloc[-1]) / weekly_pivot - 1) * 100 if pd.notna(weekly_pivot) and weekly_pivot > 0 else np.nan

    recent_range_pct = (
        (close.iloc[-config["recent_range_days"]:].max() - close.iloc[-config["recent_range_days"]:].min()) /
        close.iloc[-config["recent_range_days"]:].max() * 100
    ) if len(close) >= config["recent_range_days"] else np.nan
    tight_range_ok = pd.notna(recent_range_pct) and recent_range_pct <= config["recent_range_max_pct"]

    price_above_ma50 = close_now > ma50
    price_above_ma150 = close_now > ma150
    price_above_ma200 = close_now > ma200
    ma_stack_bull = close_now > ma50 > ma150 > ma200
    ma_stack_bear = close_now < ma50 < ma150 < ma200

    weekly_range_12w = ((weekly_close.iloc[-12:].max() / weekly_close.iloc[-12:].min()) - 1) * 100 if len(weekly_close) >= 12 and weekly_close.iloc[-12:].min() > 0 else np.nan
    weekly_range_20w = ((weekly_close.iloc[-20:].max() / weekly_close.iloc[-20:].min()) - 1) * 100 if len(weekly_close) >= 20 and weekly_close.iloc[-20:].min() > 0 else np.nan
    recent_low_6w = float(low.iloc[-30:].min()) if len(low) >= 30 else np.nan
    no_recent_breakdown = pd.notna(recent_low_6w) and close_now >= recent_low_6w * 1.03

    stage2_trend_template = (
        stage == "Stage 2"
        and ma_stack_bull
        and pd.notna(ma50_slope_pct) and ma50_slope_pct > 0.0005
        and pd.notna(ma150_slope_pct) and ma150_slope_pct >= 0
        and pd.notna(ma200_slope_pct) and ma200_slope_pct >= -0.00015
        and pd.notna(dist_from_high) and dist_from_high >= -18
        and pd.notna(advance_from_low) and advance_from_low >= 30
        and pd.notna(rs_combo) and rs_combo >= 0
    )

    stage1_base_ready = (
        stage == "Stage 1"
        and pd.notna(ma200_slope_pct) and -0.00035 <= ma200_slope_pct <= 0.00035
        and pd.notna(ma150_slope_pct) and ma150_slope_pct >= -0.00035
        and price_above_ma150
        and price_above_ma200
        and pd.notna(dist_from_high) and -30 <= dist_from_high <= -3
        and pd.notna(weekly_range_12w) and weekly_range_12w <= 20
        and pd.notna(weekly_range_20w) and weekly_range_20w <= 35
        and pd.notna(rs_combo) and rs_combo >= -5
        and no_recent_breakdown
        and not ma_stack_bear
    )

    strong_daily_vcp = (
        len(daily_depths) >= 2
        and daily_base_duration >= config["min_base_duration_days"]
        and daily_contraction_score_val >= 0.60
        and daily_depths[-1] <= min(config["max_latest_contraction_pct"], 8.0)
        and pd.notna(volume_dryup_ratio) and volume_dryup_ratio <= 0.90
    )
    strict_stage1_daily_vcp = (
        strong_daily_vcp
        and daily_depths[0] <= 30
        and max(daily_depths) <= 30
        and pd.notna(daily_breakout_distance) and -4.0 <= daily_breakout_distance <= 1.5
        and tight_range_ok
    )
    weekly_vcp_ok = (
        len(weekly_depths) >= 2
        and weekly_base_duration >= config["min_base_duration_weeks"]
        and weekly_contraction_score_val >= max(config["min_weekly_strength_score"], 0.55)
        and weekly_quality in {"strong", "moderate"}
    )

    near_pivot_stage2_ok = (
        pd.notna(daily_breakout_distance)
        and -5.0 <= daily_breakout_distance <= 1.5
        and tight_range_ok
        and pd.notna(breakout_volume_ratio) and breakout_volume_ratio >= 0.85
    )
    near_pivot_stage1_ok = (
        pd.notna(daily_breakout_distance)
        and -3.0 <= daily_breakout_distance <= 1.0
        and tight_range_ok
        and pd.notna(volume_dryup_ratio) and volume_dryup_ratio <= 0.90
        and no_recent_breakdown
    )
    near_pivot_ok = near_pivot_stage2_ok if stage == "Stage 2" else near_pivot_stage1_ok if stage == "Stage 1" else False

    breakout_today = bool(
        pd.notna(daily_breakout_distance)
        and daily_breakout_distance > 0
        and pd.notna(breakout_volume_ratio)
        and breakout_volume_ratio >= config["breakout_volume_ratio"]
        and stage2_trend_template
        and strong_daily_vcp
    )

    daily_vcp_ok = strong_daily_vcp if stage == "Stage 2" else strict_stage1_daily_vcp if stage == "Stage 1" else False
    trend_template_ok = stage2_trend_template

    if stage == "Stage 1" and (not stage1_base_ready or not strict_stage1_daily_vcp):
        daily_bucket = "watchlist"
    else:
        daily_bucket = classify_daily_bucket(
            trend_template_ok if stage == "Stage 2" else False,
            daily_vcp_ok,
            near_pivot_ok,
            breakout_today,
            tight_range_ok,
            market_regime_ok,
        )
        if stage == "Stage 1" and daily_bucket == "building_setup":
            daily_bucket = "watchlist"

    weekly_bucket = classify_weekly_bucket(stage, weekly_vcp_ok, weekly_breakout_distance, weekly_quality)
    if stage == "Stage 1" and (not stage1_base_ready or not weekly_vcp_ok):
        weekly_bucket = "weekly_watchlist"

    daily_score = score_daily(
        stage,
        trend_template_ok,
        regime.regime_label,
        liquidity_ok,
        near_pivot_ok,
        breakout_today,
        daily_contraction_score_val,
        daily_base_duration,
        dist_from_high,
        volume_dryup_ratio,
        breakout_volume_ratio,
        rs_3m,
        rs_6m,
    )
    weekly_score = score_weekly(
        stage,
        weekly_contraction_score_val,
        weekly_base_duration,
        weekly_breakout_distance,
        weekly_quality,
        rs_3m,
        rs_6m,
    )

    if stage == "Stage 1":
        if not stage1_base_ready:
            daily_score -= 12
            weekly_score -= 8
        elif not strict_stage1_daily_vcp:
            daily_score -= 8
            weekly_score -= 5
        if breakout_today:
            daily_score -= 8
        if pd.notna(daily_breakout_distance) and daily_breakout_distance > 0:
            daily_score -= 3

    if stage == "Stage 3":
        daily_score -= 8
        weekly_score -= 6
    elif stage == "Stage 4":
        daily_score -= 12
        weekly_score -= 10

    daily_score = round(float(max(0.0, daily_score)), 2)
    weekly_score = round(float(max(0.0, weekly_score)), 2)

    combo_bucket = combined_bucket(daily_bucket, weekly_bucket)
    combined_score = round(0.55 * daily_score + 0.45 * weekly_score, 2)

    volume_is_drying_up = bool(pd.notna(volume_dryup_ratio) and volume_dryup_ratio <= 0.85)
    weekly_volume_is_drying_up = bool(pd.notna(weekly_volume_dryup_ratio) and weekly_volume_dryup_ratio <= 0.90)

    notes = [stage]
    if trend_template_ok:
        notes.append("trend_template_ok")
    if stage1_base_ready:
        notes.append("stage1_base_ready")
    if daily_vcp_ok:
        notes.append("daily_vcp_ok")
    if weekly_vcp_ok:
        notes.append("weekly_vcp_ok")
    if volume_is_drying_up:
        notes.append("volume_dryup")
    if weekly_volume_is_drying_up:
        notes.append("weekly_volume_dryup")
    if breakout_today:
        notes.append("daily_breakout_volume")
    if weekly_quality == "strong":
        notes.append("weekly_strong")
    if stage == "Stage 1" and not strict_stage1_daily_vcp:
        notes.append("stage1_not_actionable")
    if stage == "Stage 1" and not stage1_base_ready:
        notes.append("stage1_needs_more_base")
    if stage == "Stage 3":
        notes.append("distribution_risk")
    if stage == "Stage 4":
        notes.append("downtrend")

    return VCPScoreCard(
        ticker, round(close_now, 2), round(ma50, 2), round(ma150, 2), round(ma200, 2), stage,
        round(float(rs_3m), 2) if pd.notna(rs_3m) else np.nan,
        round(float(rs_6m), 2) if pd.notna(rs_6m) else np.nan,
        round(float(avg_turnover_inr), 2) if pd.notna(avg_turnover_inr) else np.nan,
        daily_bucket, daily_score, round(float(daily_pivot), 2) if pd.notna(daily_pivot) else np.nan,
        round(float(daily_breakout_distance), 2) if pd.notna(daily_breakout_distance) else np.nan,
        daily_depths, daily_durations, round(float(daily_contraction_score_val), 2), round(float(daily_base_duration), 2),
        weekly_bucket, weekly_score, round(float(weekly_pivot), 2) if pd.notna(weekly_pivot) else np.nan,
        round(float(weekly_breakout_distance), 2) if pd.notna(weekly_breakout_distance) else np.nan,
        weekly_depths, weekly_durations, round(float(weekly_contraction_score_val), 2), round(float(weekly_base_duration), 2),
        weekly_quality, combo_bucket, combined_score,
        round(float(volume_dryup_ratio), 2) if pd.notna(volume_dryup_ratio) else np.nan,
        round(float(breakout_volume_ratio), 2) if pd.notna(breakout_volume_ratio) else np.nan,
        volume_is_drying_up,
        weekly_volume_is_drying_up,
        ", ".join(notes),
    )

def build_vcp_universe_report(tickers: List[str], config: Optional[dict] = None) -> Tuple[pd.DataFrame, MarketRegime]:
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    full_tickers = list(dict.fromkeys(tickers + [cfg["market_index"]]))
    data = fetch_prices(full_tickers, cfg["period"], interval="1d")
    if cfg["market_index"] not in data:
        raise RuntimeError(f"Missing market index data for {cfg['market_index']}")
    benchmark_df = data[cfg["market_index"]]
    regime = market_regime(
        benchmark_df,
        cfg["market_index"],
        cfg["market_ma_fast"],
        cfg["market_ma_slow"],
        price_data=data,
        universe_tickers=tickers,
    )

    rows = []
    for ticker in tickers:
        df = data.get(ticker)
        if df is None or df.empty:
            continue
        try:
            result = analyze_symbol(ticker, df, benchmark_df, regime, cfg)
            if result:
                rows.append(asdict(result))
        except Exception as exc:
            rows.append({"ticker": ticker, "combined_score": -1, "combined_bucket": "error", "notes": f"error: {exc}"})

    out = pd.DataFrame(rows)
    if out.empty:
        return out, regime
    order = {"high_conviction_breakout": 0, "high_conviction_near_pivot": 1, "building_setup": 2, "watchlist": 3, "error": 4}
    out["bucket_order"] = out["combined_bucket"].map(order).fillna(99)
    out = out.sort_values(["bucket_order", "combined_score", "daily_score", "weekly_score"], ascending=[True, False, False, False]).drop(columns=["bucket_order"])
    return out.reset_index(drop=True), regime

def build_industry_strength_table(df: pd.DataFrame) -> pd.DataFrame:
    summary = df.groupby("Industry").agg(
        avg_rs_3m=("rs_3m_pct", "mean"),
        avg_rs_6m=("rs_6m_pct", "mean"),
        avg_daily_score=("daily_score", "mean"),
        avg_weekly_score=("weekly_score", "mean"),
        avg_combined_score=("combined_score", "mean"),
        stock_count=("ticker", "count"),
        actionable_daily=("daily_setup_bucket", lambda x: x.isin(["near_pivot", "breakout_today"]).sum()),
        actionable_weekly=("weekly_setup_bucket", lambda x: x.isin(["weekly_near_pivot", "weekly_breakout"]).sum()),
        strong_combined=("combined_bucket", lambda x: x.isin(["high_conviction_breakout", "high_conviction_near_pivot"]).sum()),
    ).reset_index()
    summary["rs_score"] = summary[["avg_rs_3m", "avg_rs_6m"]].mean(axis=1)
    summary["rs_rank"] = summary["rs_score"].rank(pct=True, method="average") * 100
    return summary.sort_values(["avg_combined_score", "rs_rank", "strong_combined"], ascending=[False, False, False]).reset_index(drop=True)

def apply_industry_boost(report_df: pd.DataFrame, industry_df: pd.DataFrame, config: Optional[dict] = None) -> pd.DataFrame:
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    df = report_df.merge(industry_df[["Industry", "rs_rank"]], on="Industry", how="left")

    def boost(industry_rank: float) -> float:
        if pd.isna(industry_rank):
            return 0.0
        if industry_rank >= cfg["industry_boost_top"]:
            return cfg["industry_boost_top_points"]
        if industry_rank >= cfg["industry_boost_mid"]:
            return cfg["industry_boost_mid_points"]
        if industry_rank >= cfg["industry_boost_low"]:
            return cfg["industry_boost_low_points"]
        return 0.0

    df["industry_boost"] = df["rs_rank"].apply(boost)
    df["final_daily_score"] = (df["daily_score"] + 0.5 * df["industry_boost"]).round(2)
    df["final_weekly_score"] = (df["weekly_score"] + 0.5 * df["industry_boost"]).round(2)
    df["final_combined_score"] = (df["combined_score"] + df["industry_boost"]).round(2)
    return df.sort_values(["final_combined_score", "final_daily_score", "final_weekly_score"], ascending=[False, False, False]).reset_index(drop=True)

def sanitize_filename(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in name)

def export_chart(df: pd.DataFrame, symbol: str, title: str, outfile: Path, pivot: Optional[float], setup_bucket: str, score: float, stage: str, is_weekly: bool = False) -> None:
    if df.empty:
        return

    target_display_bars = 180 if not is_weekly else 104
    fast_window = 10 if is_weekly else 50
    slow_window = 30 if is_weekly else 200
    min_visible_bars = 55 if is_weekly else 120
    history_buffer = target_display_bars + slow_window + (20 if is_weekly else 60)

    working_df = df.copy().tail(history_buffer).copy()
    if working_df.empty:
        return

    close_all = working_df["Close"].astype(float)
    ma_fast_all = close_all.rolling(fast_window).mean()
    ma_slow_all = close_all.rolling(slow_window).mean()

    default_start_idx = max(0, len(working_df) - target_display_bars)

    def _first_full_window_start(series: pd.Series, target_len: int) -> Optional[int]:
        valid = np.where(series.notna().values)[0]
        if len(valid) == 0:
            return None
        first_valid = int(valid[0])
        if len(series) - first_valid >= target_len:
            return first_valid
        return None

    visible_bars = target_display_bars
    start_idx = default_start_idx

    # Ensure the selected moving averages are visible across the full plotted window.
    if is_weekly:
        max_bars_with_slow = len(working_df) - slow_window + 1
        if max_bars_with_slow > 0:
            visible_bars = min(target_display_bars, max(max_bars_with_slow, min_visible_bars))
            start_idx = max(0, len(working_df) - visible_bars)
        else:
            visible_bars = min(target_display_bars, len(working_df))
            start_idx = max(0, len(working_df) - visible_bars)
    else:
        slow_full_start = _first_full_window_start(ma_slow_all, target_display_bars)
        fast_full_start = _first_full_window_start(ma_fast_all, target_display_bars)
        if slow_full_start is not None:
            start_idx = max(default_start_idx, slow_full_start)
        elif fast_full_start is not None:
            start_idx = max(default_start_idx, fast_full_start)

    plot_df = working_df.iloc[start_idx:].copy()
    if plot_df.empty:
        return

    close = plot_df["Close"].astype(float)
    high = plot_df["High"].astype(float)
    low = plot_df["Low"].astype(float)
    volume = plot_df["Volume"].astype(float)
    x = plot_df.index

    ma_fast = ma_fast_all.iloc[start_idx:].copy()
    ma_slow = ma_slow_all.iloc[start_idx:].copy()

    if ma_fast.notna().sum() < len(plot_df):
        ma_fast = None
    if ma_slow.notna().sum() < len(plot_df):
        ma_slow = None

    pair_seq = extract_vcp_contraction_pairs(
        high,
        low,
        order=DEFAULT_CONFIG["swing_order_weekly"] if is_weekly else DEFAULT_CONFIG["swing_order_daily"],
        max_pairs=DEFAULT_CONFIG["max_contractions"],
        min_duration_bars=DEFAULT_CONFIG["min_contraction_days_weekly"] if is_weekly else DEFAULT_CONFIG["min_contraction_days_daily"],
        min_depth_pct=DEFAULT_CONFIG["min_contraction_depth_pct_weekly"] if is_weekly else DEFAULT_CONFIG["min_contraction_depth_pct_daily"],
    )
    base_duration = float(pair_seq[-1][1] - pair_seq[0][0]) if pair_seq else np.nan
    pivot_low, pivot_high, _ = compute_pivot_zone(
        high,
        DEFAULT_CONFIG["pivot_lookback_weekly"] if is_weekly else DEFAULT_CONFIG["pivot_lookback_daily"],
        base_duration=base_duration,
        is_weekly=is_weekly,
        min_band_pct=1.6 if is_weekly else 1.15,
        max_band_pct=4.8 if is_weekly else 3.6,
    )

    plt.rcParams.update({
        "font.size": 42,
        "axes.titlesize": 51,
        "axes.labelsize": 42,
        "xtick.labelsize": 36,
        "ytick.labelsize": 36,
        "legend.fontsize": 33,
    })

    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(34, 22),
        sharex=True,
        gridspec_kw={"height_ratios": [4.8, 1.0]},
    )

    ax1.plot(x, close.values, label="Close", linewidth=5.0)
    if ma_fast is not None:
        ax1.plot(x, ma_fast.values, label=("10W MA" if is_weekly else "50DMA"), linewidth=3.8, alpha=0.96)
    if ma_slow is not None:
        ax1.plot(x, ma_slow.values, label=("30W MA" if is_weekly else "200DMA"), linewidth=3.5, alpha=0.92)

    if pd.notna(pivot_low) and pd.notna(pivot_high):
        ax1.axhspan(float(pivot_low), float(pivot_high), alpha=0.22, label="Pivot zone")
        ax1.axhline(float(pivot_low), linestyle="--", linewidth=1.8, alpha=0.40)
        ax1.axhline(float(pivot_high), linestyle="--", linewidth=1.8, alpha=0.40)

    suffix = "W" if is_weekly else "D"
    y_span = float(high.max() - low.min()) if np.isfinite(high.max()) and np.isfinite(low.min()) else 0.0
    if y_span <= 0:
        y_span = max(float(high.max()) * 0.08, 1.0)

    base_label_gap = y_span * (0.065 if is_weekly else 0.045)
    horizontal_step = 2 if is_weekly else 4
    placed = []

    def _find_label_slot(bar_idx: int, anchor_y: float):
        candidates = []
        for level in range(0, 8):
            if level == 0:
                candidates.append((0, 0))
            else:
                direction = -1 if level % 2 else 1
                magnitude = (level + 1) // 2
                candidates.append((direction * magnitude * horizontal_step, direction * magnitude * base_label_gap))

        best = None
        best_penalty = None
        for x_shift, y_shift in candidates:
            cand_idx = min(max(bar_idx + x_shift, 0), len(x) - 1)
            cand_y = anchor_y + y_shift
            penalty = abs(x_shift) * 0.9 + abs(y_shift) / max(base_label_gap, 1e-9)
            overlap = False
            for prev_idx, prev_y in placed:
                if abs(cand_idx - prev_idx) <= (3 if is_weekly else 6) and abs(cand_y - prev_y) < base_label_gap * 0.90:
                    overlap = True
                    penalty += 100
                    break
            if not overlap:
                return cand_idx, cand_y
            if best is None or penalty < best_penalty:
                best = (cand_idx, cand_y)
                best_penalty = penalty
        return best if best is not None else (bar_idx, anchor_y)

    for peak_i, trough_i, depth, duration in pair_seq:
        trough_price = float(low.iloc[trough_i])
        anchor_y = trough_price - y_span * 0.02
        label_idx, label_y = _find_label_slot(trough_i, anchor_y)
        placed.append((label_idx, label_y))
        rounded_depth = int(round(depth))
        ax1.annotate(
            f"(-{rounded_depth}%, {duration}{suffix})",
            xy=(x[trough_i], trough_price),
            xytext=(x[label_idx], label_y),
            textcoords="data",
            ha="center",
            va="top",
            fontsize=28,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.18", alpha=0.10),
        )

    ax1.set_title(f"{title} | {symbol} | {setup_bucket} | {stage}", pad=16)
    ax1.grid(True, alpha=0.18)
    ax1.legend(loc="upper left", ncol=2)
    ax1.tick_params(axis="both", labelsize=36, pad=8)
    ax1.set_ylabel("Price")

    if len(x) >= 2:
        if hasattr(x, "dtype") and "datetime" in str(x.dtype):
            step = x[-1] - x[-2]
            if pd.isna(step) or step == pd.Timedelta(0):
                step = pd.Timedelta(days=7 if is_weekly else 1)
            right_pad = step * (3 if is_weekly else 6)
        else:
            right_pad = 3 if is_weekly else 6
        ax1.set_xlim(x[0], x[-1] + right_pad)

    margin_top = y_span * 0.10
    margin_bottom = y_span * 0.18
    ax1.set_ylim(max(0, float(low.min()) - margin_bottom), float(high.max()) + margin_top)

    bar_width = 4 if is_weekly else 0.9
    ax2.bar(x, volume.values, width=bar_width, alpha=0.85)
    vol_ma = volume.rolling(10 if is_weekly else 20).mean()
    if vol_ma.notna().sum() == len(volume):
        ax2.plot(x, vol_ma.values, linewidth=2.8, label=("10W Vol MA" if is_weekly else "20D Vol MA"))

    ax2.grid(True, alpha=0.18)
    ax2.set_ylabel("Volume chart")
    ax2.set_yticks([])
    ax2.tick_params(axis="y", which="both", length=0, labelleft=False)
    ax2.tick_params(axis="x", labelsize=34, pad=8)
    if len(x) >= 2:
        if hasattr(x, "dtype") and "datetime" in str(x.dtype):
            step = x[-1] - x[-2]
            if pd.isna(step) or step == pd.Timedelta(0):
                step = pd.Timedelta(days=7 if is_weekly else 1)
            right_pad = step * (3 if is_weekly else 6)
        else:
            right_pad = 3 if is_weekly else 6
        ax2.set_xlim(x[0], x[-1] + right_pad)
    if vol_ma.notna().sum() == len(volume):
        ax2.legend(loc="upper left")

    plt.subplots_adjust(right=0.96)
    fig.tight_layout(rect=[0, 0, 0.97, 1])
    outfile.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outfile, dpi=240, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)

def export_all_charts(final_report: pd.DataFrame, price_data: Dict[str, pd.DataFrame], outdir: Path) -> Dict[str, str]:
    charts_root = outdir / "charts"
    daily_dir = charts_root / "daily"
    weekly_dir = charts_root / "weekly"
    daily_dir.mkdir(parents=True, exist_ok=True)
    weekly_dir.mkdir(parents=True, exist_ok=True)
    score_map = final_report.set_index("ticker").to_dict(orient="index")
    for ticker, df in price_data.items():
        if ticker == DEFAULT_CONFIG["market_index"] or df is None or df.empty:
            continue
        row = score_map.get(ticker, {})
        export_chart(df, ticker, "Daily VCP", daily_dir / f"{sanitize_filename(ticker)}_daily.png", row.get("daily_pivot"), row.get("daily_setup_bucket", "watchlist"), float(row.get("final_daily_score", row.get("daily_score", 0)) or 0), row.get("stage", ""), False)
        weekly_df = resample_weekly(df)
        if not weekly_df.empty:
            export_chart(weekly_df, ticker, "Weekly VCP", weekly_dir / f"{sanitize_filename(ticker)}_weekly.png", row.get("weekly_pivot"), row.get("weekly_setup_bucket", "weekly_watchlist"), float(row.get("final_weekly_score", row.get("weekly_score", 0)) or 0), row.get("stage", ""), True)
    return {"daily_charts_dir": str(daily_dir), "weekly_charts_dir": str(weekly_dir)}

def _clean_stock_snapshot(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if "Company Name" not in out.columns:
        for col in ["Company Name_x", "Company Name_y"]:
            if col in out.columns:
                out["Company Name"] = out[col]
                break
    if "Industry" not in out.columns:
        for col in ["Industry_x", "Industry_y"]:
            if col in out.columns:
                out["Industry"] = out[col]
                break
    for col, fallback in {"final_daily_score": "daily_score", "final_weekly_score": "weekly_score", "final_combined_score": "combined_score"}.items():
        if col not in out.columns:
            out[col] = pd.to_numeric(out.get(fallback), errors="coerce")
    for col in ["daily_setup_bucket", "weekly_setup_bucket", "stage"]:
        if col not in out.columns:
            out[col] = pd.NA
    keep_cols = [
        "ticker", "Company Name", "Industry", "stage", "daily_setup_bucket", "weekly_setup_bucket", "combined_bucket",
        "daily_score", "weekly_score", "combined_score", "industry_boost", "final_daily_score", "final_weekly_score",
        "final_combined_score", "rs_3m_pct", "rs_6m_pct", "avg_turnover_inr", "notes",
    ]
    out = out[[c for c in keep_cols if c in out.columns]].copy()
    for col in ["daily_score", "weekly_score", "combined_score", "industry_boost", "final_daily_score", "final_weekly_score", "final_combined_score", "rs_3m_pct", "rs_6m_pct", "avg_turnover_inr"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out.drop_duplicates(subset=["ticker"]).reset_index(drop=True)

def build_stock_changes(current_df: pd.DataFrame, previous_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    df = _clean_stock_snapshot(current_df).sort_values("final_combined_score", ascending=False).reset_index(drop=True)
    df["current_rank"] = np.arange(1, len(df) + 1)
    if previous_df is None or previous_df.empty:
        df["prev_rank"] = np.nan
        df["rank_change"] = np.nan
        df["prev_score"] = np.nan
        df["combined_score_change"] = np.nan
        df["new_daily_breakout"] = False
        df["new_weekly_breakout"] = False
        df["entered_stage_2"] = False
        df["new_top_10"] = df["current_rank"] <= 10
        df["new_top_20"] = df["current_rank"] <= 20
        return df

    prev = _clean_stock_snapshot(previous_df).sort_values("final_combined_score", ascending=False).reset_index(drop=True)
    prev["prev_rank"] = np.arange(1, len(prev) + 1)
    prev = prev.rename(columns={
        "stage": "prev_stage",
        "daily_setup_bucket": "prev_daily_setup_bucket",
        "weekly_setup_bucket": "prev_weekly_setup_bucket",
        "final_combined_score": "prev_score",
    })
    df = df.merge(prev[["ticker", "prev_rank", "prev_stage", "prev_daily_setup_bucket", "prev_weekly_setup_bucket", "prev_score"]], on="ticker", how="left")
    df["rank_change"] = df["prev_rank"] - df["current_rank"]
    df["combined_score_change"] = df["final_combined_score"] - df["prev_score"]
    df["new_daily_breakout"] = (df["daily_setup_bucket"] == "breakout_today") & (df["prev_daily_setup_bucket"] != "breakout_today")
    df["new_weekly_breakout"] = (df["weekly_setup_bucket"] == "weekly_breakout") & (df["prev_weekly_setup_bucket"] != "weekly_breakout")
    df["entered_stage_2"] = (df["stage"] == "Stage 2") & (df["prev_stage"] != "Stage 2")
    df["new_top_10"] = (df["current_rank"] <= 10) & (~df["prev_rank"].between(1, 10, inclusive="both").fillna(False))
    df["new_top_20"] = (df["current_rank"] <= 20) & (~df["prev_rank"].between(1, 20, inclusive="both").fillna(False))
    return df.sort_values(["current_rank", "final_combined_score"], ascending=[True, False]).reset_index(drop=True)

def build_industry_changes(current_df: pd.DataFrame, previous_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    df = current_df.copy().sort_values(["avg_combined_score", "rs_rank", "strong_combined"], ascending=[False, False, False]).reset_index(drop=True)
    df["current_rank"] = np.arange(1, len(df) + 1)
    if previous_df is None or previous_df.empty:
        df["prev_rank"] = np.nan
        df["rank_change"] = np.nan
        df["combined_score_change"] = np.nan
        df["strong_combined_change"] = np.nan
        df["actionable_daily_change"] = np.nan
        df["actionable_weekly_change"] = np.nan
        df["new_cluster"] = df["strong_combined"].fillna(0) >= 2
        return df

    prev = previous_df.copy().sort_values(["avg_combined_score", "rs_rank", "strong_combined"], ascending=[False, False, False]).reset_index(drop=True)
    prev["prev_rank"] = np.arange(1, len(prev) + 1)
    prev = prev.rename(columns={
        "avg_combined_score": "prev_avg_combined_score",
        "rs_rank": "prev_rs_rank",
        "strong_combined": "prev_strong_combined",
        "actionable_daily": "prev_actionable_daily",
        "actionable_weekly": "prev_actionable_weekly",
    })
    cols = ["Industry", "prev_rank", "prev_avg_combined_score", "prev_rs_rank", "prev_strong_combined", "prev_actionable_daily", "prev_actionable_weekly"]
    df = df.merge(prev[cols], on="Industry", how="left")
    df["rank_change"] = df["prev_rank"] - df["current_rank"]
    df["combined_score_change"] = (df["avg_combined_score"] - df["prev_avg_combined_score"]).round(2)
    df["strong_combined_change"] = (df["strong_combined"] - df["prev_strong_combined"]).round(0)
    df["actionable_daily_change"] = (df["actionable_daily"] - df["prev_actionable_daily"]).round(0)
    df["actionable_weekly_change"] = (df["actionable_weekly"] - df["prev_actionable_weekly"]).round(0)
    df["new_cluster"] = (df["strong_combined"].fillna(0) >= 2) & (df["prev_strong_combined"].fillna(0) < 2)
    return df.sort_values(["current_rank", "avg_combined_score"], ascending=[True, False]).reset_index(drop=True)

def build_outputs(universe_path: str, outdir: str, config: Optional[dict] = None, export_all_ticker_charts: bool = True) -> Dict[str, str]:
    out_path = Path(outdir)
    out_path.mkdir(parents=True, exist_ok=True)
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    universe_df = load_nifty500_universe(universe_path)
    tickers = universe_df["Ticker"].tolist()
    report, regime = build_vcp_universe_report(tickers, config)
    if report.empty:
        raise RuntimeError("No screener results produced.")

    final_report = report.merge(universe_df, left_on="ticker", right_on="Ticker", how="left")
    industry_df = build_industry_strength_table(final_report)
    final_report = apply_industry_boost(final_report, industry_df, config)

    common_cols = ["ticker", "Company Name", "Industry", "stage", "rs_3m_pct", "rs_6m_pct", "avg_turnover_inr", "volume_dryup_ratio", "volume_is_drying_up", "weekly_volume_is_drying_up", "notes"]
    daily_cols = common_cols + ["daily_setup_bucket", "daily_score", "final_daily_score", "daily_pivot", "daily_breakout_distance_pct", "daily_contraction_depths_pct", "daily_contraction_durations", "daily_contraction_score", "daily_base_duration_days", "volume_dryup_ratio", "breakout_volume_ratio"]
    weekly_cols = common_cols + ["weekly_setup_bucket", "weekly_score", "final_weekly_score", "weekly_pivot", "weekly_breakout_distance_pct", "weekly_contraction_depths_pct", "weekly_contraction_durations", "weekly_contraction_score", "weekly_base_duration_weeks", "weekly_vcp_quality"]
    combined_cols = common_cols + ["daily_setup_bucket", "weekly_setup_bucket", "combined_bucket", "daily_score", "weekly_score", "combined_score", "industry_boost", "final_combined_score"]

    daily_df = final_report[[c for c in daily_cols if c in final_report.columns]].sort_values(["final_daily_score", "daily_score"], ascending=[False, False]).reset_index(drop=True)
    weekly_df = final_report[[c for c in weekly_cols if c in final_report.columns]].sort_values(["final_weekly_score", "weekly_score"], ascending=[False, False]).reset_index(drop=True)
    combined_df = final_report[[c for c in combined_cols if c in final_report.columns]].sort_values(["final_combined_score", "combined_score"], ascending=[False, False]).reset_index(drop=True)

    prev_combined = pd.read_csv(out_path / "vcp_combined_ranked.csv") if (out_path / "vcp_combined_ranked.csv").exists() else None
    prev_industry = pd.read_csv(out_path / "industry_strength.csv") if (out_path / "industry_strength.csv").exists() else None

    stock_changes = build_stock_changes(combined_df, prev_combined)
    industry_changes = build_industry_changes(industry_df, prev_industry)
    top_movers = stock_changes.sort_values(["new_top_10", "new_top_20", "new_daily_breakout", "new_weekly_breakout", "rank_change", "combined_score_change"], ascending=[False, False, False, False, False, False]).reset_index(drop=True)

    full_tickers = list(dict.fromkeys(tickers + [cfg["market_index"]]))
    price_data = fetch_prices(full_tickers, cfg["period"], interval="1d")
    benchmark_hist_df = price_data.get(cfg["market_index"])
    price_moves = build_price_moves(combined_df, price_data)
    history_file = update_stage_action_history(out_path, combined_df, price_data, benchmark_hist_df, universe_df, cfg)

    daily_file = out_path / "vcp_daily_ranked.csv"
    weekly_file = out_path / "vcp_weekly_ranked.csv"
    combined_file = out_path / "vcp_combined_ranked.csv"
    industry_file = out_path / "industry_strength.csv"
    regime_file = out_path / "market_regime.csv"
    stock_changes_file = out_path / "stock_changes.csv"
    industry_changes_file = out_path / "industry_changes.csv"
    top_movers_file = out_path / "top_movers.csv"
    price_moves_file = out_path / "stock_price_moves.csv"

    daily_df.to_csv(daily_file, index=False)
    weekly_df.to_csv(weekly_file, index=False)
    combined_df.to_csv(combined_file, index=False)
    industry_df.to_csv(industry_file, index=False)
    pd.DataFrame([asdict(regime)]).to_csv(regime_file, index=False)
    stock_changes.to_csv(stock_changes_file, index=False)
    industry_changes.to_csv(industry_changes_file, index=False)
    top_movers.to_csv(top_movers_file, index=False)
    price_moves.to_csv(price_moves_file, index=False)

    chart_paths = export_all_charts(final_report, price_data, out_path) if export_all_ticker_charts else {"daily_charts_dir": str(out_path / "charts" / "daily"), "weekly_charts_dir": str(out_path / "charts" / "weekly")}
    return {"daily": str(daily_file), "weekly": str(weekly_file), "combined": str(combined_file), "industry": str(industry_file), "regime": str(regime_file), "stock_changes": str(stock_changes_file), "industry_changes": str(industry_changes_file), "top_movers": str(top_movers_file), "price_moves": str(price_moves_file), "history": str(history_file), **chart_paths}


def _perf_from_close(close: pd.Series, bars_back: int) -> float:
    s = close.dropna()
    if len(s) <= bars_back:
        return np.nan
    prev = float(s.iloc[-(bars_back + 1)])
    curr = float(s.iloc[-1])
    if prev == 0:
        return np.nan
    return round((curr / prev - 1) * 100, 2)

def _perf_ytd(close: pd.Series) -> float:
    s = close.dropna()
    if s.empty:
        return np.nan
    current_year = int(s.index[-1].year)
    year_slice = s[s.index.year == current_year]
    if year_slice.empty:
        return np.nan
    first_close = float(year_slice.iloc[0])
    last_close = float(year_slice.iloc[-1])
    if first_close == 0:
        return np.nan
    return round((last_close / first_close - 1) * 100, 2)

def build_price_moves(current_df: pd.DataFrame, price_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    base = _clean_stock_snapshot(current_df).copy()
    if base.empty:
        return pd.DataFrame()
    rows = []
    for _, row in base.iterrows():
        ticker = row.get("ticker")
        df = price_data.get(ticker)
        if df is None or df.empty or "Close" not in df.columns:
            continue
        close = df["Close"].dropna()
        if close.empty:
            continue
        rows.append({
            "ticker": ticker,
            "Company Name": row.get("Company Name"),
            "Industry": row.get("Industry"),
            "stage": row.get("stage"),
            "overall_setup_label": row.get("combined_bucket"),
            "final_combined_score": row.get("final_combined_score"),
            "change_1d_pct": _perf_from_close(close, 1),
            "change_1w_pct": _perf_from_close(close, 5),
            "change_1m_pct": _perf_from_close(close, 21),
            "change_ytd_pct": _perf_ytd(close),
            "last_close": round(float(close.iloc[-1]), 2),
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    for c in ["change_1d_pct", "change_1w_pct", "change_1m_pct", "change_ytd_pct", "final_combined_score", "last_close"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out.sort_values(["change_1d_pct", "final_combined_score"], ascending=[False, False]).reset_index(drop=True)


def derive_public_action(stage: str, combined_bucket: str, score: float) -> str:
    if stage == "Stage 2":
        if combined_bucket in {"high_conviction_breakout", "high_conviction_near_pivot"} and score >= 70:
            return "Strong Structure"
        return "Advancing"
    if stage == "Stage 1":
        return "Base Building"
    if stage == "Stage 3":
        return "Transition"
    if stage == "Stage 4":
        return "Weak Structure"
    return "Mixed"

def derive_super_action(stage: str, combined_bucket: str, score: float) -> str:
    if stage == "Stage 2":
        if combined_bucket == "high_conviction_breakout" and score >= 72:
            return "Buy"
        if combined_bucket in {"high_conviction_near_pivot", "building_setup"} and score >= 62:
            return "Watch / Add on confirmation"
        return "Hold / Trend intact"
    if stage == "Stage 1":
        return "Watchlist / Early base"
    if stage == "Stage 3":
        return "Reduce / Avoid fresh longs"
    if stage == "Stage 4":
        return "Exit / Avoid"
    return "No Action"

def build_stage_action_history_snapshot(snapshot_df: pd.DataFrame, snapshot_date: pd.Timestamp) -> pd.DataFrame:
    if snapshot_df is None or snapshot_df.empty:
        return pd.DataFrame()
    out = snapshot_df.copy()
    score_col = "final_combined_score" if "final_combined_score" in out.columns else "combined_score"
    out[score_col] = pd.to_numeric(out[score_col], errors="coerce")
    out["snapshot_date"] = pd.Timestamp(snapshot_date).normalize()
    out["public_action"] = out.apply(lambda r: derive_public_action(str(r.get("stage", "")), str(r.get("combined_bucket", "")), float(pd.to_numeric(r.get(score_col), errors="coerce") if pd.notna(pd.to_numeric(r.get(score_col), errors="coerce")) else 0.0)), axis=1)
    out["super_action"] = out.apply(lambda r: derive_super_action(str(r.get("stage", "")), str(r.get("combined_bucket", "")), float(pd.to_numeric(r.get(score_col), errors="coerce") if pd.notna(pd.to_numeric(r.get(score_col), errors="coerce")) else 0.0)), axis=1)
    keep_cols = [c for c in [
        "snapshot_date", "ticker", "Company Name", "Industry", "stage", "combined_bucket", score_col,
        "volume_dryup_ratio", "volume_is_drying_up", "weekly_volume_is_drying_up",
        "public_action", "super_action"
    ] if c in out.columns]
    history = out[keep_cols].copy()
    if score_col in history.columns and score_col != "final_combined_score":
        history = history.rename(columns={score_col: "final_combined_score"})
    return history

def build_six_month_history(price_data: Dict[str, pd.DataFrame], benchmark_df: pd.DataFrame, universe_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    lookback = int(config.get("history_init_lookback_trading_days", 126))
    history_rows = []
    tickers = universe_df["Ticker"].tolist()
    benchmark_close = benchmark_df["Close"].dropna().astype(float)

    for ticker in tickers:
        df = price_data.get(ticker)
        if df is None or df.empty or len(df) < max(config.get("min_history", 300), lookback + 260):
            continue
        df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"]).copy()
        if len(df) < 260:
            continue
        snapshot_dates = df.index[-lookback:]
        company = universe_df.loc[universe_df["Ticker"] == ticker, "Company Name"].iloc[0]
        industry = universe_df.loc[universe_df["Ticker"] == ticker, "Industry"].iloc[0]

        for snap_date in snapshot_dates:
            trunc = df.loc[:snap_date].copy()
            bench_trunc = benchmark_df.loc[:snap_date].copy()
            if len(trunc) < 260 or len(bench_trunc) < 260:
                continue
            try:
                regime = market_regime(bench_trunc, config["market_index"], config["market_ma_fast"], config["market_ma_slow"], price_data=None, universe_tickers=None)
                result = analyze_symbol(ticker, trunc, bench_trunc, regime, config)
                if not result:
                    continue
                row = asdict(result)
                row["snapshot_date"] = pd.Timestamp(snap_date).normalize()
                row["Company Name"] = company
                row["Industry"] = industry
                row["public_action"] = derive_public_action(row.get("stage", ""), row.get("combined_bucket", ""), float(row.get("combined_score", 0) or 0))
                row["super_action"] = derive_super_action(row.get("stage", ""), row.get("combined_bucket", ""), float(row.get("combined_score", 0) or 0))
                history_rows.append({k: row.get(k) for k in [
                    "snapshot_date", "ticker", "Company Name", "Industry", "stage", "combined_bucket", "combined_score",
                    "volume_dryup_ratio", "volume_is_drying_up", "weekly_volume_is_drying_up", "public_action", "super_action"
                ]})
            except Exception:
                continue

    if not history_rows:
        return pd.DataFrame()
    history = pd.DataFrame(history_rows).rename(columns={"combined_score": "final_combined_score"})
    history = history.sort_values(["snapshot_date", "ticker"]).reset_index(drop=True)
    return history

def update_stage_action_history(out_path: Path, current_snapshot: pd.DataFrame, price_data: Dict[str, pd.DataFrame], benchmark_df: pd.DataFrame, universe_df: pd.DataFrame, config: dict) -> Path:
    history_file = out_path / str(config.get("history_file_name", "stage_action_history.csv"))
    today = pd.Timestamp.now("UTC").normalize().tz_localize(None)
    current_history = build_stage_action_history_snapshot(current_snapshot, today)

    if history_file.exists():
        existing = pd.read_csv(history_file, parse_dates=["snapshot_date"])
    else:
        existing = build_six_month_history(price_data, benchmark_df, universe_df, config) if bool(config.get("history_init_enabled", True)) else pd.DataFrame()

    if not current_history.empty:
        existing = pd.concat([existing, current_history], ignore_index=True) if not existing.empty else current_history

    if existing.empty:
        existing.to_csv(history_file, index=False)
        return history_file

    existing["snapshot_date"] = pd.to_datetime(existing["snapshot_date"], utc=True).dt.tz_convert(None).dt.normalize()
    existing = existing.drop_duplicates(subset=["snapshot_date", "ticker"], keep="last")
    existing = existing.sort_values(["snapshot_date", "ticker"]).reset_index(drop=True)
    existing.to_csv(history_file, index=False)
    return history_file

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Daily + Weekly VCP Screener with change tracking")
    parser.add_argument("--universe", required=True, help="Path to Nifty 500 CSV/TSV file")
    parser.add_argument("--outdir", default="outputs", help="Output directory")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    outputs = build_outputs(args.universe, args.outdir, export_all_ticker_charts=True)
    print("Saved files:")
    for key, value in outputs.items():
        print(f"- {key}: {value}")

if __name__ == "__main__":
    main()
