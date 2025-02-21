import pandas as pd

# file_path = '/home/divum/Desktop/LMS/Data_Migration/S3_skill/output/hashed_files_s3_urls.csv'
# df1 = pd.read_csv(file_path)
#
#
# file_path = '/home/divum/Desktop/LMS/Data_Migration/Documents/hashed_filename.csv'
# df2 = pd.read_csv(file_path)
# print(df2.info())
#
# # df2_data=set(df2['contenthash'].tolist())
# # df1_data=set(df1['hashedname'].tolist())
#
# # print(len(df2_data),len(df1_data))
#
# # file_path_df3 = '/home/divum/Desktop/LMS/Data_Migration/S3_skill/output/hashed_files_s3_urls.csv'
# # df3 = pd.read_csv(file_path_df3)
# #
# duplicate_rows = df2[df2.duplicated(subset=['contenthash'], keep=False)]
# print(duplicate_rows)

# print(df2.info())

file_path = '/home/divum/Desktop/LMS/Data_Migration/S3_skill/output/hashed_files_s3_urls.csv'
df1 = pd.read_csv(file_path)


file_path = '/home/divum/Desktop/LMS/Data_Migration/Documents/unique_contenthash.csv'
df2 = pd.read_csv(file_path)

missing_df = df2[~df2['contenthash'].isin(df1['hashedname'])]
# Save the missing values to a CSV file
missing_df.to_csv("missing_hash_files.csv", index=False)

# print("Missing values saved to 'missing_values.csv'")





# file_path = '/home/divum/Desktop/LMS/Data_Migration/S3_skill/output/missing_original_filenames.csv'
# df_m = pd.read_csv(file_path)
#
#
# file_path = '/home/divum/Desktop/LMS/Data_Migration/missing_values_from_uat.csv'
# df_d = pd.read_csv(file_path)



















