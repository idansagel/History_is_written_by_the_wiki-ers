import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import ast
import time

load_dotenv()

# Global variable to store the database connection
db_conn = None

# Function to establish the database connection
# data_processing.py

def connect_db():
    global db_conn
    if db_conn is None or db_conn.closed != 0:
        DATABASE_URL = os.getenv('DATABASE_URL')
        db_conn = psycopg2.connect(DATABASE_URL)
    else:
        # Reset the connection if it's in an error state
        db_conn.rollback()
    return db_conn

# Fetch unique occupations from the database
def get_unique_occupations():
    conn = connect_db()
    cur = conn.cursor()

    # Use jsonb_array_elements_text to extract each occupation and count occurrences
    query = """
    SELECT occupation, COUNT(*) as count
    FROM (
        SELECT jsonb_array_elements_text(occupation) AS occupation
        FROM public.top_figures
    ) sub
    WHERE occupation IS NOT NULL
    GROUP BY occupation
    ORDER BY count DESC;
    """

    cur.execute(query)
    occupations_counts = cur.fetchall()
    cur.close()

    # Extract occupations from the query result
    occupations = [row[0] for row in occupations_counts]

    # Add "All" at the top of the list
    occupations.insert(0, "All")

    return occupations

# Fetch the minimum birth year from the database
def get_min_year():
    conn = connect_db()
    cur = conn.cursor()

    query = """
    SELECT MIN(birth) AS min_year 
    FROM public.top_figures 
    WHERE birth IS NOT NULL;
    """

    cur.execute(query)
    min_year = cur.fetchone()[0]
    cur.close()

    return min_year

# Fetch the maximum year as the current year
def get_max_year():
    return datetime.now().year

# Fetch figures for a given year, occupation, and filtered links
# data_processing.py

def get_figures_for_year(selected_year, selected_occupation, filtered_links):
    conn = connect_db()
    cur = conn.cursor()
    
    # Base query
    query = """
    SELECT
        page_id,
        article_name,
        birth,
        death,
        latitude,
        longitude,
        color_value,
        occupation
    FROM public.top_figures
    WHERE birth <= %s AND (death >= %s OR death IS NULL OR death = 0)
    """
    params = [selected_year, selected_year]
    
    # Apply occupation filter if not "All"
    if selected_occupation != "All":
        query += " AND EXISTS (SELECT 1 FROM jsonb_array_elements_text(occupation) AS occ WHERE LOWER(occ) = LOWER(%s))"
        params.append(selected_occupation)
    
    # Apply filtered links if provided
    if filtered_links and filtered_links != "None":
        page_ids = ast.literal_eval(filtered_links)
        if len(page_ids) > 0:
            placeholders = ', '.join(['%s'] * len(page_ids))
            query += f" AND page_id IN ({placeholders})"
            params.extend(page_ids)
        else:
            # If page_ids is empty, no figures should be returned
            query += " AND FALSE"
    
    # Execute the query
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    
    # Convert to DataFrame
    df_filtered = pd.DataFrame(rows, columns=[
        'page_id',
        'article_name',
        'birth',
        'death',
        'latitude',
        'longitude',
        'color_value',
        'occupation'
    ])
    
    return df_filtered

# Fetch detailed data for a specific figure by article name
def get_figure_data(article_name):
    conn = connect_db()
    cur = conn.cursor()

    query = """
    SELECT page_id,
           article_name,
           description,
           wikipedia_link,
           rank
    FROM (
        SELECT
            page_id,
            article_name,
            description,
            wikipedia_link,
            ROW_NUMBER() OVER (ORDER BY pagerank_score DESC) AS rank
        FROM public.top_figures
    ) sub
    WHERE article_name = %s
    """
    params = [article_name]

    cur.execute(query, params)
    row = cur.fetchone()
    cur.close()

    if row:
        figure_data = {
            'page_id': row[0],
            'article_name': row[1],
            'description': row[2],
            'wikipedia_link': row[3],
            'rank': row[4]
        }
        return figure_data
    else:
        return None

# Fetch all article names from the database
def get_all_article_names():
    conn = connect_db()
    cur = conn.cursor()

    # If you want to rank by pagerank_score, you can do this:
    query = """
    SELECT article_name
    FROM public.top_figures
    ORDER BY pagerank_score DESC;  -- Ordering by pagerank_score instead of rank
    """

    cur.execute(query)
    article_names = [row[0] for row in cur.fetchall()]
    cur.close()

    return article_names

# Fetch the birth year of a figure by article name
def get_birth_year(article_name):
    conn = connect_db()
    cur = conn.cursor()
    
    query = """
    SELECT birth
    FROM public.top_figures
    WHERE article_name = %s
    """
    params = [article_name]
    
    cur.execute(query, params)
    result = cur.fetchone()
    cur.close()
    
    if result:
        return result[0]
    else:
        return None

# Function to close the database connection when the app shuts down
def close_db_connection():
    global db_conn
    if db_conn is not None:
        db_conn.close()
        db_conn = None