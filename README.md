# yang-graph

Generate a graph of YANG modules and their dependencies.



the goal is to process yang files and generate a graph for each that defines possible nodes and edges that can be connected from other yangs.

Goals:

* Only concerned with config properties
* Capture edge relationships between list keys and leafrefs in other yangs
* Capture edge relationships between leafrefs and leafrefs in other yangs
* Capture edge relationships between leafrefs and list keys in other yangs

There are already tools that capture within a single yang file, but not across multiple yang files. Yangster is one such tool that can be used to generate a graph of a single yang file. This tool will be used to generate a graph of multiple yang files. It will not be concerned with the actual data types of the properties, only the relationships between them.


There are 2 stages to the final generation. Stage 1 converts the yang files into a format that can be used by the graphing tool. Stage 2 generates the graph from the converted files. The graph file for each yang contains the list of nodes and edges that can be connected to other yangs.


This is a prototype of a pyang to handle the first stage. Improve it to capture refs also.
```bash
./generate_graph.sh
```
