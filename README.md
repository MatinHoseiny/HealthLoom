<p align="center" style="margin-top: -20px; margin-bottom: -40px;">
  <img src="media/logo.png" alt="HealthLoom Logo" width="250" />
</p>

<p align="center" style="color: #555555; font-size: 15px;">
  Secure medical document analysis and processing application.
</p>

<div align="center">

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/MatinHoseiny/HealthLoom)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](#docker-deployment)

</div>

---

## Features

* **Document Processing:** Automated parsing of PDF and text-based medical records.
* **Entity Extraction:** Identifies and profiles medications, dosages, and relevant medical history.
* **Contextual Analysis:** Interactive interface for querying uploaded document data.
* **Data Security:** Localized file storage and tracking within the deployment environment.

---

## System Architecture

HealthLoom utilizes a microservices-oriented architecture designed for accurate and performant health data extraction.

### Backend Infrastructure

The backend is engineered for reliability and high performance, leveraging **FastAPI** for concurrent request handling and efficient API routing. The core logic is powered by **LangGraph**, which orchestrates a specialized processing pipeline:

* **Ingestion Engine:** Implements advanced document parsing with cryptographic hashing to prevent redundant processing of identical files, saving system resources.
* **Extraction Pipeline:** Dedicated processing nodes designed specifically for medical entity recognition, extracting critical data such as prescriptions, dosages, and contraindications.
* **Dynamic Routing:** An intelligent routing mechanism that evaluates user queries and directs them to the optimal subsystem (e.g., retrieving specific document context, accessing patient history, or querying general medical knowledge).
* **Data Persistence:** Utilizes **PostgreSQL** with async SQLAlchemy for reliable, high-performance tracking of document metadata, health records, and conversation history.

### Tech Stack

| Component | Technology |
|---|---|
| Frontend | React (Vite), CSS |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| AI / LLM | Google Gemini API |
| Processing Pipeline | LangGraph, LangChain |
| Observability | LangFuse |
| Deployment | Docker, Docker Compose |

---

## Installation and Deployment

### Docker Deployment (Recommended)

1. Clone the repository.
2. Configure `.env` variables if required.
3. Build and start the containers:
   ```bash
   docker-compose up --build
   ```
4. Access the application at `http://localhost:5173`.

### Local Development

**Backend:**
1. Navigate to the `backend/` directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

**Frontend:**
1. Navigate to the `frontend/` directory.
2. Install dependencies and start the development server:
   ```bash
   npm install
   npm run dev
   ```

---

## Project Structure

```text
HealthLoom/
├─ backend/           # FastAPI application, LangGraph pipelines, Database schemas
├─ frontend/          # React application, UI components
├─ docker-compose.yml # Container orchestration configuration
├─ README.md          # Project documentation
```

---

## Roadmap

* Improve mobile interface responsiveness.
* Implement multi-user authentication and session management.
* Add data visualization for extracted health metrics.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
