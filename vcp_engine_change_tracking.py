from __future__ import annotations
import argparse
from dataclasses import dataclass, asdict
from pathlib import Path
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
    ma_fast: float
    ma_slow: float
    trend_up: bool
    above_fast: bool
    above_slow: bool
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

def local_peaks_troughs(close: pd.Series, order: int) -> Tuple[List[int], List[int]]:
    arr = close.values
    peaks: List[int] = []
    troughs: List[int] = []
    for i in range(order, len(arr) - order):
        window = arr[i-order:i+order+1]
        center = arr[i]
        if np.isfinite(center):
            if center == np.max(window) and np.sum(window == center) == 1:
                peaks.append(i)
            if center == np.min(window) and np.sum(window == center) == 1:
                troughs.append(i)
    return peaks, troughs

def detect_vcp_contractions(close: pd.Series, order: int, max_pairs: int, min_duration_bars: int, min_depth_pct: float) -> Tuple[List[float], List[int], float]:
    peaks, troughs = local_peaks_troughs(close, order=order)
    pairs = []
    for p in peaks:
        next_troughs = [t for t in troughs if t > p and (t - p) >= min_duration_bars]
        if not next_troughs:
            continue
        t = next_troughs[0]
        peak = close.iloc[p]
        trough = close.iloc[t]
        if peak > 0 and trough > 0:
            depth = (peak - trough) / peak * 100
            duration = t - p
            if depth >= min_depth_pct:
                pairs.append((p, t, depth, duration))
    if not pairs:
        return [], [], 0.0
    pairs = pairs[-max_pairs:]
    depths = [round(float(x[2]), 2) for x in pairs]
    durations = [int(x[3]) for x in pairs]
    base_duration = float(pairs[-1][1] - pairs[0][0])
    return depths, durations, base_duration

def contraction_score(depths: List[float]) -> float:
    if len(depths) < 2:
        return 0.0
    wins = sum(1 for i in range(1, len(depths)) if depths[i] < depths[i-1])
    return wins / (len(depths) - 1)

def compute_pivot(close: pd.Series, lookback: int) -> float:
    s = close.iloc[-lookback:-1]
    if len(s) == 0:
        return np.nan
    return float(s.max())

def market_regime(index_df: pd.DataFrame, index_symbol: str, ma_fast: int, ma_slow: int) -> MarketRegime:
    close = index_df["Close"].dropna()
    last_close = float(close.iloc[-1])
    fast = float(close.rolling(ma_fast).mean().iloc[-1])
    slow = float(close.rolling(ma_slow).mean().iloc[-1])
    above_fast = last_close > fast
    above_slow = last_close > slow
    trend_up = fast > slow and rolling_slope(close.rolling(ma_slow).mean(), 20) > 0
    label = "risk_on" if (above_fast and above_slow and trend_up) else ("mixed" if above_slow else "risk_off")
    return MarketRegime(index_symbol, round(last_close, 2), round(fast, 2), round(slow, 2), bool(trend_up), bool(above_fast), bool(above_slow), label)

def determine_stage(close: pd.Series, ma50: float, ma150: float, ma200: float) -> str:
    if len(close) < 260:
        return "Unknown"
    last = float(close.iloc[-1])
    ma200_slope = rolling_slope(close.rolling(200).mean(), 20)
    high_52w = float(close.iloc[-252:].max())
    low_52w = float(close.iloc[-252:].min())
    dist_from_high = (last / high_52w - 1) * 100 if high_52w > 0 else np.nan
    dist_from_low = (last / low_52w - 1) * 100 if low_52w > 0 else np.nan
    if last > ma50 > ma150 > ma200 and ma200_slope > 0 and dist_from_high >= -15:
        return "Stage 2"
    if last < ma50 < ma150 < ma200 and ma200_slope < 0:
        return "Stage 4"
    if ma200_slope < 0 and last < ma150 and dist_from_high <= -20:
        return "Stage 3"
    if ma200_slope >= 0 and dist_from_low <= 25 and last <= ma150:
        return "Stage 1"
    return "Stage 3"

def vcp_quality_label(score: float, base_bars: float, depths: List[float], min_base_bars: int) -> str:
    if len(depths) < 2 or base_bars < min_base_bars:
        return "weak"
    return "strong" if score >= 0.66 else ("moderate" if score >= 0.5 else "weak")

def score_daily(stage: str, trend_template_ok: bool, market_regime_ok: bool, liquidity_ok: bool, near_pivot_ok: bool, breakout_today: bool, contraction_score_val: float, base_duration: float, dist_from_high: float, volume_dryup_ratio: float, breakout_volume_ratio: float, rs_3m: float, rs_6m: float) -> float:
    score = 0.0
    if trend_template_ok:
        score += 18
    if market_regime_ok:
        score += 8
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
    df = df.dropna(subset=["Close", "Volume"]).copy()
    if len(df) < config["min_history"]:
        return None

    close = df["Close"]
    volume = df["Volume"]
    weekly_df = resample_weekly(df)
    if len(weekly_df) < 60:
        return None
    weekly_close = weekly_df["Close"]

    close_now = float(close.iloc[-1])
    ma50 = float(close.rolling(50).mean().iloc[-1])
    ma150 = float(close.rolling(150).mean().iloc[-1])
    ma200 = float(close.rolling(200).mean().iloc[-1])
    stage = determine_stage(close, ma50, ma150, ma200)

    high_52w = float(close.iloc[-252:].max())
    low_52w = float(close.iloc[-252:].min())
    dist_from_high = (close_now / high_52w - 1) * 100
    advance_from_low = (close_now / low_52w - 1) * 100

    trend_template_ok = stage == "Stage 2" and close_now > ma50 > ma150 > ma200 and rolling_slope(close.rolling(200).mean(), 20) > 0 and dist_from_high >= -15 and advance_from_low >= 30
    market_regime_ok = regime.regime_label != "risk_off"

    daily_depths, daily_durations, daily_base_duration = detect_vcp_contractions(close.iloc[-140:], config["swing_order_daily"], config["max_contractions"], config["min_contraction_days_daily"], config["min_contraction_depth_pct_daily"])
    daily_contraction_score_val = contraction_score(daily_depths)

    weekly_depths, weekly_durations, weekly_base_duration = detect_vcp_contractions(weekly_close.iloc[-52:], config["swing_order_weekly"], config["max_contractions"], config["min_contraction_days_weekly"], config["min_contraction_depth_pct_weekly"])
    weekly_contraction_score_val = contraction_score(weekly_depths)
    weekly_quality = vcp_quality_label(weekly_contraction_score_val, weekly_base_duration, weekly_depths, config["min_base_duration_weeks"])

    volume_dryup_ratio = volume_ratio(volume, config["volume_short_window"], config["volume_long_window"])
    breakout_volume_ratio = recent_breakout_volume_ratio(volume, config["volume_long_window"])
    avg_turnover_inr = avg_turnover(close, volume, 20)
    liquidity_ok = pd.notna(avg_turnover_inr) and avg_turnover_inr >= config["min_avg_turnover_inr"]

    stock_3m = pct_return(close, 63)
    stock_6m = pct_return(close, 126)
    bm_3m = pct_return(benchmark_df["Close"], 63)
    bm_6m = pct_return(benchmark_df["Close"], 126)
    rs_3m = stock_3m - bm_3m if pd.notna(stock_3m) and pd.notna(bm_3m) else np.nan
    rs_6m = stock_6m - bm_6m if pd.notna(stock_6m) and pd.notna(bm_6m) else np.nan

    daily_pivot = compute_pivot(close, config["pivot_lookback_daily"])
    daily_breakout_distance = (close_now / daily_pivot - 1) * 100 if pd.notna(daily_pivot) and daily_pivot > 0 else np.nan
    near_pivot_ok = pd.notna(daily_breakout_distance) and config["near_pivot_min_pct"] <= daily_breakout_distance <= config["near_pivot_max_pct"]
    breakout_today = bool(pd.notna(daily_breakout_distance) and daily_breakout_distance > 0 and pd.notna(breakout_volume_ratio) and breakout_volume_ratio >= config["breakout_volume_ratio"])

    weekly_pivot = compute_pivot(weekly_close, config["pivot_lookback_weekly"])
    weekly_breakout_distance = (float(weekly_close.iloc[-1]) / weekly_pivot - 1) * 100 if pd.notna(weekly_pivot) and weekly_pivot > 0 else np.nan

    recent_range_pct = (close.iloc[-config["recent_range_days"]:].max() - close.iloc[-config["recent_range_days"]:].min()) / close.iloc[-config["recent_range_days"]:].max() * 100
    tight_range_ok = recent_range_pct <= config["recent_range_max_pct"]

    daily_vcp_ok = len(daily_depths) >= 2 and daily_base_duration >= config["min_base_duration_days"] and daily_contraction_score_val >= 0.5 and daily_depths[-1] <= config["max_latest_contraction_pct"]
    weekly_vcp_ok = len(weekly_depths) >= 2 and weekly_base_duration >= config["min_base_duration_weeks"] and weekly_contraction_score_val >= config["min_weekly_strength_score"]

    daily_bucket = classify_daily_bucket(trend_template_ok, daily_vcp_ok, near_pivot_ok, breakout_today, tight_range_ok, market_regime_ok)
    weekly_bucket = classify_weekly_bucket(stage, weekly_vcp_ok, weekly_breakout_distance, weekly_quality)

    daily_score = score_daily(stage, trend_template_ok, market_regime_ok, liquidity_ok, near_pivot_ok, breakout_today, daily_contraction_score_val, daily_base_duration, dist_from_high, volume_dryup_ratio, breakout_volume_ratio, rs_3m, rs_6m)
    weekly_score = score_weekly(stage, weekly_contraction_score_val, weekly_base_duration, weekly_breakout_distance, weekly_quality, rs_3m, rs_6m)
    combo_bucket = combined_bucket(daily_bucket, weekly_bucket)
    combined_score = round(0.55 * daily_score + 0.45 * weekly_score, 2)

    notes = [stage]
    if trend_template_ok:
        notes.append("trend_template_ok")
    if daily_vcp_ok:
        notes.append("daily_vcp_ok")
    if weekly_vcp_ok:
        notes.append("weekly_vcp_ok")
    if pd.notna(volume_dryup_ratio) and volume_dryup_ratio < 0.8:
        notes.append("volume_dryup")
    if breakout_today:
        notes.append("daily_breakout_volume")
    if weekly_quality == "strong":
        notes.append("weekly_strong")

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
        ", ".join(notes),
    )

def build_vcp_universe_report(tickers: List[str], config: Optional[dict] = None) -> Tuple[pd.DataFrame, MarketRegime]:
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    full_tickers = list(dict.fromkeys(tickers + [cfg["market_index"]]))
    data = fetch_prices(full_tickers, cfg["period"], interval="1d")
    if cfg["market_index"] not in data:
        raise RuntimeError(f"Missing market index data for {cfg['market_index']}")
    benchmark_df = data[cfg["market_index"]]
    regime = market_regime(benchmark_df, cfg["market_index"], cfg["market_ma_fast"], cfg["market_ma_slow"])

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
    plot_df = df.copy().tail(180 if not is_weekly else 104)
    if plot_df.empty:
        return
    close = plot_df["Close"]
    volume = plot_df["Volume"]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    ax1.plot(plot_df.index, close.values, label="Close", linewidth=1.8)
    if pivot is not None and pd.notna(pivot):
        ax1.axhline(float(pivot), linestyle="--", linewidth=1.0)
        ax1.text(plot_df.index[-1], float(pivot), f" Pivot {pivot:.2f}", va="bottom")
    ax1.set_title(f"{title} | {symbol} | {setup_bucket} | score={score:.2f} | {stage}")
    ax1.grid(True, alpha=0.25)
    ax1.legend(loc="upper left")
    ax2.bar(plot_df.index, volume.values, width=4 if is_weekly else 1)
    vol_ma = volume.rolling(10 if is_weekly else 20).mean()
    ax2.plot(plot_df.index, vol_ma.values, linewidth=1.0)
    ax2.grid(True, alpha=0.25)
    ax2.set_ylabel("Vol")
    fig.tight_layout()
    outfile.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outfile, dpi=140, bbox_inches="tight")
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
    universe_df = load_nifty500_universe(universe_path)
    tickers = universe_df["Ticker"].tolist()
    report, regime = build_vcp_universe_report(tickers, config)
    if report.empty:
        raise RuntimeError("No screener results produced.")

    final_report = report.merge(universe_df, left_on="ticker", right_on="Ticker", how="left")
    industry_df = build_industry_strength_table(final_report)
    final_report = apply_industry_boost(final_report, industry_df, config)

    common_cols = ["ticker", "Company Name", "Industry", "stage", "rs_3m_pct", "rs_6m_pct", "avg_turnover_inr", "notes"]
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

    daily_file = out_path / "vcp_daily_ranked.csv"
    weekly_file = out_path / "vcp_weekly_ranked.csv"
    combined_file = out_path / "vcp_combined_ranked.csv"
    industry_file = out_path / "industry_strength.csv"
    regime_file = out_path / "market_regime.csv"
    stock_changes_file = out_path / "stock_changes.csv"
    industry_changes_file = out_path / "industry_changes.csv"
    top_movers_file = out_path / "top_movers.csv"

    daily_df.to_csv(daily_file, index=False)
    weekly_df.to_csv(weekly_file, index=False)
    combined_df.to_csv(combined_file, index=False)
    industry_df.to_csv(industry_file, index=False)
    pd.DataFrame([asdict(regime)]).to_csv(regime_file, index=False)
    stock_changes.to_csv(stock_changes_file, index=False)
    industry_changes.to_csv(industry_changes_file, index=False)
    top_movers.to_csv(top_movers_file, index=False)

    full_tickers = list(dict.fromkeys(tickers + [DEFAULT_CONFIG["market_index"]]))
    price_data = fetch_prices(full_tickers, DEFAULT_CONFIG["period"], interval="1d")
    chart_paths = export_all_charts(final_report, price_data, out_path) if export_all_ticker_charts else {"daily_charts_dir": str(out_path / "charts" / "daily"), "weekly_charts_dir": str(out_path / "charts" / "weekly")}
    return {"daily": str(daily_file), "weekly": str(weekly_file), "combined": str(combined_file), "industry": str(industry_file), "regime": str(regime_file), "stock_changes": str(stock_changes_file), "industry_changes": str(industry_changes_file), "top_movers": str(top_movers_file), **chart_paths}

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
