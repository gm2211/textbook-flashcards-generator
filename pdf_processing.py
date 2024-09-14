import logging as log
from concurrent.futures import as_completed, ProcessPoolExecutor

import pdfplumber

import logging_setup
from file_operations import create_pdf_copies, load_checkpoint, remove_temp_pdfs, save_checkpoint
from model import OutputRow, PageData
from text_processing import process_questions_and_answers

LEFT_COL_BBOX = (0, 0, 300, 783)
RIGHT_COL_BBOX = (300, 0, 611.64, 783)


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


def extract_columns_from_page_range(
        path: str,
        page_range: [int],
        total_pages: int,
        left_col_bbox: (int, int, int, int),
        right_col_bbox: (int, int, int, int)
):
    """Extracts the left and right columns from a given page range in a PDF copy."""
    # Hack to ensure logging is set up in the worker processes, ideally should be done in a wrap_with_logging function,
    # but ran into issues with pickling
    logging_setup.setup_logging()

    results: [PageData] = []
    page_nums_to_read_from_pdf = set([x for x in page_range])

    for page_num in page_range:
        page_data = load_checkpoint(page_num)
        if page_data is not None:
            log.info(f"Loaded checkpoint for page {page_num}")
            results.append(page_data)
            page_nums_to_read_from_pdf.remove(page_num)
            continue

    with pdfplumber.open(path) as pdf:
        for page_num in page_nums_to_read_from_pdf:
            assert page_num < total_pages, f"Page number {page_num} exceeds total pages {total_pages}"

            page = pdf.pages[page_num]

            # Extract text from the left and right columns
            left_text = page.within_bbox(left_col_bbox).extract_text()
            right_text = page.within_bbox(right_col_bbox).extract_text()
            page_data = PageData(page_number=page_num, left_col=left_text, right_col=right_text)

            # Save the extracted columns to the checkpoint
            save_checkpoint(page_data)
            log.info(f"Extracted and saved columns for page {page_num}")

            results.append(page_data)
    return results


def process_pdf_concurrently(pdf_path, max_parallelism) -> [OutputRow]:
    """Process the PDF concurrently to extract columns from pages."""
    temp_pdfs = create_pdf_copies(pdf_path, max_parallelism)
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

    # Distribute page ranges to the workers
    page_ranges = distribute_page_ranges(total_pages, max_parallelism)
    page_datas: [PageData] = []

    # Use a ThreadPoolExecutor to process pages concurrently
    with ProcessPoolExecutor(max_workers=max_parallelism) as executor:
        futures = []
        for i in range(max_parallelism):
            assigned_temp_pdf = temp_pdfs[i]
            assigned_page_range = page_ranges[i]

            future = executor.submit(
                extract_columns_from_page_range,
                assigned_temp_pdf,
                assigned_page_range,
                total_pages,
                LEFT_COL_BBOX,
                RIGHT_COL_BBOX
            )
            futures.append(future)
        log.info("Workers have started processing pages...")

        completed = 0
        for future in as_completed(futures):
            result = future.result()
            page_datas.extend(result)
            log.info(f"{completed} out of {len(futures)} workers have completed processing pages.")
            completed += 1
        log.info("All workers have completed processing pages.")

    # Sort the collected data by page number
    page_datas.sort(key=lambda x: x.page_number)  # Sort by page number

    # Remove temporary PDF copies
    remove_temp_pdfs(temp_pdfs)

    return process_questions_and_answers(page_datas)
