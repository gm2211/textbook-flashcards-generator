import json
import logging as log
import os
import shutil

import pandas as pd

from model import OutputRow, PageData

CHECKPOINT_FOLDER = "extracted_pages"


def save_checkpoint(page_data: PageData):
    """Save the extracted columns to a checkpoint file."""
    if not os.path.exists(CHECKPOINT_FOLDER):
        os.makedirs(CHECKPOINT_FOLDER)
    file_path = os.path.join(CHECKPOINT_FOLDER, f"page_{page_data.page_number}.json")
    with open(file_path, 'w') as f:
        json.dump({"left_text": page_data.left_col, "right_text": page_data.right_col}, f)


def load_checkpoint(page_num):
    """Load extracted columns from a checkpoint file if available."""
    file_path = os.path.join(CHECKPOINT_FOLDER, f"page_{page_num}.json")
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r') as f:
        data = json.load(f)
    return PageData(page_number=page_num, left_col=data['left_text'], right_col=data['right_text'])


def save_to_csv(output_rows: [OutputRow], output_csv_path):
    """Save the questions and answers to a CSV file, including the page number."""
    df = pd.DataFrame(map(lambda x: x.to_dict(), output_rows), columns=OutputRow.column_headers())
    df.to_csv(output_csv_path, index=False)
    log.info(f"CSV file saved at {output_csv_path}")


def create_pdf_copies(pdf_path, max_parallelism):
    """Create copies of the PDF for parallel processing with progress logging."""
    temp_pdfs = []
    for i in range(max_parallelism):
        temp_pdf_path = f"anatomy-copy-{i}.pdf"
        if not os.path.exists(temp_pdf_path):
            log.info(f"Creating copy {i} of the PDF...")
            shutil.copyfile(pdf_path, temp_pdf_path)
        else:
            log.info(f"Copy {i} already exists, skipping creation.")
        temp_pdfs.append(temp_pdf_path)
    return temp_pdfs


def remove_temp_pdfs(temp_pdfs):
    """Remove temporary PDF copies at the end of the process."""
    for temp_pdf in temp_pdfs:
        try:
            os.remove(temp_pdf)
            log.info(f"Removed temporary PDF: {temp_pdf}")
        except OSError as e:
            log.info(f"Error deleting temporary PDF {temp_pdf}: {e}")
