#!/usr/bin/env python3
"""
Moodle Quiz Answer Extractor

Parses saved Moodle quiz review HTML files and extracts all questions
with their correct answers into a searchable Markdown file.
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup


def clean_text(text: str) -> str:
    """Clean up extracted text by removing extra whitespace."""
    if not text:
        return ""
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_test_name(soup: BeautifulSoup) -> str:
    """Extract the test name from the page title."""
    title = soup.find('title')
    if title:
        # Format: "Test 1 - Aine korralduslik info: katse ülevaade | TÜ Moodle"
        title_text = title.get_text()
        # Remove the " | TÜ Moodle" suffix and ": katse ülevaade" part
        title_text = re.sub(r'\s*\|\s*TÜ Moodle\s*$', '', title_text)
        title_text = re.sub(r':\s*katse ülevaade\s*$', '', title_text)
        return title_text.strip()
    return "Unknown Test"


def extract_questions(soup: BeautifulSoup) -> list:
    """Extract all questions and their correct answers from the HTML."""
    questions = []
    
    # Find all question divs (they have class 'que')
    question_divs = soup.find_all('div', class_='que')
    
    for q_div in question_divs:
        question_data = {}
        
        # Get question number
        qno_span = q_div.find('span', class_='qno')
        if qno_span:
            question_data['number'] = clean_text(qno_span.get_text())
        else:
            question_data['number'] = '?'
        
        # Get question text
        qtext_div = q_div.find('div', class_='qtext')
        if qtext_div:
            question_data['text'] = clean_text(qtext_div.get_text())
        else:
            question_data['text'] = '[Question text not found]'
        
        # Get correct answers from the .rightanswer div
        rightanswer_div = q_div.find('div', class_='rightanswer')
        if rightanswer_div:
            # The rightanswer div contains the correct answers
            # Format varies: could be plain text or contain <p> tags
            
            # Get all paragraph tags for multiple answers
            answer_paragraphs = rightanswer_div.find_all('p')
            if answer_paragraphs:
                answers = []
                for p in answer_paragraphs:
                    answer_text = clean_text(p.get_text())
                    if answer_text:
                        # Remove trailing comma or period
                        answer_text = re.sub(r'[,\.]\s*$', '', answer_text)
                        answers.append(answer_text)
                question_data['answers'] = answers
            else:
                # Fallback: get all text from rightanswer
                raw_text = clean_text(rightanswer_div.get_text())
                # Remove the prefix "Õige vastus on:" or "Õiged vastused on järgmised:"
                raw_text = re.sub(r'^Õige[d]?\s+vastuse?d?\s+(on|on järgmised):\s*', '', raw_text)
                question_data['answers'] = [raw_text] if raw_text else []
        else:
            # For some question types, we might need to look at the answer input
            answer_input = q_div.find('input', class_='correct')
            if answer_input and answer_input.get('value'):
                question_data['answers'] = [answer_input.get('value')]
            else:
                question_data['answers'] = ['[Answer not found]']
        
        questions.append(question_data)
    
    return questions


def process_html_file(filepath: Path) -> dict:
    """Process a single HTML file and return extracted data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    return {
        'test_name': extract_test_name(soup),
        'questions': extract_questions(soup),
        'source_file': filepath.name
    }


def format_output(tests_data: list) -> str:
    """Format extracted data as Markdown."""
    output_lines = []
    
    for test in tests_data:
        output_lines.append(f"# {test['test_name']}\n")
        
        for q in test['questions']:
            output_lines.append(f"{q['text']}\n")
            for answer in q['answers']:
                output_lines.append(f"- {answer}\n")
            output_lines.append("\n")
    
    return ''.join(output_lines)


def main():
    """Main function to process all HTML files in the moodle folder."""
    script_dir = Path(__file__).parent
    moodle_dir = script_dir / 'moodle'
    
    if not moodle_dir.exists():
        print(f"Error: moodle directory not found at {moodle_dir}")
        return
    
    # Find all HTML files (not in subdirectories like *_files)
    html_files = [f for f in moodle_dir.iterdir() 
                  if f.is_file() and f.suffix.lower() == '.html']
    
    if not html_files:
        print("No HTML files found in moodle directory")
        return
    
    print(f"Found {len(html_files)} HTML file(s)")
    
    tests_data = []
    for html_file in sorted(html_files):
        print(f"Processing: {html_file.name}")
        try:
            test_data = process_html_file(html_file)
            tests_data.append(test_data)
            print(f"  - Extracted {len(test_data['questions'])} questions")
        except Exception as e:
            print(f"  - Error processing file: {e}")
    
    # Generate output
    output = format_output(tests_data)
    
    output_file = script_dir / 'extracted_answers.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"\nDone! Output written to: {output_file}")
    print("You can now copy the contents to Google Docs for searching.")


if __name__ == '__main__':
    main()

