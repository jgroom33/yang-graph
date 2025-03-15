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
                            'text-halign': 'center'
                        }
                    },
                    {
                        selector: 'edge',
                        style: {
                            'width': 2,
                            'line-color': '#0074D9',
                            'target-arrow-color': '#0074D9',
                            'target-arrow-shape': 'triangle'
                        }
                    }
                ],
                layout: {
                    name: 'grid',
                    rows: 1
                }
            });
        });
});
