import pandas as pd
import networkx as nx
import pickle
import os

class FigureGroupFinder:
    def __init__(self, main_id):
        self.main_id = main_id
        self.data = None
        self.graph = None
        self.clusters = None
        self.load_data()
        self.build_graph()
        self.load_or_calculate_clusters()
    
    def load_data(self):
        # Load the CSV file
        self.data = pd.read_csv('top_10000_people_articles.csv')
        
        # Convert outgoing_link_ids to lists
        self.data['outgoing_link_ids'] = self.data['outgoing_link_ids'].fillna('').apply(lambda x: [int(i) for i in x.split(',') if i])
    
    def build_graph(self):
        # Build a NetworkX graph from the data
        self.graph = nx.DiGraph()
        for _, row in self.data.iterrows():
            self.graph.add_node(row['page_id'])
            for target in row['outgoing_link_ids']:
                self.graph.add_edge(row['page_id'], target)
    
    def load_or_calculate_clusters(self, resolution=1, threshold=1e-07, seed=None):
        cluster_file = 'louvain_clusters.pkl'
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
            self.clusters = {}
            for i, community in enumerate(communities):
                for node in community:
                    self.clusters[node] = i
            
            # Save the clusters
            with open(cluster_file, 'wb') as f:
                pickle.dump(self.clusters, f)
    
    def get_neighbors(self):
        # Get all IDs having links to and from the main ID
        outgoing = set(self.graph.successors(self.main_id))
        incoming = set(self.graph.predecessors(self.main_id))
        return list(outgoing.union(incoming))
    
    def get_cluster_members(self):
        if self.main_id not in self.clusters:
            return []  # Return empty list if main_id is not in any cluster
        main_cluster = self.clusters[self.main_id]
        return [node for node, cluster in self.clusters.items() if cluster == main_cluster]
