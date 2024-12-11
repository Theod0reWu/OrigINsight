# OrigINsight

A source retrieval and claim verification system that helps users fact-check claims by searching relevant articles and optionally verifying claims using Google's Gemini AI.

## Features

- Search for relevant articles using DuckDuckGo
- Extract and process article content
- Optional claim verification using Google's Gemini AI
- Web interface using Streamlit
- Command-line interface for batch processing
- Export results to CSV or JSON

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Theod0reWu/OrigINsight.git
cd OrigINsight
```

2. Install required packages:
```bash
pip install -r requirements.txt
```


## Usage

### Web Interface (Streamlit)

Run the web interface with:

```bash
streamlit run streamlit_app.py
```


The web interface provides:
- Input field for claims to verify
- Optional Gemini API key input for claim verification
- Adjustable number of sources to retrieve
- Downloadable results in CSV format
- Detailed view of each source and verification results

### Command Line Interface

Run from command line with:

```bash
python backend/source_retrieval.py "your claim here" [options]
```

Options:
- `-n, --num-results`: Number of articles to retrieve (default: 5)
- `-o, --output`: Output file path (.csv or .json)
- `--verbose`: Print detailed processing information
- `--gemini-key`: Gemini API key for claim verification
- `--verify`: Enable claim verification using Gemini

Example:

```bash
python backend/source_retrieval.py "Earth is round" -n 10 --verify --gemini-key YOUR_API_KEY --output results.csv
```


## Gemini API Key

To use the claim verification feature:
1. Obtain a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. For the web interface: Enter the key in the sidebar
3. For command line: Use the `--gemini-key` option

## Requirements

- Python 3.7+
- streamlit
- pandas
- newspaper3k
- beautifulsoup4
- google-generativeai
- requests