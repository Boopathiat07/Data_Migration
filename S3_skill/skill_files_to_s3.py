import os
import boto3
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import logging
import json
import pandas as pd
from datetime import datetime
import mimetypes
import time
import csv
import threading
import random
from dotenv import load_dotenv

load_dotenv()

REGION_NAME = os.getenv("REGION_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
BASE_DIR = os.getenv("BASE_DIR")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
DEFAULT_S3_FOLDER = os.getenv("DEFAULT_S3_FOLDER", "").strip()
os.makedirs(OUTPUT_DIR, exist_ok=True)

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     filename='s3_upload.log'
# )

# CSV file path
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
CSV_FILE_PATH = os.path.join(OUTPUT_DIR, 'hashed_files_s3_urls.csv')
MISSING_FILENAME_CSV = os.path.join(OUTPUT_DIR, 'missing_original_filenames.csv')

# CSV lock to prevent race conditions
csv_lock = threading.Lock()

# Load CSV mapping {contenthash: filename}
csv_file_path = "contenthash_filename.csv"
hash_to_filename_map = pd.read_csv(csv_file_path).set_index("contenthash")["filename"].to_dict()

# Create S3 client
def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION_NAME
    )

# Ensure CSV exists with headers
def initialize_csv():
    if not os.path.exists(CSV_FILE_PATH):
        with open(CSV_FILE_PATH, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["hashedname", "s3_url"])  # Header row

    if not os.path.exists(MISSING_FILENAME_CSV):
        with open(MISSING_FILENAME_CSV, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["hashedname"])  # Header row for missing filenames

initialize_csv()

# Function to check if a hash exists in the CSV file dynamically
def is_file_already_uploaded(hashed_filename):
    with csv_lock:
        if os.path.exists(CSV_FILE_PATH):
            with open(CSV_FILE_PATH, mode='r', newline='') as file:
                reader = csv.reader(file)
                next(reader, None)  # Skip header
                for row in reader:
                    if row and row[0] == hashed_filename:
                        return True
    return False

def log_missing_original_filename(hashed_filename):
    """Logs missing original filenames to a separate CSV file."""
    with csv_lock, open(MISSING_FILENAME_CSV, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([hashed_filename])

def upload_file_to_s3(file_path, s3_client):
    try:
        hashed_filename = os.path.basename(file_path)

        # Check dynamically if the file has already been uploaded
        if is_file_already_uploaded(hashed_filename):
            return {'file_path': file_path, 'status': 'skipped', 'reason': 'Already uploaded'}

        original_filename = hash_to_filename_map.get(hashed_filename)

        # If original_filename is None, log it and skip upload
        if original_filename is None:
            # print(f"Skipping upload, missing original filename: {hashed_filename}")
            log_missing_original_filename(hashed_filename)
            return {"hashedname": hashed_filename, "status": "skipped", "reason": "Missing original filename"}

        base_name, file_extension = os.path.splitext(original_filename)  # Correctly extracts extension
        if not file_extension:
            file_extension = '.bin'

        # Ensure uniqueness by sleeping 1ms before generating timestamp
        time.sleep(0.001)
        # Generate unique timestamp (milliseconds)
        timestamp = int(time.time_ns() // 1_000_000)  # Convert nanoseconds to milliseconds

        unique_filename = f"{base_name}__{timestamp}{file_extension}"

        content_type = mimetypes.guess_type(original_filename)[0] or "application/octet-stream"

        # Add default directory before file name
        s3_key = f"{DEFAULT_S3_FOLDER}/{unique_filename}" if DEFAULT_S3_FOLDER else unique_filename

        s3_client.upload_file(file_path, BUCKET_NAME, s3_key, ExtraArgs={"ContentType": content_type})

        # Update CSV immediately
        with csv_lock, open(CSV_FILE_PATH, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([hashed_filename, s3_key])

        return {'file_path': file_path, 's3_key': s3_key, 'status': 'success'}
    except Exception as e:
        logging.error(f"Error uploading {file_path}: {str(e)}")
        return {'file_path': file_path, 'status': 'error', 'error_message': str(e)}


def main():
    all_files = [os.path.join(root, file) for root, _, files in os.walk(BASE_DIR) for file in files]
    logging.info(f"Found {len(all_files)} files to upload")

    s3_client = get_s3_client()
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(tqdm(executor.map(lambda f: upload_file_to_s3(f, s3_client), all_files),
                            total=len(all_files), desc="Uploading files"))

    skipped_files = sum(1 for r in results if r['status'] == 'skipped' and r.get("reason") == "Already uploaded")
    uploaded_files = sum(1 for r in results if r['status'] == 'success')
    missing_files = sum(
        1 for r in results if r['status'] == 'skipped' and r.get("reason") == "Missing original filename")

    print(f"Uploaded {uploaded_files} files. CSV report saved to {CSV_FILE_PATH}.")
    print(f"Skipped {skipped_files} files (already uploaded).")
    print(f"Logged {missing_files} files with missing original filenames to {MISSING_FILENAME_CSV}.")
    print("Check s3_upload.log for details.")

if __name__ == "__main__":
    main()
