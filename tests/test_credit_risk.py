import pytest

from src.credit_risk import BorrowerProfile, RiskParameters, assess_credit, monthly_payment


def sample_profile(**overrides):
    values = dict(
        loan_amount=1_000_000,
        term_months=36,
        annual_rate_pct=12,
        down_payment=100_000,
        collateral_value=500_000,
        monthly_income=250_000,
        monthly_fixed_charges=40_000,
        existing_monthly_credit=20_000,
        payment_delays_12m=0,
        employment_years=3,
        employment_type="CDI / Fonctionnaire",
        age=30,
        undrawn_commitment=100_000,
        ccf_pct=50,
    )
    values.update(overrides)
    return BorrowerProfile(**values)


def test_zero_interest_payment():
    assert monthly_payment(120_000, 0, 12) == pytest.approx(10_000)


def test_assessment_outputs_are_in_valid_ranges():
    result = assess_credit(sample_profile(), RiskParameters())
    assert 0 <= result["score"] <= 100
    assert 0 < result["probability_of_default"] < 1
    assert 0.05 <= result["loss_given_default"] <= 0.90
    assert result["exposure_at_default"] == pytest.approx(1_050_000)
    assert result["expected_loss"] > 0


def test_higher_score_means_lower_pd():
    low = assess_credit(
        sample_profile(payment_delays_12m=5, employment_years=0, employment_type="Informel / Sans contrat"),
        RiskParameters(),
    )
    high = assess_credit(
        sample_profile(payment_delays_12m=0, employment_years=10, employment_type="CDI / Fonctionnaire"),
        RiskParameters(),
    )
    assert high["score"] > low["score"]
    assert high["probability_of_default"] < low["probability_of_default"]


def test_invalid_income_is_rejected():
    with pytest.raises(ValueError):
        assess_credit(sample_profile(monthly_income=0), RiskParameters())
