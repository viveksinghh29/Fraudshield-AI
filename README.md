# FraudShield AI

### GenAI-Powered Credit Card Fraud Detection & Analyst Assistant

FraudShield AI is an end-to-end fraud detection platform that combines **Machine Learning, SHAP Explainable AI, and Generative AI** to detect suspicious transactions, explain model predictions, and help analysts investigate flagged transactions using natural language.

The system supports real-time transaction scoring, batch CSV analysis, model evaluation, fraud analytics, audit logging, and an AI assistant grounded in the actual prediction and explanation data.

---

## Key Features

*  **Fraud Detection** — ML-based transaction risk scoring
*  **Explainable AI** — SHAP-based explanations for individual predictions
*  **AI Analyst Assistant** — Natural-language investigation of flagged transactions
*  **Fraud Analytics** — Trends, model performance, and transaction history
*  **Batch Prediction** — Analyze transactions through CSV upload
*  **Authentication & Authorization** — JWT-based security
*  **Audit Logging** — Track predictions and analyst activity
*  **Multiple LLM Providers** — Ollama, Groq, and OpenAI-compatible APIs
*  **Model Evaluation** — Precision, Recall, F1, ROC-AUC, PR-AUC, confusion matrix, and calibration

---

## Architecture

```text
                     ┌──────────────────────┐
                     │     React Frontend   │
                     │ Dashboard • Analytics│
                     │ Prediction • AI Chat │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │    FastAPI Backend   │
                     │ Auth • REST APIs     │
                     │ Business Logic       │
                     └──────────┬───────────┘
                                │
               ┌────────────────┼────────────────┐
               ▼                ▼                ▼
        ┌────────────┐   ┌──────────────┐  ┌─────────────┐
        │ PostgreSQL │   │ ML Pipeline  │  │    Redis    │
        │            │   │ XGBoost etc. │  │    Cache    │
        └────────────┘   └──────┬───────┘  └─────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │ SHAP         │
                         │ Explainability│
                         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │ AI Assistant │
                         │ Ollama/Groq/ │
                         │ OpenAI API   │
                         └──────────────┘
```

---

## Fraud Detection Workflow

```text
Transaction
     │
     ▼
Feature Processing
     │
     ▼
ML Model Prediction
     │
     ├──► Fraud / Legitimate
     │
     ▼
SHAP Explanation
     │
     ▼
Risk Assessment
     │
     ▼
Analyst AI Assistant
     │
     ▼
Natural-Language Investigation
```

---

## Machine Learning

The platform evaluates multiple classification models:

* Logistic Regression
* Random Forest
* Gradient Boosting
* XGBoost
* LightGBM

Model selection is based on evaluation performance from the latest training run.

### Explainability

Each prediction can be analyzed using **SHAP**, providing:

* Feature contribution
* Positive/negative impact
* Prediction base value
* Top contributing features

This allows analysts to understand **why a transaction was flagged**, rather than relying on a black-box prediction.

---

## AI Analyst Assistant

The assistant allows analysts to ask questions about a flagged transaction in natural language.

Example:

```text
Why was this transaction classified as high risk?
```

```text
Which features contributed most to the fraud prediction?
```

```text
What makes this transaction suspicious?
```

Responses are grounded in the transaction's **actual prediction and SHAP explanation data** rather than fabricated transaction information.

---

## Tech Stack

| Layer               | Technologies                                   |
| ------------------- | ---------------------------------------------- |
| **Frontend**        | React 18, TypeScript, Vite, Tailwind CSS       |
| **Backend**         | FastAPI, SQLAlchemy 2.0, Pydantic v2           |
| **Database**        | PostgreSQL, Alembic                            |
| **ML**              | Scikit-learn, XGBoost, LightGBM, SMOTE, Optuna |
| **Explainability**  | SHAP                                           |
| **AI**              | Ollama, Groq, OpenAI-compatible APIs           |
| **Caching / Tasks** | Redis, Celery                                  |
| **Visualization**   | Recharts                                       |
| **Infrastructure**  | Docker Compose                                 |

---

## Analytics

FraudShield AI provides monitoring for:

* Fraud detection trends
* Transaction history
* Model performance
* Precision & Recall
* F1 Score
* ROC-AUC
* PR-AUC
* Confusion Matrix
* Model calibration
* Audit events

---

## Project Structure

```text
FraudShield-AI/
├── backend/             # FastAPI backend
│   ├── app/
│   ├── tests/
│   └── ...
│
├── frontend/            # React + TypeScript frontend
│   ├── src/
│   └── ...
│
├── ml_research/         # ML experiments & training pipeline
├── docs/                # Architecture & API documentation
├── docker-compose.yml
└── README.md
```

---

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd fraudshield-ai
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env
```

Configure the required database, JWT, and LLM settings.

### 4. Access the application

| Service      | URL                          |
| ------------ | ---------------------------- |
| Frontend     | `http://localhost:5173`      |
| API          | `http://localhost:8000`      |
| Swagger Docs | `http://localhost:8000/docs` |

For detailed installation and troubleshooting, see:

`docs/installation-guide.md`

---

## Testing

The project includes backend, API, security, and integration tests.

```bash
pytest
```

Current verified test status:

```text
201 backend tests passing
86% backend coverage
```

---

## Documentation

Detailed documentation is available in the `docs/` directory:

* **Architecture** — system design and engineering decisions
* **API** — endpoint documentation
* **Installation** — setup and troubleshooting
* **Developer Guide** — extending the system
* **Testing Guide** — test strategy and coverage
* **ER Diagram** — database design

---

## Future Improvements

* Real-time transaction streaming
* Advanced model monitoring & drift detection
* Human-in-the-loop analyst workflows
* Feature store integration
* Real-time alerting
* Cloud deployment
* Kubernetes orchestration
* Advanced fraud graph analytics
* Continuous model retraining
* Enterprise observability

---

## Author

**Vivek Kumar Singh**

AI & Machine Learning • Data Analytics • Backend Engineering • Generative AI

---
