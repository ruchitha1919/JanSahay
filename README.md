# 🌾 JanSahay – AI-Powered Citizen Assistance Platform

## 📌 Project Overview

JanSahay is an AI-powered citizen assistance platform designed to help farmers, rural communities, and people with limited digital literacy access government schemes and public services more easily.

The platform simplifies scheme discovery, eligibility checking, document guidance, claim verification, and citizen assistance through a multilingual and voice-enabled interface.

## 🎯 Project Objectives

- Make government schemes and public services more accessible to rural citizens.
- Help farmers understand scheme eligibility and application requirements.
- Provide assistance in English, Hindi, and Telugu.
- Simplify access to government-related information through AI-powered assistance.
- Enable voice-based interaction for people with limited digital literacy.
- Help citizens identify potentially fake or suspicious government-related messages and claims.

## ✨ Key Features

- **Multilingual Interface:** Supports English, Hindi, and Telugu, with language selection at the initial login screen. The selected language is maintained throughout the application.
- **Scheme Finder:** Helps citizens discover government schemes and view eligibility criteria specific to each scheme.
- **AI Assistant:** Provides guidance and answers to citizen-related queries.
- **Claim Verification:** Allows users to submit government-related messages or claims and receive one of four outcomes: Verified, False, Unverified, or Suspicious.
- **Document Assistance:** Provides document-related guidance and scheme-specific checklists.
- **Request Tracking:** Allows citizens to track their assistance requests and progress through different stages.
- **Voice Assistant:** Provides microphone access across application pages, supporting speech-to-text and text-to-speech where browser capabilities are available.
- **Multilingual Voice Support:** Supports voice interaction in English, Hindi, and Telugu based on the selected language.
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

JanSahay is currently a working prototype demonstrating multilingual citizen assistance, scheme discovery, claim verification, document guidance, request tracking, and voice-based interactions.

Some features use simulated workflows. The application is not an officially integrated government service, and its verification results do not constitute official government confirmation.

## 🚀 Live Demo

https://jansahay-ai.streamlit.app/

---

<p align="center">
  <strong>JanSahay – Bridging the Digital Accessibility Gap 🌱</strong>
</p>