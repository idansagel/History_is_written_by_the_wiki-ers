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
            birth = claims.get('P569', [{}])[0].get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('time')
            death = claims.get('P570', [{}])[0].get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('time')

            # Correctly format the year with full digits
            birth = birth.split('T')[0] if birth else None
            death = death.split('T')[0] if death else None

            # # Convert to year format with + or - for BCE
            # birth = f"+{birth[1:5]}" if birth and (birth.startswith('-') or birth.startswith('+')) else birth[:4] if birth else None
            # death = f"+{death[1:5]}" if death and (death.startswith('-') or death.startswith('+')) else death[:4] if death else None

            # Image
            if 'P18' in claims:
                image_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{claims['P18'][0]['mainsnak']['datavalue']['value']}"

            # Occupation(s) - Resolve IDs to names
            if 'P106' in claims:
                occupation_ids = [claim['mainsnak']['datavalue']['value']['id'] for claim in claims['P106']]
                occupation_names = [entity.get('labels', {}).get(occ_id, {}).get('value') for occ_id in occupation_ids
                                    if occ_id in entity.get('labels', {})]

            # Field(s) of work - Resolve IDs to names
            if 'P101' in claims:
                field_ids = [claim['mainsnak']['datavalue']['value']['id'] for claim in claims['P101']]
                field_names = [entity.get('labels', {}).get(field_id, {}).get('value') for field_id in field_ids if
                               field_id in entity.get('labels', {})]

            # Geolocation based on "place of death" or directly if available
            if 'P20' in claims:  # Place of death
                place_of_death = claims['P20'][0]['mainsnak']['datavalue']['value']['id']
                geo_response = requests.get(f'https://www.wikidata.org/wiki/Special:EntityData/{place_of_death}.json')
                geo_data = geo_response.json()
                if 'entities' in geo_data and place_of_death in geo_data['entities']:
                    geo_claims = geo_data['entities'][place_of_death].get('claims', {})
                    if 'P625' in geo_claims:
                        location = geo_claims['P625'][0]['mainsnak']['datavalue']['value']
                        lat, lon = location['latitude'], location['longitude']

            # If no location found, use directly available geolocation (if any)
            if not lat and not lon and 'P625' in claims:
                location = claims['P625'][0]['mainsnak']['datavalue']['value']
                lat, lon = location['latitude'], location['longitude']

        return birth, death, image_url, description, occupation_names, field_names, lat, lon

    additional_data = []
    print("Fetching additional data from Wikidata...")
    for index, row in tqdm(top_10000_df.iterrows(), total=top_10000_df.shape[0], desc="Processing articles"):
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

    print("Process completed successfully!")


pagerank_file = 'pagerank_results.csv'
people_articles_file = 'wikipedia_people_articles.csv'
wikilinks_file = 'wikilinks.csv'
merged_output_file = 'merged_data.csv'
output_file = 'top_10000_people_articles.csv'

# Step 1: Merge and save
merge_and_save_data(pagerank_file, people_articles_file, wikilinks_file, merged_output_file, how_many=100)

# Step 2: Fetch Wikidata and save
fetch_wikidata_and_save(merged_output_file, output_file)