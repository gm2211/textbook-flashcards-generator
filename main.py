from pdf_utils import process_pdf_concurrently
from file_operations import save_to_csv
import time


def log_execution_time(start_time, message):
    """Log the time since the start of execution with a custom message."""
    elapsed_time = time.time() - start_time
    print(f"{message} - Time elapsed: {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    # Path to your PDF
    pdf_path = "anatomy.pdf"
    # Path to save the CSV
    output_csv_path = "output_questions_answers.csv"

    # Step 1: Extract columns from pages concurrently
    print("Starting PDF processing...")
    start_time = time.time()  # Start tracking time
    question_answer_pairs = process_pdf_concurrently(pdf_path)

    # Step 2: Save the data to CSV
    save_to_csv(question_answer_pairs, output_csv_path)

    log_execution_time(start_time, "Finished processing and saving data")
