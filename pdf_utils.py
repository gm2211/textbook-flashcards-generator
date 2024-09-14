import shutil
import os
from concurrent.futures import ThreadPoolExecutor
import pdfplumber
from text_processing import process_questions_and_answers
from file_operations import load_checkpoint, save_checkpoint  # Import checkpoint functions

MAX_PARALLELISM = 32


def create_pdf_copies(pdf_path, max_parallelism):
    """Create copies of the PDF for parallel processing with progress logging."""
    temp_pdfs = []
    for i in range(max_parallelism):
        temp_pdf_path = f"anatomy-copy-{i}.pdf"
        if not os.path.exists(temp_pdf_path):
            print(f"Creating copy {i} of the PDF...")
            shutil.copyfile(pdf_path, temp_pdf_path)
        else:
            print(f"Copy {i} already exists, skipping creation.")
        temp_pdfs.append(temp_pdf_path)
    return temp_pdfs


def remove_temp_pdfs(temp_pdfs):
    """Remove temporary PDF copies at the end of the process."""
    for temp_pdf in temp_pdfs:
        try:
            os.remove(temp_pdf)
            print(f"Removed temporary PDF: {temp_pdf}")
        except OSError as e:
            print(f"Error deleting temporary PDF {temp_pdf}: {e}")


def distribute_page_ranges(total_pages, max_parallelism):
    """Distributes pages into chunks for parallel processing with logging."""
    print("Distributing pages among workers...")
    page_ranges = []
    start_page = 14  # Start from page 14, as the first 14 pages are garbage
    pages_per_worker = (total_pages - start_page) // max_parallelism
    for i in range(max_parallelism):
        if i == max_parallelism - 1:
            page_range = range(start_page + i * pages_per_worker, total_pages)
        else:
            page_range = range(start_page + i * pages_per_worker, start_page + (i + 1) * pages_per_worker)
        page_ranges.append(page_range)
        print(f"Worker {i} will process pages {page_range}")
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
                print(f"Loaded checkpoint for page {page_num}")
            else:
                page = pdf.pages[page_num]
                # Extract text from the left and right columns
                left_text = page.within_bbox((0, 0, 300, 783)).extract_text()
                right_text = page.within_bbox((300, 0, 611.64, 783)).extract_text()

                # Save the extracted columns to the checkpoint
                save_checkpoint(page_num, left_text, right_text)
                print(f"Extracted and saved columns for page {page_num}")

            results.append((page_num, left_text, right_text))
    return results


def process_pdf_concurrently(pdf_path):
    """Process the PDF concurrently to extract columns from pages."""
    temp_pdfs = create_pdf_copies(pdf_path, MAX_PARALLELISM)
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

    # Distribute page ranges to the workers
    page_ranges = distribute_page_ranges(total_pages, MAX_PARALLELISM)
    page_data = []

    # Use a ThreadPoolExecutor to process pages concurrently
    with ThreadPoolExecutor(max_workers=MAX_PARALLELISM) as executor:
        futures = [
            executor.submit(extract_columns_from_page_range, temp_pdfs[i], page_ranges[i], total_pages)
            for i in range(MAX_PARALLELISM)
        ]

        # Collect the results as they are completed
        for future in futures:
            result = future.result()
            page_data.extend(result)
        print("All workers have completed processing pages.")

    # Sort the collected data by page number
    page_data.sort(key=lambda x: x[0])  # Sort by page number

    # Remove temporary PDF copies
    remove_temp_pdfs(temp_pdfs)

    return process_questions_and_answers(page_data)