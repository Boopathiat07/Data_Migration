import pandas as pd
import os

file_path = '/home/divum/Desktop/LMS/Data_Migration/Documents/hashed_filename.csv'

# Check if the file exists, if not, create an empty one with headers
if not os.path.exists(file_path):
    df = pd.DataFrame(columns=['hashedname', 'file_name'])  # Define expected columns
    df.to_csv(file_path, index=False)
    print(f"File created: {file_path}")
else:
    print("File already exists.")

df = pd.read_csv(file_path)

print(df.info())

def extract_columns(input_csv, output_csv):
    # Read the input CSV file
    df = pd.read_csv(input_csv)
    df_filtered = df[['contenthash', 'filename']]
    try:
        # Read the existing output file if it exists
        existing_df = pd.read_csv(output_csv)
    except FileNotFoundError:
        existing_df = pd.DataFrame(columns=['contenthash', 'filename'])
        existing_df.to_csv(output_csv, index=False)

    # Identify new contenthashes not already present
    new_entries = df_filtered[~df_filtered['contenthash'].isin(existing_df['contenthash'])]
    duplicate_entries = df_filtered[df_filtered['contenthash'].isin(existing_df['contenthash'])]

    if not new_entries.empty:
        # Append new entries to the existing file with header if newly created
        new_entries.to_csv(output_csv, mode='a', header=False, index=False)
        print(f"Appended {len(new_entries)} new entries to {output_csv}")
    else:
        print("No new contenthash found. File remains unchanged.")

    if not duplicate_entries.empty:
        print(f"Duplicate contenthash found: {duplicate_entries['contenthash'].tolist()}")


# Example usage
input_file = '/home/divum/Desktop/LMS/Data_Migration/Documents/file_submission_skills_10_feb.csv'
# input_file = '/home/divum/Desktop/LMS/Data_Migration/Documents/intro_temp_files_10_feb.csv'
output_file = '/home/divum/Desktop/LMS/Data_Migration/Documents/hashed_filename.csv'
extract_columns(input_file, output_file)


