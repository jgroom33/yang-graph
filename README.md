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

The final stage is rendering the graph. This is done with cytograph.js. The graph is rendered in a web browser.

```bash
## Perform stage 1 and 2
./generate_graph.sh
## Start the web server
npm install  # run once
npm start
```
