# Moodle Quiz Answer Extractor

Extract questions and correct answers from saved Moodle quiz review pages into a searchable document for exam prep.

## Quick Start

### 1. Save your Moodle quiz pages

1. Open a completed quiz review page in your browser (the page showing all questions with correct answers)
2. Save the page: **File → Save Page As → "Webpage, Complete"**
3. Save it to the `moodle/` folder in this project

Repeat for all tests you want to extract.

### 2. Run the extractor

```bash
# First time setup (creates virtual environment)
python3 -m venv venv
source venv/bin/activate
pip install beautifulsoup4

# Run the extractor
python3 extract_answers.py
```

### 3. Use the output

The script generates `extracted_answers.md` containing all questions and correct answers. Copy the contents to Google Docs and use **Cmd+F** to search during your exam.

## Example Output

```markdown
## Question 1
**Q:** Valige jäegmisest nimekirjast õiged väided OS aine kohta:

**Correct Answer(s):**
- Kursus annab ülevaate operatsioonisüsteemidest...
- Pärast kursuse läbimist mõistavad tudengid mäluhalduse...
```

## Subsequent Runs

After initial setup, just activate the venv and run:

```bash
source venv/bin/activate
python3 extract_answers.py
```

## Supported Question Types

- ✅ Multiple choice (single answer)
- ✅ Multiple choice (multiple answers)
- ✅ Short answer / text input

