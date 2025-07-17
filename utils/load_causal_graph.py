import networkx as nx
import json
from typing import Dict

def load_causal_graph(path: str) -> Dict:
    with open(path, "r") as f:
        graph_data = json.load(f)

    edges = graph_data["edges"]
    nodes = graph_data["nodes"]

    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    dot_graph = "digraph {\n"
    for src, dst in edges:
        dot_graph += f"{src} -> {dst};\n"
    dot_graph += "}"

    return {
        "nodes": nodes,
        "edges": edges,
        "dot_graph": dot_graph,
        "nx_graph": G  # optional
    }