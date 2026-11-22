# Simulateur de risque de crédit

Application web en **Python** et **Streamlit** pour illustrer l'analyse du risque de crédit d'un emprunteur individuel.

## Fonctionnalités

- Saisie des caractéristiques du prêt et de la situation financière de l'emprunteur.
- Calcul d'un score de crédit explicable sur 100 points.
- Estimation indicative de la probabilité de défaut (PD).
- Estimation de la perte en cas de défaut (LGD), de l'exposition au défaut (EAD) et de la perte attendue (EL).
- Calcul de la mensualité et du taux d'effort.
- Décision indicative : accord, étude complémentaire ou refus.
- Visualisation de la contribution des critères au score et analyse de sensibilité de la perte attendue.
- Export des résultats au format CSV.

## Installation locale

Python 3.10 ou plus récent est recommandé.

```bash
git clone https://github.com/edmondadankanhounde392-web/credit-risk-simulator.git
cd credit-risk-simulator
python -m venv .venv
```

Activer l'environnement virtuel :

- Windows : `.venv\\Scripts\\activate`
- Linux/macOS : `source .venv/bin/activate`

Installer les dépendances et lancer l'application :

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Méthodologie résumée

Le moteur applique des règles explicites pour calculer un score, puis transforme ce score en PD indicative au moyen d'une fonction logistique paramétrée manuellement.

- **PD** : probabilité indicative de défaut.
- **LGD** : part de l'exposition qui serait perdue en cas de défaut, estimée ici par une heuristique liée aux garanties et à l'apport.
- **EAD** : exposition au défaut, calculée comme le prêt augmenté de la fraction mobilisable d'un engagement non décaissé.
- **EL** : perte attendue, calculée par `PD × EAD × LGD`.

La documentation détaillée est disponible dans [docs/methodology.md](docs/methodology.md).

## Limites importantes

La PD n'est pas issue d'une régression logistique entraînée sur un historique de crédits. Les paramètres ne sont pas calibrés sur un portefeuille réel. La LGD est simplifiée et ne modélise pas les délais ni les coûts de recouvrement. Les décisions sont pédagogiques et ne doivent pas être utilisées pour une véritable décision d'octroi de crédit.

## Structure

```text
.
├── app.py
├── src/
│   ├── __init__.py
│   └── credit_risk.py
├── docs/
│   └── methodology.md
├── tests/
│   └── test_credit_risk.py
├── requirements.txt
└── README.md
```

## Auteur

Projet personnel de démonstration en statistiques, probabilités et analyse du risque de crédit.
