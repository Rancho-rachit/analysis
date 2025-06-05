# Setup and Run Instructions

## Prerequisites
- Python 3.8 or higher
- MySQL database
- Google Gemini API key
- uv (Python package installer)

## Environment Setup
1. Create a `.env` file in the project root with the following variables:
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name

# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key

# GeckoTerminal API Configuration
GECKO_TERMINAL_API_URL=https://api.geckoterminal.com/api/v2
```

## Installation
1. Create and activate a virtual environment using uv:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies using uv:
```bash
uv pip install -r requirements.txt
```

## Running the Project
Run the analysis with default settings (analyzes 3 tokens):
```bash
python main.py
```

Run with custom number of tokens:
```bash
python main.py --tokens 5
```
