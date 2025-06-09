import networkx as nx
from queue import PriorityQueue
from networkx.drawing.nx_agraph import read_dot, write_dot
import re
import json

class DisjointSet:
    def __init__(self):
        self.parent = {}

    def find(self, u):
        if self.parent[u] != u:
            self.parent[u] = self.find(self.parent[u])
        return self.parent[u]

    def union(self, u, v):
        pu, pv = self.find(u), self.find(v)
        if pu != pv:
            self.parent[pu] = pv

    def add(self, u):
        if u not in self.parent:
            self.parent[u] = u

    def get_groups(self):
        group_map = {}
        for u in self.parent:
            root = self.find(u)
            if root not in group_map:
                group_map[root] = []
            group_map[root].append(u)
        return list(group_map.values())

def edge_shrinking_partition_to_tagged_graph(graph: nx.DiGraph, threshold: float = 0.6) -> nx.DiGraph:
    """
    Returns a single nx.DiGraph with each node tagged by its group ID.
    """
    ds = DisjointSet()

    for node in graph.nodes:
        ds.add(node)

    pq = PriorityQueue()
    for u, v, data in graph.edges(data=True):
        w = data.get("weight", 0)
        pq.put((-float(w), u, v))

    while not pq.empty():
        neg_w, u, v = pq.get()
        w = -neg_w
        if w < threshold:
            break
        if ds.find(u) != ds.find(v):
            ds.union(u, v)

    groups = ds.get_groups()


    output_graph = nx.DiGraph()
    output_graph.add_nodes_from(graph.nodes(data=True))
    output_graph.add_edges_from(graph.edges(data=True))

    for group_id, group_nodes in enumerate(groups):
        for node in group_nodes:
            output_graph.nodes[node]["group"] = group_id

    return output_graph

def get_clustering_commit(hunk_graph: nx.DiGraph):
    commit = {}
    clustered_graph = edge_shrinking_partition_to_tagged_graph(hunk_graph)
    for node in clustered_graph.nodes:
        group = clustered_graph.nodes[node]["group"]
        if group not in commit:
            commit[group] = clustered_graph.nodes[node]["diff_content"].replace("\\ No newline at end of file", "")
        else:
            commit[group] += clustered_graph.nodes[node]["diff_content"].replace("\\ No newline at end of file", "")

    return commit


if __name__ == "__main__":
    pass
    # hunk_graph = nx.nx_agraph.read_dot("hunk_graph.dot")
    # clustered_graph = edge_shrinking_partition_to_tagged_graph(hunk_graph)
    # commit = get_clustering_commit(clustered_graph)
    # # nx.nx_agraph.write_dot(clustered_graph, "clustered_graph.dot")
    # fp = open("commit.json", "w")
    # json.dump(commit, fp)
    # fp.close()