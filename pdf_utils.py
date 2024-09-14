import logging as log
import os
import shutil

import pdfplumber

from file_operations import load_checkpoint, save_checkpoint  # Import checkpoint functions


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


def distribute_page_ranges(total_pages, max_parallelism):
    """Distributes pages into chunks for parallel processing with logging."""
    log.info("Distributing pages among workers...")
    page_ranges = []
    start_page = 14  # Start from page 14, as the first 14 pages are garbage
    pages_per_worker = (total_pages - start_page) // max_parallelism
    for i in range(max_parallelism):
        if i == max_parallelism - 1:
            page_range = range(start_page + i * pages_per_worker, total_pages)
        else:
            page_range = range(start_page + i * pages_per_worker, start_page + (i + 1) * pages_per_worker)
        page_ranges.append(page_range)
        log.info(f"Worker {i} will process pages {page_range}")
    return page_ranges


def extract_columns_from_page_range(pdf_copy_path, page_range, total_pages):
    """Extracts the left and right columns from a given page range in a PDF copy."""
    results = []
    with pdfplumber.open(pdf_copy_path) as pdf:
        for page_num in page_range:
            assert page_num < total_pages, f"Page number {page_num} exceeds total pages {total_pages}"

            # Check if the page has already been processed (using checkpoints)
            left_text, right_text = load_checkpoint(page_num)
            if left_text is not None and right_text is not None:
                log.info(f"Loaded checkpoint for page {page_num}")
            else:
                page = pdf.pages[page_num]
                # Extract text from the left and right columns
                left_text = page.within_bbox((0, 0, 300, 783)).extract_text()
                right_text = page.within_bbox((300, 0, 611.64, 783)).extract_text()

                # Save the extracted columns to the checkpoint
                save_checkpoint(page_num, left_text, right_text)
                log.info(f"Extracted and saved columns for page {page_num}")

            results.append((page_num, left_text, right_text))
    return results
