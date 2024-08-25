import pandas as pd

# File paths
pagerank_file = 'pagerank_results.csv'
people_articles_file = 'wikipedia_people_articles.csv'
wikilinks_file = 'wikilinks.csv'
output_file = 'top_10000_people_articles.csv'

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
top_10000_df = sorted_df.head(10000)

# Select the required columns for the output file
output_df = top_10000_df[['page_title_from', 'page_id_from', 'pagerank_score', 'wikipedia link']]

# Rename columns for clarity
output_df = output_df.rename(columns={
    'page_title_from': 'article_name',
    'page_id_from': 'page_id'
})

# Save the top 10,000 people articles to a CSV file
print(f"Saving results to {output_file}...")
output_df.to_csv(output_file, index=False)

print("Process completed successfully!")