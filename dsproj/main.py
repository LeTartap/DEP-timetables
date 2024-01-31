import pandas as pd  # needed for most operation
import numpy as np
from sqlalchemy import create_engine

from datetime import datetime  # Import the datetime class from the datetime module
import re

pd.options.mode.chained_assignment = None  # default='warn'

# Load the data into pandas dataframes
data_2013_2014 = pd.read_csv('content/Activiteitenoverzicht_2013-2014_v2.csv')
data_2014_2015 = pd.read_csv('content/Activiteitenoverzicht_2014-2015_v2.csv')
data_2015_2016 = pd.read_csv('content/Activiteitenoverzicht_2015-2016_v2.csv')
data_2016_2017 = pd.read_csv('content/Activiteitenoverzicht_2016-2017_v2.csv')


# Reordering the columns of the 2016-2017 data to match the order of the 2013-2014 data
columns_order = data_2013_2014.columns
data_2014_2015_reordered = data_2014_2015[columns_order]
data_2015_2016_reordered = data_2015_2016[columns_order]
data_2016_2017_reordered = data_2016_2017[columns_order]
data_2013_2014['academic_year'] = "2013"
data_2014_2015_reordered['academic_year'] = "2014"
data_2015_2016_reordered['academic_year'] = "2015"
data_2016_2017_reordered['academic_year'] = "2016"

# Merging the two datasets
merged_data = pd.concat([data_2013_2014, data_2014_2015_reordered, data_2015_2016_reordered, data_2016_2017_reordered],
                        ignore_index=True)
# Concatenate all DataFrames into one
# merged_dataframe = pd.concat(dataframes, ignore_index=True)

# Now we'll try to export this merged dataframe to a new CSV file
merged_file_path = 'content/Merged_Activity_Data.csv'
merged_data.to_csv(merged_file_path, index=False, encoding='utf-8-sig')
print(merged_data.shape[0])
merged_data.dropna(subset=['Datum'], inplace=True)
merged_data.dropna(subset=['Zaal-Activiteit'], inplace=True)
merged_data = merged_data[merged_data['Grootte'] != 0]
merged_data.reset_index(drop=True, inplace=True)

# Provide the path for download
merged_file_path

def determine_correct_hostkey(row):
    # Example logic to determine which hostkey is valid
    # This may need to be adjusted based on the specific patterns in your data
    if "#" in row['Hostkey']:
        return row['Hostkey.1']
    else:
        return row['Hostkey']


# Apply the function to each row to create a new 'Combined Hostkey' column
merged_data['Combined Hostkey'] = merged_data.apply(determine_correct_hostkey, axis=1)
merged_data = merged_data.drop(columns=['Hostkey', 'Hostkey.1'])
merged_data.dropna(subset=['Combined Hostkey'], inplace=True)
merged_data.reset_index(drop=True, inplace=True)
print("Merged shape:")
print(merged_data.shape[0])
print(merged_data.head())
valid_programs_df = pd.read_csv('content/overview of programs and abbreviations.csv')
valid_program_codes = valid_programs_df['Abbreviation'].unique().tolist()


def parse_activity_name_with_validation(row, valid_codes):
    """
    Splits the 'Naam-Activiteit' into three parts based on whitespace and assigns them to
    'Program Code', 'Year/Module', and 'Activity Name'. Validates the first part against a list of valid program codes.
    """
    parts = row['Naam-Activiteit'].split(maxsplit=2)  # Split by whitespace, max 2 splits
    # Ensure there are three parts even if there are not enough splits
    parts += [''] * (3 - len(parts))

    # Check if the first part is a valid program code
    program_code = parts[0] if parts[0] in valid_codes else 'GENERIC'

    # Assign to respective new columns
    row['Program Code'] = program_code
    row['Year/Module'] = parts[1] if len(parts) > 1 else ''
    row['Activity Name'] = parts[2] if len(parts) > 2 else ''

    return row


# Apply the parsing function with validation to each row
parsed_data = merged_data.apply(
    lambda row: parse_activity_name_with_validation(row, valid_program_codes), axis=1)


# Drop the original 'Naam-Activiteit' column as it's now redundant
parsed_data.drop('Naam-Activiteit', axis=1, inplace=True)
reordered_columns = ['Program Code', 'Year/Module', 'Activity Name'] + [col for col in parsed_data.columns if
                                                                        col not in ['Program Code', 'Year/Module',
                                                                                    'Activity Name']]
parsed_data = parsed_data[reordered_columns]
# Exporting this full data to a new CSV file
full_merged_file_path = 'content/Full_Merged_Activity_Data.csv'
parsed_data.to_csv(full_merged_file_path, index=False, encoding='utf-8-sig')

full_merged_file_path
print("Parsed data:")
parsed_data['Year/Module'].replace('', np.nan, inplace=True)

parsed_data = parsed_data.dropna(subset=['Year/Module'])
parsed_data = parsed_data.dropna(subset=['Program Code'])

parsed_data.reset_index(drop=True, inplace=True)

print(parsed_data.shape[0])
print(parsed_data.head())


def update_year_module(year_module):
    if year_module in ['B1-PM','MI','MOD1', 'MOD2', 'MOD3', 'MOD4', 'MOD01', 'MOD02', 'MOD03', 'MOD04', 'M1', 'M2', 'M3', 'M4']:
        return 'B1'
    elif year_module in ['MOD5', 'MOD6', 'MOD7', 'MOD8', 'MOD05', 'MOD06', 'MOD07', 'MOD08', 'M5', 'M6', 'M7', 'M8']:
        return 'B2'
    elif year_module in ['B3/PM','MOD9', 'MOD10', 'MOD11', 'MOD12', 'MOD09', 'M9', 'M10', 'M11', 'M12']:
        return 'B3'
    elif year_module in ['M2/M3']:
        return 'M'
    else:
        return year_module


parsed_data['Year/Module'] = parsed_data['Year/Module'].apply(update_year_module)
parsed_data = parsed_data[parsed_data['Year/Module'].isin(['B1', 'B2', 'B3', 'M'])]

# Displaying first few rows of the updated DataFrame
print(parsed_data.head())
data = parsed_data
print(data.shape[0])
# Get unique values from the 'Activiteitstype' column


# Function to determine the correct hostkey value
def convert_to_date_only(value):
    if isinstance(value, str):
        # Check for 'YYYY/MM/DD HH:MM:SS' format
        try:
            return datetime.strptime(value, '%Y/%m/%d %H:%M:%S').strftime('%Y-%m-%d')
        except ValueError:
            # Check for 'MM/DD/YYYY HH:MM:SS' format
            try:
                return datetime.strptime(value, '%m/%d/%Y %H:%M:%S').strftime('%Y-%m-%d')
            except ValueError:
                # Return the original string if it's not a matching date format
                return value
    else:
        # Return the value as-is if it's not a string
        return value


def is_correct_date_format(value):
    correct_date_format_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    return isinstance(value, str) and correct_date_format_pattern.match(value)


# Checking if all rows are now in the correct 'YYYY-MM-DD' format
total_rows = data.shape[0]
correct_format_matches = data['Datum'].apply(is_correct_date_format)
boolean_correct_format_matches = correct_format_matches.apply(lambda x: x is not None)
# Count the number of True values where the pattern was matched
boolean_correct_format_count = boolean_correct_format_matches.sum()

all_rows_correct_format = boolean_correct_format_count == total_rows
print(all_rows_correct_format, boolean_correct_format_count, total_rows)
for column in data.columns:
    data[column] = data[column].apply(convert_to_date_only)
correct_format_matches = data['Datum'].apply(is_correct_date_format)
boolean_correct_format_matches = correct_format_matches.apply(lambda x: x is not None)
# Count the number of True values where the pattern was matched
boolean_correct_format_count = boolean_correct_format_matches.sum()

all_rows_correct_format = boolean_correct_format_count == total_rows
# Display the first few rows of the updated dataset to verify the changes
print(all_rows_correct_format, boolean_correct_format_count, total_rows)


def is_date_format(value):
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    return isinstance(value, str) and bool(date_pattern.match(value))





# Display the first few rows of the updated dataset to verify the changes
# data[['Hostkey', 'Hostkey.1', 'Combined Hostkey']].head()
# Assuming 'data' is your DataFrame and it has the columns 'Program Code' and 'Year/Module'
def update_program_code(row):
    # Check if 'Year/Module' is 'GENERIC' or 'UNKNOWN', and return None if so
    if row['Year/Module'] == 'GENERIC' or row['Year/Module'] == 'UNKNOWN':
        return None
    elif row['Year/Module'] == 'PM':
        return None
    else:
        # Otherwise, add the first character of 'Year/Module' to 'Program Code'
        return row['Program Code'] + ' ' + row['Year/Module'][0]


# Apply the function to each row and drop rows where the function returns None
data['Program Code'] = data.apply(update_program_code, axis=1)
data.dropna(subset=['Program Code'], inplace=True)
data = data[data['Program Code'] != 'AM B']
data = data[data['Program Code'] != 'PSTS B']
data = data[data['Program Code'] != 'GENERIC B']
data = data[data['Program Code'] != 'CME B']
data = data[data['Program Code'] != 'GENERIC M']
data = data[data['Program Code'] != 'NT B']
data = data[data['Program Code'] != 'HS B']
data = data[data['Program Code'] != 'HMI B']
data = data[data['Program Code'] != 'EST B']
data = data[data['Program Code'] != 'BA B']
data = data[data['Program Code'] != 'TM B']
data = data[data['Program Code'] != 'PSY M']
data = data[data['Program Code'] != 'TI M']
data = data[data['Program Code'] != 'MPS I']
data = data[data['Program Code'] != 'ELAN B']
data.reset_index(drop=True, inplace=True)

print(data.shape[0])


print(data.head())
print(data.shape[0])


def calculate_duration(row):
    try:
        # Check if both times are strings, if not, they might be NaN or another type
        if isinstance(row['Tijd van'], str) and isinstance(row['Tijd tot en met'], str):
            start_time = datetime.strptime(row['Tijd van'].strip(), '%H:%M:%S')
            end_time = datetime.strptime(row['Tijd tot en met'].strip(), '%H:%M:%S')
            return (end_time - start_time).seconds / 3600  # This will give you the duration in hours
        else:
            return None  # Return None if one of the times is not a string
    except Exception as e:
        print(f"Error processing row {row.name}: {e}")
        return None


# Apply the function to the dataframe to create a new 'Duration' column
data['duration'] = data.apply(calculate_duration, axis=1)
data.dropna(subset=['duration'], inplace=True)
data.reset_index(drop=True, inplace=True)

# Display the first few rows to verify the new column
print(data.head())
print(data.shape[0])

# Dictionary of Dutch to English translations for the column headers

translations = {
    'Program Code': 'program_code',
    'Year/Module': 'program_type',
    'Activity Name': 'activity_name',
    'Beschrijving-Activiteit': 'activity_description',
    'Activiteitstype': 'activity_type',
    'Datum': 'date',
    'Tijd van': 'start_time',
    'Tijd tot en met': 'end_time',
    'Grootte': 'size',
    'Zaal-Activiteit': 'room',
    'Combined Hostkey': 'course_code'
}

# Apply the translations to the DataFrame's columns
data.rename(columns=translations, inplace=True)
data['course_code'] = data['course_code'].astype(str)
data.drop_duplicates()
data.reset_index(drop=True, inplace=True)
# Display the first few rows to verify the changes
# Assuming 'df' is your DataFrame
print("Program code should change here")
print(data.head())
print(data.shape[0])
# Load the datasets
teacher_2013_2014_path = 'content/UT_courses_Osiris_with_teacher_2013-2014.csv'
teacher_2014_2015_path = 'content/UT_courses_Osiris_with_teacher_2014-2015.csv'
teacher_2015_path = 'content/Docentenoverzicht_2015_Osiris.csv'
teacher_2016_path = 'content/Docentenoverzicht_2016_Osiris.csv'

# Read the CSV files
teacher_2013_2014 = pd.read_csv(teacher_2013_2014_path)
teacher_2014_2015 = pd.read_csv(teacher_2014_2015_path)
teacher_2015 = pd.read_csv(teacher_2015_path)
teacher_2016 = pd.read_csv(teacher_2016_path)

# For the 2013-2014 and 2014-2015 datasets, drop the 'Teacher-lastname' column
teacher_2013_2014.drop(columns=['Teacher-lastname'], inplace=True)
teacher_2014_2015.drop(columns=['Teacher-lastname'], inplace=True)

# For the 2015 and 2016 datasets, rename 'Medewerker' to 'teacher_id'
teacher_2015.rename(columns={'Medewerker': 'teacher_id'}, inplace=True)
teacher_2016.rename(columns={'Medewerker': 'teacher_id'}, inplace=True)

# For the 2013-2014 and 2014-2015 datasets, rename 'Teachernr' to 'teacher_id'
teacher_2013_2014.rename(columns={'Teachernr': 'teacher_id'}, inplace=True)
teacher_2014_2015.rename(columns={'Teachernr': 'teacher_id'}, inplace=True)

# Concatenate all teacher dataframes and drop duplicates based on 'teacher_id'
combined_teachers = pd.concat([teacher_2013_2014, teacher_2014_2015, teacher_2015, teacher_2016])
combined_teachers.drop_duplicates(subset='teacher_id', inplace=True)
combined_teachers.reset_index(drop=True, inplace=True)

# Display the first few rows and the number of unique teacher IDs

# Assuming df is your DataFrame
combined_teachers = combined_teachers[['teacher_id']]
combined_teachers = combined_teachers.dropna()
print(combined_teachers.head())
print(combined_teachers['teacher_id'].nunique())
# Renaming columns for the 2013 and 2014 files
teacher_2013_2014.rename(columns={
    'Collegeyear': 'year',
    'Course': 'course_code',
    'Coursename': 'course_name',
    'teacher_id': 'teacher_id'
}, inplace=True)

teacher_2014_2015.rename(columns={
    'Collegeyear': 'year',
    'Course': 'course_code',
    'Coursename': 'course_name',
    'teacher_id': 'teacher_id'
}, inplace=True)

# Renaming columns for the 2015 and 2016 files
teacher_2015.rename(columns={
    'Collegejaar': 'year',
    'Cursus': 'course_code',
    'Cursusnaam': 'course_name',
    'teacher_id': 'teacher_id'
}, inplace=True)

teacher_2016.rename(columns={
    'Collegejaar': 'year',
    'Cursus': 'course_code',
    'Cursusnaam': 'course_name',
    'teacher_id': 'teacher_id'
}, inplace=True)
# Merging all course data into one DataFrame
all_courses = pd.concat([teacher_2013_2014, teacher_2014_2015, teacher_2015, teacher_2016]).drop_duplicates()

full_merged_file_path = 'content/allCourses.csv'
all_courses.to_csv(full_merged_file_path, index=False, encoding='utf-8-sig')
all_courses['program_code'] = ''  # Placeholder for program foreign key
all_courses['year'] = all_courses['year'].astype(str).str.replace('.0', '', regex=False)
all_courses['course_code'] = all_courses['course_code'].astype(str).str.replace('.0', '', regex=False)
# Step 1: Get a list of valid course codes from the 'courses' DataFrame
valid_course_codes = all_courses['course_code'].unique()
print("Valid course codes:")
print(valid_course_codes)
# Step 2: Filter the 'activities' DataFrame to only keep rows with valid course codes
data = data[data['course_code'].isin(valid_course_codes)]

# Print the unique values
all_courses_with_program = pd.merge(all_courses, data, on='course_code', how='left')
print(all_courses_with_program.head())

all_courses_with_program = all_courses_with_program.drop(
    columns=['program_code_x', 'program_type', 'activity_name', 'activity_description', 'activity_type', 'date'])
all_courses_with_program = all_courses_with_program.drop(
    columns=['start_time', 'end_time', 'size', 'room', 'academic_year', 'duration'])
all_courses_with_program.drop_duplicates(subset='course_code', inplace=True)
all_courses_with_program.reset_index(drop=True, inplace=True)
all_courses_with_program.rename(columns={'program_code_y': 'program_code'}, inplace=True)
unique_teacher_count = all_courses_with_program['teacher_id'].nunique()
data.rename(columns={'academic_year': 'year'}, inplace=True)
data = data[['course_code', 'program_code', 'activity_name', 'start_time', 'end_time', 'year', 'activity_description',
             'activity_type', 'duration', 'date', 'room']]




print(all_courses_with_program.head())
print(all_courses_with_program.shape[0])
print(data.head())
print(data.shape[0])
programs = pd.read_csv('content/overview of programs and abbreviations.csv')


# Define a function to extract the program type and update the name
def extract_program_type(name):
    program_type = name[0] if name.startswith(('B ', 'M ')) else ''
    updated_name = name[2:] if program_type else name
    return program_type, updated_name


# Apply the function to the 'Name' column
programs[['program_type', 'name']] = programs.apply(lambda row: pd.Series(extract_program_type(row['Name'])), axis=1)
programs = programs.drop(columns=['Name', 'Unnamed: 2'])
programs.rename(columns={'Abbreviation': 'program_code'}, inplace=True)
programs.rename(columns={'name': 'program_name'}, inplace=True)
programs['program_code'] = programs['program_code'] + ' ' + programs['program_type'].str[0]
new_row = {
    'program_code': 'ST M',
    'program_type': 'M',
    'program_name': 'Scheikundige Technologie'
}

programs = pd.concat([programs, pd.DataFrame([new_row])], ignore_index=True)

new_row = {
    'program_code': 'IEM B',
    'program_type': 'B',
    'program_name': 'Industrial Enginneriing'
}
programs = pd.concat([programs, pd.DataFrame([new_row])], ignore_index=True)

new_row = {
    'program_code': 'CS B',
    'program_type': 'B',
    'program_name': 'Communication Science'
}

programs = pd.concat([programs, pd.DataFrame([new_row])], ignore_index=True)
new_row = {
    'program_code': 'TEL B',
    'program_type': 'B',
    'program_name': 'Telematics'
}
programs = pd.concat([programs, pd.DataFrame([new_row])], ignore_index=True)
new_row = {
    'program_code': 'TW M',
    'program_type': 'M',
    'program_name': 'Technische Wiskunde'
}
programs = pd.concat([programs, pd.DataFrame([new_row])], ignore_index=True)


print(programs.head())
print(programs.shape[0])
driver = 'postgresql'
username = 'dab_ds23241a_123'
dbname = username  # it is the same as the username
password = 'BdleaEuFH036h8hi'
server = 'bronto.ewi.utwente.nl'
port = '5432'
# Creating the connection pool for SQL
engine = create_engine(f'{driver}://{username}:{password}@{server}:{port}/{dbname}?client_encoding=utf8')


def clean_data(text):
    if isinstance(text, str):
        return text.encode('latin1', 'ignore').decode('latin1')
    else:
        return text


# Clean the data in the DataFrame
all_courses_with_program['course_name'] = all_courses_with_program['course_name'].apply(clean_data)
#
# # Insert data from DataFrame into the 'Courses' table in the database
combined_teachers.to_sql('teacher', con=engine, schema='timetables', if_exists='append', index=False, method='multi')
programs.to_sql('program', con=engine, schema='timetables', if_exists='append', index=False, method='multi')
#
all_courses_with_program.to_sql('courses', con=engine, schema='timetables', if_exists='append', index=False,
                                 method='multi')
# Close the connection if you're done with it
data.to_sql('activities', con=engine, schema='timetables', if_exists='append', index=False, method='multi')

engine.dispose()
