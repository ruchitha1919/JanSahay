# 🌾 JanSahay – Local Citizen Assistance Prototype

## 📌 Project Overview

JanSahay is a local demonstration prototype designed to help farmers, rural communities, and people with limited digital literacy explore sample scheme guidance and public-service workflows.

The prototype demonstrates scheme discovery, eligibility checks, document guidance, claim checks, and citizen assistance through a multilingual interface. It does not connect to an AI model, a government system, or a live fact-checking source.

## 🎯 Project Objectives

- Make government schemes and public services more accessible to rural citizens.
- Help farmers understand scheme eligibility and application requirements.
- Provide assistance in English, Hindi, and Telugu.
- Provide deterministic, locally grounded assistance without implying a live AI service.
- Read visible page content aloud when the browser has a voice for the selected language.
- Help citizens identify potentially fake or suspicious government-related messages and claims.

## ✨ Key Features

- **Multilingual Interface:** Supports English, Hindi, and Telugu, with language selection at the initial login screen. The selected language is maintained throughout the application.
- **Scheme Finder:** Helps citizens discover government schemes and view eligibility criteria specific to each scheme.
- **Local Assistant:** Uses the configured demonstration schemes and the signed-in citizen's saved cases to answer supported scheme, document, service, and request questions. Unsupported questions are acknowledged; exchanges are retained in the local SQLite interaction history. This is deterministic rule-based guidance, not AI.
- **Claim Check:** Compares submitted text with a small set of facts about this local prototype and deterministic scam-wording rules. It returns Verified, False, Unverified, or Suspicious only where those local rules support that result. Unknown claims remain Unverified; results are not official verification and do not consult external sources.
- **Document Assistance:** Provides document-related guidance and scheme-specific checklists.
- **Request Tracking:** Allows citizens to track their assistance requests and progress through different stages.
- **Page Reader:** Reads visible main-page text on login, citizen, and volunteer screens in the selected English, Telugu, or Hindi locale. It excludes navigation and hidden content, cancels playback when stopped or when page content changes, and requires a browser voice matching the selected language. It does not accept microphone input or use a different-language fallback voice.
- **Telephone Assistance:** Demonstrates an IVR-based assistance experience with a clickable phone number and simulated call interaction.
- **Service Directory:** Helps citizens explore relevant assistance services.
- **Reminders:** Helps citizens keep track of important follow-ups.
- **Community Insights:** Demonstrates community-level assistance insights.
- **Farmer-focused Design:** Uses an agriculture-inspired visual theme throughout the application.

## 🛠️ Technology Stack

| Category | Technology |
|---|---|
| Programming Language | Python |
| Frontend | Streamlit |
| Database | SQLite |
| Testing | Pytest |
| Development Environment | VS Code |
| Version Control | Git and GitHub |
| AI-assisted Development | GitHub Copilot |
| Development Methodology | BMAD Method |

## 📂 Project Structure

```text
JanSahay/
│
├── app.py
├── requirements.txt
│
├── jansahay/
│   ├── __init__.py
│   ├── db.py
│   ├── i18n.py
│   ├── rules.py
│   └── voice.py
│
├── tests/
│   ├── test_app.py
│   └── test_db.py
│
└── .gitignore
```

## ⚙️ Installation and Usage

### 1. Clone the repository

```bash
git clone https://github.com/ruchitha1919/JanSahay.git
cd JanSahay
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

For Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application locally

```bash
streamlit run app.py
```

### 6. Access the application

Open your browser and visit:

**http://localhost:8501**

## 📝 Project Status

JanSahay is currently a working prototype demonstrating multilingual citizen assistance, scheme discovery, local claim checks, document guidance, request tracking, and browser-based page reading.

The assistant, verification, schemes, office listings, and telephone behaviors are local demonstrations. No paid or external AI/verification APIs are used. Browser speech is available only when the user's browser supplies a matching language voice; without one, the reader reports that speech is unavailable instead of using a mismatched voice. The application is not an officially integrated government service, and claim results do not constitute official government confirmation.

## 🚀 Live Demo

https://jansahay-ai.streamlit.app/

---

<p align="center">
  <strong>JanSahay – Bridging the Digital Accessibility Gap 🌱</strong>
</p>