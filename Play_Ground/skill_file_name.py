import pandas as pd

# File paths
input_file = "/home/divum/Desktop/LMS/Data_Migration/Documents/file_submission_skills_10_feb.csv"
output_file = "/home/divum/Desktop/LMS/Data_Migration/Documents/intro_temp_files_10_feb.csv"
combined_file = "/home/divum/Desktop/LMS/Data_Migration/Documents/combined_unique_contenthash.csv"

# Read CSV files
df1 = pd.read_csv(input_file, usecols=["contenthash", "filename"])
df2 = pd.read_csv(output_file, usecols=["contenthash", "filename"])

# Combine both DataFrames
combined_df = pd.concat([df1, df2])

print(len(combined_df["contenthash"]))

# Remove duplicates based on 'contenthash'
unique_df = combined_df.drop_duplicates(subset=["contenthash"], keep="first")

print(len(unique_df["contenthash"]))
# Save to a new CSV file
# unique_df.to_csv(combined_file, index=False)

print(f"Combined file saved at: {combined_file}")
