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
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     filename='s3_upload.log'
# )

# CSV file path
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
CSV_FILE_PATH = os.path.join(OUTPUT_DIR, f'hashed_files_s3_urls_{timestamp}.csv')

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

initialize_csv()

def upload_file_to_s3(file_path, s3_client):
    try:
        hashed_filename = os.path.basename(file_path)
        original_filename = hash_to_filename_map.get(hashed_filename, hashed_filename)

        base_name, file_extension = os.path.splitext(original_filename)  # Correctly extracts extension
        # If no extension, use the default
        if not file_extension:
            file_extension = '.bin'

        # Generate a unique timestamp with milliseconds
        timestamp = int(time.time_ns() // 1_000_000)  # Nanoseconds to milliseconds
        # Append a short random string for extra uniqueness
        random_suffix = f"{random.randint(1000, 9999)}"  # 4-digit random number
        unique_filename = f"{base_name}__{timestamp}_{random_suffix}{file_extension}"

        content_type = mimetypes.guess_type(original_filename)[0] or "application/octet-stream"

        s3_client.upload_file(file_path, BUCKET_NAME, unique_filename, ExtraArgs={"ContentType": content_type})

        # Update CSV immediately
        with csv_lock, open(CSV_FILE_PATH, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([hashed_filename, unique_filename])

        return {'file_path': file_path, 's3_key': unique_filename, 'status': 'success'}
    except Exception as e:
        logging.error(f"Error uploading {file_path}: {str(e)}")
        return {'file_path': file_path, 'status': 'error', 'error_message': str(e)}


def main():
    all_files = [os.path.join(root, file) for root, _, files in os.walk(BASE_DIR) for file in files]
    logging.info(f"Found {len(all_files)} files to upload")

    s3_client = get_s3_client()
    with ThreadPoolExecutor(max_workers=10) as executor:
        list(tqdm(executor.map(lambda f: upload_file_to_s3(f, s3_client), all_files), total=len(all_files),
                  desc="Uploading files"))

    print(f"Upload complete. CSV report saved to {CSV_FILE_PATH}")
    print("Check s3_upload.log for details.")


if __name__ == "__main__":
    main()
