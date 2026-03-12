import timeit
import networkx as nx
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from teacher.basic_reporter import BasicTeacher

def create_large_graph(num_nodes=1000, num_edges=5000):
    G = nx.DiGraph()
    for i in range(num_nodes):
        node_type = 'class' if i % 10 == 0 else 'function'
        G.add_node(f"Node_{i}", type=node_type)

    for i in range(num_edges):
        u = f"Node_{i % num_nodes}"
        v = f"Node_{(i + 1) % num_nodes}"
        G.add_edge(u, v)
    return G

def benchmark():
    teacher = BasicTeacher()
    G = create_large_graph(10000, 50000)

    # Measure execution time
    start = timeit.default_timer()
    for _ in range(10):
        teacher.generate_lesson(G, "large_file.py")
    end = timeit.default_timer()

    print(f"Time taken: {end - start:.4f} seconds")

if __name__ == '__main__':
    benchmark()