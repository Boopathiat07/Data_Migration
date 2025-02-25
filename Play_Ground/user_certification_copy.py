import pandas as pd

user_file_path = "/home/divum/Downloads/OneDrive_2025-02-04/02 2025 DB dumps/user data 2feb2024.csv"
existing_certification = "/home/divum/Desktop/LMS/Data_Migration_Files/User Current Certification level_final.xlsx - Sheet2 (1).csv"

user_file_path_df = pd.read_csv(user_file_path)
existing_certification_df = pd.read_csv(existing_certification)

# print(user_file_path_df.shape[0])
# print(existing_certification_df.info())

# Get the list of unique user IDs from both dataframes
user_ids = set(user_file_path_df['id'])
existing_user_ids = set(existing_certification_df['id'])

# Find users in user_file_path_df but NOT in existing_certification_df
only_in_user_file = user_file_path_df[~user_file_path_df['id'].isin(existing_user_ids)][['id', 'username', 'employee_code', 'name']]

# Rename columns to match existing_certification_df
only_in_user_file = only_in_user_file.rename(columns={
    'username': 'Username',
    'employee_code': 'Employee Code',
    'name': 'Name'
})

# Create an empty DataFrame with the same structure as existing_certification_df
new_users_df = pd.DataFrame(columns=existing_certification_df.columns)

# Fill required columns with data from only_in_user_file
for col in only_in_user_file.columns:
    new_users_df[col] = only_in_user_file[col]

# Append new users to existing certification DataFrame
updated_certification_df = pd.concat([existing_certification_df, new_users_df], ignore_index=True)

print(updated_certification_df.shape[0])

# Save or print results
updated_certification_df.to_csv("/home/divum/Desktop/LMS/Data_Migration_Files/updated_certification.csv", index=False)

print(f"Updated certification records: {len(updated_certification_df)}")