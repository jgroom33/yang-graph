document.addEventListener("DOMContentLoaded", function () {
  fetch("graph.json")
    .then((response) => response.json())
    .then((data) => {
      // Extract nodes and edges from Cytoscape.js format
      const elements = data.graph || {
        nodes: data.nodes || [],
        edges: data.edges || [],
      };
      const nodes = (
        data.graph ? elements.filter((e) => e.data.id) : elements.nodes
      ).map((n) => n.data);
      const edges = (
        data.graph ? elements.filter((e) => !e.data.id) : elements.edges
      ).map((e) => e.data);

      // Create a set of node IDs
      const nodeIds = new Set(nodes.map((n) => n.id));

      // Add placeholder nodes for missing targets
      const placeholderNodes = [];
      edges.forEach((edge) => {
        if (!nodeIds.has(edge.target)) {
          placeholderNodes.push({
            id: edge.target,
            type: "unknown",
            module: edge.target.split(":")[0] || "unknown",
            description: "Referenced but not defined in processed YANG modules",
            key: null,
            isPlaceholder: true,
          });
          nodeIds.add(edge.target);
        }
      });

      // Combine original and placeholder nodes
      const allNodes = nodes.concat(placeholderNodes);
      const allElements = allNodes
        .map((n) => ({ data: n }))
        .concat(edges.map((e) => ({ data: e })));

      const cy = cytoscape({
        container: document.getElementById("cy"),
        elements: allElements,
        style: [
          {
            selector: "node",
            style: {
              label: "data(id)",
              "background-color": "#0074D9",
              color: "#fff",
              "text-valign": "center",
              "text-halign": "center",
              width: "100px",
              height: "100px",
              "font-size": "12px",
            },
          },
          {
            selector: "node[isPlaceholder]",
            style: {
              "background-color": "#999999",
              opacity: 0.6,
              label: 'data(id) + " (missing)"',
            },
          },
          {
            selector: "edge",
            style: {
              width: 2,
              "line-color": "#0074D9",
              "target-arrow-color": "#0074D9",
              "target-arrow-shape": "triangle",
              label: "data(relationship)",
              "font-size": "10px",
            },
          },
        ],
        layout: {
          name: "breadthfirst",
          directed: true,
          padding: 10,
        },
      });

      // Click handler to show node info only
      cy.on("tap", "node", function (evt) {
        const node = evt.target;
        const data = node.data();
        alert(
          `Node: ${data.id}\nModule: ${data.module}\nDescription: ${
            data.description
          }\nKey: ${data.key || "N/A"}`
        );
      });
    })
    .catch((error) => {
      console.error("Error loading or rendering graph:", error);
      alert("Failed to load graph.json. Check the console for details.");
    });
});
