# Méthodologie du simulateur

## 1. Objectif

Le projet illustre une chaîne simplifiée d'analyse du risque de crédit pour un emprunteur individuel. Les données saisies sont des caractéristiques financières, socio-économiques et professionnelles.

## 2. Score de crédit

Un score compris entre 0 et 100 est calculé à partir de sept dimensions : revenu, capacité de remboursement, historique de paiement, stabilité et type d'emploi, garanties, apport personnel et âge. Chaque dimension contribue selon des règles explicites dans `src/credit_risk.py`.

Le score est un indicateur synthétique conçu pour rendre le raisonnement transparent. Les pondérations sont des choix de prototype et ne représentent pas une norme bancaire.

## 3. Probabilité de défaut (PD)

Le score est transformé en probabilité indicative par :

`PD = 1 / (1 + exp(-(3 - 0,075 × score)))`

Cette fonction est monotone décroissante : une hausse du score entraîne une baisse de la PD estimée. Les coefficients sont fixés manuellement. Il ne s'agit donc pas d'une régression logistique entraînée sur des observations historiques, et la PD ne doit pas être interprétée comme une probabilité empiriquement calibrée.

## 4. Exposition au défaut (EAD)

`EAD = montant du prêt + CCF × engagement non décaissé`

Le CCF (Credit Conversion Factor) est saisi en pourcentage puis converti en proportion dans le calcul.

## 5. Perte en cas de défaut (LGD)

Le prototype utilise une heuristique fondée sur le rapport entre garanties plus apport personnel et montant du prêt :

`LGD = clamp(0,90 - 0,55 × (garanties + apport) / prêt ; 0,05 ; 0,90)`

Cette approximation ne prend pas en compte les coûts de recouvrement, les délais de réalisation des sûretés, les décotes spécifiques ni les effets juridiques.

## 6. Perte attendue (EL)

`EL = PD × EAD × LGD`

La perte attendue est exprimée en FCFA.

## 7. Taux d'effort

La mensualité est calculée selon la formule d'un prêt amortissable à échéances constantes. Le taux d'effort est :

`(mensualité + charges fixes + mensualités des autres crédits) / revenu mensuel × 100`

## 8. Décision indicative

Les seuils de PD maximale et de taux d'effort maximal sont paramétrables. Le moteur propose un accord indicatif, une étude complémentaire ou un refus indicatif. Ces libellés ne constituent pas une recommandation financière réelle.

## 9. Pistes d'amélioration scientifique

Pour passer à un modèle statistique robuste, il faudra notamment :
- constituer un jeu de données documenté, légalement exploitable et représentatif ;
- définir précisément l'événement de défaut et l'horizon temporel ;
- séparer les données d'entraînement, de validation et de test ;
- entraîner et comparer une régression logistique et des modèles d'arbres ;
- évaluer discrimination, calibration, stabilité et biais ;
- documenter les variables, les valeurs manquantes et les limites d'usage.
