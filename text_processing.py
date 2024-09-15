import logging as log
import os
import re

from unidecode import unidecode  # Import unidecode for sanitizing text

from file_operations import write_to_file
from model import Answer, BookData, OutputRow, Question, RawPageData

MAIN_QUESTIONS = "MAIN QUESTIONS"

BACK = "Back"

ANSWERS = "ANSWERS"

QUESTIONS = "QUESTIONS"

INTRODUCTION = "INTRODUCTION"

QUESTIONS_ANSWERS_FOLDER = "questions_answers"


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


def parse_questions(lines: list[(str, int)], chapter: int) -> list[Question]:
    questions = []
    question_number = None
    question_text_lines = []
    options = {}
    option_pattern = re.compile(r'^([A-Z])\.\s+(.+)')  # Regex to match options like "A. Option text"
    question_pattern = re.compile(r'^(\d+)\s+(.+)')  # Regex to match the start of a question like "66 A 23-year-old..."
    last_question_num = 0  # Keep track of the last correct question number
    last_page_number = None

    for line, page_number in lines:
        line = line.strip()

        # Check if line starts a new question
        question_match = question_pattern.match(line)
        if question_match:
            cur_question_num = int(question_match.group(1))

            # Check if the question number is logically incorrect (like 1285 instead of 128)
            if cur_question_num > last_question_num + 1:
                log.warning(
                    f"Question number {cur_question_num} is out of sequence. Adjusting to {last_question_num + 1}."
                )
                cur_question_num = last_question_num + 1

            # If we already have a question stored, finalize it and start a new one
            if question_number is not None:
                question = Question(
                    chapter=chapter,
                    page_number=page_number,
                    question_number=question_number,
                    text=' '.join(question_text_lines),
                    question_options=options
                )
                questions.append(question)

            # Reset for new question
            question_number = cur_question_num
            last_question_num = question_number  # Update the last valid question number
            question_text_lines = [question_match.group(2)]  # Start collecting text for this question
            options = {}
            continue

        # If it's not a new question, check for options
        option_match = option_pattern.match(line)
        if option_match:
            options[option_match.group(1)] = option_match.group(2)  # Add option key (A, B, etc.) and text
        else:
            # Continue collecting text for the current question
            question_text_lines.append(line)
        last_page_number = page_number

    # Add the last question to the list
    if question_number is not None:
        question = Question(
            chapter=chapter,
            page_number=last_page_number,
            question_number=question_number,
            text=' '.join(question_text_lines),
            question_options=options
        )
        questions.append(question)

    return questions


def parse_answers(lines: list[(str, int)], chapter: int) -> list[Answer]:
    answers = []
    answer_letter = None
    answer_text_lines = []
    answer_pattern = re.compile(r'^(\d+)\s+([A-Z])\.\s+(.+)')
    last_page_number = None
    last_answer_number = 0  # Keep track of the last correct answer number

    def handle_new_answer_start(new_answer_start):
        nonlocal last_answer_number, answer_letter, answer_text_lines, answer

        current_answer_number = int(new_answer_start.group(1))
        # Check if the answer number is logically incorrect
        if current_answer_number > last_answer_number + 1:
            log.warning(
                f"Answer number {current_answer_number} is out of sequence. Adjusting to {last_answer_number + 1}."
            )
            current_answer_number = last_answer_number + 1

        # If we already have an answer queued up, finalize it and start a new one
        if last_answer_number is not None:
            answer = Answer(
                chapter=chapter,
                page_number=page_number,
                question_number=last_answer_number,
                answer_letter=answer_letter,
                text=' '.join(answer_text_lines)  # Join all lines into a single string
            )
            answers.append(answer)

        # Start new answer
        last_answer_number = current_answer_number  # Update the last valid answer number
        answer_letter = new_answer_start.group(2)  # Capture the letter (e.g., B)
        answer_text_lines = [new_answer_start.group(3)]  # Start collecting text for this answer

        return answer_letter, answer_text_lines

    for line, page_number in lines:
        line = line.strip()

        # Check if line starts a new answer
        found_new_answer_start = answer_pattern.match(line)
        if found_new_answer_start:
            answer_letter, answer_text_lines = handle_new_answer_start(found_new_answer_start)
            continue

        # Continue collecting text for the current answer
        answer_text_lines.append(line)
        last_page_number = page_number

    # Add the last answer to the list
    answer = Answer(
        chapter=chapter,
        page_number=last_page_number,
        question_number=last_answer_number,
        answer_letter=answer_letter,
        text=' '.join(answer_text_lines)  # Join all lines into a single string
    )
    answers.append(answer)

    return answers


def chapter_folder(chapter_number):
    return f"{QUESTIONS_ANSWERS_FOLDER}/chapter_{chapter_number}"


def process_questions_and_answers(page_datas: [RawPageData]) -> list[OutputRow]:
    """
    Process the extracted column data into questions and answers, while also including the page number
    from which the question and answer were extracted.
    """

    pages = BookData([], {})
    for page_data in page_datas:
        page_num, left_col, right_col = page_data.page_number, page_data.left_col, page_data.right_col
        sanitized_lines = f"{sanitize_text(left_col)}\n{sanitize_text(right_col)}\n".split("\n")
        page_start_idx = len(pages.lines)
        for idx in range(len(sanitized_lines)):
            pages.page_number_by_line_idx[page_start_idx + idx] = page_num
        pages.lines.extend(sanitized_lines)

    pages.lines = handle_line_breaks(pages.lines)
    write_to_file("anatomy.txt", "\n".join(pages.lines))

    chapter_number = 1  # Track chapters where the question numbers reset
    is_answers_section = False

    questions_lines_by_chapter = {}
    answers_lines_by_chapter = {}
    questions_so_far = []
    answers_so_far = []
    is_introduction = False

    for idx, line in enumerate(pages.lines):
        if is_introduction and QUESTIONS not in line:
            continue
        if INTRODUCTION in line:
            is_introduction = True
            introduction_index = line.find(INTRODUCTION)
            line = line[:introduction_index]
        if ANSWERS in line:
            questions_lines_by_chapter[chapter_number] = questions_so_far
            questions_so_far = []
            is_answers_section = True
            is_introduction = False  # Redundant because the first section after introduction is always questions
        elif QUESTIONS in line:
            if is_answers_section:
                answers_lines_by_chapter[chapter_number] = answers_so_far
                answers_so_far = []
                chapter_number += 1
            is_answers_section = False
            is_introduction = False

        page_num = pages.page_number_by_line_idx[idx]

        if line != BACK and line != QUESTIONS and line != MAIN_QUESTIONS and line != ANSWERS:
            if is_answers_section:
                answers_so_far.append((line, page_num))
            else:
                questions_so_far.append((line, page_num))

    answers_lines_by_chapter[chapter_number] = answers_so_far

    # Parse questions and answers for each chapter
    parsed_question_by_chapter_by_number = {}
    for chapter_number, lines_with_pages in questions_lines_by_chapter.items():
        if not os.path.exists(chapter_folder(chapter_number)):
            os.makedirs(chapter_folder(chapter_number))
        for question in parse_questions(lines_with_pages, chapter_number):
            write_to_file(
                f"{chapter_folder(chapter_number)}/question_{question.question_number}.txt",
                question.to_dict()
            )
            if chapter_number not in parsed_question_by_chapter_by_number:
                parsed_question_by_chapter_by_number[chapter_number] = {}
            parsed_question_by_chapter_by_number[chapter_number][question.question_number] = question

    output_rows = []
    for chapter_number, lines_with_pages in answers_lines_by_chapter.items():
        if not os.path.exists(chapter_folder(chapter_number)):
            os.makedirs(chapter_folder(chapter_number))
        for answer in parse_answers(lines_with_pages, chapter_number):
            write_to_file(
                f"{chapter_folder(chapter_number)}/answer_{answer.question_number}.txt",
                answer.to_dict()
            )
            try:
                question = parsed_question_by_chapter_by_number[chapter_number][answer.question_number]
            except KeyError:
                log.warning(
                    f"Answer found for question {answer.question_number} "
                    f"in chapter {chapter_number} page {answer.page_number} but question not found."
                )
                continue
            assert answer.question_number == question.question_number, "Number on answer doesn't match that on question"
            output_rows.append(
                OutputRow(
                    chapter=chapter_number,
                    page_number=answer.page_number,
                    question_number=answer.question_number,
                    question=question.text,
                    question_options="\n".join(
                        [" ".join([letter, option]) for letter, option in question.question_options.items()]
                    ),
                    answer_letter=answer.answer_letter,
                    answer=answer.text
                )
            )

    log.info(f"Processed {len(output_rows)} question-answer pairs.")
    return output_rows
