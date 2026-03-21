"""
TradeClaw — Rule Engine & Scoring
Applies pre-filters, core signal rules, and computes composite scores.
"""
import logging

logger = logging.getLogger("tradeclaw.rule_engine")

# -- Configurable Settings --
LIQUIDITY_MIN = 3_000_000
SPREAD_MAX = 0.005           # 0.5% (was 0.15%)
MARKET_CAP_MIN = 50_000_000
MARKET_CAP_MAX = 5_000_000_000

MOMENTUM_5M_MIN = 0.001      # 0.1% (was 0.5%)
MOMENTUM_15M_MIN = 0.002     # 0.2% (was 1.0%)
REL_VOLUME_MIN = 1.1         # (was 1.5)
RSI_MIN = 40                 # (was 45)
RSI_MAX = 80                 # (was 72)
REL_STRENGTH_MIN = -0.005    # allow slight negative RS
BODY_WICK_MIN = 0.2          # (was 0.4)
TREND_PERSIST_MIN = 0.33     # 1/3 candles (was 2/3)

P_WIN_ASSUMED = 0.50
FEE_MAKER_PCT = 0.001        # Binance Spot Maker
FEE_TAKER_PCT = 0.001        # Binance Spot Taker
SLIPPAGE_PCT = 0.001
SAFETY_MARGIN = 0.002
ROUND_TRIP_COST = FEE_TAKER_PCT * 2 + SLIPPAGE_PCT * 2

TARGET_PCT = 0.012          # 1.2%
STOP_LOSS_PCT = 0.006       # 0.6%
MIN_RR_RATIO = 1.5

WEIGHTS = {
    "w1": 0.25,
    "w2": 0.20,
    "w3": 0.20,
    "w4": 0.15,
    "w5": 0.08,
    "w6": 0.07,
    "w7": 0.05,
    "w8": 0.08,
    "w9": 0.05,
}

def apply_prefilters(f: dict) -> tuple[bool, str]:
    if f["volume_24h_usdt"] < LIQUIDITY_MIN:
        return False, "FAIL_LIQUIDITY"
    if f.get("spread_pct", 0) > SPREAD_MAX:
        return False, "FAIL_SPREAD"
    if f.get("already_pumped", False):
        return False, "FAIL_ALREADY_PUMPED"
    if f["momentum_5m"] <= -0.005:  # allow flat/slight dip (was <= 0)
        return False, "FAIL_NO_MOMENTUM_5M"
    if f["momentum_15m"] <= -0.005: # allow flat/slight dip (was <= 0)
        return False, "FAIL_NO_MOMENTUM_15M"
    return True, "PASS"

def apply_core_rules(f: dict) -> tuple[bool, str]:
    if f["momentum_5m"] < MOMENTUM_5M_MIN:
        return False, "FAIL_5M_THRESHOLD"
    if f["momentum_15m"] < MOMENTUM_15M_MIN:
        return False, "FAIL_15M_THRESHOLD"
    if f["rel_volume"] < REL_VOLUME_MIN:
        return False, "FAIL_REL_VOLUME"
    if f["rsi"] < RSI_MIN or f["rsi"] > RSI_MAX:
        return False, "FAIL_RSI"
    if f.get("rel_strength_5m", 0) < REL_STRENGTH_MIN:
        return False, "FAIL_REL_STRENGTH"
    if f["body_wick_ratio"] < BODY_WICK_MIN:
        return False, "FAIL_BODY_WICK"
    if f["trend_persistence"] < TREND_PERSIST_MIN:
        return False, "FAIL_TREND_PERSIST"
    
    # Compute gross edge
    gross_edge = TARGET_PCT * P_WIN_ASSUMED - STOP_LOSS_PCT * (1 - P_WIN_ASSUMED)
    net_edge = gross_edge - ROUND_TRIP_COST - SAFETY_MARGIN
    if net_edge <= 0 or (TARGET_PCT / STOP_LOSS_PCT) < MIN_RR_RATIO:
        # Note: Depending on P_WIN_ASSUMED and default TARGET_PCT, it might always reject here unless adjusted.
        return False, "FAIL_FEE_VIABILITY"

    return True, "PASS"

def normalize(val: float, min_val: float, max_val: float) -> float:
    if max_val == min_val:
        return 0.5
    res = (val - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, res))

def score_candidates(candidates: list[dict]) -> list[dict]:
    """
    Computes score for pre-filtered candidates across the local universe.
    Candidates should be a list of feature dicts.
    """
    if not candidates:
        return []

    # get universe min/max bounds for normalization
    get_min = lambda k: min(c[k] for c in candidates)
    get_max = lambda k: max(c[k] for c in candidates)

    b = {
        "m5": (get_min("momentum_5m"), get_max("momentum_5m")),
        "m15": (get_min("momentum_15m"), get_max("momentum_15m")),
        "rv": (get_min("rel_volume"), get_max("rel_volume")),
        "rs": (get_min("rel_strength_5m"), get_max("rel_strength_5m")),
        "bw": (get_min("body_wick_ratio"), get_max("body_wick_ratio")),
        "tp": (get_min("trend_persistence"), get_max("trend_persistence")),
        "br": (0.0, 1.0), # rank is already 0-1
        "sp": (get_min("spread_pct"), get_max("spread_pct"))
    }

    for c in candidates:
        n_m5  = normalize(c["momentum_5m"], *b["m5"])
        n_m15 = normalize(c["momentum_15m"], *b["m15"])
        n_rv  = normalize(c["rel_volume"], *b["rv"])
        n_rs  = normalize(c.get("rel_strength_5m", 0), *b["rs"])
        n_bw  = normalize(c["body_wick_ratio"], *b["bw"])
        n_tp  = normalize(c["trend_persistence"], *b["tp"])
        n_br  = normalize(c.get("breakout_rank", 0), *b["br"])
        n_sp  = normalize(c.get("spread_pct", 0), *b["sp"])

        rsi_penalty = max(0.0, c["rsi"] - RSI_MAX) / 30.0

        score = (
            WEIGHTS["w1"] * n_m5 +
            WEIGHTS["w2"] * n_m15 +
            WEIGHTS["w3"] * n_rv +
            WEIGHTS["w4"] * n_rs +
            WEIGHTS["w5"] * n_bw +
            WEIGHTS["w6"] * n_tp +
            WEIGHTS["w7"] * n_br -
            WEIGHTS["w8"] * rsi_penalty -
            WEIGHTS["w9"] * n_sp
        )

        # Scale to 0-100 logic
        score_100 = max(0.0, min(100.0, score * 100))
        c["composite_score"] = score_100

        if score_100 >= 75:
            c["confidence"] = "HIGH"
        elif score_100 >= 55:
            c["confidence"] = "MEDIUM"
        else:
            c["confidence"] = "LOW"

    return sorted(candidates, key=lambda c: c["composite_score"], reverse=True)
