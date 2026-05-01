# Poonawalla Fincorp Loan Wizard — Model Cards

## 1A. Credit Risk Dataset Generation (n=50,000)

- Credit Risk: 50000 rows | Default rate: 27.53% | Saved: C:\Users\ipate\Downloads\69d73c0904439_TenzorX_Problem_Statements\loan-onboarding\data\credit_risk_train.csv

## 1B. Fraud Detection Dataset (n=30,000)

- Fraud: 30000 rows | Fraud rate: 5.00% | Saved: C:\Users\ipate\Downloads\69d73c0904439_TenzorX_Problem_Statements\loan-onboarding\data\fraud_train.csv

## 1C. Age Estimation Validation Dataset (n=20,000)

- Age Validation: 20000 rows | Flag rate: 10.30% | Saved: C:\Users\ipate\Downloads\69d73c0904439_TenzorX_Problem_Statements\loan-onboarding\data\age_validation_train.csv

## 1D. Loan Offer Dataset (n=40,000)

- Loan Offers: 40000 rows | Avg Rate: 12.78% | Saved: C:\Users\ipate\Downloads\69d73c0904439_TenzorX_Problem_Statements\loan-onboarding\data\loan_offers_train.csv

## 1E. Speech Intent Dataset (n=5,000)

- Speech Intents: 5000 records | 8 classes | Saved: C:\Users\ipate\Downloads\69d73c0904439_TenzorX_Problem_Statements\loan-onboarding\data\speech_intents_train.jsonl

## 1F. Emotion/Stress Feature Dataset (n=15,000)

- Emotion: 15000 rows | 40 MFCC features | 5 classes | Saved: C:\Users\ipate\Downloads\69d73c0904439_TenzorX_Problem_Statements\loan-onboarding\data\emotion_features_train.csv

## 2A. Credit Risk Classifier (XGBoost + Optuna)

- Best Optuna AUC (val): 0.9581
- Test AUC: 0.9544 | F1: 0.9425 | Train Time: 37.7s
- Saved → C:\Users\ipate\Downloads\69d73c0904439_TenzorX_Problem_Statements\loan-onboarding\models\credit_risk_xgb.pkl
- Top-5 features: emi_to_income_ratio(0.641) | credit_score(0.297) | geo_mismatch(0.023) | video_stress_score(0.007) | monthly_income(0.006)

## 2B. Fraud Detection (XGBoost + class_weight)

- Test AUC: 0.9664 | F1: 0.5972 | Train Time: 0.6s | Saved: C:\Users\ipate\Downloads\69d73c0904439_TenzorX_Problem_Statements\loan-onboarding\models\fraud_detector.pkl

## 2C. Age Estimation Validator

- AUC: 1.0000 | F1: 0.9763 | Regression MAE: 3.42y | Saved: C:\Users\ipate\Downloads\69d73c0904439_TenzorX_Problem_Statements\loan-onboarding\models\age_validator.pkl

## 2D. Loan Offer Engine (Gradient Boosting Regressor)

- Amount Prediction RMSE: ₹5,666 | Saved: C:\Users\ipate\Downloads\69d73c0904439_TenzorX_Problem_Statements\loan-onboarding\models\offer_engine.pkl

## 2E. Speech Intent Classifier (TF-IDF + XGBoost)

- Macro F1: 0.8613 | Classes: 8 | Saved: C:\Users\ipate\Downloads\69d73c0904439_TenzorX_Problem_Statements\loan-onboarding\models\intent_classifier.pkl

## 2F. Emotion / Stress Classifier (MLP)

- Weighted F1: 0.9960 | Classes: ['anxious' 'confident' 'evasive' 'neutral' 'stressed'] | Saved: C:\Users\ipate\Downloads\69d73c0904439_TenzorX_Problem_Statements\loan-onboarding\models\emotion_clf.pkl

## 3. Writing Model Cards Report


---
_Report generated: 2026-04-18 00:30:39_


## Final Summary Table

| Model | Algorithm | Train Size | Metric | Status |
|-------|-----------|------------|--------|--------|
| Credit Risk XGBoost | XGBoost | 35,020 | AUC=0.954 | ✅ PASS |
| Fraud Detector | XGBoost | 21,012 | AUC=0.966 | ✅ PASS |
| Age Validator | LogisticReg + LinReg | 14,008 | AUC=1.000 | ✅ |
| Loan Offer Engine | LightGBM Regressor | 28,016 | RMSE=₹5,666 | ✅ |
| Speech Intent | TF-IDF + XGBoost | 3,502 | MacroF1=0.861 | ✅ |
| Emotion Classifier | MLP (256-128-64) | 10,506 | WeightedF1=0.996 | ✅ |