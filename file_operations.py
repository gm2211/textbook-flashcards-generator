import json
import os
import pandas as pd


def save_checkpoint(page_num, left_text, right_text):
    """Save the extracted columns to a checkpoint file."""
    checkpoint_folder = "extracted_pages"
    if not os.path.exists(checkpoint_folder):
        os.makedirs(checkpoint_folder)
        file_path = os.path.join(checkpoint_folder, f"page_{page_num}.json")
        with open(file_path, 'w') as f:
            json.dump({"left_text": left_text, "right_text": right_text}, f)


def load_checkpoint(page_num):
    """Load extracted columns from a checkpoint file if available."""
    checkpoint_folder = "extracted_pages"
    file_path = os.path.join(checkpoint_folder, f"page_{page_num}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
    return data['left_text'], data['right_text']


def save_to_csv(question_answer_pairs, output_csv_path):
    """Save the questions and answers to a CSV file."""
    df = pd.DataFrame(question_answer_pairs, columns=['chapter', 'question_number', 'question', 'answer'])
    df.to_csv(output_csv_path, index=False)
    print(f"CSV file saved at {output_csv_path}")
