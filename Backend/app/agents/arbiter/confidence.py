"""
app/agents/arbiter/confidence.py
──────────────────────────────────
Confidence scoring and threshold logic for the Arbiter.
Applies rule-based adjustments on top of the LLM's raw scores.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings

_settings = get_settings()


@dataclass
class ConfidenceResult:
    signal: str           # BUY | HOLD | SELL
    bull_confidence: float
    bear_confidence: float
    net_confidence: float
    confidence_label: str  # HIGH | MEDIUM | LOW
    override_reason: str | None = None


def compute_verdict(
    bull_confidence: float,
    bear_confidence: float,
    *,
    threshold: float | None = None,
    dominant_advantage: float | None = None,
) -> ConfidenceResult:
    """
    Core arbitration logic.

    Rules:
    - BUY:  bull - bear >= dominant_advantage AND bull >= threshold
    - SELL: bear - bull >= dominant_advantage AND bear >= threshold
    - HOLD: everything else (including when both scores are low)

    Both threshold and dominant_advantage are read from settings if not provided,
    allowing per-request overrides.
    """
    threshold = threshold or _settings.ARBITER_CONFIDENCE_THRESHOLD
    dominant_advantage = dominant_advantage or _settings.ARBITER_DOMINANT_ADVANTAGE

    # Clamp to [0, 1]
    bull = max(0.0, min(1.0, bull_confidence))
    bear = max(0.0, min(1.0, bear_confidence))
    net = abs(bull - bear)

    override_reason: str | None = None

    # Determine raw signal
    if bull - bear >= dominant_advantage and bull >= threshold:
        signal = "BUY"
    elif bear - bull >= dominant_advantage and bear >= threshold:
        signal = "SELL"
    else:
        signal = "HOLD"
        if net < threshold:
            override_reason = (
                f"Net confidence {net:.2f} below threshold {threshold:.2f} — defaulting to HOLD"
            )

    # Confidence label
    if net >= 0.40:
        label = "HIGH"
    elif net >= 0.20:
        label = "MEDIUM"
    else:
        label = "LOW"

    return ConfidenceResult(
        signal=signal,
        bull_confidence=round(bull, 4),
        bear_confidence=round(bear, 4),
        net_confidence=round(net, 4),
        confidence_label=label,
        override_reason=override_reason,
    )


def reconcile_with_llm(
    llm_signal: str,
    llm_bull: float,
    llm_bear: float,
    rule_result: ConfidenceResult,
) -> ConfidenceResult:
    """
    Reconcile the LLM's verdict with the rule-based verdict.
    The rule-based system acts as a safety override —
    if the LLM says BUY but net confidence is below threshold, HOLD wins.
    """
    if rule_result.override_reason:
        # Rule-based override takes precedence
        return rule_result

    # If LLM and rules agree, return the rule result (which has precise score rounding)
    if llm_signal == rule_result.signal:
        return rule_result

    # Disagrement: trust the rule engine, log the discrepancy
    return ConfidenceResult(
        signal=rule_result.signal,
        bull_confidence=rule_result.bull_confidence,
        bear_confidence=rule_result.bear_confidence,
        net_confidence=rule_result.net_confidence,
        confidence_label=rule_result.confidence_label,
        override_reason=(
            f"Rule engine overrode LLM signal '{llm_signal}' → '{rule_result.signal}' "
            f"(bull={rule_result.bull_confidence:.2f}, bear={rule_result.bear_confidence:.2f})"
        ),
    )
