import re
from unidecode import unidecode  # Import unidecode for sanitizing text


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


def process_questions_and_answers(page_data):
    """Process the extracted column data into questions and answers."""
    questions = {}
    answers = {}
    questions_answer_by_chapter = {}
    chapter_number = 1  # Track chapters where the question numbers reset
    is_answers_section = False
    is_questions_section = False

    for page_num, left_col, right_col in page_data:
        print(f"Processing extracted content from page {page_num}...")

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
                            # Sanitize the answer text before saving
                            answers[number] = sanitize_text(text)
                        elif text:
                            # Sanitize the question text before saving
                            questions[number] = sanitize_text(text)
                        number = int(match.group(1))
                        text = match.group(2).strip()
                    else:
                        text += f" {line}"

    # Combine questions and answers based on question number
    question_answer_pairs = []
    for chapter_number, (questions, answers) in questions_answer_by_chapter.items():
        for question_number, question in questions.items():
            answer = answers.get(question_number, "")
            # Sanitize both the question and the answer before adding them to the result
            question_answer_pairs.append(
                (chapter_number, question_number, sanitize_text(question), sanitize_text(answer)))

    print(f"Processed {len(question_answer_pairs)} question-answer pairs.")
    return question_answer_pairs