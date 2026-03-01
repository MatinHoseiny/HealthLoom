<p align="center" style="margin-top: -20px; margin-bottom: -40px;">
  <img src="media/logo.png" alt="HealthLoom Logo" width="250" />
</p>

<p align="center" style="color: #aaaaaa; font-size: 15px;">
  An intelligent, secure health document analysis tool — upload, analyze, and understand your medical history.
</p>

<div align="center">

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/MatinHoseiny/HealthLoom)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)]()

</div>

<hr style="height:2px;border:none;background:linear-gradient(90deg,#00c6ff,#0072ff);border-radius:1px;">

## 🚀 Highlights
<div align="center">

| | |
|:--:|:--:|
| 📄 **Smart Document Analysis** | AI-driven medical document parsing |
| 💊 **Medication Tracking** | Automatic extraction and profiling |
| 💬 **Interactive Chat** | Context-aware AI assistant |
| 🔒 **Secure Storage** | Localized file and data tracking |

</div>

<hr style="height:2px;border:none;background:linear-gradient(90deg,#00c6ff,#0072ff);border-radius:1px;">

## 📸 App Media

<div align="center">
  <table>
    <tr>
      <td align="center" width="50%">
        <img src="" alt="Upload Interface" width="95%" style="border-radius:14px; box-shadow:0 0 15px rgba(0,0,0,0.35); margin:8px;" /><br>
        <sub><b>Upload Interface</b><br><i>Seamlessly add your medical documents</i></sub>
      </td>
      <td align="center" width="50%">
        <img src="" alt="Analysis Chat" width="95%" style="border-radius:14px; box-shadow:0 0 15px rgba(0,0,0,0.35); margin:8px;" /><br>
        <sub><b>Analysis Chat</b><br><i>Talk dynamically with your data</i></sub>
      </td>
    </tr>
  </table>
</div>

<hr style="height:2px;border:none;background:linear-gradient(90deg,#00c6ff,#0072ff);border-radius:1px;">

## ⚙️ System Overview

> Built for secure, accurate, and rapid health data comprehension.

- **Automated Processing** of uploaded PDF and text documents
- **Extraction:** text, medications, dates, and medical history
- **LangGraph Integration:** utilizing state-of-the-art conversational pipelines

<hr style="height:2px;border:none;background:linear-gradient(90deg,#00c6ff,#0072ff);border-radius:1px;">

## 🧠 Deep Analysis Capabilities

The HealthLoom backend is a highly capable and specifically engineered system for medical text reasoning:

* **⚡ Optimized Document Processing:** Utilizes advanced parsing libraries and hash-tracking to ensure documents are not re-processed unnecessarily.
* **💊 Medication Extractor:** A specific node focused on identifying prescriptions, dosages, and warnings.
* **💬 Interactive Conversation Router:** Routes user questions between the database, document context, or general health knowledge.

<hr style="height:2px;border:none;background:linear-gradient(90deg,#00c6ff,#0072ff);border-radius:1px;">

## 🛠 Tech Stack

<div align="center">

| Layer | Technology |
|-------|-------------|
| 🎨 Frontend | React (Vite) + CSS |
| ⚙️ Backend | FastAPI (Python) |
| 🗄️ Database | SQLite |
| 🧠 AI Engine | LangGraph / LangChain |
| 🐳 Packaging | Docker & Docker Compose |

</div>

<p align="center">
  <img src="https://img.shields.io/badge/React-18-blue?logo=react&logoColor=white&style=for-the-badge" />
  <img src="https://img.shields.io/badge/FastAPI-Modern-green?logo=fastapi&style=for-the-badge" />
  <img src="https://img.shields.io/badge/Docker-Containerized-blueviolet?logo=docker&logoColor=white&style=for-the-badge" />
</p>

<hr style="height:2px;border:none;background:linear-gradient(90deg,#00c6ff,#0072ff);border-radius:1px;">

## 🚀 Quick Install

### 🐳 Using Docker
1. Clone the repository
2. Configure `.env` variables if needed
3. Run `docker-compose up --build`
4. Access the frontend at `http://localhost:5173`

### 💻 Local Run
1. Go to `backend/` and run `pip install -r requirements.txt` followed by `uvicorn main:app --reload`
2. Go to `frontend/` and run `npm install` followed by `npm run dev`

<hr style="height:2px;border:none;background:linear-gradient(90deg,#00c6ff,#0072ff);border-radius:1px;">

## 📁 Project Structure

```
HealthLoom/
├─ 📂 backend/         # FastAPI, LangGraph nodes, DB schemas
├─ 📂 frontend/        # React components, UI styling
├─ 📄 docker-compose.yml 
├─ 📄 README.md        # Documentation
```

<hr style="height:2px;border:none;background:linear-gradient(90deg,#00c6ff,#0072ff);border-radius:1px;">

## 🔮 Roadmap

- 📱 Mobile responsiveness improvements
- 🩺 Multi-user support
- 📊 Data visualization for health metrics

<hr style="height:2px;border:none;background:linear-gradient(90deg,#00c6ff,#0072ff);border-radius:1px;">

## 📜 License



<hr style="height:2px;border:none;background:linear-gradient(90deg,#00c6ff,#0072ff);border-radius:1px;">

<div align="center">

**Built with ❤️.**

[![GitHub stars](https://img.shields.io/github/stars/MatinHoseiny/HealthLoom?style=social)](https://github.com/MatinHoseiny/HealthLoom)
[![GitHub forks](https://img.shields.io/github/forks/MatinHoseiny/HealthLoom?style=social)](https://github.com/MatinHoseiny/HealthLoom)
</div>
