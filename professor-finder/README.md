# 🎓 AdvisorScout (v2)

**The Intelligent PhD Advisor & Faculty Discovery Pipeline**

AdvisorScout is a powerful, automated tool designed to help prospective PhD students and researchers find the perfect academic mentor. It bypasses the limitations of manual searching by scraping high-quality faculty directories across hundreds of universities, enriching profiles with research data, and ranking them using a custom keyword-matching engine.

---

## 🚀 Key Features

- **🌐 Multi-University Support**: Pre-configured to scrape hundreds of faculty directories from top US and Australian universities (QS 300-800 bracket).
- **🔍 Intelligent Enrichment**: Automatically visits individual profile pages to extract:
  - Emails and contact information.
  - Research bios and expertise.
  - Google Scholar profiles.
  - Lab website URLs.
- **🎯 Keyword-Based Scoring**: Ranks professors based on how well their research interests align with *your* specific keywords (e.g., AI, Device Design, Medical Imaging).
- **📊 Beautiful Reports**: Generates a high-quality, interactive HTML dashboard and a structured CSV for your application tracking.
- **⚡ Performance & Stability**:
  - **Deduplication**: Handles faculty listed in multiple departments.
  - **Caching**: Saves progress locally to avoid redundant requests.
  - **Concurrency**: Uses multi-threading for fast profile enrichment.

---

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/AdvisorScout.git
   cd AdvisorScout
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 📖 Usage

### 1. Configure your interests
Open `config.py` and update the `SEARCH_KEYWORDS` list with your research interests:
```python
SEARCH_KEYWORDS = ["AI", "Medical Imaging", "Device Design", "Wearables"]
```

### 2. Run the pipeline
Execute the orchestrator script:
```bash
python main.py
```

The tool will run through four phases:
1. **Scraping**: Discovering faculty links from university directories.
2. **Enrichment**: Fetching detailed bios and interests.
3. **Scoring**: Ranking profiles based on keyword matches.
4. **Reporting**: Finalizing the HTML and CSV output.

### 3. View results
Once complete, the tool will automatically open the results dashboard:
- **HTML Report**: `results/professors_report.html`
- **CSV Data**: `results/professors_data.csv`

---

## ⚙️ Configuration

You can fine-tune the behavior in `config.py`:
- `MIN_MATCH_SCORE`: Set the threshold for relevant results (0.0 to 1.0).
- `REQUEST_DELAY`: Adjust delay between requests to avoid rate limits.
- `QS_UNIVERSITIES`: Modify the target list of institutions.

---

## 🤝 Contributing

Contributions are welcome! If you have scrapers for additional universities or want to improve the scoring algorithm, feel free to open a Pull Request.

---

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*“Finding the right advisor is 50% of the PhD journey. AdvisorScout does the heavy lifting for you.”*
