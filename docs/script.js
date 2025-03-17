document.addEventListener('DOMContentLoaded', function() {
    fetch('graph.json')
        .then(response => response.json())
        .then(data => {
            const cy = cytoscape({
                container: document.getElementById('cy'),
                elements: data.graph,
                style: [
                    {
                        selector: 'node',
                        style: {
                            'label': 'data(id)',
                            'background-color': '#0074D9',
                            'color': '#fff',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'width': '100px', // Increased width
                            'height': '100px', // Increased height
                            'font-size': '12px' // Increased font size
                        }
                    },
                    {
                        selector: 'edge',
                        style: {
                            'width': 2,
                            'line-color': '#0074D9',
                            'target-arrow-color': '#0074D9',
                            'target-arrow-shape': 'triangle',
                            'label': 'data(relationship)',
                            'font-size': '10px'
                        }
                    }
                ],
                layout: {
                    name: 'breadthfirst',
                    directed: true,
                    padding: 10
                }
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
        });
});
