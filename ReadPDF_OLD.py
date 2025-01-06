import os
import re
import pdfplumber
import csv

course_pattern = r'\b[A-Z]{4}-\d{3}-\d{3}\b'


def is_course_line(line):
    """Checks if a line contains the course pattern."""
    return bool(re.search(course_pattern, line))


def extract_pdf_data_with_pdfplumber(pdf_path):
    extracted_data = []
    college_name = ""
    semester = ""
    year = ""

    # Open the PDF with pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extract text from the page
            text = page.extract_text()

            # Split text into lines
            lines = text.split('\n')

            # Extract College Name, Semester, and Year from the header
            for line in lines:
                if "COLLEGE:" in line:
                    college_name = line.split("COLLEGE:")[1].strip()
                if "GRADE DISTRIBUTION REPORT FOR" in line:
                    try:
                        semester_year = line.split("GRADE DISTRIBUTION REPORT FOR")[1].strip()
                        semester, year = semester_year.split(' ')
                    except Exception as e:
                        print(f"Error extracting semester/year from {pdf_path}: {e}")
                        return  # Skip this PDF

                # Break early if both are found
                if college_name and semester and year:
                    break

            # Process course data
            for line in lines:
                if is_course_line(line):
                    # Split the line into parts based on spaces
                    parts = line.split(' ')
                    course_parts = parts[0].split('-')  # Split course code into Department, Course, Section
                    rest_of_line = parts[1:]  # Remaining part of the line

                    # Find the last numeric field in the line
                    last_numeric_index = len(rest_of_line) - 1
                    for i in reversed(range(len(rest_of_line))):
                        if rest_of_line[i].isdigit() or rest_of_line[i].replace('.', '', 1).isdigit():
                            last_numeric_index = i
                            break

                    # Instructor's name includes all parts after the last numeric field
                    instructor_name = ' '.join(rest_of_line[last_numeric_index + 1:])
                    rest_of_line = rest_of_line[:last_numeric_index + 1]  # Keep only numeric fields

                    # Combine everything into the desired format
                    temp0 = course_parts + rest_of_line + [instructor_name] + [college_name, semester, year]
                    extracted_data.append(temp0)
    # Return the structured data for further processing
    #return extracted_data
    # for data in extracted_data:
    #     print(data)
    save_to_csv(extracted_data)


def save_to_csv(data, output_folder="test_folder"):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Get the filename from the last three elements of the array
    file_name = '_'.join(data[0][-3:]).replace(' ', '_').upper() + ".csv"  # Example: 'ENGINEERING_SPRING_2024.csv'
    file_path = os.path.join(output_folder, file_name)

    # Define the headers based on the image provided
    headers = [
        'Department', 'Course', 'Section', 'A', 'B', 'C', 'D', 'F', 'A-F', 'GPA',
        'I', 'S', 'U', 'Q', 'X', 'Total', 'Instructor', 'College', 'Semester', 'Year'
    ]

    # Write the data to the CSV file
    with open(file_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        # Write the header
        writer.writerow(headers)
        # Write the data rows
        for row in data:
            writer.writerow(row)

    print(f"CSV saved to: {file_path}")


# Example usage
current_path = os.getcwd()  # Get the current working directory
pdf_path = os.path.join(current_path, "data", "grd20203EN.pdf")  # Append the relative path to the file

# Extract data and print results
extracted_lines = extract_pdf_data_with_pdfplumber(pdf_path)
# print("Extracted Course Lines:")
# for line in extracted_lines:
#     print(line)
