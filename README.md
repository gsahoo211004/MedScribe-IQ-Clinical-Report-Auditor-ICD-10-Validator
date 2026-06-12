# MedScribe-IQ

MedScribe-IQ is a clinical report auditor built with Streamlit, spaCy, and Google Gemini. It processes discharge summaries through an AI-powered pipeline that performs NLP entity extraction, negation detection, ICD-10 validation, LLM audit summarization, and MLflow run logging.

## Key Features

- Streamlit web UI for entering and auditing clinical text
- Medical entity extraction using spaCy and a custom medical dictionary
- Negation detection to avoid coding conditions that are denied or absent
- ICD-10 validation via a local lookup dictionary with optional WHO API fallback
- Audit report generation with Google Gemini
- Pipeline metrics and run tracking using MLflow
- Docker and Docker Compose support for local deployment

## Architecture Overview

The core app lives in `app.py` and uses the following modules:

- `src/nlp/extractor.py` — medical entity extraction and negation detection
- `src/icd/validator.py` — ICD-10 validation, local code lookup, WHO API fallback
- `src/llm/summarizer.py` — Gemini-powered audit summary generation
- `src/mlops/tracker.py` — MLflow logging for pipeline runs
- `src/database.py` — SQLAlchemy models and PostgreSQL database schema (optional)

## Getting Started

### Requirements

- Python 3.12+
- `pip` package manager
- Optional: Docker and Docker Compose for containerized deployment

### Local Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/<your-org>/MedScribe-IQ.git
   cd MedScribe-IQ
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. (Optional) Install the spaCy English model if needed:

   ```bash
   python -m spacy download en_core_web_sm
   ```

5. Create a `.env` file in the project root with the following values:

   ```env
   GEMINI_API_KEY=your_gemini_api_key
   ICD_CLIENT_ID=your_who_icd_client_id
   ICD_CLIENT_SECRET=your_who_icd_client_secret
   DB_USER=postgres
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=medscribe_iq
   ```

   - `GEMINI_API_KEY` is required for LLM audit summaries.
   - `ICD_CLIENT_ID` and `ICD_CLIENT_SECRET` are optional and used only when WHO ICD API access is available.

### Running Locally

Run the Streamlit app:

```bash
streamlit run app.py
```

Open the app in your browser at:

```
http://localhost:8501
```

### Docker Compose

Use Docker Compose to run the app together with PostgreSQL:

```bash
docker compose up --build
```

The app will be available at `http://localhost:8501`.

## MLflow Tracking

Pipeline runs are logged to a local SQLite tracking store by default.

To inspect run details, start MLflow UI with:

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Then open:

```
http://localhost:5000
```

## Important Notes

- The current primary user interface is the Streamlit app in `app.py`.
- The `src/database.py` module defines PostgreSQL models and can be used to initialize database tables if you want to persist reports and audit data.
- The WHO ICD API is optional; without it the app falls back to the in-project local ICD-10 dictionary.

## Project Structure

- `app.py` — main Streamlit application
- `Dockerfile` — container image definition
- `docker-compose.yml` — app + PostgreSQL service configuration
- `requirements.txt` — Python dependencies
- `src/` — pipeline modules and helpers
- `tests/` — test folder (add tests here)
- `reports/` — output reports directory

## Troubleshooting

- If spaCy cannot load `en_core_web_sm`, run:

  ```bash
  python -m spacy download en_core_web_sm
  ```

- If the LLM summary fails, verify `GEMINI_API_KEY` is set and valid.
- If WHO API calls fail, check `ICD_CLIENT_ID` / `ICD_CLIENT_SECRET` and network connectivity.
