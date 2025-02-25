import pandas as pd
import re
base_path="/home/divum/Downloads/"
lo_old_new_mapping_source="Skill_LO Mapping.xlsx - LO Mapping.csv"
moodle_lo_2_b_mapped="Skill Pending List - Need mapping for competency.csv"

lo_old_new_mapping_source_df=pd.read_csv(base_path+lo_old_new_mapping_source)
moodle_lo_2_b_mapped_df=pd.read_csv(base_path+moodle_lo_2_b_mapped)

def clean_moodle_name(name):
    # Remove 'Workorder' followed by optional space and digits
    name = re.sub(r'\bWorkorder\s*\d*\b', '', name, flags=re.IGNORECASE)
    # Remove extra spaces
    return ' '.join(name.split()).strip().lower()

# Apply function
moodle_lo_2_b_mapped_df["Moodle Competency Name"] = moodle_lo_2_b_mapped_df["Moodle Competency Name"].apply(clean_moodle_name)

# Drop duplicates
moodle_lo_2_b_mapped_df = moodle_lo_2_b_mapped_df.drop_duplicates().reset_index(drop=True)
# old_name=moodle_lo_2_b_mapped_df["Moodle Competency Name"].to_list()
# print(old_name)


lo_old_new_mapping_source_df["Skill"] = lo_old_new_mapping_source_df["Skill"].apply(clean_moodle_name)

print(lo_old_new_mapping_source_df.info())
print(moodle_lo_2_b_mapped_df.info())


# Perform left join
merged_df = moodle_lo_2_b_mapped_df.merge(
    lo_old_new_mapping_source_df,
    left_on="Moodle Competency Name",
    right_on="Skill",
    how="left"
)

# Extract successfully merged rows (matched data)
merged_data = merged_df.dropna(subset=["Skill"])
print(merged_data.shape[0])
merged_data.to_csv("/home/divum/Desktop/LMS/Data_Migration/Documents/--------mapped_lo.csv")

# Extract unmatched data (left DataFrame rows without a match)
unmatched_data = merged_df[merged_df["Skill"].isna()].drop(columns=["Skill", "Current Learning Outcome"])
print(unmatched_data.shape[0])
unmatched_data.to_csv("/home/divum/Desktop/LMS/Data_Migration/Documents/--------unmapped_lo.csv")
print(unmatched_data.info())
print(lo_old_new_mapping_source_df.info())
# Combine the merged and unmatched data
# final_df = pd.concat([merged_data, unmatched_data], ignore_index=True)
#
# print(final_df)


from rapidfuzz import process, fuzz  # Faster than fuzzywuzzy

# Fuzzy match function
def fuzzy_merge(left_df, right_df, left_key, right_key, threshold=85):
    matches = []
    for name in left_df[left_key]:
        best_match, score, _ = process.extractOne(name, right_df[right_key], scorer=fuzz.ratio)
        if score >= threshold:  # Match only if similarity is above threshold
            matches.append(best_match)
        else:
            matches.append(None)
    left_df["Matched Skill"] = matches
    return left_df

# Perform fuzzy matching
matched_df = fuzzy_merge(unmatched_data, lo_old_new_mapping_source_df, "Moodle Competency Name", "Skill")

# Merge based on the best fuzzy matches
merged_df = matched_df.merge(
    lo_old_new_mapping_source_df,
    left_on="Matched Skill",
    right_on="Skill",
    how="left"
)

# Extract matched and unmatched rows
merged_data = merged_df.dropna(subset=["Skill"])
print("----Matched records:", merged_data.shape[0])
merged_data.to_csv("/home/divum/Desktop/LMS/Data_Migration/Documents/new_mapped_lo.csv", index=False)

unmatched_data = merged_df[merged_df["Skill"].isna()].drop(columns=["Skill", "Current Learning Outcome", "Matched Skill"])
print("----------Unmatched records:", unmatched_data.shape[0])
unmatched_data.to_csv("/home/divum/Desktop/LMS/Data_Migration/Documents/unmapped_lo.csv", index=False)
