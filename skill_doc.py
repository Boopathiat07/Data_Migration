import pandas as pd
import psycopg2
import json
import numpy as np
from datetime import datetime
import os


# Utility function to convert numpy types to Python native types
def to_python_type(value):
    """Convert numpy and pandas types to standard Python types"""
    if isinstance(value, (np.integer, np.int64)):
        return int(value)
    elif isinstance(value, (np.floating, np.float64)):
        return float(value)
    elif pd.isna(value):
        return None
    elif isinstance(value, np.bool_):
        return bool(value)
    elif isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    return value


# Function to get mapping between old course names and new course names
def get_old_course_and_new_course_mapping():
    old_and_new_course_mapping_df = pd.read_csv(
        "/home/divum/Desktop/LMS/Data_Migration/Documents/old_and_new_course_mapping.csv")
    old_and_new_course_mapping_df['old_course_name'] = old_and_new_course_mapping_df['old_course_name'].str.strip()
    old_and_new_course_mapping_df['new_course_name'] = old_and_new_course_mapping_df['new_course_name'].str.strip()
    return old_and_new_course_mapping_df.set_index('old_course_name')['new_course_name'].to_dict()


# Function to establish database connections
def connect_to_databases():
    try:
        assessment_conn = psycopg2.connect("postgresql://postgres:Bp4N5$TCvpRv@localhost:5432/gm_a")
        course_conn = psycopg2.connect("postgresql://postgres:Bp4N5$TCvpRv@localhost:5432/gm_c")
        user_conn = psycopg2.connect("postgresql://postgres:Bp4N5$TCvpRv@localhost:5432/gm_u")

        return assessment_conn, course_conn, user_conn
    except Exception as e:
        print(f"Error connecting to databases: {e}")
        raise


# Function to get user ID from employee code
def get_user_id_from_employee_code(user_cursor, employee_code):
    if employee_code is None or pd.isna(employee_code):
        return None

    # Convert employee_code to string if it's a numeric type
    if isinstance(employee_code, (np.integer, np.floating, int, float)):
        employee_code = str(int(employee_code))

    query = """
        SELECT id FROM public."user" WHERE employee_id = %s
    """
    user_cursor.execute(query, (employee_code,))
    result = user_cursor.fetchone()
    if result:
        return result[0]
    return None


# Function to insert data into course_assessment table
def insert_course_assessment(assessment_cursor, data):
    query = """
        INSERT INTO course_assessment 
        (assessment_subtype, course_id, assessment_id, created_by, created_at, updated_by, updated_at, skill_document)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
        RETURNING id;
    """
    assessment_cursor.execute(query, data)
    return assessment_cursor.fetchone()[0]


# Function to insert data into assessment_learning_outcomes table
def insert_assessment_learning_outcomes(course_cursor, data):
    query = """
        INSERT INTO assessment_learning_outcomes 
        (assessment_id, course_id, learning_outcome_id, created_by, created_at, updated_by, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    course_cursor.execute(query, data)


# Function to insert data into learner_skill_assessment table
def insert_learner_skill_assessment(assessment_cursor, data):
    query = """
        INSERT INTO learner_skill_assessment 
        (user_id, assessment_id, uploaded_learner_document, status, created_by, created_at, updated_by, updated_at, start_date, work_order_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    assessment_cursor.execute(query, data)


# Main function to process and insert data
def process_and_insert():
    try:
        # Connect to databases
        assessment_conn, course_conn, user_conn = connect_to_databases()
        assessment_cursor = assessment_conn.cursor()
        course_cursor = course_conn.cursor()
        user_cursor = user_conn.cursor()

        # Get course mapping
        course_mapping = get_old_course_and_new_course_mapping()

        # Read CSV files
        df1 = pd.read_csv("/home/divum/Desktop/LMS/Data_Migration/Documents/new_competency_n_Workorder_10_feb.csv")
        df2 = pd.read_csv("/home/divum/Desktop/LMS/Data_Migration/Documents/new_file_submission_skills_10_feb.csv")
        df3 = pd.read_csv("/home/divum/Desktop/LMS/Data_Migration/Documents/new_intro_temp_files_10_feb.csv")

        # Cache for employee_code to user_id mapping
        employee_code_to_user_id = {}

        # Convert key columns to string to ensure consistent lookup
        df3['userid'] = df3['userid'].astype(str)
        df1['userid'] = df1['userid'].astype(str)
        if 'grader' in df1.columns:
            df1['grader'] = df1['grader'].apply(lambda x: str(x) if pd.notna(x) else None)

        # Track inserted assessment IDs for later use
        inserted_assessment_ids = {}  # Key: assignmentid, Value: assessment_id

        # Step 1: Process Sheet 3 data to create course_assessment entries
        print("Processing Sheet 3 to create course_assessment entries...")
        grouped = df3.groupby(['assignmentid', 'assignmentname', 'coursename'])

        for (assignmentid, assignmentname, coursename), group in grouped:
            # Convert assignmentid to int
            assignmentid = to_python_type(assignmentid)

            print("**********Ass ", assignmentname, assignmentid)
            # Check if this assignment has already been processed
            if assignmentid in inserted_assessment_ids:
                print(f"Assignment ID {assignmentid} already processed. Skipping.")
                continue

            # Get course_id from course mapping
            new_course_name = course_mapping.get(str(coursename).strip())

            print("***** COurse NAME ", new_course_name)
            if not new_course_name:
                print(f"Warning: No mapping found for course name '{coursename}'. Skipping this entry.")
                continue

            course_cursor.execute("SELECT id FROM courses WHERE course_name = %s", (new_course_name,))
            course_id_result = course_cursor.fetchone()
            if not course_id_result:
                print(f"Warning: No course found for course name '{new_course_name}'. Skipping this entry.")
                continue
            course_id = course_id_result[0]
            print("******COurseID ", course_id)

            # Find a valid user for this entry
            valid_user_row = None
            for _, row in group.iterrows():
                employee_code = str(row['employee_code'])
                user_id = None
                print("********EMP : ", employee_code)
                if employee_code not in employee_code_to_user_id:
                    user_id = get_user_id_from_employee_code(user_cursor, employee_code)
                    if user_id:
                        employee_code_to_user_id[employee_code] = user_id
                        valid_user_row = row
                        break
                else:
                    user_id = employee_code_to_user_id[employee_code]
                    valid_user_row = row
                    break

            if not valid_user_row:
                print(
                    f"Warning: No valid user found for any entry in assignment {assignmentid}. Skipping this assignment.")
                continue

            user_id = employee_code_to_user_id[str(valid_user_row['userid'])]

            # Prepare skill_document
            skill_document = {"name": "", "field_skill": {"learner_url": [], "trainer_url": []}}

            for _, row in group.iterrows():
                file_category = "trainer_document" if "worksheet" in str(
                    row['filename']).lower() else "learner_document"
                file_data = {
                    "file_name": str(row['filename']),
                    "file_type": "pdf",
                    "file_url": str(row['contenthash']),
                    "file_category": file_category
                }

                if file_category == "trainer_document":
                    skill_document["field_skill"]["trainer_url"].append(file_data)
                else:
                    skill_document["field_skill"]["learner_url"].append(file_data)

            # Insert course_assessment
            timecreated = to_python_type(valid_user_row.get('timecreated'))
            timemodified = to_python_type(valid_user_row.get('timemodified'))

            assessment_id = insert_course_assessment(assessment_cursor, (
                'skill', course_id, assignmentid, user_id, timecreated, user_id, timemodified,
                json.dumps(skill_document)
            ))

            # Store mapping of assignmentid to assessment_id
            inserted_assessment_ids[assignmentid] = assessment_id

            # Insert assessment_learning_outcomes - always use 400 as learning_outcome_id
            insert_assessment_learning_outcomes(course_cursor, (
                assessment_id, course_id, 400, user_id, timecreated, user_id, timemodified
            ))

        # Step 2: Process Sheet 1 and Sheet 2 data to create learner_skill_assessment entries
        print("Processing Sheet 1 and Sheet 2 to create learner_skill_assessment entries...")
        for assignmentid, assessment_id in inserted_assessment_ids.items():
            # Find all rows in Sheet 1 for this assignment
            assignment_rows = df1[df1['assignmentid'] == assignmentid]

            for _, row1 in assignment_rows.iterrows():
                # Get user_id
                learner_employee_code = str(row1['userid'])
                if learner_employee_code not in employee_code_to_user_id:
                    learner_user_id = get_user_id_from_employee_code(user_cursor, learner_employee_code)
                    if learner_user_id is None:
                        print(f"Warning: No user found for employee_code {learner_employee_code}. Skipping this entry.")
                        continue
                    employee_code_to_user_id[learner_employee_code] = learner_user_id

                learner_user_id = employee_code_to_user_id[learner_employee_code]

                # Get grader_user_id
                grader_employee_code = row1.get('grader')
                grader_user_id = None

                if grader_employee_code and not pd.isna(grader_employee_code):
                    grader_employee_code = str(grader_employee_code)
                    if grader_employee_code not in employee_code_to_user_id:
                        grader_user_id = get_user_id_from_employee_code(user_cursor, grader_employee_code)
                        employee_code_to_user_id[grader_employee_code] = grader_user_id
                    else:
                        grader_user_id = employee_code_to_user_id[grader_employee_code]

                # Get submission data for this user's submission
                subid = to_python_type(row1.get('subid'))
                submission_data = df2[df2['submissionid'] == subid] if subid and not pd.isna(subid) else pd.DataFrame()

                # Handle missing submission data
                if submission_data.empty:
                    contenthash_list = []
                    timecreated_submission = None
                    timemodified_submission = None
                else:
                    # Convert contenthash values to strings
                    contenthash_values = [str(h) for h in submission_data['contenthash'].tolist()]
                    contenthash_list = [contenthash_values]
                    timecreated_submission = to_python_type(submission_data['timecreated'].iloc[0])
                    timemodified_submission = to_python_type(submission_data['timemodified'].iloc[-1])

                # Map status
                status_value = to_python_type(row1.get('status'))
                if status_value == 'submitted':
                    status = 'approved'
                elif status_value in ['new', 'draft']:
                    status = 'pending'
                else:
                    status = 'yts'

                # Get workorder data
                workorderdate = to_python_type(row1.get('workorderdate'))
                workorder = to_python_type(row1.get('workorder'))

                # Insert learner_skill_assessment
                insert_learner_skill_assessment(assessment_cursor, (
                    learner_user_id, assessment_id, json.dumps(contenthash_list),
                    status, grader_user_id, timecreated_submission,
                    grader_user_id, timemodified_submission,
                    workorderdate, workorder
                ))

        # Commit all transactions
        # assessment_conn.commit()
        # course_conn.commit()
        # user_conn.commit()
        print("Data migration completed successfully!")

    except Exception as e:
        # Rollback in case of error
        assessment_conn.rollback()
        course_conn.rollback()
        user_conn.rollback()
        print(f"Error during migration: {e}")
        raise

    finally:
        # Close cursors and connections
        if 'assessment_cursor' in locals():
            assessment_cursor.close()
        if 'course_cursor' in locals():
            course_cursor.close()
        if 'user_cursor' in locals():
            user_cursor.close()
        if 'assessment_conn' in locals():
            assessment_conn.close()
        if 'course_conn' in locals():
            course_conn.close()
        if 'user_conn' in locals():
            user_conn.close()


if __name__ == "__main__":
    process_and_insert()