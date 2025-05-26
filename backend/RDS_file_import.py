import os
import csv
import mysql.connector
from dotenv import load_dotenv

# MySQL RDS connection details
rds_config = {
    'user': 'RDS_USER',
    'password': 'RDS_PASSWORD',  # Replace with your RDS password
    'host': 'RDS_HOST',  # Replace with your RDS endpoint
    'database': 'RDS_DATABASE',
}

def load_csv_to_rds(file_path, table_name, connection):
    """Load CSV data into RDS MySQL table."""
    cursor = connection.cursor()

    try:
        with open(file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header row

            # Build the insert query dynamically
            query = f"""
                INSERT INTO {table_name} 
                (department, course, section, a, b, c, d, f, af, gpa, i, s, u, q, x, total, instructor, college, semester, year) 
                VALUES ({','.join(['%s'] * 20)});
            """
            # Insert each row into the table
            for row in reader:
                cursor.execute(query, row)
            
        connection.commit()
        print(f"Successfully loaded: {file_path}")
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
    finally:
        cursor.close()

def batch_import_csvs_to_rds(directory, table_name):
    """Import all CSV files in a directory to RDS."""
    connection = mysql.connector.connect(**rds_config)
    try:
        for file_name in os.listdir(directory):
            if file_name.endswith('.csv'):
                file_path = os.path.abspath(os.path.join(directory, file_name))
                print(f"Importing file: {file_path}")
                load_csv_to_rds(file_path, table_name, connection)
    finally:
        connection.close()

# Example usage
csv_directory = os.path.join(os.getcwd(), "formatted_data")  # Replace with your CSV folder path
batch_import_csvs_to_rds(csv_directory, "grade_data")
