import pandas as pd
import numpy as np
import igraph as ig
from tqdm import tqdm
from collections import defaultdict

# Parameters
chunk_size = 1000000  # Number of rows to process at once
beta = 0.85  # Damping factor for PageRank
output_file = 'pagerank_results.csv'  # Output file for PageRank results

# Initialize lists to hold the data
edges = []
id_map = {}
reverse_id_map = {}
current_id = 0

# Reading the file in chunks
for chunk in tqdm(pd.read_csv('wikilinks.csv', sep='\t', chunksize=chunk_size), desc="Reading data"):
    for from_id, to_id in zip(chunk['page_id_from'], chunk['page_id_to']):
        # Map original IDs to consecutive integers
        if from_id not in id_map:
            id_map[from_id] = current_id
            reverse_id_map[current_id] = from_id
            current_id += 1
        if to_id not in id_map:
            id_map[to_id] = current_id
            reverse_id_map[current_id] = to_id
            current_id += 1

        # Add edge using mapped IDs
        edges.append((id_map[from_id], id_map[to_id]))

print("Creating graph...")
# Create the graph
graph = ig.Graph(edges=edges, directed=True)

print("Computing PageRank...")
# Compute PageRank using igraph's implementation
pagerank_scores = graph.pagerank(damping=beta, implementation="prpack")

# Create a DataFrame with the results, mapping back to original IDs
pagerank_df = pd.DataFrame({
    'page_id': [reverse_id_map[i] for i in range(graph.vcount())],
    'pagerank_score': pagerank_scores
})

# Save the PageRank results to a CSV file
pagerank_df.to_csv(output_file, index=False)

print(f"PageRank computation complete. Results saved to {output_file}.")