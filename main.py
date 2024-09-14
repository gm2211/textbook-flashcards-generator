import logging as log

import logging_setup
from file_operations import save_to_csv
from model import OutputRow
from pdf_processing import process_pdf_concurrently

MAX_PARALLELISM = 32

if __name__ == "__main__":
    logging_setup.setup_logging()

    # Path to your PDF
    pdf_path = "anatomy.pdf"
    # Path to save the CSV
    output_csv_path = "output_questions_answers.csv"

    # Step 1: Extract columns from pages concurrently
    log.info("Starting PDF processing...")
    output_rows: [OutputRow] = process_pdf_concurrently(pdf_path, MAX_PARALLELISM)

    # Step 2: Save the data to CSV
    save_to_csv(output_rows, output_csv_path)
