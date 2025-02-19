import pandas as pd

# Load the CSV file
file_path = '/home/divum/Desktop/LMS/Data_Migration/Documents/User Current Certification level_final.xlsx - Sheet2.csv'  # Replace with your file path
df = pd.read_csv(file_path)

# # Print the columns of the DataFrame
# print("Columns in the CSV file:")
# print(df.columns)
# #
# Get unique jobRole values
unique_job_roles = df['JobRole'].unique()

# Print the unique job roles
print("Unique Job Roles:")
print(unique_job_roles)