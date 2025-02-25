import json
import csv


def json_to_csv(json_file, csv_file):
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Extract employee data
    employee_data = data.get("employee_data", [])

    if not employee_data:
        print("No data found in JSON file.")
        return

    # Extract field names from the first dictionary
    fieldnames = employee_data[0].keys()

    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(employee_data)

    print(f"CSV file '{csv_file}' has been created successfully.")


# Usage
json_file = '/home/divum/Desktop/LMS/Darwin_response.json'  # Replace with your JSON file path
csv_file = '/home/divum/Desktop/LMS/Darwin_response.csv'  # Replace with your desired output CSV file path
json_to_csv(json_file, csv_file)