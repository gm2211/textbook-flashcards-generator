from dataclasses import dataclass

CHAPTER_NUMBER_COL = 'chapter'
PAGE_NUMBER_COL = 'page'
QUESTION_NUMBER_COL = 'question_number'
QUESTION_COL = 'question'
QUESTION_OPTIONS_COL = 'question_options'
ANSWER_LETTER_COL = 'answer_letter'
ANSWER_COL = 'answer'


@dataclass
class RawPageData:
    page_number: int
    left_col: str
    right_col: str


@dataclass
class BookData:
    lines: list[str]
    page_number_by_line_idx: dict[int, int]


@dataclass
class Question:
    chapter: int
    page_number: int
    question_number: int
    text: str
    question_options: dict[str, str]

    def to_dict(self):
        return {
            'chapter': self.chapter,
            'page': self.page_number,
            'question_number': self.question_number,
            'text': self.text,
            'question_options': self.question_options
        }


@dataclass
class Answer:
    chapter: int
    page_number: int
    question_number: int
    answer_letter: str
    text: str

    def to_dict(self):
        return {
            'chapter': self.chapter,
            'page': self.page_number,
            'question_number': self.question_number,
            'text': self.text
        }


@dataclass
class OutputRow:
    page_number: int
    chapter: int
    question_number: int
    question: str
    question_options: str
    answer_letter: str
    answer: str

    @staticmethod
    def column_headers():
        return [
            CHAPTER_NUMBER_COL,
            PAGE_NUMBER_COL,
            QUESTION_NUMBER_COL,
            QUESTION_COL,
            QUESTION_OPTIONS_COL,
            ANSWER_LETTER_COL,
            ANSWER_COL
        ]

    def to_dict(self):
        return {
            CHAPTER_NUMBER_COL: self.chapter,
            PAGE_NUMBER_COL: self.page_number,
            QUESTION_NUMBER_COL: self.question_number,
            QUESTION_COL: self.question,
            QUESTION_OPTIONS_COL: self.question_options,
            ANSWER_LETTER_COL: self.answer_letter,
            ANSWER_COL: self.answer
        }
