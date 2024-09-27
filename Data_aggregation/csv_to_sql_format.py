import pandas as pd
import json
import ast
import csv
import numpy as np

# Define the input and output CSV file paths
input_file = 'src/top_10000_people_articles.csv'
output_file = 'src/top_10000_people_articles_sql.csv'

# Read the CSV file into a pandas DataFrame
df = pd.read_csv(input_file)

# Function to convert string representations of lists to JSON format
def fix_quoted_string(column_data):
    try:
        # Safely evaluate the string representation of a list to a Python list
        python_list = ast.literal_eval(column_data)
        # Convert the Python list back to a JSON-formatted string
        return json.dumps(python_list)
    except (ValueError, SyntaxError):
        # If it fails (due to NaN or improper format), return the original value
        return column_data

# Apply the function to the 'occupation' and 'field' columns
df['occupation'] = df['occupation'].apply(fix_quoted_string)
df['field'] = df['field'].apply(fix_quoted_string)

# Add noise to latitude and longitude
def add_noise_to_coordinates(df, noise_scale=0.0001):
    df['latitude'] = df['latitude'] + np.random.normal(0, noise_scale, size=len(df))
    df['longitude'] = df['longitude'] + np.random.normal(0, noise_scale, size=len(df))
    return df

# Apply the noise to the latitude and longitude
df = add_noise_to_coordinates(df)

# Remove rows where 'birth' is null or empty
df = df.dropna(subset=['birth'])  # This line removes rows with missing birth years

# Ensure birth column is converted to nullable integer (Int64)
df['birth'] = df['birth'].astype('Int64')

# Function to process death column
def process_death(death_value):
    if pd.isna(death_value):
        return pd.NA  # Use pandas NA for missing values
    else:
        return int(death_value)  # Cast non-NaN to int

# Apply the function to the death column and set dtype to Int64
df['death'] = df['death'].apply(process_death).astype('Int64')

# Check if the changes were applied successfully
print(df[['birth', 'death']].head())

# Normalize the row index for the color of the dots on the map
def calculate_color_value(df):
    df['color_value'] = 1.0 - (df.index - df.index.min()) / (df.index.max() - df.index.min())
    return df

# Apply the color value calculation
df = calculate_color_value(df)

# Fix the outgoing_link_ids column to format it as a PostgreSQL array
def fix_outgoing_links_column(column_data):
    try:
        # Check if the data is a list; if not, handle it accordingly
        if isinstance(column_data, str):
            links_list = ast.literal_eval(column_data)
            # Format as a PostgreSQL array literal
            return '{' + ','.join(map(str, links_list)) + '}'
        elif isinstance(column_data, (list, tuple)):
            # In case it's already a list or tuple
            return '{' + ','.join(map(str, column_data)) + '}'
        else:
            # If it's not a list or string, return an empty array or string representation
            return '{}'
    except (ValueError, SyntaxError, TypeError):
        # If there's an issue (e.g., NaN or improper format), return empty array
        return '{}'

# Apply the function to fix 'outgoing_link_ids' column
df['outgoing_link_ids'] = df['outgoing_link_ids'].apply(fix_outgoing_links_column)

# Save the processed DataFrame to CSV without adding extra quotes
df.to_csv(output_file, index=False, quoting=csv.QUOTE_MINIMAL, na_rep='')