import os
import shutil
import mysql.connector

# MySQL connection details
db_config = {
    'user': 'raj',
    'password': 'root',
    'host': 'localhost',
    'database': 'grade_distribution',
    'allow_local_infile': True
}

# Directory for MySQL to access files
mysql_data_dir = "C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/"

connection = mysql.connector.connect(**db_config)
cursor = connection.cursor()
cursor.execute("TRUNCATE TABLE grade_data;")
cursor.close()
quit()

def move_file_to_mysql_dir(file_path):
    """Move file to MySQL secure directory."""
    dest_path = os.path.join(mysql_data_dir, os.path.basename(file_path))
    shutil.copy(file_path, dest_path)
    return dest_path

def load_csv_to_mysql(file_path, table_name, connection):
    cursor = connection.cursor()

    # Move file to MySQL's secure directory
    file_path_in_mysql = move_file_to_mysql_dir(file_path)
    escaped_path = file_path_in_mysql.replace("\\", "/")  # Replace backslashes with forward slashes

    # MySQL LOAD DATA INFILE query
    query = f"""
        LOAD DATA INFILE '{escaped_path}'
        INTO TABLE {table_name}
        FIELDS TERMINATED BY ',' 
        ENCLOSED BY '"' 
        LINES TERMINATED BY '\n'
        IGNORE 1 ROWS
        (department, course, section, a, b, c, d, f, af, gpa, i, s, u, q, x, total, instructor, college, semester, year);
        """

    try:
        cursor.execute(query)
        connection.commit()
        print(f"Successfully loaded: {file_path}")
    except mysql.connector.Error as e:
        print(f"Error loading {file_path}: {e}")
    finally:
        cursor.close()

# Function to process all CSV files in a directory
def batch_import_csvs(directory, table_name):
    connection = mysql.connector.connect(**db_config)
    try:
        for file_name in os.listdir(directory):
            if file_name.endswith('.csv'):
                file_path = os.path.abspath(os.path.join(directory, file_name))
                print(f"Importing file: {file_path}")
                load_csv_to_mysql(file_path, table_name, connection)
    finally:
        connection.close()

# Example usage
# csv_directory = os.path.join(os.getcwd(), "formatted_data")  # Replace with your CSV folder path
# batch_import_csvs(csv_directory, "grade_data")
