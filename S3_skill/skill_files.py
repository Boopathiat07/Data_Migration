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

load_dotenv()

REGION_NAME=os.getenv("REGION_NAME")
AWS_ACCESS_KEY_ID=os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME=os.getenv("BUCKET_NAME")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='s3_upload.log'
)

# S3 configuration
S3_BUCKET = BUCKET_NAME
S3_REGION = REGION_NAME  # Change to your region
S3_PREFIX = 'database_files/'  # Optional prefix for S3 objects
BASE_DIR = '/home/divum/Desktop/LMS/Data_Migration/Documents/PDF_sample'

# CSV file path (in the base directory)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
CSV_FILE_PATH = os.path.join(BASE_DIR, f'hashed_files_s3_urls_{timestamp}.csv')


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


# Upload a single file to S3
def upload_file_to_s3(file_path, s3_client):
    try:
        # Get the hashed filename without directory path
        hashed_filename = os.path.basename(file_path)

        # Determine S3 key by removing base directory and adding prefix
        relative_path = os.path.relpath(file_path, start=BASE_DIR)
        s3_key = os.path.join(S3_PREFIX, relative_path) if S3_PREFIX else relative_path

        # Replace backslashes with forward slashes for S3 compatibility
        s3_key = s3_key.replace('\\', '/')

        content_type = get_content_type(hashed_filename)

        # Upload the file
        response = s3_client.upload_file(file_path, S3_BUCKET, s3_key, ExtraArgs={"ContentType": content_type})

        print("******** ", response, " - ", s3_key)
        return {
            'file_path': file_path,
            'hashed_filename': hashed_filename,
            's3_key': s3_key,
            's3_url': s3_key,
            'status': 'success'
        }
    except Exception as e:
        logging.error(f"Error uploading {file_path}: {str(e)}")
        return {
            'file_path': file_path,
            'hashed_filename': os.path.basename(file_path),
            'status': 'error',
            'error_message': str(e)
        }


# Create CSV report
def create_csv_report(results):
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

    # def get_presigned_url(s3_client, s3_key, expiry_time=300):
    #     url = s3_client.generate_presigned_url(
    #         'get_object',
    #         Params={'Bucket': S3_BUCKET, 'Key':s3_key },
    #         ExpiresIn=expiry_time
    #     )
    #     return url
    # # Create S3 client
    # s3_client = get_s3_client()
    # res = get_presigned_url(s3_client=s3_client, s3_key="database_files/file_submission_skills_10_feb.csv")
    # print(" ********* : ", res)

    # Results container
    results = []

    # Upload files in parallel with progress bar
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(upload_file_to_s3, file_path, s3_client) for file_path in all_files]
        for future in tqdm(futures, total=len(all_files), desc="Uploading files"):
            result = future.result()
            results.append(result)

    # Count successes and failures
    successes = [r for r in results if r['status'] == 'success']
    failures = [r for r in results if r['status'] == 'error']

    logging.info(f"Successfully uploaded {len(successes)} files")
    if failures:
        logging.warning(f"Failed to upload {len(failures)} files")

    # Save results to JSON file (in current directory)
    with open('upload_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Create CSV report in base directory
    csv_path = create_csv_report(results)

    print(f"Upload complete. Uploaded {len(successes)}/{len(all_files)} files successfully.")
    print(f"Results saved to upload_results.json")
    print(f"CSV report saved to {csv_path}")
    print(f"Check s3_upload.log for detailed information.")


if __name__ == "__main__":
    main()