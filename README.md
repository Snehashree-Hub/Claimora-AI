# Claimora AI

**AI-Powered Health Insurance Claim Assistance Platform**

Claimora is a full-stack project designed to simplify the health insurance claim journey through AI-assisted guidance, document handling, eligibility checks, fraud-risk analysis, claim tracking, and hospital and doctor recommendations.

## Features

- AI-powered health insurance claim assistance
- Claim document upload and verification workflow
- Policy and eligibility analysis
- Fraud-risk detection support
- Claim status tracking
- Hospital and doctor recommendations
- Hospital location and map integration
- Retrieval-Augmented Generation (RAG) support
- React-based web interface
- FastAPI backend

## Technology Stack

### Frontend
- React
- Vite
- React Router
- Recharts
- Leaflet and React Leaflet
- Framer Motion

### Backend
- Python
- FastAPI
- Machine learning components
- RAG-based document retrieval
- SQLite for local development

## Project Structure

```text
health_insurance_claim_agent/
├── backend/
│   ├── app/
│   ├── data/
│   ├── datasets/
│   ├── ml_models/
│   ├── rag/
│   ├── recommendation/
│   └── requirements.txt
├── claimora-frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

## Local Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd health_insurance_claim_agent
```

### 2. Backend setup

Create and activate a Python virtual environment, then install the backend dependencies:

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r .\backend\requirements.txt
```

Configure the required environment variables in a local `.env` file. Never commit API keys or credentials.

Start the backend using the entry point configured in the project.

### 3. Frontend setup

```bash
cd claimora-frontend
npm install
npm run dev
```

Configure frontend environment variables locally according to the API URL settings used by the application.

## Important Notes

- This project is intended for demonstration and development.
- AI-generated guidance and fraud-risk indicators are not definitive insurance decisions.
- Hospital, doctor, policy, and claim information must be verified with the relevant providers or insurer.
- Do not upload real patient records, credentials, API keys, or confidential documents to a public repository.

## License

No license has been assigned yet.
