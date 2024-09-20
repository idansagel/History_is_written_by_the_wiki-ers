import pandas as pd
import numpy as np
import datetime
import pickle
import itertools
import ast
import os

def load_and_process_data():
    # Load the data
    if os.environ.get('RENDER') == 'true':
        DATA_FILE = 'top_10000_people_articles.csv'
    else:
        DATA_FILE = 'src/top_10000_people_articles.csv'

    df = pd.read_csv(DATA_FILE)

    # Filter out rows where birth or death is NaN
    df = df.dropna(subset=['birth'])

    # Normalize the row index for the color of the dots on the map:
    df['color_value'] = 1.0 - (df.index - df.index.min()) / (df.index.max() - df.index.min())

    # Calculate the year range for the timeline, excluding NaN values and converting to int
    min_year = np.int16(df['birth'].min())
    max_year = datetime.datetime.now().year

    return df, min_year, max_year, get_unique_occupations(df)

def get_unique_occupations(df, count=50):
    # Get unique occupations for the dropdown options
    df['occupation'] = df['occupation'].apply(lambda x: ast.literal_eval(x))
    all_occupations = list(itertools.chain(*df['occupation']))
    frequency = pd.Series(all_occupations).value_counts().to_dict()
    unique_occupations = list(frequency.keys())
    unique_occupations.append("All")
    unique_occupations.sort(key=lambda x: (x != "All", -frequency.get(x, 0)))
    return unique_occupations[:count]
