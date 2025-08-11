// Graph interaction functionality
let graphData = null;
let isHighlighted = false;
let visibleNodes = [];

// Initialize graph interactions
function initializeGraphInteractions(data) {
    console.log('Loading graph JavaScript...');
    
    graphData = data;
    visibleNodes = [...graphData.nodes];
    
    console.log('Graph data loaded:', graphData);
    
    // Wait for Plotly to load
    setTimeout(function() {
        console.log('Setting up Plotly interactions...');
        const plotElement = document.querySelector('.plotly-graph-div');
        if (!plotElement) {
            console.error('Plot element not found!');
            return;
        }
        
        console.log('Plot element found, setting up events...');
        
        // Click event handler
        plotElement.on('plotly_click', function(data) {
            console.log('Graph clicked:', data);
            if (!data.points || data.points.length === 0) return;
            
            const point = data.points[0];
            const traceName = point.data.name;
            
            if (traceName === 'Entities') {
                const clickedNode = point.customdata;
                console.log('Node clicked:', clickedNode);
                
                if (isHighlighted) {
                    resetGraphHighlight();
                } else {
                    highlightConnectedNodes(clickedNode);
                }
            } else if (traceName === 'Edge Info') {
                const edgeInfo = point.customdata.split('|');
                const node1 = edgeInfo[0];
                const node2 = edgeInfo[1];
                console.log('Edge clicked:', node1, '->', node2);
                
                if (isHighlighted) {
                    resetGraphHighlight();
                } else {
                    highlightConnectedNodes(node1);
                }
            }
        });
        
        // Double-click to reset
        plotElement.on('plotly_doubleclick', function() {
            if (isHighlighted) {
                resetGraphHighlight();
            }
        });
        
        console.log('Graph functions registered successfully');
        
    }, 1000);
}

function highlightConnectedNodes(clickedNode) {
    console.log('Highlighting connected nodes for:', clickedNode);
    const connectedNodes = graphData.adjacency[clickedNode] || [];
    const nodeColors = [...graphData.originalColors];
    
    // Dim all nodes first
    for (let i = 0; i < nodeColors.length; i++) {
        const hex = graphData.originalColors[i];
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        nodeColors[i] = `rgba(${r},${g},${b},0.3)`;
    }
    
    // Highlight clicked node and connected nodes
    const clickedIndex = graphData.nodes.indexOf(clickedNode);
    if (clickedIndex !== -1) {
        nodeColors[clickedIndex] = graphData.originalColors[clickedIndex];
    }
    
    connectedNodes.forEach(node => {
        const index = graphData.nodes.indexOf(node);
        if (index !== -1) {
            nodeColors[index] = graphData.originalColors[index];
        }
    });
    
    const plotElement = document.querySelector('.plotly-graph-div');
    Plotly.restyle(plotElement, {'marker.color': [nodeColors]}, [2]);
    isHighlighted = true;
}

function resetGraphHighlight() {
    console.log('Resetting graph highlight');
    const nodeColors = graphData.nodes.map((node, index) => {
        return visibleNodes.includes(node) ? graphData.originalColors[index] : 'rgba(0,0,0,0)';
    });
    const plotElement = document.querySelector('.plotly-graph-div');
    Plotly.restyle(plotElement, {'marker.color': [nodeColors]}, [2]);
    isHighlighted = false;
}

function updateNodeVisibility() {
    console.log('Updating node visibility, visible nodes:', visibleNodes);
    
    // Update node visibility
    const nodeColors = graphData.nodes.map((node, index) => {
        return visibleNodes.includes(node) ? graphData.originalColors[index] : 'rgba(0,0,0,0)';
    });
    
    const nodeTexts = graphData.nodes.map(node => {
        return visibleNodes.includes(node) ? node : '';
    });
    
    console.log('Updating node colors and texts...');
    const plotElement = document.querySelector('.plotly-graph-div');
    Plotly.restyle(plotElement, {
        'marker.color': [nodeColors],
        'text': [nodeTexts]
    }, [2]);
    
    // Update edge visibility - only show edges between visible nodes
    const edgeX = [];
    const edgeY = [];
    const visibleEdgeHoverX = [];
    const visibleEdgeHoverY = [];
    const visibleEdgeHoverText = [];
    
    graphData.edges.forEach(edge => {
        const [node1, node2] = edge;
        if (visibleNodes.includes(node1) && visibleNodes.includes(node2)) {
            const [x0, y0] = [graphData.positions[node1][0], graphData.positions[node1][1]];
            const [x1, y1] = [graphData.positions[node2][0], graphData.positions[node2][1]];
            edgeX.push(x0, x1, null);
            edgeY.push(y0, y1, null);
            
            // Add hover point at midpoint
            visibleEdgeHoverX.push((x0 + x1) / 2);
            visibleEdgeHoverY.push((y0 + y1) / 2);
            visibleEdgeHoverText.push(`<b>${node1} ←→ ${node2}</b><br>Relationship: <i>related</i>`);
        }
    });
    
    console.log('Updating edge traces...');
    Plotly.restyle(plotElement, {'x': [edgeX], 'y': [edgeY]}, [0]);
    Plotly.restyle(plotElement, {'x': [visibleEdgeHoverX], 'y': [visibleEdgeHoverY], 'hovertext': [visibleEdgeHoverText]}, [1]);
    
    isHighlighted = false;
}

// Global functions for external access
window.updateGraphNodeVisibility = function(newVisibleNodes) {
    console.log('updateGraphNodeVisibility called with:', newVisibleNodes);
    visibleNodes = newVisibleNodes;
    updateNodeVisibility();
};

window.resetGraphHighlight = resetGraphHighlight;

window.showOnlyConnectedNodes = function() {
    console.log('showOnlyConnectedNodes called');
    // Find all nodes that have connections
    const connectedNodes = [];
    for (const [node, connections] of Object.entries(graphData.adjacency)) {
        if (connections.length > 0) {
            connectedNodes.push(node);
            connections.forEach(conn => {
                if (!connectedNodes.includes(conn)) {
                    connectedNodes.push(conn);
                }
            });
        }
    }
    
    visibleNodes = connectedNodes;
    updateNodeVisibility();
    
    // Update checkboxes
    const checkboxes = document.querySelectorAll('#nodeControlsContainer input[type="checkbox"]');
    checkboxes.forEach(cb => {
        if (cb.dataset.type === 'individual-node') {
            cb.checked = connectedNodes.includes(cb.dataset.value);
        } else if (cb.dataset.type === 'entity-type') {
            const typeNodes = document.querySelectorAll(`input[data-entity-type="${cb.dataset.value}"]`);
            const hasVisibleNodes = Array.from(typeNodes).some(node => connectedNodes.includes(node.dataset.value));
            cb.checked = hasVisibleNodes;
        }
    });
};