import logging as log
import re

from unidecode import unidecode  # Import unidecode for sanitizing text

from model import OutputRow


def handle_line_breaks(lines):
    """
    Handle word continuation across lines due to hyphenation.
    Join lines where a word is split across two lines (indicated by a dash at the end of a line).
    """
    processed_lines = []
    previous_line = ""

    for line in lines:
        line = line.strip()  # Clean any unnecessary whitespace
        if previous_line.endswith('-'):  # If the previous line ends with a dash, join with the current line
            previous_line = previous_line[:-1] + line  # Remove the dash and concatenate without spaces
        else:
            if previous_line:
                processed_lines.append(previous_line)
            previous_line = line

    if previous_line:
        processed_lines.append(previous_line)  # Add the final processed line

    return processed_lines


def sanitize_text(text):
    """
    Sanitize text by converting any Unicode characters to ASCII equivalents.
    This will handle things like smart quotes, non-standard dashes, etc.
    """
    return unidecode(text)


def process_questions_and_answers(page_data) -> [OutputRow]:
    """
    Process the extracted column data into questions and answers, while also including the page number
    from which the question and answer were extracted.
    """
    questions = {}
    answers = {}
    questions_answer_by_chapter = {}
    chapter_number = 1  # Track chapters where the question numbers reset
    is_answers_section = False
    is_questions_section = False

    for page_num, left_col, right_col in page_data:
        log.info(f"Processing extracted content from page {page_num}...")

        # Combine left and right columns, processing them sequentially
        left_lines = handle_line_breaks(left_col.split('\n')) if left_col else []
        right_lines = handle_line_breaks(right_col.split('\n')) if right_col else []

        # Join left and right columns text
        full_text = '\n'.join(left_lines + right_lines).strip()

        # Detect if we are in the answers section (looking for "Answers" keyword)
        if "answers" in full_text.lower():
            is_answers_section = True
            is_questions_section = False
        elif "questions" in full_text.lower():
            if is_answers_section:
                questions_answer_by_chapter[chapter_number] = (questions, answers)
                questions = {}
                answers = {}
                chapter_number += 1
            is_questions_section = True
            is_answers_section = False

        if not is_questions_section and not is_answers_section:
            continue

        # Process each column separately
        number = None
        text = ""
        for col in [left_lines, right_lines]:
            for line in col:
                # Use regex to detect questions and answers
                match = re.match(r"(\d+)\s(.+)", line)
                if match or number is not None:
                    if match:
                        if text and is_answers_section:
                            # Sanitize and save the answer text, now including the page number
                            answers[number] = (sanitize_text(text), page_num)
                        elif text:
                            # Sanitize and save the question text, now including the page number
                            questions[number] = (sanitize_text(text), page_num)
                        number = int(match.group(1))
                        text = match.group(2).strip()
                    else:
                        text += f" {line}"

    # Combine questions and answers based on question number, including page number in the output
    output_rows = []
    for chapter_number, (questions, answers) in questions_answer_by_chapter.items():
        for question_number, (question, page_num) in questions.items():
            answer, answer_page_num = answers.get(question_number, ("", page_num))
            # Sanitize the question and answer before saving
            output_rows.append((
                OutputRow(
                    chapter=chapter_number,
                    page_number=page_num,
                    question_number=question_number,
                    question=sanitize_text(question),
                    answer=sanitize_text(answer)
                )
            ))

    log.info(f"Processed {len(output_rows)} question-answer pairs.")
    return output_rows
