"""
TradeClaw — Signal Engine
Generates, filters, and emits trading signals using the rule engine.
Tracks rejections and computes full lifecycle fields (expiry, evaluation_at, TP/SL prices).
"""
import logging
import time
from datetime import datetime

from .rule_engine import apply_prefilters, apply_core_rules, score_candidates
from .rule_engine import TARGET_PCT, STOP_LOSS_PCT

logger = logging.getLogger("tradeclaw.signal_engine")

MAX_SIGNALS_PER_CYCLE = 3
COOLDOWN_SECONDS      = 15 * 60     # 15 min cooldown per coin
SIGNAL_EXPIRY_SECONDS = 20 * 60     # 20 min entry window
HOLD_PERIOD_SECS      = 4 * 60 * 60 # 4h hold period — how long trade plays out

# In-memory trackers (reset on restart; DB is source of truth)
_cooldown_tracker: dict[str, float] = {}
_active_signals:   set[str]         = set()


def _generate_signal_id(symbol: str) -> str:
    now = datetime.utcnow()
    clean_symbol = symbol.replace("USDT", "")
    return f"{clean_symbol}_{now.strftime('%Y%m%d_%H%M%S')}"


def _has_active_signal(symbol: str) -> bool:
    clean_symbol = symbol.replace("USDT", "")
    return any(sig_id.startswith(clean_symbol + "_") for sig_id in _active_signals)


def expire_signals(current_time: int | None = None) -> list[str]:
    # Placeholder — active tracker cleanup happens via DB in evaluator
    return []


def clear_trackers():
    _cooldown_tracker.clear()
    _active_signals.clear()


def generate_signals(market_data: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Process computed features and generate filtered trading signals.
    Returns: (signals, rejections)
    """
    if not market_data:
        return [], []

    now = int(time.time())
    candidates = []
    rejections  = []

    # ── 1. Pre-filter + cooldown gate ──────────────────────────────────
    for f in market_data:
        sym = f.get("symbol")
        if not sym:
            continue
        if _cooldown_tracker.get(sym, 0) > now - COOLDOWN_SECONDS:
            continue
        if _has_active_signal(sym):
            continue

        pf_pass, pf_reason = apply_prefilters(f)
        if not pf_pass:
            rejections.append({
                "symbol":         sym,
                "reject_reason":  pf_reason,
                "score":          0.0,
                "feature_vector": f,
                "rejected_at":    now,
            })
            continue
        candidates.append(f)

    # ── 2. Score across universe ────────────────────────────────────────
    scored_candidates = score_candidates(candidates)

    # ── 3. Core rule filter ─────────────────────────────────────────────
    viable = []
    for c in scored_candidates:
        core_pass, core_reason = apply_core_rules(c)
        if not core_pass:
            rejections.append({
                "symbol":         c["symbol"],
                "reject_reason":  core_reason,
                "score":          c.get("composite_score", 0.0),
                "feature_vector": c,
                "rejected_at":    now,
            })
            continue
        viable.append(c)

    # ── 4. Top K cut ────────────────────────────────────────────────────
    top_signals = viable[:MAX_SIGNALS_PER_CYCLE]
    for c in viable[MAX_SIGNALS_PER_CYCLE:]:
        rejections.append({
            "symbol":         c["symbol"],
            "reject_reason":  "NOT_TOP_K",
            "score":          c.get("composite_score", 0.0),
            "feature_vector": c,
            "rejected_at":    now,
        })

    # ── 5. Build signal records ─────────────────────────────────────────
    signals = []
    for item in top_signals:
        symbol    = item["symbol"]
        price     = item["price"]
        signal_id = _generate_signal_id(symbol)

        expiry_at     = now + SIGNAL_EXPIRY_SECONDS
        evaluation_at = expiry_at + HOLD_PERIOD_SECS    # when outcome check runs

        entry_low           = round(price * 0.999, 8)
        entry_high          = round(price * 1.001, 8)
        entry_price_assumed = round((entry_low + entry_high) / 2, 8)

        target_price = round(entry_price_assumed * (1 + TARGET_PCT), 8)
        stop_price   = round(entry_price_assumed * (1 - STOP_LOSS_PCT), 8)

        signal = {
            # Identity
            "id":                   signal_id,
            "symbol":               symbol,
            # Timestamps
            "generated_at":         now,
            "expiry_at":            expiry_at,
            "hold_period_secs":     HOLD_PERIOD_SECS,
            "evaluation_at":        evaluation_at,
            # Trade params
            "entry_low":            entry_low,
            "entry_high":           entry_high,
            "entry_price_assumed":  entry_price_assumed,
            "target_pct":           round(TARGET_PCT * 100, 4),
            "stop_loss_pct":        round(STOP_LOSS_PCT * 100, 4),
            "target_price":         target_price,
            "stop_price":           stop_price,
            # Quality
            "score":                item["composite_score"],
            "confidence":           item.get("confidence", "LOW"),
            "reason":               (
                f"Mom5m +{item['momentum_5m']*100:.1f}% | "
                f"Vol {item['rel_volume']:.1f}x | "
                f"RSI {item['rsi']:.0f} | "
                f"RS +{item.get('rel_strength_5m', 0)*100:.2f}%"
            ),
            "feature_vector":       item,
            # Lifecycle
            "status":               "ACTIVE",
            "fcm_sent":             False,
        }

        signals.append(signal)
        _cooldown_tracker[symbol] = now
        _active_signals.add(signal_id)

        logger.info(
            f"🟢 Signal: {signal_id} | {symbol} | "
            f"Score {item['composite_score']:.1f} [{item['confidence']}] | "
            f"Entry ~{entry_price_assumed:.4f} → TP {target_price:.4f} | "
            f"SL {stop_price:.4f} | Eval in {HOLD_PERIOD_SECS//3600}h"
        )

    return signals, rejections
