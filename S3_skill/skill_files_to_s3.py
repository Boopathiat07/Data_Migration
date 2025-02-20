import os
import boto3
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import logging
import json
import pandas as pd
from datetime import datetime
import mimetypes
from dotenv import load_dotenv
import time
import csv
import os
import random

load_dotenv()

REGION_NAME=os.getenv("REGION_NAME")
AWS_ACCESS_KEY_ID=os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME=os.getenv("BUCKET_NAME")
BASE_DIR=os.getenv("BASE_DIR")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='s3_upload.log'
)

# S3 configuration
S3_BUCKET = BUCKET_NAME
S3_REGION = REGION_NAME  # Change to your region
# S3_PREFIX = '/'  # Optional prefix for S3 objects

# CSV file path (in the base directory)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
CSV_FILE_PATH = os.path.join(BASE_DIR, f'hashed_files_s3_urls_{timestamp}.csv')

# Load CSV mapping {contenthash: filename}
csv_file_path = "contenthash_filename.csv"  # Update with correct path
hash_to_filename_map = pd.read_csv(csv_file_path).set_index("contenthash")["filename"].to_dict()

# Path for missing filenames CSV
missing_filenames_csv = "missing_filenames.csv"

# Create S3 client
def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=S3_REGION
    )

# Find all files recursively
def find_all_files(base_dir):
    all_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            file_path = os.path.join(root, file)
            # Only include files (not directories)
            if os.path.isfile(file_path):
                all_files.append(file_path)
    return all_files

def get_content_type(file_name):
    """
    Determines the appropriate Content-Type for a given file.

    :param file_name: Name of the file (with extension).
    :return: Content-Type string.
    """
    # Try to guess Content-Type based on file extension
    content_type, _ = mimetypes.guess_type(file_name)

    # Handle common types explicitly
    if content_type:
        return content_type

    # Handle known types manually (for safety)
    extension = file_name.lower().split('.')[-1]

    content_types_map = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif"
    }

    return content_types_map.get(extension, "application/octet-stream")  # Default to binary stream

def generate_unique_filename(original_filename):
    # Split filename and extension
    base_name, file_extension = os.path.splitext(original_filename)  # Correctly extracts extension

    # If no extension, use the default
    if not file_extension:
        file_extension = '.bin'

        # Generate a unique timestamp with milliseconds
    timestamp = int(time.time_ns() // 1_000_000)  # Nanoseconds to milliseconds

    # Append a short random string for extra uniqueness
    random_suffix = f"{random.randint(1000, 9999)}"  # 4-digit random number

    unique_filename = f"{base_name}__{timestamp}_{random_suffix}{file_extension}"

    return unique_filename

def upload_file_to_s3(file_path, s3_client):
    try:
        # Extract the hashed filename (filename stored locally before mapping)
        hashed_filename = os.path.basename(file_path)

        # Get actual filename from mapping, or fallback to hashed filename
        original_filename = hash_to_filename_map.get(hashed_filename, None)

        if original_filename is None:
            # Create the file only when we encounter a missing filename
            if not os.path.exists(missing_filenames_csv):
                with open(missing_filenames_csv, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["contenthash", "s3_key", "upload_timestamp"])  # Header row

            # Log missing filename
            timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(missing_filenames_csv, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([hashed_filename, "", timestamp_str])

            # Use hashed filename as fallback
            original_filename = hashed_filename

        # Generate a unique filename without duplicating the extension
        unique_filename = generate_unique_filename(original_filename)

        # print("HAshed Name : ", hashed_filename, " , Original Name : ", original_filename , " Unique Name : ", unique_filename)

        # Construct the S3 key (folder + unique filename)
        # s3_key = f"{S3_PREFIX}{unique_filename}"

        s3_key = unique_filename

        # Get Content-Type
        content_type = get_content_type(original_filename)

        # Upload file to S3
        s3_client.upload_file(file_path, S3_BUCKET, s3_key, ExtraArgs={"ContentType": content_type})

        return {
            'file_path': file_path,
            'hashed_filename': hashed_filename,
            'original_filename': original_filename,
            'unique_filename': unique_filename,
            's3_key': s3_key,
            's3_url': s3_key,
            'status': 'success'
        }

    except Exception as e:
        logging.error(f"Error uploading {file_path}: {str(e)}")
        return {
            'file_path': file_path,
            # 'hashed_filename': hashed_filename,
            'status': 'error',
            'error_message': str(e)
        }

def create_csv_report(results):
    os.makedirs(BASE_DIR, exist_ok=True)  # ✅ Ensure directory exists
    # Filter successful uploads
    successful_results = [r for r in results if r['status'] == 'success']

    # Create DataFrame
    df = pd.DataFrame([
        {
            'hashedname': r['hashed_filename'],
            's3_url': r['s3_url']
        }
        for r in successful_results
    ])

    # Save to CSV in the base directory
    df.to_csv(CSV_FILE_PATH, index=False)

    return CSV_FILE_PATH

# Main function
def main():
    # Find all files
    all_files = find_all_files(BASE_DIR)
    logging.info(f"Found {len(all_files)} files to upload")

    # Create S3 client
    s3_client = get_s3_client()

    # Results container
    results = []

    # Upload files in parallel with progress bar
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(upload_file_to_s3, file_path, s3_client) for file_path in
                   all_files]
        # futures = [executor.submit(upload_file_to_s3, file_path, s3_client) for file_path in all_files]
        for future in tqdm(futures, total=len(all_files), desc="Uploading files"):
            result = future.result()
            results.append(result)

    # Count successes and failures
    successes = [r for r in results if r['status'] == 'success']
    failures = [r for r in results if r['status'] == 'error']

    logging.info(f"Successfully uploaded {len(successes)} files")
    if failures:
        logging.warning(f"Failed to upload {len(failures)} files")

    # # Save results to JSON file (in current directory)
    # with open('upload_results.json', 'w') as f:
    #     json.dump(results, f, indent=2)

    # Create CSV report in base directory
    csv_path = create_csv_report(results)

    print(f"Upload complete. Uploaded {len(successes)}/{len(all_files)} files successfully.")
    print(f"Results saved to upload_results.json")
    print(f"CSV report saved to {csv_path}")
    print(f"Check s3_upload.log for detailed information.")


if __name__ == "__main__":
    main()
