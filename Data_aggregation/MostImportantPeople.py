import os
import pickle
import re

import pandas as pd
import requests
from tqdm import tqdm


# Function to save the merged DataFrame (Step 1)
def merge_and_save_data(pagerank_file, people_articles_file, wikilinks_file, merged_output_file, how_many=10000):
    # Load the pagerank results
    print("Loading PageRank results...")
    pagerank_df = pd.read_csv(pagerank_file)

    # Load the people articles
    print("Loading people articles...")
    people_articles_df = pd.read_csv(people_articles_file)

    # Load the wikilinks data (to get the article names)
    print("Loading wikilinks data...")
    wikilinks_df = pd.read_csv(wikilinks_file, sep='\t', usecols=['page_id_from', 'page_title_from']).drop_duplicates()

    # Merge pagerank results with article names from the wikilinks data
    print("Merging PageRank results with article names...")
    pagerank_with_names_df = pd.merge(pagerank_df, wikilinks_df, left_on='page_id', right_on='page_id_from')

    # Merge with people_articles_df to get the Wikipedia link
    print("Merging with people articles to get Wikipedia links...")
    merged_df = pd.merge(pagerank_with_names_df, people_articles_df[['article name', 'wikipedia link']],
                         left_on='page_title_from', right_on='article name', how='inner')

    # Sort the merged results by pagerank score in descending order
    print("Sorting results...")
    sorted_df = merged_df.sort_values(by='pagerank_score', ascending=False)

    # Select the top 10,000 rows
    top_10000_df = sorted_df.head(how_many)

    # Save the merged DataFrame
    print(f"Saving merged data to {merged_output_file}...")
    top_10000_df.to_csv(merged_output_file, index=False)

    print("Merge and save completed successfully!")
    return top_10000_df


# Function to get additional data from Wikidata (Step 2)
def fetch_wikidata_and_save(merged_input_file, output_file):
    # Load the merged data
    print("Loading merged data...")
    top_10000_df = pd.read_csv(merged_input_file)

    def parse_year(date_string):
        if not date_string:
            return None

        match = re.match(r'([+-])(\d+)-(\d{2})-(\d{2})', date_string)
        if match:
            sign, year, month, day = match.groups()
            year = int(year)
            return -year if sign == '-' else year
        return None

    def format_year(year):
        if year is None:
            return None
        if year < 0:
            return f"-{abs(year):04d}"  # BC year
        else:
            return f"{year:04d}"  # AD year without +

    query_cache = {}
    def get_wikidata_label(entity_id, language='en'):
        # Check if the query is in the cache
        cache_key = (entity_id, language)
        if cache_key in query_cache:
            return query_cache[cache_key]

        url = "https://www.wikidata.org/w/api.php"
        params = {
            'action': 'wbgetentities',
            'ids': entity_id,
            'format': 'json',
            'props': 'labels',
            'languages': language
        }

        response = requests.get(url, params=params)
        data = response.json()

        result = None
        if 'entities' in data and entity_id in data['entities']:
            entity = data['entities'][entity_id]
            if 'labels' in entity and language in entity['labels']:
                result = entity['labels'][language]['value']

        # Cache the result
        query_cache[cache_key] = result

        return result

    # Function to query Wikidata and get the required information
    def get_wikidata_info(wikipedia_title):
        url = f'https://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki&titles={wikipedia_title}&props=claims|descriptions|labels&languages=en&format=json'
        response = requests.get(url)
        data = response.json()

        # Initialize fields
        birth, death, image_url, description, occupation_names, field_names = None, None, None, None, [], []
        lat, lon = None, None

        if 'entities' in data:
            entity = next(iter(data['entities'].values()))

            # Description
            description = entity.get('descriptions', {}).get('en', {}).get('value')

            # Claims (facts)
            claims = entity.get('claims', {})

            # Birth and death
            def get_date(property_id, earliest=True):
                date_claims = claims.get(property_id, [])
                years = []
                for claim in date_claims:
                    date_value = claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('time')
                    if date_value:
                        year = parse_year(date_value)
                        if year is not None:
                            years.append(year)

                if years:
                    selected_year = min(years) if earliest else max(years)
                    return format_year(selected_year)
                return None

            birth = get_date('P569', earliest=True)  # Choose earliest birth year
            death = get_date('P570', earliest=False)  # Choose latest death year

            # Image URL
            image_url = None
            if 'P18' in claims:
                try:
                    image_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{claims['P18'][0]['mainsnak']['datavalue']['value']}"
                except KeyError:
                    image_url = None

            # Occupation(s) - Resolve IDs to names
            occupation_names = []
            if 'P106' in claims:
                try:
                    occupation_ids = [claim['mainsnak']['datavalue']['value']['id'] for claim in claims['P106']]
                    occupation_names = [get_wikidata_label(occ_id) for occ_id in occupation_ids]
                except KeyError:
                    occupation_names = []

            # Field(s) of work - Resolve IDs to names
            field_names = []
            if 'P101' in claims:
                try:
                    field_ids = [claim['mainsnak']['datavalue']['value']['id'] for claim in claims['P101']]
                    field_names = [get_wikidata_label(field_id) for field_id in field_ids]
                except KeyError:
                    field_names = []

            lat, lon = None, None

            def get_location(place_id):
                try:
                    geo_response = requests.get(
                        f'https://www.wikidata.org/wiki/Special:EntityData/{place_id}.json')
                    geo_data = geo_response.json()
                    if 'entities' in geo_data and place_id in geo_data['entities']:
                        geo_claims = geo_data['entities'][place_id].get('claims', {})
                        if 'P625' in geo_claims:
                            location = geo_claims['P625'][0]['mainsnak']['datavalue']['value']
                            return location['latitude'], location['longitude']
                except (KeyError, IndexError, requests.RequestException):
                    pass
                return None, None

            def get_location_from_claims(claims, property_ids):
                for pid in property_ids:
                    if pid in claims:
                        try:
                            place_id = claims[pid][0]['mainsnak']['datavalue']['value']['id']
                            lat, lon = get_location(place_id)
                            if lat is not None and lon is not None:
                                return lat, lon
                        except (KeyError, IndexError):
                            continue
                return None, None

            # List of properties to check, in order of preference
            # P20: Place of birth, P19: Place of death, P551: Residence, P27: Country of citizenship,
            # P937: Work location, P69: Educated at, P119: Place of burial
            property_ids = ['P119', 'P20', 'P19', 'P551', 'P27', 'P937', 'P69']

            lat, lon = get_location_from_claims(claims, property_ids)

            # If still not found, use directly available geolocation (if any)
            if lat is None and lon is None and 'P625' in claims:
                try:
                    location = claims['P625'][0]['mainsnak']['datavalue']['value']
                    lat, lon = location['latitude'], location['longitude']
                except KeyError:
                    lat, lon = None, None


        return birth, death, image_url, description, occupation_names, field_names, lat, lon

    def save_checkpoint(data, processed_rows, filename):
        with open(filename, 'wb') as f:
            pickle.dump({'data': data, 'processed_rows': processed_rows}, f)

    def load_checkpoint(filename):
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                checkpoint = pickle.load(f)
            return checkpoint['data'], checkpoint['processed_rows']
        return [], 0

    CHECKPOINT_FILE = 'wikidata_checkpoint.pkl'
    ROWS_PER_CHECKPOINT = 500

    # Load from checkpoint if it exists
    additional_data, start_row = load_checkpoint(CHECKPOINT_FILE)

    print("Fetching additional data from Wikidata...")
    for index, row in tqdm(top_10000_df.iloc[start_row:].iterrows(), total=top_10000_df.shape[0] - start_row,
                           desc="Processing articles", initial=start_row):
        wikipedia_title = row['page_title_from']
        birth, death, image_url, description, occupation_names, field_names, lat, lon = get_wikidata_info(
            wikipedia_title)

        additional_data.append({
            'birth': birth,
            'death': death,
            'image_url': image_url,
            'description': description,
            'occupation': occupation_names,
            'field': field_names,
            'latitude': lat,
            'longitude': lon
        })

        # Save checkpoint every ROWS_PER_CHECKPOINT rows
        if (index + 1) % ROWS_PER_CHECKPOINT == 0:
            save_checkpoint(additional_data, index + 1, CHECKPOINT_FILE)

    # Save final checkpoint
    save_checkpoint(additional_data, len(top_10000_df), CHECKPOINT_FILE)

    # Convert additional data to DataFrame
    additional_data_df = pd.DataFrame(additional_data)

    # Combine the original DataFrame with the additional data
    output_df = pd.concat([top_10000_df.reset_index(drop=True), additional_data_df], axis=1)

    # Select the required columns for the output file
    output_df = output_df[['page_title_from', 'page_id_from', 'pagerank_score', 'wikipedia link',
                           'birth', 'death', 'image_url', 'description', 'occupation', 'field', 'latitude',
                           'longitude']]

    # Rename columns for clarity
    output_df = output_df.rename(columns={
        'page_title_from': 'article_name',
        'page_id_from': 'page_id'
    })

    # Save the top 10,000 people articles to a CSV file
    print(f"Saving results to {output_file}...")
    output_df.to_csv(output_file, index=False)

    # Remove the checkpoint file after successful completion
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)

    print("Process completed successfully!")


pagerank_file = 'pagerank_results.csv'
people_articles_file = 'wikipedia_people_articles.csv'
wikilinks_file = 'wikilinks.csv'
merged_output_file = 'merged_data.csv'
output_file = 'top_10000_people_articles_backup.csv'

# Step 1: Merge and save
merge_and_save_data(pagerank_file, people_articles_file, wikilinks_file, merged_output_file)

# Step 2: Fetch Wikidata and save
fetch_wikidata_and_save(merged_output_file, output_file)