# AI VC Analyst Toolkit

An suite of AI-powered tools designed to automate the initial stages of venture capital deal flow analysis. This project uses Google's Gemini Pro model to understand, analyze, and query documents related to startups.

---

## Features

This toolkit contains three distinct agents:

* **🔍 Deal Screener (`deal_screener_bot.py`):** A command-line chatbot that filters a collection of startup deal notes based on natural language queries.
* **🤔 Deep Dive Analyst (`deep_dive_bot.py`):** A Q&A chatbot that performs a detailed analysis of a single deal note, using the note as its sole source of truth.
* **✍️ Questionnaire Agent (`questionnaire_agent.py`):** An AI agent that analyzes a pitch deck (PDF) and automatically generates a tailored follow-up questionnaire.

---

## Project Structure

```
.
├── notes/
│   ├── deal_note_Hexafun_...json
│   └── deal_note_Naario_...json
├── config.py
├── llm_gemini.py
├── deal_screener_bot.py
├── deep_dive_bot.py
├── questionnaire_agent.py
├── requirements.txt
└── README.md
```

---

## Setup and Installation

### 1. Prerequisites

* Python 3.9+
* A Google AI Studio API Key.

### 2. Get the Code

Clone the repository or download the files to your local machine.

### 3. Create a Virtual Environment

It's highly recommended to use a virtual environment.

```bash
# Create the virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies

Install all the required libraries using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 5. Configure Your Gemini API Key

1. Open the `config.py` file.
2. Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
3. Paste your key into the file, replacing `"YOUR_GEMINI_API_KEY"`.

---

## Usage

You can run each agent independently from your terminal.

```bash
# Run the deal screener
python deal_screener_bot.py

# Run the deep dive analyst
python deep_dive_bot.py

# Run the questionnaire agent
python questionnaire_agent.py
```