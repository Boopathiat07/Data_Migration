# import pandas as pd
#
# input_file_1 = "/home/divum/Desktop/LMS/Data_Migration/Documents/file_submission_skills_10_feb.csv"
# input_file_2 = "/home/divum/Desktop/LMS/Data_Migration/Documents/intro_temp_files_10_feb.csv"
# input_file_3 = "/home/divum/Desktop/LMS/Data_Migration/Documents/competency_n_Workorder_10_feb.csv"
# input_file_4 = "/home/divum/Desktop/LMS/Data_Migration/S3_skill/output/combined_hashed_files_s3_urls.csv"
#
#
# pd_1 = pd.read_csv(input_file_1)
# pd_2 = pd.read_csv(input_file_2)
# pd_3 = pd.read_csv(input_file_3)
# pd_4 = pd.read_csv(input_file_4)
#
# print(pd_4.info())
#
# # print(pd_1.info())
# #
# # print(pd_2.info())
# #
# # print(pd_3.info())

import pandas as pd
import json

# Load data from CSV files
input_file_1 = "/home/divum/Desktop/LMS/Data_Migration/Documents/file_submission_skills_10_feb.csv"
input_file_2 = "/home/divum/Desktop/LMS/Data_Migration/Documents/intro_temp_files_10_feb.csv"
input_file_3 = "/home/divum/Desktop/LMS/Data_Migration/Documents/competency_n_Workorder_10_feb.csv"
input_file_4 = "/home/divum/Desktop/LMS/Data_Migration/S3_skill/output/combined_hashed_files_s3_urls.csv"

DF1 = pd.read_csv(input_file_1)
DF2 = pd.read_csv(input_file_2)
DF3 = pd.read_csv(input_file_3)
DF4 = pd.read_csv(input_file_4)


# Function to generate JSON structure
def generate_json(group, df4):
    json_structure = {
        "name": "",
        "field_skill": {
            "learner_url": [],
            "trainer_url": []
        }
    }

    for _, row in group.iterrows():
        file_name = row['filename']
        content_hash = row['contenthash']

        # Get s3_url from DF4 based on contenthash
        s3_url = df4[df4['hashedname'] == content_hash]['s3_url'].values
        file_url = s3_url[0] if len(s3_url) > 0 else ""

        file_info = {
            "file_name": file_name,
            "file_type": "pdf",
            "file_url": file_url,
            "file_category": "trainer_document" if "worksheet" in file_name.lower() else "learner_document"
        }

        if "worksheet" in file_name.lower():
            json_structure["field_skill"]["trainer_url"].append(file_info)
        else:
            json_structure["field_skill"]["learner_url"].append(file_info)

    return json.dumps(json_structure, indent=2)


# Process DF2 to aggregate by assignmentid
final_data = []

grouped = DF2.groupby('assignmentid')
for assignmentid, group in grouped:
    json_data = generate_json(group, DF4)
    last_row = group.iloc[-1]  # Get the last row for assignment if multiple exist

    final_data.append({
        "timecreated": last_row["timecreated"],
        "timemodified": last_row["timemodified"],
        "assignmentid": assignmentid,
        "assignmentname": last_row["assignmentname"],
        "courseid": last_row["courseid"],
        "coursename": last_row["coursename"],
        "userid": last_row["userid"],
        "assessment_json": json_data
    })

# Convert to DataFrame
result_df = pd.DataFrame(final_data)

# Save to file
result_df.to_csv("processed_assessments.csv", index=False)

# Print sample output
print(result_df.head())
