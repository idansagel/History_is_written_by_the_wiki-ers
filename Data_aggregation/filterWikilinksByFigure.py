import pandas as pd
from tqdm import tqdm
from collections import defaultdict

# Read the top 10000 people articles
top_articles = pd.read_csv('top_10000_people_articles.csv')
top_page_ids = set(top_articles['page_id'])

# Create a dictionary to store outgoing links for each page_id
outgoing_links = {}  # Changed from defaultdict(set) to regular dict

# Set the chunk size
chunk_size = 100000  # Adjust this based on your available memory

# Read and process the large file in chunks
print("Processing wikilinks.csv...")
for chunk in tqdm(pd.read_csv('wikilinks.csv', sep='\t', chunksize=chunk_size), desc="Processing data"):
    # Filter the chunk for rows where both page_id_from and page_id_to are in top_page_ids
    filtered_chunk = chunk[chunk['page_id_from'].isin(top_page_ids) & chunk['page_id_to'].isin(top_page_ids)]
    
    # Update the outgoing_links dictionary
    for _, row in filtered_chunk.iterrows():
        if row['page_id_from'] not in outgoing_links:
            outgoing_links[row['page_id_from']] = set()
        outgoing_links[row['page_id_from']].add(str(row['page_id_to']))

# Convert sets to comma-separated strings, only for non-empty sets
for page_id in outgoing_links:
    if outgoing_links[page_id]:  # Only process non-empty sets
        outgoing_links[page_id] = ','.join(outgoing_links[page_id])
    else:
        del outgoing_links[page_id]  # Remove empty sets from the dictionary

# Add the new column to top_articles DataFrame
print("Updating top_10000_people_articles.csv...")
top_articles['outgoing_link_ids'] = top_articles['page_id'].map(outgoing_links)

# Save the updated DataFrame
top_articles.to_csv('top_10000_people_articles.csv', index=False)

print("Update complete. Results saved in 'top_10000_people_articles.csv'")