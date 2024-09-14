from dataclasses import dataclass

CHAPTER_NUMBER_COL = 'chapter'
PAGE_NUMBER_COL = 'page'
QUESTION_NUMBER_COL = 'question_number'
QUESTION_COL = 'question'
ANSWER_COL = 'answer'


@dataclass
class PageData:
    page_number: int
    left_col: str
    right_col: str


@dataclass
class OutputRow:
    page_number: int
    chapter: int
    question_number: int
    question: str
    answer: str

    @staticmethod
    def column_headers():
        return [CHAPTER_NUMBER_COL, PAGE_NUMBER_COL, QUESTION_NUMBER_COL, QUESTION_COL, ANSWER_COL]

    def to_dict(self):
        return {
            CHAPTER_NUMBER_COL: self.chapter,
            PAGE_NUMBER_COL: self.page_number,
            QUESTION_NUMBER_COL: self.question_number,
            QUESTION_COL: self.question,
            ANSWER_COL: self.answer
        }
