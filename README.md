# Advanced Cypher Queries and Graph Pattern Matching: Virtual Laboratory

## Team Members

| Name | Roll No. |
| :--- | :---: |
| Tanishque Suthar | 53 |
| Nihal Sinha | 51 |
| Vanshika Somnani | 52 |
| Harsh Tanwani | 54 |
| Sakshi Thorat | 55 |

---

An interactive, educational Streamlit virtual laboratory experiment for learning and evaluating **Advanced Cypher Queries, Multi-Hop Traversal, and Graph Pattern Matching** on an **Academic Citation & Co-authorship Knowledge Graph**.

---

## 1. What the App Does

The application transforms theoretical concepts of Graph Databases (such as Neo4j and openCypher) into a hands-on, runnable laboratory partitioned into 4 core sections:

1. **Theory**: Detailed conceptual background explaining the Labeled Property Graph (LPG) model, index-free adjacency, Cypher syntax, variable-length path expansions, intermediate aggregation (`WITH`, `COLLECT()`), structural motifs, and traversal complexity ($O(b^k)$).
2. **Simulation Sandbox**: An in-memory graph execution engine (NetworkX) providing:
   - **Guided Cypher Presets**: 5 pre-configured advanced query scenarios with interactive tuning controls (hop depth $k$, citation thresholds, year filters).
   - **Custom Cypher Query Editor**: An interactive editor to write, modify, and execute Cypher patterns against the graph.
   - **Interactive 2D Plotly Subgraph Visualizer**: Visualizes the entire network and dynamically highlights matched paths and nodes in distinct colors.
   - **Complexity Curve**: Contrasts theoretical exponential expansion $O(b^k)$ with selectively pruned Cypher execution.
   - **Experimental Data Log Book**: Allows students to record experimental trials, observe metrics, and download trial records as CSV.
3. **Concept Assessment Quiz**: 10 self-grading conceptual questions testing Cypher syntax, execution semantics, and graph theory with instant feedback and explanations.
4. **Report Generation**: Dynamically compiles student metadata, recorded trial benchmarks, and observations into an official, downloadable PDF report (`lab_report.pdf`) generated using `fpdf2`.

---

## 2. Graph Data Model & What the Current Data Looks Like

The simulation operates on an embedded, realistic **Academic Research Knowledge Graph** (28 nodes, 93 edges) that requires no external database or server setup.

### Node Schema & Entities
- **`:Author` Nodes (12 scholars)**:
  - Properties: `id`, `name`, `field`, `institution`, `h_index`.
  - Examples:
    - `A1`: Dr. Ada Lovelace (Algorithms & AI, Oxford Inst, h-index: 48)
    - `A2`: Dr. Alan Turing (Theory & Crypto, Cambridge Univ, h-index: 52)
    - `A5`: Dr. Geoffrey Hinton (Deep Learning, Univ of Toronto, h-index: 55)
    - `A9`: Dr. Jennifer Widom (Graph Databases, Stanford Univ, h-index: 38)
    - `A11`: Dr. Jure Leskovec (Graph Neural Networks, Stanford Univ, h-index: 44)
- **`:Paper` Nodes (16 publications)**:
  - Properties: `id`, `title`, `year`, `citations`, `venue`, `topic`, `authors`.
  - Examples:
    - `P1`: *"Foundations of Analytical Engines"* (2015, 620 citations, JACM, Authors: A1, A2)
    - `P4`: *"Deep Hierarchical Representations"* (2017, 1320 citations, NeurIPS, Authors: A5, A6)
    - `P8`: *"Graph Neural Networks for Relational Reasoning"* (2019, 1450 citations, NeurIPS, Authors: A11, A5)
    - `P10`: *"Declarative Pattern Matching over Linked Networks"* (2020, 410 citations, SIGMOD, Authors: A9, A8)
    - `P16`: *"Recursive Knowledge Graph Traversal & Equilibrium"* (2024, 220 citations, KDD, Authors: A8, A10)

### Relationship Schema & Structural Motifs
- **`-[:AUTHORED]->`**: Directed from an `:Author` to a `:Paper`.
- **`-[:CITES]->`**: Directed from newer/applied papers to foundational papers.
  - Multi-hop chains span 1 to 4 hops (e.g., `P16 -> P13 -> P8 -> P4 -> P1`).
  - Contains an intentional circular citation loop (`P16 -> P10 -> P7 -> P16`) for cycle detection exercises.
- **`-[:COLLABORATED_WITH]->`**: Undirected/bidirectional links between scholars who have co-authored at least one paper, creating co-authorship clusters and open triadic bridges.

---

## 3. What the Cypher Queries Do

The application implements and executes 5 guided pattern-matching scenarios alongside a custom query runner:

### 1. Multi-Hop Citation Lineage
- **Cypher Query**:
  ```cypher
  MATCH path = (p1:Paper {id: $source})-[:CITES*1..$k]->(p2:Paper)
  WHERE p2.year >= $min_year AND p2.citations >= $min_citations
  RETURN p1.title AS Source, p2.title AS Ancestor, p2.year AS Year,
         p2.citations AS Citations, length(path) AS Hops
  ORDER BY Hops ASC, Citations DESC
  ```
- **What it does**: Traces ancestral research across $k$ variable hops ($k \in [1, 4]$) originating from a modern paper. It applies property filters on publication year and citation volume to discover foundational precursor papers.

### 2. Co-authorship Triadic Closures (Hidden Bridges)
- **Cypher Query**:
  ```cypher
  MATCH (a1:Author)-[:AUTHORED]->(p1:Paper)<-[:AUTHORED]-(bridge:Author)
        -[:AUTHORED]->(p2:Paper)<-[:AUTHORED]-(a2:Author)
  WHERE a1.id < a2.id AND NOT (a1)-[:COLLABORATED_WITH]-(a2)
  RETURN a1.name AS Author_1, bridge.name AS Bridge_Colleague,
         a2.name AS Author_2, p1.title AS Joint_Paper_1, p2.title AS Joint_Paper_2
  ```
- **What it does**: Detects open triangles (triadic closures). It finds pairs of researchers who have never published together, but share a mutual collaborator (`bridge`), predicting high-probability future collaborations and hidden research synergies.

### 3. High-Impact Aggregation (`WITH` & `COLLECT`)
- **Cypher Query**:
  ```cypher
  MATCH (a:Author)-[:AUTHORED]->(p:Paper)
  WHERE p.citations >= $min_paper_cites
  WITH a, count(p) AS qualifying_papers, sum(p.citations) AS total_citations,
       collect(p.title) AS landmark_papers
  WHERE qualifying_papers >= $min_papers
  RETURN a.name AS Author, a.institution AS Institution, a.h_index AS H_Index,
         qualifying_papers, total_citations, landmark_papers
  ORDER BY total_citations DESC
  ```
- **What it does**: Demonstrates multi-stage query pipelining. It aggregates paper count and total citations per author, bundles individual paper titles into a list using `collect()`, and filters out scholars who do not meet the post-aggregation threshold.

### 4. Shortest Interdisciplinary Path & Research Bridge
- **Cypher Query**:
  ```cypher
  MATCH p = shortestPath((start:Author {id: $author_a})-[*]-(target:Author {id: $author_b}))
  RETURN p, length(p) AS path_length
  ```
- **What it does**: Executes minimal-hop pathfinding (bidirectional BFS) between two researchers across different disciplines (e.g., Algorithms vs. Graph Neural Networks), revealing intermediate bridge authors and cross-domain publications.

### 5. Cyclic Citation Ring Detection
- **Cypher Query**:
  ```cypher
  MATCH path = (p:Paper)-[:CITES*2..$max_hops]->(p)
  RETURN p.title AS Anchor_Paper, length(path) AS Loop_Length, path
  ```
- **What it does**: Discovers circular reference loops where papers cite each other in closed loops (e.g., `P16 -> P10 -> P7 -> P16`), illustrating motif detection for citation cartel analysis and graph sanity verification.

### Custom Cypher Query Editor
Students can enter free-form Cypher queries or use quick-load presets, such as:
- Filtering nodes: `MATCH (a:Author) WHERE a.h_index >= 45 RETURN a.name, a.institution, a.h_index`
- Filtered relationships: `MATCH (a:Author)-[:AUTHORED]->(p:Paper) WHERE p.year >= 2020`
- Variable-length paths: `MATCH path = (p1:Paper {id: 'P16'})-[:CITES*1..3]->(p2:Paper)`
- Collaboration hops: `MATCH (a1:Author)-[:COLLABORATED_WITH*1..2]-(a2:Author)`

---

## 4. Performance Metrics & Visualizations

Every query execution dynamically updates:
- **Execution Latency**: Time in milliseconds (typically 1–7 ms for in-memory graph traversal).
- **Paths Matched**: Total count of distinct paths satisfying the graph pattern.
- **Nodes Visited & Selectivity**: Ratio of matched subgraph nodes relative to the total graph (28 nodes).
- **Interactive 2D Subgraph Diagram**:
  - Author nodes displayed as navy blue circles (size scaled to h-index).
  - Paper nodes displayed as teal squares (size scaled to citation count).
  - Matched paths and nodes illuminated with glowing amber halos and crimson edges.
  - Hover tooltips displaying entity metadata (title, year, citations, field, institution).
- **Complexity Curve**: Plots depth $k$ vs. theoretical paths $O(b^k)$ vs. selectively pruned paths.

---

## 5. Assessment & PDF Report Generation

- **Quiz**: 10 questions covering variable-length bounds, `WITH` clause mechanics, `COLLECT()` behavior, relationship uniqueness, `OPTIONAL MATCH` semantics, index-free adjacency benefits, and $O(b^k)$ path explosion.
- **PDF Export**: Generates an official report containing the student's name, ID, date, score badge, experiment objectives, logged trials table, analysis notes, and an instructor/student signature block.

---

## 6. How to Run the App

From the project root:

```bash
# Run using the configured virtual environment
.venv/bin/streamlit run template.py
```

Then open `http://localhost:8501` in your browser.
