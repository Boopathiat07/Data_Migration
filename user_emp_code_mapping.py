import pandas as pd

# Step 1: Read the CSV files into pandas DataFrames
CSV_FILE_PATH = "/home/divum/Desktop/LMS/Data_Migration/"
attendees_df = pd.read_csv(CSV_FILE_PATH+'Documents/intro_temp_files_10_feb.csv')
user_df = pd.read_csv(CSV_FILE_PATH+'Documents/all_users.csv')

# Step 2: Merge the DataFrames based on the matching 'userid' and 'id' columns
# We will use a left join to keep all records from attendees and match employee_code from the user CSV
merged_df = pd.merge(attendees_df, user_df[['id', 'employee_code']], left_on='userid', right_on='id', how='left')

# Step 3: Rename 'id' (from user_df) to 'user_id'
merged_df.rename(columns={'id': 'user_id'}, inplace=True)

# Step 3: Optionally, remove the 'id' column from the merged DataFrame (if it's not needed)
# merged_df.drop(columns=['user_id'], inplace=True)

# Step 4: Write the resulting DataFrame back to a CSV file
merged_df.to_csv(CSV_FILE_PATH+'Documents/new_intro_temp_files_10_feb.csv', index=False)

print("Merged CSV saved as 'merged_attendees_with_employee_code.csv'")