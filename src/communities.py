import pandas as pd
import networkx as nx
import pickle
import os
from collections import defaultdict
import logging
from data_processing import load_and_process_data, get_unique_occupations
import math

logging.basicConfig(level=logging.INFO)

class FigureGroupFinder:
    def __init__(self):
        self.data, self.min_year, self.max_year = load_and_process_data()
        self.unique_occupations = get_unique_occupations(self.data)
        self.graph = None
        self.clusters = None
        self.neighbors_cache = {}
        self.cluster_members_cache = {}
        self.build_graph()
        self.load_or_calculate_clusters()
    
    def build_graph(self):
        self.graph = nx.DiGraph()
        edges_added = 0
        nodes_with_links = 0
        for _, row in self.data.iterrows():
            page_id = int(row['page_id'])
            self.graph.add_node(page_id)
            outgoing_links = row['outgoing_link_ids']
            
            if isinstance(outgoing_links, str):
                # Split the string by comma and convert to integers
                try:
                    outgoing_links = [int(link.strip()) for link in outgoing_links.split(',') if link.strip()]
                except ValueError:
                    logging.warning(f"Invalid outgoing_link_ids for page_id {page_id}: {outgoing_links}")
                    continue
            elif isinstance(outgoing_links, (int, float)):
                # If it's a single number and not NaN, convert to a list
                if not math.isnan(outgoing_links):
                    outgoing_links = [int(outgoing_links)]
                else:
                    outgoing_links = []
            elif isinstance(outgoing_links, tuple):
                # If it's a tuple, convert to a list
                outgoing_links = list(outgoing_links)
            elif pd.isna(outgoing_links):
                # If it's NaN, set to an empty list
                outgoing_links = []
            
            if isinstance(outgoing_links, list):
                for target in outgoing_links:
                    if not math.isnan(target):  # Additional check to avoid NaN values
                        self.graph.add_edge(page_id, int(target))
                        edges_added += 1
                if outgoing_links:
                    nodes_with_links += 1
            else:
                logging.warning(f"Unexpected type for outgoing_link_ids: {type(outgoing_links)} for page_id {page_id}")
        
        logging.info(f"Graph built with {self.graph.number_of_nodes()} nodes, {edges_added} edges, and {nodes_with_links} nodes with outgoing links")
        
        # Additional check
        if edges_added == 0:
            logging.error("No edges were added to the graph. Printing first few rows of outgoing_link_ids:")
            for _, row in self.data.head().iterrows():
                logging.error(f"Page ID: {row['page_id']}, outgoing_link_ids: {row['outgoing_link_ids']}")

    def load_or_calculate_clusters(self, resolution=1, threshold=1e-07, seed=None):
        cluster_file = os.path.join(os.path.dirname(__file__), 'louvain_clusters.pkl')
        if os.path.exists(cluster_file):
            with open(cluster_file, 'rb') as f:
                self.clusters = pickle.load(f)
        else:
            communities = nx.community.louvain_communities(
                self.graph.to_undirected(),
                weight='weight',
                resolution=resolution,
                threshold=threshold,
                seed=seed
            )
            self.clusters = {node: i for i, community in enumerate(communities) for node in community}
            
            with open(cluster_file, 'wb') as f:
                pickle.dump(self.clusters, f)
    
    def get_neighbors(self, main_id):
        if main_id not in self.neighbors_cache:
            outgoing = set(self.graph.successors(main_id))
            incoming = set(self.graph.predecessors(main_id))
            self.neighbors_cache[main_id] = outgoing.union(incoming)
            if not self.neighbors_cache[main_id]:
                logging.warning(f"No neighbors found for page_id {main_id}")
        return self.neighbors_cache[main_id]
    
    def get_cluster_members(self, main_id):
        if main_id not in self.cluster_members_cache:
            if main_id not in self.clusters:
                self.cluster_members_cache[main_id] = set()
            else:
                main_cluster = self.clusters[main_id]
                self.cluster_members_cache[main_id] = {node for node, cluster in self.clusters.items() if cluster == main_cluster}
        return self.cluster_members_cache[main_id]

def precompute_data(figure_finder):
    figures_by_year = defaultdict(set)
    figures_by_occupation = defaultdict(set)
    figures_by_group = {'neighbors': defaultdict(set), 'louvain': defaultdict(set)}

    total_rows = len(figure_finder.data)
    processed_rows = 0

    for _, row in figure_finder.data.iterrows():
        page_id = row['page_id']
        birth_year = int(row['birth'])
        death_year = int(row['death']) if pd.notna(row['death']) else figure_finder.max_year

        for year in range(birth_year, min(death_year, figure_finder.max_year) + 1):
            figures_by_year[year].add(page_id)

        for occupation in row['occupation']:
            figures_by_occupation[occupation].add(page_id)

        neighbors = figure_finder.get_neighbors(page_id)
        cluster_members = figure_finder.get_cluster_members(page_id)

        figures_by_group['neighbors'][page_id] = neighbors
        figures_by_group['louvain'][page_id] = cluster_members

        # Add this page_id to its neighbors' lists
        for neighbor in neighbors:
            figures_by_group['neighbors'][neighbor].add(page_id)

        processed_rows += 1
        if processed_rows % 1000 == 0:
            logging.info(f"Processed {processed_rows} rows out of {total_rows} total rows.")

    logging.info(f"Processed all {processed_rows} rows out of {total_rows} total rows.")
    
    # Verify that neighbors are not empty
    empty_neighbors = sum(1 for neighbors in figures_by_group['neighbors'].values() if not neighbors)
    logging.info(f"Number of entries with empty neighbors: {empty_neighbors}")

    return figures_by_year, figures_by_occupation, figures_by_group

def save_precomputed_data(figures_by_year, figures_by_occupation, figures_by_group, filename='precomputed_data.pkl'):
    full_path = os.path.join(os.path.dirname(__file__), filename)
    data_to_save = {
        'by_year': {year: list(figures) for year, figures in figures_by_year.items()},
        'by_occupation': {occ: list(figures) for occ, figures in figures_by_occupation.items()},
        'by_group': {
            'neighbors': {pid: list(neighbors) for pid, neighbors in figures_by_group['neighbors'].items()},
            'louvain': {pid: list(members) for pid, members in figures_by_group['louvain'].items()}
        }
    }
    with open(full_path, 'wb') as f:
        pickle.dump(data_to_save, f)

def load_precomputed_data(filename='precomputed_data.pkl'):
    full_path = os.path.join(os.path.dirname(__file__), filename)
    try:
        with open(full_path, 'rb') as f:
            data = pickle.load(f)
        return (
            defaultdict(set, {year: set(figures) for year, figures in data['by_year'].items()}),
            defaultdict(set, {occ: set(figures) for occ, figures in data['by_occupation'].items()}),
            {
                'neighbors': defaultdict(set, {pid: set(neighbors) for pid, neighbors in data['by_group']['neighbors'].items()}),
                'louvain': defaultdict(set, {pid: set(members) for pid, members in data['by_group']['louvain'].items()})
            }
        )
    except (EOFError, pickle.UnpicklingError) as e:
        logging.error(f"Error loading precomputed data: {str(e)}")
        raise

def get_or_create_precomputed_data(filename='precomputed_data.pkl'):
    full_path = os.path.join(os.path.dirname(__file__), filename)
    try:
        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
            figures_by_year, figures_by_occupation, figures_by_group = load_precomputed_data(filename)
            logging.info("Precomputed data loaded successfully.")
        else:
            raise FileNotFoundError("Precomputed data file is empty or doesn't exist.")
    except (FileNotFoundError, EOFError, pickle.UnpicklingError) as e:
        logging.info(f"Precomputed data not found or corrupted: {str(e)}. Generating...")
        try:
            figure_finder = FigureGroupFinder()
            figures_by_year, figures_by_occupation, figures_by_group = precompute_data(figure_finder)
            save_precomputed_data(figures_by_year, figures_by_occupation, figures_by_group, filename)
            logging.info("Precomputed data generated and saved.")
        except Exception as e:
            logging.error(f"Error during data precomputation: {str(e)}")
            raise

    # Ensure proper structure
    figures_by_year = defaultdict(set, figures_by_year)
    figures_by_occupation = defaultdict(set, figures_by_occupation)
    figures_by_group = {
        'neighbors': defaultdict(set, figures_by_group['neighbors']),
        'louvain': defaultdict(set, figures_by_group['louvain'])
    }

    return figures_by_year, figures_by_occupation, figures_by_group