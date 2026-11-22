from __future__ import annotations

import io
import pandas as pd
import plotly.express as px
import streamlit as st

from src.credit_risk import BorrowerProfile, RiskParameters, assess_credit

st.set_page_config(
    page_title="Simulateur de risque de crédit",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Simulateur de risque de crédit")
st.caption(
    "Outil pédagogique d'aide à l'analyse d'un dossier de crédit. "
    "Les résultats sont indicatifs et ne remplacent pas une décision bancaire."
)

with st.sidebar:
    st.header("Paramètres de décision")
    max_pd = st.slider("PD maximale acceptée (%)", 1.0, 60.0, 20.0, 1.0)
    max_ratio = st.slider("Taux d'effort maximal (%)", 10.0, 70.0, 40.0, 1.0)
    margin = st.slider("Marge de risque ajoutée au taux (%)", 0.0, 10.0, 2.0, 0.25)

st.subheader("1. Caractéristiques du crédit")
c1, c2, c3 = st.columns(3)
with c1:
    loan_amount = st.number_input("Montant du prêt (FCFA)", min_value=1_000.0, value=1_000_000.0, step=50_000.0)
    term = st.number_input("Durée (mois)", min_value=1, max_value=360, value=36)
with c2:
    annual_rate = st.number_input("Taux annuel (%)", min_value=0.0, max_value=100.0, value=12.0, step=0.5)
    down_payment = st.number_input("Apport personnel (FCFA)", min_value=0.0, value=100_000.0, step=10_000.0)
with c3:
    collateral = st.number_input("Valeur estimée des garanties (FCFA)", min_value=0.0, value=500_000.0, step=25_000.0)
    undrawn = st.number_input("Engagement non décaissé (FCFA)", min_value=0.0, value=0.0, step=25_000.0)
    ccf = st.slider("CCF (%)", 0, 100, 50, 5)

st.subheader("2. Situation financière de l'emprunteur")
c1, c2, c3 = st.columns(3)
with c1:
    income = st.number_input("Revenu mensuel net (FCFA)", min_value=1.0, value=250_000.0, step=10_000.0)
    fixed = st.number_input("Charges fixes mensuelles (FCFA)", min_value=0.0, value=40_000.0, step=5_000.0)
with c2:
    existing = st.number_input("Mensualités des crédits en cours (FCFA)", min_value=0.0, value=20_000.0, step=5_000.0)
    delays = st.number_input("Retards de paiement sur 12 mois", min_value=0, max_value=12, value=0)
with c3:
    age = st.number_input("Âge (années)", min_value=18, max_value=100, value=30)
    seniority = st.number_input("Ancienneté professionnelle (années)", min_value=0.0, max_value=60.0, value=3.0, step=0.5)
    employment = st.selectbox("Type d'emploi", ["CDI / Fonctionnaire", "CDD", "Indépendant", "Informel / Sans contrat"])

run = st.button("Évaluer le risque de crédit", type="primary", use_container_width=True)

if run:
    try:
        borrower = BorrowerProfile(
            loan_amount=loan_amount,
            term_months=int(term),
            annual_rate_pct=annual_rate,
            down_payment=down_payment,
            collateral_value=collateral,
            monthly_income=income,
            monthly_fixed_charges=fixed,
            existing_monthly_credit=existing,
            payment_delays_12m=int(delays),
            employment_years=seniority,
            employment_type=employment,
            age=int(age),
            undrawn_commitment=undrawn,
            ccf_pct=float(ccf),
        )
        parameters = RiskParameters(max_pd_pct=max_pd, max_debt_service_pct=max_ratio, risk_margin_pct=margin)
        result = assess_credit(borrower, parameters)
        st.session_state["assessment"] = result
    except ValueError as exc:
        st.error(str(exc))

result = st.session_state.get("assessment")
if result:
    st.divider()
    st.subheader("3. Résultats de l'évaluation")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Score de crédit", f'{result["score"]}/100')
    k2.metric("Probabilité de défaut (PD)", f'{result["probability_of_default"]:.1%}')
    k3.metric("Perte attendue (EL)", f'{result["expected_loss"]:,.0f} FCFA')
    k4.metric("Taux d'effort", f'{result["debt_service_ratio"]:.1f}%')

    if result["decision"] == "Accord indicatif":
        st.success(result["decision"])
    elif result["decision"] == "Étude complémentaire":
        st.warning(result["decision"])
    else:
        st.error(result["decision"])
    for reason in result["reasons"]:
        st.write(f"• {reason}")

    a, b = st.columns(2)
    with a:
        st.markdown("**Indicateurs de risque**")
        st.write(f'- LGD (perte en cas de défaut) : **{result["loss_given_default"]:.1%}**')
        st.write(f'- EAD (exposition au défaut) : **{result["exposure_at_default"]:,.0f} FCFA**')
        st.write(f'- Mensualité estimée : **{result["monthly_payment"]:,.0f} FCFA**')
        st.write(f'- Taux annuel suggéré : **{result["suggested_rate_pct"]:.2f}%**')
    with b:
        parts = pd.DataFrame({"Critère": list(result["score_parts"].keys()), "Points": list(result["score_parts"].values())})
        fig = px.bar(parts, x="Points", y="Critère", orientation="h", title="Décomposition du score")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Sensibilité de la perte attendue à la PD**")
    pds = [max(0.0, result["probability_of_default"] * factor) for factor in (0.5, 0.75, 1.0, 1.25, 1.5)]
    sensitivity = pd.DataFrame({
        "PD": [f"{p:.1%}" for p in pds],
        "Perte attendue (FCFA)": [p * result["exposure_at_default"] * result["loss_given_default"] for p in pds],
    })
    fig2 = px.line(sensitivity, x="PD", y="Perte attendue (FCFA)", markers=True, title="Sensibilité de l'EL à la probabilité de défaut")
    st.plotly_chart(fig2, use_container_width=True)

    export = {
        "score": result["score"],
        "PD_pct": result["probability_of_default"] * 100,
        "LGD_pct": result["loss_given_default"] * 100,
        "EAD_FCFA": result["exposure_at_default"],
        "EL_FCFA": result["expected_loss"],
        "mensualite_FCFA": result["monthly_payment"],
        "taux_effort_pct": result["debt_service_ratio"],
        "taux_suggere_pct": result["suggested_rate_pct"],
        "decision_indicative": result["decision"],
    }
    csv = pd.DataFrame([export]).to_csv(index=False).encode("utf-8-sig")
    st.download_button("Télécharger les résultats (CSV)", data=csv, file_name="evaluation_risque_credit.csv", mime="text/csv")

    with st.expander("Voir les détails du calcul"):
        st.json({"score_parts": result["score_parts"], "parametres": result["parameters"]})

st.divider()
st.caption(
    "Avertissement méthodologique : la PD provient ici d'une fonction logistique paramétrée manuellement "
    "à partir d'un score explicable. Elle n'est ni entraînée sur des données historiques ni calibrée. "
    "La LGD est une heuristique simplifiée. Ne pas utiliser pour accorder/refuser réellement un crédit."
)
