# FraudShield AI

### GenAI-Powered Credit Card Fraud Detection & Analyst Assistant

FraudShield AI is an end-to-end fraud detection platform that combines **Machine Learning, SHAP Explainable AI, and Generative AI** to detect suspicious transactions, explain model predictions, and help analysts investigate flagged transactions using natural language.

The system supports real-time transaction scoring, batch CSV analysis, model evaluation, fraud analytics, audit logging, and an AI assistant grounded in actual prediction and explanation data.

---

## 🚀 Key Features

* 🔍 **Fraud Detection** — ML-based transaction risk scoring
* 🧠 **Explainable AI** — SHAP-based explanations for individual predictions
* 🤖 **AI Analyst Assistant** — Natural-language investigation of flagged transactions
* 📊 **Fraud Analytics** — Trends, model performance, and transaction history
* 📁 **Batch Prediction** — Analyze transactions through CSV upload
* 🔐 **Authentication & Authorization** — JWT-based security
* 📝 **Audit Logging** — Track predictions and analyst activity
* 🔌 **Multiple LLM Providers** — Ollama, Groq, and OpenAI-compatible APIs
* 📈 **Model Evaluation** — Precision, Recall, F1, ROC-AUC, PR-AUC, confusion matrix, and calibration

---

## 🏗️ Architecture

```text
                     ┌──────────────────────┐
                     │    React Frontend    │
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
                ┌───────────────┼────────────────┐
                ▼               ▼                ▼
         ┌────────────┐  ┌──────────────┐  ┌─────────────┐
         │ PostgreSQL │  │ ML Pipeline  │  │    Redis    │
         │            │  │ XGBoost etc. │  │    Cache    │
         └────────────┘  └──────┬───────┘  └─────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │     SHAP     │
                         │Explainability│
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

## 🔄 Fraud Detection Workflow

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

## 🤖 Machine Learning

FraudShield AI evaluates multiple classification models:

* Logistic Regression
* Random Forest
* Gradient Boosting
* XGBoost
* LightGBM

Model selection is based on evaluation performance from the latest training run.

### Explainable AI with SHAP

Each prediction can be analyzed using **SHAP**, providing:

* Feature contribution
* Positive/negative impact
* Prediction base value
* Top contributing features

This allows analysts to understand **why a transaction was flagged**, rather than relying on a black-box prediction.

---

## 💬 AI Analyst Assistant

The AI assistant allows analysts to investigate flagged transactions using natural language.

Example questions:

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

## 🛠️ Tech Stack

| Layer                | Technologies                                   |
| -------------------- | ---------------------------------------------- |
| **Frontend**         | React 18, TypeScript, Vite, Tailwind CSS       |
| **Backend**          | FastAPI, SQLAlchemy 2.0, Pydantic v2           |
| **Database**         | PostgreSQL, Alembic                            |
| **Machine Learning** | Scikit-learn, XGBoost, LightGBM, SMOTE, Optuna |
| **Explainability**   | SHAP                                           |
| **AI / LLM**         | Ollama, Groq, OpenAI-compatible APIs           |
| **Caching / Tasks**  | Redis, Celery                                  |
| **Visualization**    | Recharts                                       |
| **Infrastructure**   | Docker Compose                                 |

---

## 📊 Analytics

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

## 📁 Project Structure

```text
FraudShield-AI/
│
├── backend/                  # FastAPI backend
│   ├── app/
│   ├── tests/
│   └── ...
│
├── frontend/                 # React + TypeScript frontend
│   ├── src/
│   └── ...
│
├── ml_research/              # ML experiments & training pipeline
├── docs/                     # Architecture & API documentation
├── docker-compose.yml
└── README.md
```

---

# ⚡ Quick Start

## 1. Clone the Repository

```bash
git clone <repository-url>
cd fraudshield-ai
```

---

## 2. Configure Environment

Create the backend environment file.

### macOS / Linux

```bash
cp backend/.env.example backend/.env
```

### Windows PowerShell

```powershell
Copy-Item backend/.env.example backend/.env
```

Configure the required database, JWT, Redis, and LLM settings inside:

```text
backend/.env
```

> ⚠️ **Important:** Never commit `.env` files, API keys, passwords, or other secrets to GitHub.

---

# 🔵 Running the Backend

Open **Terminal 1**.

### Navigate to the backend

```powershell
cd "C:\Users\Lenovo\Desktop\PROJECTS\Fraudshield AI\backend"
```

### Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### Start the FastAPI server

```powershell
python -m uvicorn app.main:app --reload
```

The backend will run at:

```text
http://127.0.0.1:8000
```

### Swagger API Documentation

```text
http://127.0.0.1:8000/docs
```

> **Windows note:** Use `python -m uvicorn` instead of `uvicorn` to ensure the command uses the project's active virtual environment.

Keep Terminal 1 running.

---

# 🟢 Running the Frontend

Open **Terminal 2**.

### Navigate to the project root

```powershell
cd "C:\Users\Lenovo\Desktop\PROJECTS\Fraudshield AI"
```

### Navigate to the frontend

```powershell
cd frontend
```

### Install dependencies

```powershell
npm install
```

> Run `npm install` the first time, or whenever `package.json` changes.

### Start the development server

```powershell
npm run dev
```

The frontend will typically be available at:

```text
http://localhost:5173
```

Keep Terminal 2 running.

---

# ▶️ Run Frontend and Backend Together

FraudShield AI requires **two terminals** during local development.

### Terminal 1 — Backend

```powershell
cd "C:\Users\Lenovo\Desktop\PROJECTS\Fraudshield AI\backend"
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

### Terminal 2 — Frontend

```powershell
cd "C:\Users\Lenovo\Desktop\PROJECTS\Fraudshield AI"
cd frontend
npm install
npm run dev
```

### Local URLs

| Service      | URL                          |
| ------------ | ---------------------------- |
| Frontend     | `http://localhost:5173`      |
| Backend API  | `http://127.0.0.1:8000`      |
| Swagger Docs | `http://127.0.0.1:8000/docs` |

Open the frontend in your browser:

```text
http://localhost:5173
```

---

# 🔐 Authentication

FraudShield AI uses **JWT-based authentication**.

### Available Roles

* `admin`
* `analyst`
* `viewer`

Authentication endpoints are available through Swagger:

```text
http://127.0.0.1:8000/docs
```

### Main Authentication Endpoints

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
```

For local development, create a user through the registration endpoint before logging into the frontend.

---

# 🧪 Testing

The project includes backend, API, security, and integration tests.

From the `backend` directory:

```powershell
pytest
```

### Current Verified Test Status

```text
201 backend tests passing
86% backend coverage
```

---

# 📚 Documentation

Detailed documentation is available in the `docs/` directory:

* **Architecture** — System design and engineering decisions
* **API** — Endpoint documentation
* **Installation** — Setup and troubleshooting
* **Developer Guide** — Extending the system
* **Testing Guide** — Test strategy and coverage
* **ER Diagram** — Database design

---

# 🛠️ Troubleshooting

## Backend: `ModuleNotFoundError: No module named 'app'`

Make sure you are inside the `backend` directory:

```powershell
cd "C:\Users\Lenovo\Desktop\PROJECTS\Fraudshield AI\backend"
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then run:

```powershell
python -m uvicorn app.main:app --reload
```

---

## Backend: Uvicorn Launcher Error

If you see an error referring to an old project path or `uvicorn.exe`, use:

```powershell
python -m uvicorn app.main:app --reload
```

instead of:

```powershell
uvicorn app.main:app --reload
```

---

## Frontend Dependencies Missing

From the frontend directory:

```powershell
npm install
npm run dev
```

---

## Stop the Servers

Press:

```text
Ctrl + C
```

in each running terminal.

---

# 🚀 Future Improvements

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

# 👨‍💻 Author

**Vivek Kumar Singh**

AI & Machine Learning • Data Analytics • Backend Engineering • Generative AI
