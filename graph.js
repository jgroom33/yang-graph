// Load the graph data (replace with your graph.yml content)
const graphData = {
  graph: [
    {
      data: {
        id: "ciena-mef-fp:flow_points",
        type: "list",
        module: "ciena-mef-fp",
        description: "No description available",
        key: "id",
      },
    },
    {
      data: {
        id: "ciena-mef-fd:fd",
        type: "list",
        module: "ciena-mef-fd",
        description: "No description available",
        key: "name",
      },
    },
    {
      data: {
        source: "ciena-mef-fp:flow_points",
        target: "ciena-mef-fd:fd",
        relationship: "references_key:name",
      },
    },
  ],
};

const elements = graphData.graph;

// Initialize Cytoscape
const cy = cytoscape({
  container: document.getElementById("cy"),
  elements: elements,
  style: [
    {
      selector: "node",
      style: {
        label: "data(id)",
        "background-color": "#0074D9",
        color: "#fff",
        "text-valign": "center",
        "text-halign": "center",
        width: "120px",
        height: "120px",
        "font-size": "12px",
      },
    },
    {
      selector: "edge",
      style: {
        label: "data(relationship)",
        width: 2,
        "line-color": "#ccc",
        "target-arrow-color": "#ccc",
        "target-arrow-shape": "triangle",
        "curve-style": "bezier",
        "font-size": "10px",
        display: "none", // Initially hide edges
      },
    },
  ],
  layout: {
    name: "breadthfirst",
    directed: true,
    padding: 10,
  },
});

// Mark nodes with outgoing edges as collapsible
cy.nodes().forEach((node) => {
  const outgoing = cy.edges(`[source="${node.id()}"]`);
  if (outgoing.length > 0) {
    node.data("hasRelationships", true);
    node.data("collapsed", true);
  }
});

// Click handler to expand/collapse relationships
cy.on("tap", "node", function (evt) {
  const node = evt.target;
  const data = node.data();

  if (data.hasRelationships) {
    const outgoingEdges = cy.edges(`[source="${node.id()}"]`);
    if (data.collapsed) {
      outgoingEdges.show();
      node.data("collapsed", false);
      cy.layout({ name: "breadthfirst", roots: [node] }).run(); // Re-layout from clicked node
    } else {
      outgoingEdges.hide();
      node.data("collapsed", true);
      cy.layout({ name: "breadthfirst" }).run(); // Re-layout full graph
    }
  } else {
    alert(
      `Node: ${data.id}\nModule: ${data.module}\nDescription: ${
        data.description
      }\nKey: ${data.key || "N/A"}`
    );
  }
});
