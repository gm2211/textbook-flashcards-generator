import logging as log
from concurrent.futures import as_completed, ProcessPoolExecutor

import pdfplumber

from model import OutputRow
from pdf_utils import (create_pdf_copies, distribute_page_ranges, extract_columns_from_page_range, remove_temp_pdfs)
from text_processing import process_questions_and_answers


def process_pdf_concurrently(pdf_path, max_parallelism) -> [OutputRow]:
    """Process the PDF concurrently to extract columns from pages."""
    temp_pdfs = create_pdf_copies(pdf_path, max_parallelism)
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

    # Distribute page ranges to the workers
    page_ranges = distribute_page_ranges(total_pages, max_parallelism)
    page_data = []

    # Use a ThreadPoolExecutor to process pages concurrently
    with ProcessPoolExecutor(max_workers=max_parallelism) as executor:
        futures = [
            executor.submit(extract_columns_from_page_range, temp_pdfs[i], page_ranges[i], total_pages)
            for i in range(max_parallelism)
        ]
        log.info("Workers have started processing pages...")

        completed = 0
        for future in as_completed(futures):
            result = future.result()
            page_data.extend(result)
            log.info(f"Completed {completed} out of {len(futures)}")
            completed += 1
        log.info("All workers have completed processing pages.")

    # Sort the collected data by page number
    page_data.sort(key=lambda x: x[0])  # Sort by page number

    # Remove temporary PDF copies
    remove_temp_pdfs(temp_pdfs)

    return process_questions_and_answers(page_data)
