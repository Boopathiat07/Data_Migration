import pandas as pd

file_path = '/home/divum/Desktop/LMS/Data_Migration/Documents/hashed_filename.csv'
df2 = pd.read_csv(file_path)
df_unique = df2.drop_duplicates(subset=['contenthash'], keep='first')

# Save the unique contenthash data to a new CSV file
output_file = "/home/divum/Desktop/LMS/Data_Migration/Documents/unique_contenthash.csv"
df_unique.to_csv(output_file, index=False)