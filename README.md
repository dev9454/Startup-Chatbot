# AI VC Analyst Toolkit - Chatbots

An suite of AI-powered tools designed to automate the initial stages of venture capital deal flow analysis. This project uses AWS Bedrock with the Llama 3 model to understand, analyze, and query documents related to startups.

---

## Features

This toolkit contains three distinct agents:

* **🔍 Deal Screener (`deal_screener_bot.py`):** A command-line chatbot that filters a collection of startup deal notes based on natural language queries. You can search by criteria like revenue, founder background, sector, and more.

* **🤔 Deep Dive Analyst (`deep_dive_bot.py`):** A Q&A chatbot that performs a detailed analysis of a *single* deal note. It uses the deal note as its sole source of truth to answer specific questions, preventing factual errors or "hallucinations."

* **✍️ Questionnaire Agent (`questionnaire_agent.py`):** An AI agent that reads a startup's pitch deck (in PDF format), identifies missing information and potential red flags from an investor's perspective, and automatically generates a tailored follow-up questionnaire for the founders.

---

## Project Structure

Your project should be organized with the following file structure:

```
.
├── notes/
│   ├── deal_note_Hexafun_...json
│   └── deal_note_Naario_...json
├── deal_screener_bot.py
├── deep_dive_bot.py
├── questionnaire_agent.py
├── requirements.txt
└── README.md
```

---

## Setup and Installation

Follow these steps to set up and run the project.

### 1. Prerequisites

* Python 3.8+
* An AWS Account with access to Amazon Bedrock and the `meta.llama3-70b-instruct-v1:0` model enabled in the `us-east-1` region.

### 2. Clone the Repository

First, get the code onto your local machine.

```bash
git clone <your-repository-url>
cd <your-repository-name>
```

### 3. Create a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

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

### 5. Configure AWS Credentials

The scripts need your AWS credentials to access Bedrock. The easiest way is to configure them via the AWS CLI.

```bash
aws configure
```

You will be prompted for your **AWS Access Key ID**, **Secret Access Key**, and **Default Region**. Make sure to set the default region to `us-east-1`.

---

## Usage

You can run each agent independently from your terminal.

### Running the Deal Screener

This bot will run a few example queries against the JSON files in the `notes/` folder.

```bash
python deal_screener_bot.py
```

### Running the Deep Dive Analyst

This bot will ask specific questions about the Hexafun and Naario deal notes.

```bash
python deep_dive_bot.py
```

### Running the Questionnaire Agent

This agent will analyze a pitch deck and generate questions. The script is pre-configured to run with a mock pitch deck. To use your own PDF:

1.  Place your PDF in the project directory.
2.  Open `questionnaire_agent.py` and modify the `if __name__ == "__main__":` block at the bottom to point to your file's path.

```bash
python questionnaire_agent.py
```