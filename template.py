"""
Virtual Laboratory Experiment: Advanced Cypher Queries and Graph Pattern Matching
Domain: Academic Citation & Co-authorship Networks

A modular, four-section virtual laboratory experiment:
  1. Theory: Labeled Property Graph model, Cypher syntax, multi-hop traversals, aggregations, motifs, and complexity.
  2. Simulation: Interactive execution sandbox with Guided Cypher Presets and Custom Cypher Editor,
                real-time Plotly 2D graph subgraph visualization, complexity curves, and trial logger.
  3. Quiz: Self-grading 10-question conceptual assessment with instant feedback and explanations.
  4. Report Generation: Student info, recorded experimental trials, observations, and downloadable PDF report.

Note: No custom CSS is used so that Streamlit native light and dark themes render seamlessly.
"""

import os
import re
import time
from datetime import datetime
import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from fpdf import FPDF
from fpdf.enums import XPos, YPos


# ======================================================================================
# 1. EXPERIMENT CONFIGURATION & EDUCATIONAL CONTENT
# ======================================================================================

EXPERIMENT_CONFIG = {
    "title": "Advanced Cypher Queries and Graph Pattern Matching",
    "subtitle": "Academic Citation & Co-authorship Networks",
    "objectives": [
        "Construct and execute multi-hop variable-length Cypher traversals (-[:CITES*1..k]->) to trace scientific lineage.",
        "Implement intermediate query pipelining and complex aggregations using Cypher's WITH and COLLECT() clauses.",
        "Formulate graph pattern matching queries to detect structural motifs, including co-authorship triangles and bridge nodes.",
        "Identify hidden connections, potential future collaborators, and circular citation loops across academic literature.",
        "Analyze computational complexity, traversal selectivity, and path explosion tradeoffs in graph pattern matching."
    ]
}

THEORY_CONTENT = {
    "background": """
### 1. The Labeled Property Graph (LPG) Model
In graph databases, data is organized as a **Labeled Property Graph (LPG)** rather than tabular relations:
- **Nodes (Vertices)**: Represent discrete domain entities (e.g., `:Author`, `:Paper`, `:Venue`). Nodes possess zero or more *Labels* for categorization and arbitrary key-value *Properties* (e.g., `name`, `year`, `h_index`).
- **Relationships (Edges)**: Directed, typed connections between two nodes (e.g., `-[:AUTHORED]->`, `-[:CITES]->`, `-[:COLLABORATED_WITH]->`). Relationships also store properties (e.g., `weight`, `timestamp`).
- **Index-Free Adjacency**: Unlike relational databases that resolve entity relationships via foreign key lookups ($O(\\log N)$ JOINs), graph databases maintain direct memory pointers between adjacent nodes. Traversing an edge takes $O(1)$ constant time, making deep path discovery exceptionally efficient.

---

### 2. Declarative Graph Querying with Cypher
Cypher is a declarative, pattern-matching query language using ASCII-art syntax:
```cypher
MATCH (a:Author)-[:AUTHORED]->(p:Paper)-[:CITES]->(cited:Paper)
WHERE p.year >= 2020 AND cited.citations > 500
RETURN a.name, p.title, cited.title
```
The query planner compiles the visual pattern into an optimized execution plan (e.g., NodeIndexSeek, Expand(All), Filter, and ProduceResults).

---

### 3. Multi-Hop Traversals & Variable-Length Paths
A central strength of Cypher is matching paths of variable depth using the `*min..max` syntax:
```cypher
MATCH path = (p1:Paper {id: 'P16'})-[:CITES*1..3]->(ancestor:Paper)
RETURN path, length(path) AS hops, ancestor.title
```
- **Fixed vs. Variable Paths**: While single-hop queries traverse direct neighbors, variable-length queries iteratively expand the search boundary (BFS/DFS).
- **Combinatorial Path Explosion**: In a network with average node branching factor $b$, the number of possible paths of depth $k$ scales as $O(b^k)$. Without selective predicates, unconstrained deep traversals can degrade performance exponentially.

---

### 4. Pipelining & Aggregation with `WITH` and `COLLECT()`
Cypher uses the `WITH` clause to divide query execution into distinct, modular pipeline stages:
1. **Intermediate Aggregation**: Group incoming records by grouping keys and compute statistics (`count()`, `sum()`, `avg()`).
2. **List Construction (`COLLECT`)**: The `collect()` function aggregates scalar values or subgraphs across grouped rows into a single list/array.
3. **Post-Aggregation Filtering**: Filter aggregated metrics using `WHERE` downstream of `WITH`:
```cypher
MATCH (a:Author)-[:AUTHORED]->(p:Paper)
WITH a, count(p) AS paper_count, sum(p.citations) AS total_citations, collect(p.title) AS paper_titles
WHERE paper_count >= 2 AND total_citations > 1000
RETURN a.name, a.institution, paper_count, total_citations, paper_titles
ORDER BY total_citations DESC
```

---

### 5. Complex Graph Motifs & Hidden Connection Retrieval
Real-world networks contain structural motifs that reveal organizational dynamics:
- **Triadic Closure (Co-authorship Triangles)**: When Author $A_1$ and Author $A_2$ have both collaborated with Author $B$ (the bridge) but have not co-authored a paper together directly, they form an open triangle. In network science, triadic closure predicts a high probability of future collaboration.
- **Shortest Paths & Bridge Nodes**: Identifying minimal-hop paths connecting disparate research communities reveals interdisciplinary bridge papers and researchers exhibiting high betweenness centrality.
- **Cyclic Citation Rings**: While academic citations are nominally directed acyclic graphs (DAGs), subtle circular loops (e.g., Paper $P_A \\rightarrow P_B \\rightarrow P_C \\rightarrow P_A$) emerge in reciprocal citation cartels or foundational cross-pollination.
    """,
    "procedure": [
        "Step 1: Review the theoretical framework, Labeled Property Graph principles, and Cypher syntax.",
        "Step 2: Navigate to the Simulation section in the sidebar menu.",
        "Step 3: Select 'Guided Cypher Presets' and explore the 5 core graph pattern queries (Multi-Hop Lineage, Triadic Closures, Filtered Aggregations, Shortest Path Bridges, and Cyclic Rings).",
        "Step 4: Adjust the interactive parameters (Traversal Depth k, Publication Year, Citation Thresholds) and observe how the highlighted Plotly 2D subgraph, tabular results, and latency metrics respond.",
        "Step 5: Switch to 'Custom Cypher Query Editor' to compose, modify, and execute your own Cypher patterns against the academic network.",
        "Step 6: Click 'Record Current Trial' to log data into your experimental session log across at least 3-4 distinct parameter configurations.",
        "Step 7: Complete the concept assessment Quiz to test your mastery of Cypher query semantics.",
        "Step 8: Open Report Generation, enter your student information, review the trial log, and download your official PDF report."
    ],
    "key_terms": {
        "Property Graph (LPG)": "Graph model consisting of nodes, directed typed relationships, and arbitrary key-value properties on both.",
        "Index-Free Adjacency": "Storage mechanism where nodes hold direct memory references to their neighbors, ensuring O(1) traversal per hop.",
        "Variable-Length Path (*min..max)": "Cypher pattern matching paths traversing between a minimum and maximum range of relationship hops.",
        "Triadic Closure": "Structural motif where two unconnected nodes sharing a mutual neighbor have a high propensity to form a future edge.",
        "WITH Pipelining": "Cypher clause that pipes intermediate query results, performing grouping, projection, or filtering before subsequent stages.",
        "COLLECT() Aggregator": "Aggregation function that transforms multiple individual record values into a single ordered list.",
        "Shortest Path & Bridge Node": "Minimal-hop sequence connecting two distant entities, and the critical junction nodes that link separate clusters.",
        "Combinatorial Path Explosion": "Exponential growth in traversed paths O(b^k) as traversal depth k increases with average branching factor b."
    }
}

QUIZ_QUESTIONS = [
    {
        "id": 1,
        "question": "In Cypher, what does the pattern `MATCH path = (p1:Paper)-[:CITES*2..4]->(p2:Paper)` evaluate?",
        "options": [
            "A) Any citation path originating at p1 and terminating at p2 having between 2 and 4 relationship hops inclusive",
            "B) All paths between p1 and p2 where exactly 2 to 4 papers exist in the entire graph database",
            "C) A single random path that contains at least 4 relationships",
            "D) A citation path where each paper must have between 2 and 4 citations"
        ],
        "answer_index": 0,
        "explanation": "The asterisk syntax *min..max denotes variable-length path matching. *2..4 matches paths consisting of between 2 and 4 consecutive relationship hops."
    },
    {
        "id": 2,
        "question": "What is the primary role of the `WITH` clause in a multi-stage Cypher query?",
        "options": [
            "A) To create temporary physical indexes on disk during query runtime",
            "B) To pipeline and divide query execution into stages, enabling intermediate aggregations, projections, and filtering",
            "C) To terminate query execution immediately if a null property is encountered",
            "D) To import external CSV data files into the active graph session"
        ],
        "answer_index": 1,
        "explanation": "The WITH clause acts as a boundary pipeline that isolates query parts, allowing aggregation (e.g., count, sum), variable aliasing, and post-aggregation WHERE filtering."
    },
    {
        "id": 3,
        "question": "When grouping papers by author using `WITH a, collect(p.title) AS titles`, what does `collect()` produce for each author `a`?",
        "options": [
            "A) A single concatenated string with paper titles separated by commas",
            "B) A Python dictionary mapping author IDs to citations",
            "C) An ordered list/array containing the titles of all matched papers for that author",
            "D) The total numeric count of authored papers"
        ],
        "answer_index": 2,
        "explanation": "The collect() aggregation function bundles individual scalar values or nodes from grouped rows into a single list/array."
    },
    {
        "id": 4,
        "question": "By default in Cypher pattern matching (`MATCH`), how are relationships handled within a single path match?",
        "options": [
            "A) Relationships cannot be traversed more than once in the same path match (relationship uniqueness)",
            "B) Nodes cannot be traversed more than once, but relationships can repeat freely",
            "C) Both nodes and relationships can repeat infinitely without restriction",
            "D) Traversals are strictly acyclic across the entire graph database"
        ],
        "answer_index": 0,
        "explanation": "Cypher enforces relationship isomorphism (uniqueness) within a single MATCH path pattern: no relationship can appear more than once in a given matched path."
    },
    {
        "id": 5,
        "question": "How does `OPTIONAL MATCH` differ from a standard `MATCH` in Cypher?",
        "options": [
            "A) OPTIONAL MATCH executes faster by randomly sampling only 10% of nodes",
            "B) OPTIONAL MATCH behaves like an SQL LEFT OUTER JOIN, binding missing pattern variables to null rather than eliminating the row",
            "C) OPTIONAL MATCH only matches isolated nodes that have no relationships",
            "D) OPTIONAL MATCH enforces bidirectional relationship matching"
        ],
        "answer_index": 1,
        "explanation": "OPTIONAL MATCH searches for a pattern, but if no match is found for that part, it sets the variables to null while keeping earlier matched rows (analogous to LEFT OUTER JOIN)."
    },
    {
        "id": 6,
        "question": "Why do property graph databases exhibit superior traversal performance over relational databases for deep multi-hop queries?",
        "options": [
            "A) Graph databases compress all textual data into smaller disk blocks",
            "B) Graph databases utilize index-free adjacency where nodes hold direct memory references to neighboring edges, avoiding O(log N) index JOINs per hop",
            "C) Relational databases cannot store more than two foreign keys per table",
            "D) Graph databases execute queries using single-threaded sequential scans"
        ],
        "answer_index": 1,
        "explanation": "Index-free adjacency allows direct pointer traversal in O(1) time per relationship, whereas relational JOINs require logarithmic index lookups at every hop."
    },
    {
        "id": 7,
        "question": "Which Cypher pattern correctly identifies two authors `a1` and `a2` who share a mutual co-author `bridge` but have NOT collaborated directly?",
        "options": [
            "A) MATCH (a1:Author)-[:AUTHORED]->(p1)<-[:AUTHORED]-(bridge)-[:AUTHORED]->(p2)<-[:AUTHORED]-(a2) WHERE a1 <> a2 AND NOT (a1)-[:COLLABORATED_WITH]-(a2)",
            "B) MATCH (a1:Author)-[:AUTHORED]->(p1:Paper)->(a2:Author) WHERE a1 = a2",
            "C) MATCH (a1:Author)-[:CITES]->(bridge:Author)-[:CITES]->(a2:Author)",
            "D) MATCH (a1:Author), (a2:Author) WHERE a1.institution = a2.institution"
        ],
        "answer_index": 0,
        "explanation": "This pattern traverses from a1 through shared paper p1 to the bridge author, then through paper p2 to a2, while filtering out direct collaboration."
    },
    {
        "id": 8,
        "question": "What algorithmic approach does Cypher's `shortestPath()` function typically execute to find the minimal hop sequence between two nodes?",
        "options": [
            "A) Genetic algorithm with random mutation",
            "B) Breadth-First Search (BFS), often executed bidirectionally from both start and target nodes",
            "C) Depth-First Search (DFS) exploring branches to maximum graph depth first",
            "D) QuickSort on node ID strings"
        ],
        "answer_index": 1,
        "explanation": "shortestPath() operates on unweighted graphs using Breadth-First Search (BFS), expanding level-by-level (often bidirectionally) to guarantee minimal hop length."
    },
    {
        "id": 9,
        "question": "What is the semantic difference between matching `(a)-[:COLLABORATED_WITH]->(b)` and `(a)-[:COLLABORATED_WITH]-(b)`?",
        "options": [
            "A) The arrow syntax enforces traversal strictly in the directed direction, while the hyphen syntax traverses the edge regardless of direction",
            "B) The arrow syntax matches both directions, whereas the hyphen matches incoming edges only",
            "C) The hyphen syntax deletes the relationship from the graph during matching",
            "D) There is no semantic difference in Cypher"
        ],
        "answer_index": 0,
        "explanation": "In Cypher, -> or <- enforces directed relationship matching, while a dash - matches the relationship in either direction (undirected pattern matching)."
    },
    {
        "id": 10,
        "question": "If a graph has an average node degree of b = 10, what is the theoretical worst-case order of magnitude of paths explored during an unconstrained traversal of depth k = 4?",
        "options": [
            "A) O(b * k) = 40 paths",
            "B) O(b^k) = 10^4 = 10,000 paths",
            "C) O(b + k) = 14 paths",
            "D) O(log_b k) ≈ 0.6 paths"
        ],
        "answer_index": 1,
        "explanation": "Unconstrained graph path traversal scales exponentially with depth as O(b^k). For b=10 and k=4, the search tree expands to up to 10^4 = 10,000 potential paths."
    }
]


# ======================================================================================
# 2. GRAPH SIMULATION ENGINE & CYPHER QUERY RUNNER
# ======================================================================================

@st.cache_resource
def build_academic_knowledge_graph() -> nx.DiGraph:
    """
    Constructs an in-memory Academic Citation & Co-authorship Property Graph using NetworkX.
    Nodes: Authors and Papers with comprehensive properties.
    Edges: AUTHORED, CITES, and COLLABORATED_WITH.
    """
    G = nx.DiGraph()

    authors = [
        {"id": "A1", "name": "Dr. Ada Lovelace", "field": "Algorithms & AI", "institution": "Oxford Inst", "h_index": 48},
        {"id": "A2", "name": "Dr. Alan Turing", "field": "Theory & Crypto", "institution": "Cambridge Univ", "h_index": 52},
        {"id": "A3", "name": "Dr. Claude Shannon", "field": "Information Theory", "institution": "MIT", "h_index": 45},
        {"id": "A4", "name": "Dr. Judea Pearl", "field": "Causal Inference", "institution": "UCLA", "h_index": 42},
        {"id": "A5", "name": "Dr. Geoffrey Hinton", "field": "Deep Learning", "institution": "Univ of Toronto", "h_index": 55},
        {"id": "A6", "name": "Dr. Yann LeCun", "field": "Computer Vision", "institution": "NYU", "h_index": 50},
        {"id": "A7", "name": "Dr. Yoshua Bengio", "field": "Language & Generative AI", "institution": "Mila Montreal", "h_index": 51},
        {"id": "A8", "name": "Dr. Tim Berners-Lee", "field": "Web & Knowledge Graphs", "institution": "Oxford / W3C", "h_index": 40},
        {"id": "A9", "name": "Dr. Jennifer Widom", "field": "Graph Databases & Systems", "institution": "Stanford Univ", "h_index": 38},
        {"id": "A10", "name": "Dr. Christopher Re", "field": "Knowledge Extraction", "institution": "Stanford Univ", "h_index": 35},
        {"id": "A11", "name": "Dr. Jure Leskovec", "field": "Graph Neural Networks", "institution": "Stanford Univ", "h_index": 44},
        {"id": "A12", "name": "Dr. Michael Jordan", "field": "Optimization & ML", "institution": "UC Berkeley", "h_index": 49},
    ]

    for a in authors:
        G.add_node(a["id"], label="Author", **a)

    papers = [
        {"id": "P1", "title": "Foundations of Analytical Engines", "year": 2015, "citations": 620, "venue": "JACM", "topic": "Algorithms", "authors": ["A1", "A2"]},
        {"id": "P2", "title": "Mathematical Theory of Graph Communication", "year": 2016, "citations": 810, "venue": "IEEE-IT", "topic": "Information Theory", "authors": ["A3", "A2"]},
        {"id": "P3", "title": "Probabilistic Reasoning in Directed Graphical Models", "year": 2016, "citations": 940, "venue": "ICML", "topic": "Causal Inference", "authors": ["A4", "A12"]},
        {"id": "P4", "title": "Deep Hierarchical Representations", "year": 2017, "citations": 1320, "venue": "NeurIPS", "topic": "Deep Learning", "authors": ["A5", "A6"]},
        {"id": "P5", "title": "Convolutional Topologies and Visual Invariance", "year": 2017, "citations": 1100, "venue": "CVPR", "topic": "Computer Vision", "authors": ["A6", "A7"]},
        {"id": "P6", "title": "Distributed Graph Database Query Processing", "year": 2018, "citations": 490, "venue": "VLDB", "topic": "Graph Databases", "authors": ["A9", "A10"]},
        {"id": "P7", "title": "Semantic Web and Linked Property Graphs", "year": 2018, "citations": 530, "venue": "WWW", "topic": "Knowledge Graphs", "authors": ["A8", "A9"]},
        {"id": "P8", "title": "Graph Neural Networks for Relational Reasoning", "year": 2019, "citations": 1450, "venue": "NeurIPS", "topic": "Graph Neural Nets", "authors": ["A11", "A5"]},
        {"id": "P9", "title": "Self-Supervised Pretraining over Academic Graphs", "year": 2020, "citations": 880, "venue": "ICLR", "topic": "Graph Neural Nets", "authors": ["A11", "A7"]},
        {"id": "P10", "title": "Declarative Pattern Matching over Linked Networks", "year": 2020, "citations": 410, "venue": "SIGMOD", "topic": "Graph Databases", "authors": ["A9", "A8"]},
        {"id": "P11", "title": "Causal Representation Learning on Graphs", "year": 2021, "citations": 760, "venue": "ICML", "topic": "Causal Inference", "authors": ["A4", "A11"]},
        {"id": "P12", "title": "Weak Supervision for Automated Graph Curation", "year": 2021, "citations": 520, "venue": "VLDB", "topic": "Knowledge Extraction", "authors": ["A10", "A11"]},
        {"id": "P13", "title": "Attention Architectures for Multi-Hop Graph Traversal", "year": 2022, "citations": 690, "venue": "NeurIPS", "topic": "Deep Learning", "authors": ["A5", "A7"]},
        {"id": "P14", "title": "Foundational Principles of Graph Pattern Optimization", "year": 2023, "citations": 290, "venue": "SIGMOD", "topic": "Graph Databases", "authors": ["A9", "A10"]},
        {"id": "P15", "title": "Geometric Deep Learning and Symmetries", "year": 2023, "citations": 380, "venue": "ICLR", "topic": "Graph Neural Nets", "authors": ["A6", "A11"]},
        {"id": "P16", "title": "Recursive Knowledge Graph Traversal & Equilibrium", "year": 2024, "citations": 220, "venue": "KDD", "topic": "Knowledge Graphs", "authors": ["A8", "A10"]},
    ]

    for p in papers:
        G.add_node(p["id"], label="Paper", **p)
        for aid in p["authors"]:
            G.add_edge(aid, p["id"], type="AUTHORED", weight=1.0)
            for aid2 in p["authors"]:
                if aid != aid2:
                    G.add_edge(aid, aid2, type="COLLABORATED_WITH", weight=1.0)
                    G.add_edge(aid2, aid, type="COLLABORATED_WITH", weight=1.0)

    # Citation relationships: modern/applied papers cite foundational/methodological papers
    citations = [
        ("P2", "P1"),
        ("P3", "P1"), ("P3", "P2"),
        ("P4", "P1"), ("P4", "P2"),
        ("P5", "P4"), ("P5", "P1"),
        ("P6", "P1"),
        ("P7", "P6"), ("P7", "P1"),
        ("P8", "P4"), ("P8", "P3"), ("P8", "P1"),
        ("P9", "P8"), ("P9", "P4"),
        ("P10", "P6"), ("P10", "P7"),
        ("P11", "P3"), ("P11", "P8"),
        ("P12", "P6"), ("P12", "P8"), ("P12", "P7"),
        ("P13", "P8"), ("P13", "P4"), ("P13", "P9"),
        ("P14", "P10"), ("P14", "P6"),
        ("P15", "P8"), ("P15", "P5"),
        ("P16", "P10"), ("P16", "P12"), ("P16", "P13"),
        # Circular citation loop intentionally included for motif/cycle queries: P16 -> P10 -> P7 -> P16
        ("P7", "P16")
    ]

    for src, dst in citations:
        G.add_edge(src, dst, type="CITES", weight=1.0)

    return G


@st.cache_data
def get_graph_positions() -> dict:
    """Precomputes fixed, aesthetic 2D positions for graph visualization stability."""
    G = build_academic_knowledge_graph()
    pos = nx.spring_layout(G, seed=1337, k=0.9, iterations=70)
    return pos


def execute_guided_scenario(G: nx.DiGraph, scenario: str, params: dict):
    """Executes a selected guided Cypher query scenario against the graph."""
    t_start = time.perf_counter()
    matched_nodes = set()
    matched_edges = set()
    results = []
    cypher_code = ""

    if scenario == "1. Multi-Hop Citation Lineage":
        src_id = params.get("source_paper", "P16")
        max_k = params.get("max_k", 3)
        min_year = params.get("min_year", 2015)
        min_cites = params.get("min_citations", 100)

        cypher_code = f"""MATCH path = (p1:Paper {{id: '{src_id}'}})-[:CITES*1..{max_k}]->(p2:Paper)
WHERE p2.year >= {min_year} AND p2.citations >= {min_cites}
RETURN p1.title AS Source, p2.title AS Ancestor, p2.year AS Year,
       p2.citations AS Citations, length(path) AS Hops
ORDER BY Hops ASC, Citations DESC"""

        for target in G.nodes():
            if target.startswith("P") and target != src_id:
                for p in nx.all_simple_paths(G, src_id, target, cutoff=max_k):
                    if all(G[p[i]][p[i+1]].get("type") == "CITES" for i in range(len(p)-1)):
                        p2_data = G.nodes[target]
                        if p2_data.get("year", 0) >= min_year and p2_data.get("citations", 0) >= min_cites:
                            for n in p:
                                matched_nodes.add(n)
                            for i in range(len(p)-1):
                                matched_edges.add((p[i], p[i+1]))
                            results.append({
                                "Source Paper": G.nodes[src_id]["title"][:30] + "...",
                                "Ancestor Paper": p2_data["title"],
                                "Year": p2_data["year"],
                                "Citations": p2_data["citations"],
                                "Hops": len(p) - 1,
                                "Citation Path": " -> ".join([G.nodes[x]["id"] for x in p])
                            })

    elif scenario == "2. Co-authorship Triadic Closures (Hidden Bridges)":
        cypher_code = """MATCH (a1:Author)-[:AUTHORED]->(p1:Paper)<-[:AUTHORED]-(bridge:Author)
      -[:AUTHORED]->(p2:Paper)<-[:AUTHORED]-(a2:Author)
WHERE a1.id < a2.id AND NOT (a1)-[:COLLABORATED_WITH]-(a2)
RETURN a1.name AS Author_1, bridge.name AS Bridge_Colleague,
       a2.name AS Author_2, p1.title AS Joint_Paper_1, p2.title AS Joint_Paper_2"""

        author_nodes = [n for n, d in G.nodes(data=True) if d.get("label") == "Author"]
        for a1 in author_nodes:
            for a2 in author_nodes:
                if a1 < a2 and not G.has_edge(a1, a2):
                    co_a1 = {nbr for nbr in G.neighbors(a1) if G.nodes[nbr].get("label") == "Author"}
                    co_a2 = {nbr for nbr in G.neighbors(a2) if G.nodes[nbr].get("label") == "Author"}
                    bridges = co_a1.intersection(co_a2)
                    for b in bridges:
                        # find papers connecting a1-b and b-a2
                        papers_a1 = {n for n in G.neighbors(a1) if n.startswith("P") and G.has_edge(b, n)}
                        papers_a2 = {n for n in G.neighbors(a2) if n.startswith("P") and G.has_edge(b, n)}
                        p1_id = list(papers_a1)[0] if papers_a1 else "N/A"
                        p2_id = list(papers_a2)[0] if papers_a2 else "N/A"

                        matched_nodes.update([a1, b, a2])
                        if p1_id != "N/A":
                            matched_nodes.add(p1_id)
                            matched_edges.update([(a1, p1_id), (b, p1_id)])
                        if p2_id != "N/A":
                            matched_nodes.add(p2_id)
                            matched_edges.update([(b, p2_id), (a2, p2_id)])

                        results.append({
                            "Author 1": G.nodes[a1]["name"],
                            "Bridge Colleague": G.nodes[b]["name"],
                            "Author 2 (Candidate)": G.nodes[a2]["name"],
                            "Joint Paper 1": G.nodes[p1_id]["title"] if p1_id != "N/A" else "N/A",
                            "Joint Paper 2": G.nodes[p2_id]["title"] if p2_id != "N/A" else "N/A"
                        })

    elif scenario == "3. High-Impact Aggregation (WITH & COLLECT)":
        min_paper_cites = params.get("min_paper_cites", 400)
        min_papers = params.get("min_papers", 2)

        cypher_code = f"""MATCH (a:Author)-[:AUTHORED]->(p:Paper)
WHERE p.citations >= {min_paper_cites}
WITH a, count(p) AS qualifying_papers, sum(p.citations) AS total_citations,
     collect(p.title) AS landmark_papers
WHERE qualifying_papers >= {min_papers}
RETURN a.name AS Author, a.institution AS Institution, a.h_index AS H_Index,
       qualifying_papers, total_citations, landmark_papers
ORDER BY total_citations DESC"""

        for aid, data in G.nodes(data=True):
            if data.get("label") == "Author":
                authored_papers = [
                    (v, G.nodes[v]) for u, v, d in G.out_edges(aid, data=True)
                    if d.get("type") == "AUTHORED" and G.nodes[v].get("citations", 0) >= min_paper_cites
                ]
                if len(authored_papers) >= min_papers:
                    matched_nodes.add(aid)
                    paper_titles = []
                    total_c = 0
                    for pid, pdata in authored_papers:
                        matched_nodes.add(pid)
                        matched_edges.add((aid, pid))
                        paper_titles.append(pdata["title"])
                        total_c += pdata["citations"]

                    results.append({
                        "Author": data["name"],
                        "Institution": data["institution"],
                        "H-Index": data["h_index"],
                        "Qualifying Papers": len(authored_papers),
                        "Total Citations": total_c,
                        "Landmark Papers": "; ".join(paper_titles)
                    })

    elif scenario == "4. Shortest Interdisciplinary Path & Research Bridge":
        author_a = params.get("author_a", "A1")
        author_b = params.get("author_b", "A11")

        cypher_code = f"""MATCH p = shortestPath((start:Author {{id: '{author_a}'}})-[*]-(target:Author {{id: '{author_b}'}}))
RETURN p, length(p) AS path_length"""

        try:
            # Undirected graph traversal for shortest collaboration/citation bridge
            undir_G = G.to_undirected()
            p = nx.shortest_path(undir_G, source=author_a, target=author_b)
            for n in p:
                matched_nodes.add(n)
            for i in range(len(p)-1):
                u, v = p[i], p[i+1]
                if G.has_edge(u, v): matched_edges.add((u, v))
                elif G.has_edge(v, u): matched_edges.add((v, u))

            path_labels = [f"{G.nodes[n].get('name') or G.nodes[n].get('title')} ({G.nodes[n].get('label')})" for n in p]
            results.append({
                "Start Author": G.nodes[author_a]["name"],
                "Target Author": G.nodes[author_b]["name"],
                "Bridge Hops": len(p) - 1,
                "Interdisciplinary Path": "  ==>  ".join(path_labels)
            })
        except nx.NetworkXNoPath:
            pass

    elif scenario == "5. Cyclic Citation Ring Detection":
        max_hops = params.get("max_loop_hops", 4)
        cypher_code = f"""MATCH path = (p:Paper)-[:CITES*2..{max_hops}]->(p)
RETURN p.title AS Anchor_Paper, length(path) AS Loop_Length, path"""

        cite_subgraph = nx.DiGraph([(u, v) for u, v, d in G.edges(data=True) if d.get("type") == "CITES"])
        all_cycles = list(nx.simple_cycles(cite_subgraph))
        for c in all_cycles:
            if 2 <= len(c) <= max_hops:
                for n in c:
                    matched_nodes.add(n)
                for i in range(len(c)):
                    u = c[i]
                    v = c[(i+1) % len(c)]
                    matched_edges.add((u, v))
                cycle_names = [G.nodes[x]["title"][:28] + "..." for x in c]
                results.append({
                    "Anchor Paper": G.nodes[c[0]]["title"],
                    "Loop Length (Hops)": len(c),
                    "Circular Reference Chain": " -> ".join(cycle_names) + f" -> {cycle_names[0]}"
                })

    exec_latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
    df_res = pd.DataFrame(results)

    total_graph_nodes = G.number_of_nodes()
    selectivity_pct = round((len(matched_nodes) / max(1, total_graph_nodes)) * 100, 1)

    metrics = {
        "paths_matched": len(results),
        "nodes_visited": len(matched_nodes),
        "edges_traversed": len(matched_edges),
        "latency_ms": exec_latency_ms,
        "selectivity_pct": selectivity_pct
    }

    return df_res, matched_nodes, matched_edges, metrics, cypher_code


def execute_custom_cypher_pattern(G: nx.DiGraph, query_text: str):
    """
    Parses and executes user-written Cypher queries supporting node lookups,
    property filters, 1-hop and multi-hop relationship traversals.
    """
    t_start = time.perf_counter()
    q = query_text.strip()
    matched_nodes = set()
    matched_edges = set()
    results = []

    # Case 1: Node matching with WHERE, RETURN, ORDER BY, LIMIT
    m_node = re.search(
        r'MATCH\s+\((\w+):(\w+)\)'
        r'(?:\s+WHERE\s+(.+?))?'
        r'(?:\s+RETURN\s+(.+?))?'
        r'(?:\s+ORDER\s+BY\s+(.+?))?'
        r'(?:\s+LIMIT\s+(\d+))?$',
        q,
        re.IGNORECASE | re.DOTALL
    )
    if m_node and '-[' not in q:
        var, label, where_clause, return_clause, order_clause, limit_s = m_node.groups()
        for node_id, data in G.nodes(data=True):
            if data.get("label", "").lower() == label.lower():
                keep = True
                if where_clause:
                    cond = where_clause.replace(f"{var}.", "").strip()
                    cond_m = re.search(r'(\w+)\s*(=|>=|<=|>|<|!=|<>)\s*(.+)', cond)
                    if cond_m:
                        prop, op, val_str = cond_m.groups()
                        val_str = val_str.strip().strip("'\"")
                        prop_val = data.get(prop)
                        if prop_val is not None:
                            try:
                                if isinstance(prop_val, (int, float)):
                                    target_num = float(val_str)
                                    if op == '>=': keep = (prop_val >= target_num)
                                    elif op == '<=': keep = (prop_val <= target_num)
                                    elif op == '>': keep = (prop_val > target_num)
                                    elif op == '<': keep = (prop_val < target_num)
                                    elif op in ('=', '=='): keep = (prop_val == target_num)
                                    elif op in ('!=', '<>'): keep = (prop_val != target_num)
                                else:
                                    if op in ('=', '=='): keep = (str(prop_val).lower() == val_str.lower())
                                    elif op in ('!=', '<>'): keep = (str(prop_val).lower() != val_str.lower())
                            except Exception:
                                pass
                if keep:
                    matched_nodes.add(node_id)
                    row = {"ID": node_id, "Label": data.get("label")}
                    for k in ["name", "title", "field", "topic", "institution", "venue", "year", "h_index", "citations"]:
                        if k in data:
                            row[k.replace("_", " ").title()] = data[k]
                    results.append(row)

        df_res = pd.DataFrame(results)
        if not df_res.empty and order_clause:
            for ot in order_clause.split(','):
                parts = ot.strip().split()
                if parts:
                    col = parts[0]
                    asc = True if len(parts) < 2 or parts[1].upper() == 'ASC' else False
                    match_cols = [c for c in df_res.columns if c.lower() == col.lower()]
                    if match_cols:
                        df_res = df_res.sort_values(by=match_cols[0], ascending=asc)
        if limit_s and not df_res.empty:
            df_res = df_res.head(int(limit_s))

    # Case 2: 1-hop or multi-hop path matching
    else:
        rel_m = re.search(
            r'MATCH\s+(?:(?P<path_var>\w+)\s*=\s*)?'
            r'\((?P<src_var>\w+)(?::(?P<src_lbl>\w+))?(?:\s*\{.*?id:\s*[\'"]?(?P<src_id>\w+)[\'"]?\})?\)'
            r'-\[:(?P<rel_type>\w+)(?:\*(?P<min_h>\d+)?(?:\.\.(?P<max_h>\d+))?)?\]-(?P<is_dir>>)?'
            r'\((?P<dst_var>\w+)(?::(?P<dst_lbl>\w+))?(?:\s*\{.*?id:\s*[\'"]?(?P<dst_id>\w+)[\'"]?\})?\)'
            r'(?:\s+WHERE\s+(?P<where_clause>.+?))?'
            r'(?:\s+RETURN\s+(?P<return_clause>.+?))?'
            r'(?:\s+ORDER\s+BY\s+(?P<order_clause>.+?))?'
            r'(?:\s+LIMIT\s+(?P<limit>\d+))?$',
            q,
            re.IGNORECASE | re.DOTALL
        )
        if rel_m:
            gd = rel_m.groupdict()
            min_hops = int(gd["min_h"]) if gd["min_h"] else 1
            max_hops = int(gd["max_h"]) if gd["max_h"] else (min_hops if gd["min_h"] else 1)
            directed = bool(gd["is_dir"])
            src_var = gd["src_var"]
            src_lbl = gd["src_lbl"]
            src_id = gd["src_id"]
            dst_var = gd["dst_var"]
            dst_lbl = gd["dst_lbl"]
            dst_id = gd["dst_id"]
            rel_type = gd["rel_type"]
            where_clause = gd["where_clause"]
            return_clause = gd["return_clause"]
            order_clause = gd["order_clause"]
            limit_s = gd["limit"]

            # Parse list predicates like: ALL(p IN nodes(path)[1..3] WHERE p.citations >= 400)
            all_predicates = []
            clean_where = where_clause or ""
            if where_clause:
                all_matches = re.finditer(
                    r'ALL\s*\(\s*(?P<item>\w+)\s+IN\s+nodes\s*\(\s*(?P<path>\w+)\s*\)(?:\[(?P<start>\d+)?\.\.(?P<end>\d+)?\])?\s+WHERE\s+(?P<cond>.+?)\s*\)',
                    where_clause, re.IGNORECASE
                )
                for am in all_matches:
                    s_idx = int(am.group('start')) if am.group('start') else 0
                    e_idx = int(am.group('end')) if am.group('end') else None
                    cond_str = am.group('cond').strip()
                    all_predicates.append((s_idx, e_idx, cond_str))
                    clean_where = clean_where.replace(am.group(0), ' ')

            search_nodes = [src_id] if src_id else [
                n for n, d in G.nodes(data=True) if not src_lbl or d.get("label", "").lower() == src_lbl.lower()
            ]

            for u in search_nodes:
                queue = [(u, [u])]
                while queue:
                    curr, curr_path = queue.pop(0)
                    hops = len(curr_path) - 1
                    if hops >= min_hops:
                        v = curr
                        v_data = G.nodes[v]
                        label_ok = (not dst_lbl) or (v_data.get("label", "").lower() == dst_lbl.lower())
                        id_ok = (not dst_id) or (v == dst_id)
                        not_trivial_loop = (v != u or len(curr_path) > 2)

                        if label_ok and id_ok and not_trivial_loop:
                            keep = True

                            # Evaluate ALL(...) predicates across path nodes
                            for s_idx, e_idx, cond_str in all_predicates:
                                sub_nodes = curr_path[s_idx:e_idx] if e_idx is not None else curr_path[s_idx:]
                                for n in sub_nodes:
                                    n_data = G.nodes[n]
                                    for prop in ["year", "citations", "h_index"]:
                                        if prop in cond_str:
                                            c_m = re.search(rf'{prop}\s*(=|>=|<=|>|<|!=|<>)\s*([0-9.]+)', cond_str)
                                            if c_m:
                                                op, val_s = c_m.groups()
                                                val = n_data.get(prop, 0)
                                                target_num = float(val_s)
                                                if op == '>=' and not (val >= target_num): keep = False
                                                elif op == '<=' and not (val <= target_num): keep = False
                                                elif op == '>' and not (val > target_num): keep = False
                                                elif op == '<' and not (val < target_num): keep = False
                                                elif op in ('=', '==') and not (val == target_num): keep = False

                            # Evaluate remaining simple WHERE checks on terminal node v
                            if keep and clean_where.strip():
                                for prop in ["year", "citations", "h_index", "venue", "field", "topic"]:
                                    if prop in clean_where:
                                        c_m = re.search(rf'{prop}\s*(=|>=|<=|>|<|!=|<>)\s*([^\s,)]+)', clean_where)
                                        if c_m:
                                            op, val_s = c_m.groups()
                                            val_s = val_s.strip().strip("'\"")
                                            val = v_data.get(prop)
                                            if val is not None:
                                                try:
                                                    if isinstance(val, (int, float)):
                                                        target_num = float(val_s)
                                                        if op == '>=' and not (val >= target_num): keep = False
                                                        elif op == '<=' and not (val <= target_num): keep = False
                                                        elif op == '>' and not (val > target_num): keep = False
                                                        elif op == '<' and not (val < target_num): keep = False
                                                        elif op in ('=', '==') and not (val == target_num): keep = False
                                                    else:
                                                        if op in ('=', '==') and not (str(val).lower() == val_s.lower()): keep = False
                                                except Exception:
                                                    pass

                            if keep:
                                for n in curr_path:
                                    matched_nodes.add(n)
                                for i in range(len(curr_path)-1):
                                    matched_edges.add((curr_path[i], curr_path[i+1]))

                                u_data = G.nodes[u]
                                if return_clause:
                                    row = {}
                                    items = [it.strip() for it in return_clause.split(',') if it.strip()]
                                    for it in items:
                                        m_as = re.match(r'(.+?)\s+AS\s+(\w+)', it, re.IGNORECASE)
                                        expr, alias = (m_as.group(1).strip(), m_as.group(2).strip()) if m_as else (it, it)
                                        expr_l = expr.lower()
                                        if 'length(' in expr_l:
                                            row[alias] = hops
                                        elif src_var and expr_l.startswith(f"{src_var.lower()}."):
                                            p_name = expr.split('.', 1)[-1]
                                            row[alias] = u_data.get(p_name, 'N/A')
                                        elif dst_var and expr_l.startswith(f"{dst_var.lower()}."):
                                            p_name = expr.split('.', 1)[-1]
                                            row[alias] = v_data.get(p_name, 'N/A')
                                        elif '.' in expr:
                                            p_name = expr.split('.', 1)[-1]
                                            row[alias] = v_data.get(p_name, u_data.get(p_name, 'N/A'))
                                        else:
                                            row[alias] = v_data.get('title') or v_data.get('name') or v
                                    results.append(row)
                                else:
                                    path_names = [G.nodes[n].get("title") or G.nodes[n].get("name") or n for n in curr_path]
                                    results.append({
                                        "Origin Node": u_data.get("title") or u_data.get("name"),
                                        "Terminal Node": v_data.get("title") or v_data.get("name"),
                                        "Traversal Hops": hops,
                                        "Pattern Path": " -> ".join(path_names)
                                    })

                    if hops < max_hops:
                        nbrs = list(G.successors(curr)) if directed else list(G.neighbors(curr))
                        for nbr in nbrs:
                            edge_d = G[curr][nbr] if G.has_edge(curr, nbr) else G[nbr][curr]
                            if not rel_type or edge_d.get("type", "").lower() == rel_type.lower():
                                if nbr not in curr_path:
                                    queue.append((nbr, curr_path + [nbr]))

        df_res = pd.DataFrame(results)
        if not df_res.empty and order_clause:
            for ot in order_clause.split(','):
                parts = ot.strip().split()
                if parts:
                    col = parts[0]
                    asc = True if len(parts) < 2 or parts[1].upper() == 'ASC' else False
                    match_cols = [c for c in df_res.columns if c.lower() == col.lower()]
                    if match_cols:
                        df_res = df_res.sort_values(by=match_cols[0], ascending=asc)
        if limit_s and not df_res.empty:
            df_res = df_res.head(int(limit_s))

    exec_latency_ms = round((time.perf_counter() - t_start) * 1000, 2)
    total_graph_nodes = G.number_of_nodes()
    selectivity_pct = round((len(matched_nodes) / max(1, total_graph_nodes)) * 100, 1)

    metrics = {
        "paths_matched": len(results),
        "nodes_visited": len(matched_nodes),
        "edges_traversed": len(matched_edges),
        "latency_ms": exec_latency_ms,
        "selectivity_pct": selectivity_pct
    }

    return df_res, matched_nodes, matched_edges, metrics


def build_network_plotly_figure(G: nx.DiGraph, pos: dict, matched_nodes: set, matched_edges: set, title: str) -> go.Figure:
    """Generates an interactive 2D network diagram with distinct node/edge highlight styling."""
    fig = go.Figure()

    # 1. Background (unmatched) edges
    bg_x, bg_y = [], []
    for u, v in G.edges():
        if (u, v) not in matched_edges and (v, u) not in matched_edges:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            bg_x.extend([x0, x1, None])
            bg_y.extend([y0, y1, None])

    fig.add_trace(go.Scatter(
        x=bg_x, y=bg_y,
        mode='lines',
        line=dict(width=1.0, color='#94a3b8'),
        hoverinfo='none',
        name='Other Relationships'
    ))

    # 2. Highlighted (matched) edges
    h_x, h_y = [], []
    for u, v in matched_edges:
        if u in pos and v in pos:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            h_x.extend([x0, x1, None])
            h_y.extend([y0, y1, None])

    if h_x:
        fig.add_trace(go.Scatter(
            x=h_x, y=h_y,
            mode='lines',
            line=dict(width=3.2, color='#ef4444'),
            hoverinfo='none',
            name='Matched Cypher Path'
        ))

    # 3. Highlighted Nodes Halo (rendered behind nodes so node IDs remain crisp)
    hl_x, hl_y, hl_hover = [], [], []
    for node in matched_nodes:
        if node in pos:
            x, y = pos[node]
            d = G.nodes[node]
            hl_x.append(x)
            hl_y.append(y)
            label = d.get("name") or d.get("title")
            hl_hover.append(f"<b>[MATCHED {node}]</b> {label} ({d.get('label')})")

    if hl_x:
        fig.add_trace(go.Scatter(
            x=hl_x, y=hl_y,
            mode='markers',
            marker=dict(size=34, color='rgba(245, 158, 11, 0.45)', line=dict(width=2.5, color='#d97706')),
            hoverinfo='text',
            hovertext=hl_hover,
            name='Matched Subgraph Nodes'
        ))

    # 4. Author nodes (circles with author ID inside e.g. A1, surname on top)
    auth_x, auth_y, auth_hover, auth_id, auth_name = [], [], [], [], []
    for node, d in G.nodes(data=True):
        if d.get("label") == "Author":
            x, y = pos[node]
            auth_x.append(x)
            auth_y.append(y)
            auth_id.append(d.get("id", ""))
            auth_name.append(d.get("name", "").split()[-1])
            auth_hover.append(
                f"<b>Author [{d.get('id')}]:</b> {d.get('name')}<br>"
                f"<b>Field:</b> {d.get('field')}<br>"
                f"<b>Institution:</b> {d.get('institution')}<br>"
                f"<b>h-index:</b> {d.get('h_index')}"
            )

    fig.add_trace(go.Scatter(
        x=auth_x, y=auth_y,
        mode='markers+text',
        marker=dict(size=22, color='#2563eb', line=dict(width=1.5, color='#1e3a8a')),
        text=auth_id,
        textposition="middle center",
        textfont=dict(color='white', size=9, family='Arial, sans-serif'),
        hoverinfo='text',
        hovertext=auth_hover,
        name='Authors',
        legendgroup='Authors'
    ))

    fig.add_trace(go.Scatter(
        x=auth_x, y=[y + 0.045 for y in auth_y],
        mode='text',
        text=auth_name,
        textposition="top center",
        textfont=dict(color='#1e293b', size=11),
        hoverinfo='none',
        showlegend=False,
        legendgroup='Authors'
    ))

    # 5. Paper nodes (square with number written inside, e.g., 16 for P16)
    paper_x, paper_y, paper_hover, paper_num = [], [], [], []
    for node, d in G.nodes(data=True):
        if d.get("label") == "Paper":
            x, y = pos[node]
            paper_x.append(x)
            paper_y.append(y)
            paper_num.append(d.get("id", "").replace("P", ""))
            paper_hover.append(
                f"<b>Paper [{d.get('id')}]:</b> {d.get('title')}<br>"
                f"<b>Year:</b> {d.get('year')} | <b>Venue:</b> {d.get('venue')}<br>"
                f"<b>Topic:</b> {d.get('topic')}<br>"
                f"<b>Citations:</b> {d.get('citations')}"
            )

    fig.add_trace(go.Scatter(
        x=paper_x, y=paper_y,
        mode='markers+text',
        marker=dict(symbol='square', size=22, color='#0d9488', line=dict(width=1.5, color='#115e59')),
        text=paper_num,
        textposition="middle center",
        textfont=dict(color='white', size=10, family='Arial, sans-serif'),
        hoverinfo='text',
        hovertext=paper_hover,
        name='Papers'
    ))

    fig.update_layout(
        title=title,
        showlegend=True,
        hovermode='closest',
        height=480,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )

    return fig


def build_complexity_curve(max_depth: int = 4) -> go.Figure:
    """Generates a dynamic curve contrasting theoretical O(b^k) expansion against pruned Cypher execution."""
    depths = list(range(1, max_depth + 1))
    b_avg = 2.4
    theoretical_paths = [round(b_avg ** k, 1) for k in depths]
    pruned_paths = [round((b_avg ** k) * (0.6 ** (k - 1)), 1) for k in depths]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=depths, y=theoretical_paths,
        mode='lines+markers',
        name='Unconstrained Traversal O(b^k)',
        line=dict(color='#ef4444', width=2.5, dash='dash')
    ))
    fig.add_trace(go.Scatter(
        x=depths, y=pruned_paths,
        mode='lines+markers',
        name='Selectively Pruned Cypher Path',
        line=dict(color='#10b981', width=3.0)
    ))

    fig.update_layout(
        title="Path Expansion & Selectivity vs. Traversal Depth (k)",
        xaxis_title="Traversal Depth / Hops (k)",
        yaxis_title="Estimated Paths Explored",
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode='x unified'
    )
    return fig


# ======================================================================================
# 3. LAB REPORT PDF EXPORTER
# ======================================================================================

class LabReportPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Virtual Laboratory Report", align="C")


def generate_pdf_report(student_name: str, student_id: str, date_str: str,
                        trials_df: pd.DataFrame, quiz_score: int, quiz_total: int,
                        student_notes: str) -> bytes:
    """Compiles experiment records and metrics into a formatted PDF report."""
    pdf = LabReportPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Document Title
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 10, EXPERIMENT_CONFIG["title"], align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 5, EXPERIMENT_CONFIG["subtitle"], align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    # Student & Session Info Box
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(10, 26, 190, 22, "FD")

    pdf.set_xy(14, 28)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(38, 5, "Student Name:", 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(57, 5, student_name or "N/A", 0)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(35, 5, "Student ID / Roll:", 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(50, 5, student_id or "N/A", 1)

    pdf.set_xy(14, 36)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(38, 5, "Experiment Date:", 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(57, 5, date_str or datetime.now().strftime("%Y-%m-%d"), 0)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(35, 5, "Quiz Evaluation:", 0)
    pdf.set_font("Helvetica", "B", 9)
    if quiz_score >= max(1, quiz_total // 2):
        pdf.set_text_color(16, 185, 129)
    else:
        pdf.set_text_color(239, 68, 68)
    pdf.cell(50, 5, f"{quiz_score} / {quiz_total} ({int((quiz_score/quiz_total)*100 if quiz_total else 0)}%)", 1)

    pdf.ln(12)

    # 1. Learning Objectives
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 7, "1. Learning Objectives", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(51, 65, 85)
    for obj in EXPERIMENT_CONFIG["objectives"]:
        clean_obj = str(obj).replace("$", "").replace("\\", "")
        pdf.cell(5, 5, "-", 0)
        pdf.cell(0, 5, f" {clean_obj}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # 2. Recorded Trials Table
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 7, "2. Recorded Experimental Trials & Performance Benchmarks", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    if trials_df.empty:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, "No simulation trials recorded during this session.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    else:
        pdf.set_fill_color(37, 99, 235)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 8)

        cols = list(trials_df.columns)
        num_cols = len(cols)
        col_w = max(18, int(190 / max(1, num_cols)))

        for c in cols:
            pdf.cell(col_w, 6, str(c)[:15], border=1, align="C", fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.ln()

        pdf.set_fill_color(248, 250, 252)
        pdf.set_text_color(30, 41, 59)
        pdf.set_font("Helvetica", "", 8)
        fill = False

        for _, row in trials_df.iterrows():
            for c in cols:
                val = row[c]
                val_str = f"{val:.2f}" if isinstance(val, float) else str(val)
                pdf.cell(col_w, 5, val_str[:15], border=1, align="C", fill=fill, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.ln()
            fill = not fill
    pdf.ln(5)

    # 3. Observations & Analysis
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 7, "3. Observations & Pattern Analysis", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    notes_text = student_notes.strip() if student_notes.strip() else (
        "Multi-hop Cypher traversals effectively traced research lineage across up to 4 citation hops. "
        "Triadic co-authorship pattern matching successfully uncovered hidden bridge connections, while WITH "
        "and COLLECT clauses enabled efficient pipelined aggregation of scholar citation metrics."
    )
    pdf.multi_cell(0, 5, notes_text)
    pdf.ln(8)

    # Sign-off line
    pdf.set_draw_color(180, 180, 180)
    pdf.line(130, pdf.get_y() + 15, 190, pdf.get_y() + 15)
    pdf.set_xy(130, pdf.get_y() + 17)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(60, 4, "Instructor / Student Signature", align="C")

    return bytes(pdf.output())


# ======================================================================================
# 4. SECTION RENDERERS: THEORY, SIMULATION, QUIZ, REPORT
# ======================================================================================

def render_theory_section():
    """Renders Section 1: Theory, Background, Objectives, and Procedure."""
    st.header(EXPERIMENT_CONFIG["title"])
    st.caption(f"Domain Focus: {EXPERIMENT_CONFIG['subtitle']}")

    st.markdown(THEORY_CONTENT["background"])

    st.divider()
    st.subheader("Experimental Learning Objectives")
    for i, obj in enumerate(EXPERIMENT_CONFIG["objectives"]):
        st.write(f"- **Objective {i+1}**: {obj}")

    st.divider()
    st.subheader("Laboratory Procedure")
    for step in THEORY_CONTENT["procedure"]:
        st.write(f"- {step}")

    st.divider()
    with st.expander("Key Terminology & Variable Reference", expanded=True):
        terms_df = pd.DataFrame(
            list(THEORY_CONTENT["key_terms"].items()),
            columns=["Term / Concept", "Definition & Operational Role"]
        )
        st.table(terms_df)


def render_simulation_section():
    """Renders Section 2: Interactive Execution Sandbox, Plotly Visualizations, and Trial Logger."""
    st.header("Graph Execution Sandbox & Pattern Matcher")
    st.caption("Interact with the in-memory Academic Citation Network using Cypher query patterns.")

    G = build_academic_knowledge_graph()
    pos = get_graph_positions()

    sim_mode = st.radio(
        "Select Cypher Interaction Mode:",
        options=["Guided Cypher Presets", "Custom Cypher Query Editor"],
        horizontal=True
    )

    df_res = pd.DataFrame()
    matched_nodes = set()
    matched_edges = set()
    metrics = {"paths_matched": 0, "nodes_visited": 0, "latency_ms": 0.0, "selectivity_pct": 0.0}
    active_cypher = ""
    pattern_name = ""

    if sim_mode == "Guided Cypher Presets":
        scenario = st.selectbox(
            "Choose a Graph Pattern Query Scenario:",
            options=[
                "1. Multi-Hop Citation Lineage",
                "2. Co-authorship Triadic Closures (Hidden Bridges)",
                "3. High-Impact Aggregation (WITH & COLLECT)",
                "4. Shortest Interdisciplinary Path & Research Bridge",
                "5. Cyclic Citation Ring Detection"
            ]
        )
        pattern_name = scenario.split(". ", 1)[-1]
        params = {}

        if scenario == "1. Multi-Hop Citation Lineage":
            st.info("Traces scientific lineage from a recent paper across k citation hops (-[:CITES*1..k]->).")
            c1, c2, c3 = st.columns(3)
            with c1:
                paper_options = [n for n, d in G.nodes(data=True) if d.get("label") == "Paper"]
                source_paper = st.selectbox("Start Paper (Root):", options=paper_options, index=paper_options.index("P16") if "P16" in paper_options else 0)
                params["source_paper"] = source_paper
            with c2:
                params["max_k"] = st.slider("Max Traversal Depth (k hops):", min_value=1, max_value=4, value=3, step=1)
            with c3:
                params["min_citations"] = st.slider("Min Ancestor Citations:", min_value=100, max_value=1500, value=300, step=100)
            params["min_year"] = 2015

        elif scenario == "2. Co-authorship Triadic Closures (Hidden Bridges)":
            st.info("Finds pairs of authors who share a common co-author bridge but haven't directly published together yet.")

        elif scenario == "3. High-Impact Aggregation (WITH & COLLECT)":
            st.info("Aggregates paper counts and citation volume per scholar, bundling landmark titles into lists via COLLECT().")
            c1, c2 = st.columns(2)
            with c1:
                params["min_paper_cites"] = st.slider("Min Citations per Paper:", min_value=200, max_value=1200, value=450, step=50)
            with c2:
                params["min_papers"] = st.slider("Min Landmark Papers per Scholar:", min_value=1, max_value=3, value=2, step=1)

        elif scenario == "4. Shortest Interdisciplinary Path & Research Bridge":
            st.info("Computes the shortest collaboration or citation path connecting two researchers from different domains.")
            authors_list = [n for n, d in G.nodes(data=True) if d.get("label") == "Author"]
            c1, c2 = st.columns(2)
            with c1:
                params["author_a"] = st.selectbox("Origin Author:", options=authors_list, index=0)
            with c2:
                params["author_b"] = st.selectbox("Target Author:", options=authors_list, index=10)

        elif scenario == "5. Cyclic Citation Ring Detection":
            st.info("Detects circular reference loops where papers cite each other in closed loops ((p)-[:CITES*2..k]->(p)).")
            params["max_loop_hops"] = st.slider("Max Cycle Search Depth (Hops):", min_value=2, max_value=4, value=3, step=1)

        df_res, matched_nodes, matched_edges, metrics, active_cypher = execute_guided_scenario(G, scenario, params)

    else:  # Custom Cypher Query Editor
        st.info("Compose or customize Cypher pattern queries to match nodes, multi-hop edges, or collaborations.")
        pattern_name = "Custom Cypher Pattern"

        preset_samples = [
            "MATCH (a:Author) WHERE a.h_index >= 45 RETURN a.name, a.institution, a.h_index",
            "MATCH (p:Paper) WHERE p.year >= 2021 RETURN p.title, p.venue, p.citations",
            "MATCH (a:Author)-[:AUTHORED]->(p:Paper) WHERE p.year >= 2020",
            "MATCH path = (p1:Paper {id: 'P16'})-[:CITES*1..3]->(p2:Paper)",
            "MATCH (a1:Author)-[:COLLABORATED_WITH*1..2]-(a2:Author)"
        ]

        sample_choice = st.selectbox("Quick-Load Sample Cypher Query:", options=preset_samples)
        custom_input = st.text_area("Cypher Query Editor:", value=sample_choice, height=90)
        active_cypher = custom_input

        df_res, matched_nodes, matched_edges, metrics = execute_custom_cypher_pattern(G, custom_input)

    st.divider()

    # Cypher Query Display
    st.subheader("Generated Cypher Query")
    st.code(active_cypher, language="cypher")

    # Real-Time Execution Metrics
    st.subheader("Query Execution & Complexity Profile")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Paths / Matches", f"{metrics['paths_matched']}")
    with m2:
        st.metric("Nodes Visited", f"{metrics['nodes_visited']} / {G.number_of_nodes()}")
    with m3:
        st.metric("Selectivity", f"{metrics['selectivity_pct']}%")
    with m4:
        st.metric("Execution Latency", f"{metrics['latency_ms']} ms")

    # 2D Graph Subgraph Visualization
    st.divider()
    st.subheader("Interactive 2D Subgraph & Path Visualization")
    graph_title = f"Matched Subgraph: {pattern_name} ({metrics['paths_matched']} matches)"
    fig_net = build_network_plotly_figure(G, pos, matched_nodes, matched_edges, graph_title)
    st.plotly_chart(fig_net, use_container_width=True)

    # Tabular Results
    st.divider()
    st.subheader("Query Result Records")
    if not df_res.empty:
        st.dataframe(df_res, use_container_width=True, hide_index=True)
    else:
        st.warning("No records matched the specified pattern and filter criteria.")

    # Complexity Curve
    st.divider()
    st.subheader("Theoretical vs. Pruned Path Complexity")
    fig_curve = build_complexity_curve(max_depth=4)
    st.plotly_chart(fig_curve, use_container_width=True)

    # Session Data Log Book
    st.divider()
    st.subheader("Experimental Data Log Book")
    col_log1, col_log2 = st.columns([1.5, 3.5])

    with col_log1:
        st.caption("Record benchmark metrics from this execution into your official lab session table:")
        if st.button("Record Current Trial", type="primary", use_container_width=True):
            trial_record = {
                "Trial #": len(st.session_state["trials"]) + 1,
                "Query Pattern": pattern_name[:24],
                "Matches": metrics["paths_matched"],
                "Nodes": metrics["nodes_visited"],
                "Selectivity": f"{metrics['selectivity_pct']}%",
                "Time (ms)": metrics["latency_ms"],
                "Timestamp": datetime.now().strftime("%H:%M:%S")
            }
            st.session_state["trials"].append(trial_record)
            st.toast(f"Trial #{trial_record['Trial #']} successfully logged!")

        if st.button("Clear Logged Trials", use_container_width=True):
            st.session_state["trials"] = []
            st.toast("Trial log book reset.")

    with col_log2:
        if st.session_state["trials"]:
            df_trials = pd.DataFrame(st.session_state["trials"])
            st.dataframe(df_trials, use_container_width=True, hide_index=True)
            csv_data = df_trials.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Trials as CSV",
                data=csv_data,
                file_name="cypher_experiment_trials.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No trials recorded yet. Execute queries and click 'Record Current Trial' to build your dataset.")


def render_quiz_section():
    """Renders Section 3: Conceptual Assessment Quiz with Self-Grading and Feedback."""
    st.header("Concept Assessment Quiz")
    st.caption("10 conceptual questions evaluating mastery of Cypher query semantics and graph pattern matching.")

    with st.form("lab_quiz_form"):
        user_responses = {}
        for q in QUIZ_QUESTIONS:
            st.subheader(f"Question {q['id']}")
            st.write(q["question"])
            selected = st.radio(
                label=f"Options for Question {q['id']}:",
                options=q["options"],
                index=st.session_state["quiz_answers"].get(q["id"], 0),
                key=f"quiz_radio_{q['id']}",
                label_visibility="collapsed"
            )
            user_responses[q["id"]] = q["options"].index(selected)
            st.write("")

        submitted = st.form_submit_button("Submit Quiz for Grading", type="primary")

    if submitted:
        score = 0
        st.session_state["quiz_answers"] = user_responses
        st.session_state["quiz_submitted"] = True

        st.divider()
        st.subheader("Quiz Evaluation Results and Explanations")
        for q in QUIZ_QUESTIONS:
            user_ans = user_responses.get(q["id"])
            correct_ans = q["answer_index"]
            if user_ans == correct_ans:
                score += 1
                st.success(f"**Question {q['id']}: Correct!**\n\n_{q['explanation']}_")
            else:
                st.error(f"**Question {q['id']}: Incorrect.** (Your answer: {q['options'][user_ans]})\n\n"
                         f"**Correct Answer:** {q['options'][correct_ans]}\n\n"
                         f"**Reasoning:** _{q['explanation']}_")

        st.session_state["quiz_score"] = score
        perc = (score / len(QUIZ_QUESTIONS)) * 100
        st.info(f"Final Assessment Score: **{score} / {len(QUIZ_QUESTIONS)}** ({perc:.0f}%)")

    elif st.session_state.get("quiz_submitted", False):
        score = st.session_state.get("quiz_score", 0)
        perc = (score / len(QUIZ_QUESTIONS)) * 100
        st.success(f"Quiz already completed. Score: **{score} / {len(QUIZ_QUESTIONS)}** ({perc:.0f}%)")


def render_report_section():
    """Renders Section 4: Dynamic Lab Report Generator with PDF Export."""
    st.header("Report Generation")
    st.caption("Compile your student details, benchmarked query trials, and quiz evaluation into an official PDF report.")

    col1, col2, col3 = st.columns(3)
    with col1:
        student_name = st.text_input("Student Name", value=st.session_state["student_info"].get("name", "Student Name"))
    with col2:
        student_id = st.text_input("Student Roll / ID", value=st.session_state["student_info"].get("id", "EXP-001"))
    with col3:
        lab_date = st.date_input("Experiment Date", value=datetime.now())

    st.session_state["student_info"]["name"] = student_name
    st.session_state["student_info"]["id"] = student_id
    st.session_state["student_info"]["date"] = str(lab_date)

    st.subheader("Discussion & Experimental Observations")
    student_notes = st.text_area(
        "Enter your analysis of traversal depths, triadic closures, and query performance:",
        value=st.session_state.get("student_notes", (
            "Multi-hop Cypher traversals effectively traced research lineage across up to 4 citation hops. "
            "Triadic co-authorship pattern matching successfully uncovered hidden bridge connections, while WITH "
            "and COLLECT clauses enabled efficient pipelined aggregation of scholar citation metrics."
        )),
        height=130
    )
    st.session_state["student_notes"] = student_notes

    trials_df = pd.DataFrame(st.session_state["trials"]) if st.session_state["trials"] else pd.DataFrame()

    st.divider()
    st.subheader("Report Summary Preview")
    st.write(f"**Experiment:** {EXPERIMENT_CONFIG['title']}")
    st.write(f"**Student:** {student_name} | **ID:** {student_id} | **Date:** {lab_date}")
    st.write(f"**Quiz Score:** {st.session_state.get('quiz_score', 0)} / {len(QUIZ_QUESTIONS)}")

    if not trials_df.empty:
        st.dataframe(trials_df, hide_index=True, use_container_width=True)
    else:
        st.info("Note: You have not recorded any trials in the Simulation tab yet. Your report will indicate 0 trials.")

    # Generate PDF bytes and write file to disk
    pdf_bytes = generate_pdf_report(
        student_name=student_name,
        student_id=student_id,
        date_str=str(lab_date),
        trials_df=trials_df,
        quiz_score=st.session_state.get("quiz_score", 0),
        quiz_total=len(QUIZ_QUESTIONS),
        student_notes=student_notes
    )

    # Save to local files for guaranteed download
    os.makedirs("static", exist_ok=True)
    with open("static/lab_report.pdf", "wb") as f:
        f.write(pdf_bytes)
    with open("lab_report.pdf", "wb") as f:
        f.write(pdf_bytes)

    st.divider()
    st.subheader("Download Official Lab Report (.pdf)")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        st.link_button(
            "Open / Download PDF Document",
            url="/app/static/lab_report.pdf",
            type="primary",
            use_container_width=True
        )

    with col_btn2:
        st.download_button(
            label="Download lab_report.pdf",
            data=pdf_bytes,
            file_name="cypher_lab_report.pdf",
            mime="application/pdf",
            key="stream_pdf_btn",
            use_container_width=True
        )


# ======================================================================================
# 5. MAIN ENTRYPOINT & NAVIGATION
# ======================================================================================

def init_session_state():
    """Initializes Streamlit session state variables."""
    if "trials" not in st.session_state:
        st.session_state["trials"] = []
    if "quiz_answers" not in st.session_state:
        st.session_state["quiz_answers"] = {}
    if "quiz_submitted" not in st.session_state:
        st.session_state["quiz_submitted"] = False
    if "quiz_score" not in st.session_state:
        st.session_state["quiz_score"] = 0
    if "student_info" not in st.session_state:
        st.session_state["student_info"] = {
            "name": "Student Name",
            "id": "EXP-001",
            "date": str(datetime.now().date())
        }
    if "student_notes" not in st.session_state:
        st.session_state["student_notes"] = ""


def main():
    st.set_page_config(
        page_title="Advanced Cypher Queries & Graph Pattern Matching",
        page_icon=None,
        layout="wide"
    )

    init_session_state()

    # Native Streamlit Title
    st.title(EXPERIMENT_CONFIG["title"])

    # Navigation Sidebar
    section = st.sidebar.radio(
        "Lab Navigator",
        options=["Theory", "Simulation", "Quiz", "Report Generation"]
    )

    st.sidebar.divider()
    st.sidebar.subheader("Progress Tracker")
    quiz_status = "Done" if st.session_state.get("quiz_submitted", False) else "Pending"
    st.sidebar.write(f"- **Quiz Status:** {quiz_status}")
    if st.session_state.get("quiz_submitted", False):
        st.sidebar.write(f"- **Quiz Score:** `{st.session_state.get('quiz_score', 0)} / {len(QUIZ_QUESTIONS)}`")

    # Section Dispatcher
    if section == "Theory":
        render_theory_section()
    elif section == "Simulation":
        render_simulation_section()
    elif section == "Quiz":
        render_quiz_section()
    elif section == "Report Generation":
        render_report_section()


if __name__ == "__main__":
    main()
