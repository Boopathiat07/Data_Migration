import pandas as pd

# Load the original CSV
file_path = "/home/divum/Desktop/LMS/Data_Migration/Documents/hashed_filename.csv"
df2 = pd.read_csv(file_path)

# Count occurrences of each contenthash
contenthash_counts = df2.groupby("contenthash").size().reset_index(name="count")

# Save to a new CSV file
output_file = "/home/divum/Desktop/LMS/Data_Migration/Documents/contenthash_counts.csv"
contenthash_counts.to_csv(output_file, index=False)

print(f"✅ Unique contenthash with counts saved to: {output_file}")