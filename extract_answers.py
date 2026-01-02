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


def normalize_for_comparison(text: str) -> str:
    """Normalize text for comparison (lowercase, remove extra spaces, punctuation)."""
    if not text:
        return ""
    # Lowercase and remove extra whitespace
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def parse_existing_answers(filepath: Path) -> set:
    """
    Parse the existing extracted_answers.txt file and return a set of 
    (question, frozenset(answers)) tuples for comparison.
    """
    existing_qa = set()
    
    if not filepath.exists():
        return existing_qa
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by double newlines to get blocks
    lines = content.split('\n')
    
    current_question = None
    current_answers = []
    
    for line in lines:
        line = line.rstrip()
        
        # Skip empty lines - they mark end of a Q&A block
        if not line:
            if current_question and current_answers:
                # Normalize and store the Q&A pair
                norm_question = normalize_for_comparison(current_question)
                norm_answers = frozenset(normalize_for_comparison(a) for a in current_answers)
                existing_qa.add((norm_question, norm_answers))
            current_question = None
            current_answers = []
            continue
        
        # Check if it's an answer line (starts with "- ")
        if line.startswith('- '):
            answer = line[2:].strip()
            if answer:
                current_answers.append(answer)
        # Check if it's a test header (contains ":" and looks like a header)
        elif ':' in line and ('Test' in line or 'test' in line or 'Katsete' in line):
            # It's likely a test name header, skip it
            continue
        else:
            # It's a question line
            if current_question and current_answers:
                # Save previous Q&A before starting new one
                norm_question = normalize_for_comparison(current_question)
                norm_answers = frozenset(normalize_for_comparison(a) for a in current_answers)
                existing_qa.add((norm_question, norm_answers))
            current_question = line
            current_answers = []
    
    # Don't forget the last Q&A pair
    if current_question and current_answers:
        norm_question = normalize_for_comparison(current_question)
        norm_answers = frozenset(normalize_for_comparison(a) for a in current_answers)
        existing_qa.add((norm_question, norm_answers))
    
    return existing_qa


def is_duplicate(question_text: str, answers: list, existing_qa: set) -> bool:
    """
    Check if a question-answer pair already exists.
    Both the question AND the answers must match for it to be a duplicate.
    """
    norm_question = normalize_for_comparison(question_text)
    norm_answers = frozenset(normalize_for_comparison(a) for a in answers)
    
    return (norm_question, norm_answers) in existing_qa


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
                        # Remove leading/trailing comma or period
                        answer_text = re.sub(r'^[,\.\s]+', '', answer_text)
                        answer_text = re.sub(r'[,\.]\s*$', '', answer_text)
                        if answer_text:  # Only add if still has content
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
    """Format extracted data as plain text."""
    output_lines = []
    
    for test in tests_data:
        output_lines.append(f"{test['test_name']}\n\n")
        
        for q in test['questions']:
            output_lines.append(f"{q['text']}\n")
            for answer in q['answers']:
                # Clean up answer - remove leading commas/spaces
                answer = re.sub(r'^[,\.\s]+', '', answer).strip()
                if answer:  # Only add non-empty answers
                    output_lines.append(f"- {answer}\n")
            output_lines.append("\n")
    
    return ''.join(output_lines)


def main():
    """Main function to process all HTML files in the moodle folder."""
    script_dir = Path(__file__).parent
    moodle_dir = script_dir / 'moodle'
    output_file = script_dir / 'extracted_answers.txt'
    
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
    
    # Parse existing answers to avoid duplicates
    existing_qa = parse_existing_answers(output_file)
    print(f"Found {len(existing_qa)} existing question-answer pairs")
    
    tests_data = []
    total_new = 0
    total_skipped = 0
    
    for html_file in sorted(html_files):
        print(f"Processing: {html_file.name}")
        try:
            test_data = process_html_file(html_file)
            original_count = len(test_data['questions'])
            
            # Filter out duplicate questions
            new_questions = []
            file_skipped = 0
            for q in test_data['questions']:
                if is_duplicate(q['text'], q['answers'], existing_qa):
                    total_skipped += 1
                    file_skipped += 1
                else:
                    new_questions.append(q)
                    # Add to existing set to avoid duplicates within current batch
                    norm_q = normalize_for_comparison(q['text'])
                    norm_a = frozenset(normalize_for_comparison(a) for a in q['answers'])
                    existing_qa.add((norm_q, norm_a))
                    total_new += 1
            
            test_data['questions'] = new_questions
            
            if new_questions:
                tests_data.append(test_data)
                print(f"  - Found {len(new_questions)} new questions (skipped {file_skipped} duplicates from {original_count} total)")
            else:
                print(f"  - No new questions found (all {original_count} were duplicates)")
                
        except Exception as e:
            print(f"  - Error processing file: {e}")
    
    if not tests_data or total_new == 0:
        print(f"\nNo new questions to add. Skipped {total_skipped} duplicate(s).")
        return
    
    # Generate output for new questions only
    new_output = format_output(tests_data)
    
    # Append to existing file or create new one
    if output_file.exists():
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(new_output)
        print(f"\nAppended {total_new} new question(s) to: {output_file}")
    else:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(new_output)
        print(f"\nCreated new file with {total_new} question(s): {output_file}")
    
    print(f"Skipped {total_skipped} duplicate question(s).")
    print("You can now copy the contents to Google Docs for searching.")


if __name__ == '__main__':
    main()

