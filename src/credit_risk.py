"""Transparent, rule-based credit-risk assessment engine.

This is an educational/decision-support prototype. Its probability of default is
a manually parameterized score-to-PD mapping, not a statistically trained or
calibrated model.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import math


@dataclass
class BorrowerProfile:
    loan_amount: float
    term_months: int
    annual_rate_pct: float
    down_payment: float
    collateral_value: float
    monthly_income: float
    monthly_fixed_charges: float
    existing_monthly_credit: float
    payment_delays_12m: int
    employment_years: float
    employment_type: str
    age: int
    undrawn_commitment: float = 0.0
    ccf_pct: float = 50.0


@dataclass
class RiskParameters:
    max_pd_pct: float = 20.0
    max_debt_service_pct: float = 40.0
    risk_margin_pct: float = 2.0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def monthly_payment(principal: float, annual_rate_pct: float, months: int) -> float:
    """Return the monthly instalment for a standard amortizing loan."""
    if months <= 0:
        raise ValueError("La durée doit être strictement positive.")
    if principal < 0:
        raise ValueError("Le montant du prêt ne peut pas être négatif.")
    monthly_rate = annual_rate_pct / 100 / 12
    if monthly_rate == 0:
        return principal / months
    factor = (1 + monthly_rate) ** months
    return principal * monthly_rate * factor / (factor - 1)


def assess_credit(profile: BorrowerProfile, params: RiskParameters) -> dict:
    """Compute a transparent score, indicative PD, LGD, EAD and decision."""
    if profile.loan_amount <= 0 or profile.monthly_income <= 0:
        raise ValueError("Le prêt et le revenu mensuel doivent être positifs.")
    if profile.term_months <= 0 or profile.age < 18:
        raise ValueError("Durée invalide ou âge inférieur à 18 ans.")
    if not 0 <= profile.ccf_pct <= 100:
        raise ValueError("Le CCF doit être compris entre 0 et 100 %.")

    instalment = monthly_payment(
        profile.loan_amount, profile.annual_rate_pct, profile.term_months
    )
    debt_service = (
        instalment + profile.monthly_fixed_charges + profile.existing_monthly_credit
    )
    debt_ratio = debt_service / profile.monthly_income * 100

    # Score out of 100. Each component is explicit and can be reviewed.
    income_score = 15 if profile.monthly_income >= 3 * instalment else (
        10 if profile.monthly_income >= 2 * instalment else 4
    )
    affordability_score = 20 if debt_ratio <= 30 else (
        15 if debt_ratio <= 40 else 8 if debt_ratio <= 50 else 0
    )
    history_score = {0: 15, 1: 11, 2: 7, 3: 3}.get(
        profile.payment_delays_12m, 0
    )
    employment_score = min(10, max(0, profile.employment_years * 2))
    if profile.employment_type == "CDI / Fonctionnaire":
        employment_score += 10
    elif profile.employment_type == "CDD":
        employment_score += 6
    elif profile.employment_type == "Indépendant":
        employment_score += 5
    else:
        employment_score += 2
    collateral_ratio = profile.collateral_value / profile.loan_amount
    collateral_score = 10 if collateral_ratio >= 1.5 else (
        7 if collateral_ratio >= 1 else 3 if collateral_ratio >= 0.5 else 0
    )
    down_ratio = profile.down_payment / (profile.loan_amount + profile.down_payment)
    down_score = 5 if down_ratio >= 0.3 else 3 if down_ratio >= 0.15 else 0
    age_score = 5 if 25 <= profile.age <= 60 else 3
    score_parts = {
        "Revenu et capacité de remboursement": income_score,
        "Taux d'endettement": affordability_score,
        "Historique de paiement": history_score,
        "Stabilité et type d'emploi": min(20, employment_score),
        "Garanties": collateral_score,
        "Apport personnel": down_score,
        "Âge": age_score,
    }
    score = int(round(_clamp(sum(score_parts.values()), 0, 100)))

    # Monotonic score-to-PD mapping, deliberately marked as indicative.
    # Higher scores imply lower PD. This is not a fitted logistic regression.
    logit = 3.0 - 0.075 * score
    pd = 1 / (1 + math.exp(-logit))

    # Simple collateral-based LGD heuristic, capped to [5%, 90%].
    secured_coverage = (profile.collateral_value + profile.down_payment) / profile.loan_amount
    lgd = _clamp(0.9 - 0.55 * secured_coverage, 0.05, 0.90)

    ead = profile.loan_amount + (profile.ccf_pct / 100) * profile.undrawn_commitment
    expected_loss = pd * ead * lgd
    annual_risk_cost_pct = pd * lgd * 100
    suggested_rate_pct = profile.annual_rate_pct + annual_risk_cost_pct + params.risk_margin_pct

    decision = "Accord indicatif"
    reasons = []
    if pd * 100 > params.max_pd_pct:
        reasons.append("La probabilité de défaut dépasse le seuil autorisé.")
    if debt_ratio > params.max_debt_service_pct:
        reasons.append("Le taux d'effort dépasse le seuil autorisé.")
    if reasons:
        decision = "Refus indicatif"
    elif pd * 100 > params.max_pd_pct * 0.8 or debt_ratio > params.max_debt_service_pct * 0.85:
        decision = "Étude complémentaire"
        reasons.append("Le dossier est proche d'au moins un seuil de risque.")
    else:
        reasons.append("Les indicateurs calculés respectent les seuils paramétrés.")

    return {
        "score": score,
        "score_parts": score_parts,
        "probability_of_default": pd,
        "loss_given_default": lgd,
        "exposure_at_default": ead,
        "expected_loss": expected_loss,
        "monthly_payment": instalment,
        "debt_service_ratio": debt_ratio,
        "suggested_rate_pct": suggested_rate_pct,
        "decision": decision,
        "reasons": reasons,
        "profile": asdict(profile),
        "parameters": asdict(params),
    }
