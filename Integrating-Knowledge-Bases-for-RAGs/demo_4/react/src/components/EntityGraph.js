import React, { useEffect, useState, useCallback } from 'react';
import Plot from 'react-plotly.js';

const EntityGraph = ({ graphData, visibleNodes }) => {
  const [plotData, setPlotData] = useState([]);
  const [isHighlighted, setIsHighlighted] = useState(false);
  const [originalColors, setOriginalColors] = useState([]);

  const colorMap = {
    'PERSON': '#FF6B6B',
    'ORG': '#4ECDC4',
    'GPE': '#45B7D1',
    'PRODUCT': '#96CEB4'
  };

  // Helper function to normalize edge data
  const normalizeEdge = (edge) => {
    if (Array.isArray(edge)) {
      return edge; // Already in [node1, node2] format
    } else if (edge && typeof edge === 'object') {
      // Handle object format like {source: 'node1', target: 'node2'}
      if (edge.source && edge.target) {
        return [edge.source, edge.target];
      }
      // Handle other object formats
      if (edge[0] && edge[1]) {
        return [edge[0], edge[1]];
      }
    }
    console.warn('Unknown edge format:', edge);
    return null;
  };

  // Initialize plot data
  useEffect(() => {
    console.log('EntityGraph received graphData:', graphData);
    
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
      console.log('No graph data available');
      return;
    }

    const { nodes, edges, positions } = graphData;
    
    console.log('Nodes:', nodes);
    console.log('Edges:', edges);
    console.log('Positions:', positions);

    // Create edge traces
    const edgeX = [];
    const edgeY = [];
    const edgeHoverX = [];
    const edgeHoverY = [];
    const edgeHoverText = [];

    // Safely handle edges
    if (edges && Array.isArray(edges)) {
      edges.forEach(edge => {
        const normalizedEdge = normalizeEdge(edge);
        if (!normalizedEdge) return;
        
        const [node1, node2] = normalizedEdge;
        
        if (positions && positions[node1] && positions[node2]) {
          const [x0, y0] = positions[node1];
          const [x1, y1] = positions[node2];
          
          edgeX.push(x0, x1, null);
          edgeY.push(y0, y1, null);
          
          // Add hover point at midpoint
          edgeHoverX.push((x0 + x1) / 2);
          edgeHoverY.push((y0 + y1) / 2);
          edgeHoverText.push(`<b>${node1} ←→ ${node2}</b><br>Relationship: <i>related</i>`);
        }
      });
    }

    const edgeTrace = {
      x: edgeX,
      y: edgeY,
      mode: 'lines',
      line: { width: 4, color: '#888' },
      hoverinfo: 'none',
      name: 'Relationships',
      showlegend: false,
      type: 'scatter'
    };

    const edgeHoverTrace = {
      x: edgeHoverX,
      y: edgeHoverY,
      mode: 'markers',
      marker: {
        size: 15,
        color: 'rgba(0,0,0,0)',
        line: { width: 0 }
      },
      hoverinfo: 'text',
      hovertext: edgeHoverText,
      name: 'Edge Info',
      showlegend: false,
      type: 'scatter'
    };

    // Create node traces
    const nodeX = [];
    const nodeY = [];
    const nodeText = [];
    const nodeColors = [];
    const nodeInfo = [];

    nodes.forEach(node => {
      if (positions && positions[node]) {
        const [x, y] = positions[node];
        nodeX.push(x);
        nodeY.push(y);
        nodeText.push(node);

        // Determine node type and color - improved detection
        let nodeType = 'unknown';
        
        // Check if we have node type information in the graph data
        if (graphData.nodeTypes && graphData.nodeTypes[node]) {
          nodeType = graphData.nodeTypes[node];
        } else {
          // Fallback to simple string matching
          const nodeLower = node.toLowerCase();
          if (nodeLower.includes('elon') || nodeLower.includes('octavia') || nodeLower.includes('bellamy')) {
            nodeType = 'PERSON';
          } else if (nodeLower.includes('spacex') || nodeLower.includes('tesla') || nodeLower.includes('company')) {
            nodeType = 'ORG';
          } else if (nodeLower.includes('california') || nodeLower.includes('space station')) {
            nodeType = 'GPE';
          }
        }

        nodeColors.push(colorMap[nodeType] || '#CCCCCC');

        // Add node info
        const connections = graphData.adjacency && graphData.adjacency[node] ? graphData.adjacency[node] : [];
        const connectionInfo = connections.length > 0 
          ? `Connections: ${connections.slice(0, 3).join(', ')}${connections.length > 3 ? ` and ${connections.length - 3} more...` : ''}`
          : 'No connections';
        
        nodeInfo.push(`<b>${node}</b><br>Type: <i>${nodeType}</i><br>${connectionInfo}`);
      }
    });

    const nodeTrace = {
      x: nodeX,
      y: nodeY,
      mode: 'markers+text',
      text: nodeText,
      textposition: 'middle center',
      textfont: { color: 'white', size: 12, family: 'Arial Black' },
      hoverinfo: 'text',
      hovertext: nodeInfo,
      marker: {
        size: 50,
        color: nodeColors,
        line: { width: 3, color: 'white' }
      },
      name: 'Entities',
      showlegend: false,
      type: 'scatter'
    };

    setPlotData([edgeTrace, edgeHoverTrace, nodeTrace]);
    setOriginalColors(nodeColors);
  }, [graphData]);

  // Update visibility when visibleNodes changes
  useEffect(() => {
    if (!graphData || !plotData.length || !originalColors.length) return;

    const updatedPlotData = [...plotData];
    const nodeTrace = updatedPlotData[2]; // Node trace is at index 2

    // Update node colors and text based on visibility
    const nodeColors = graphData.nodes.map((node, index) => {
      return visibleNodes.includes(node) ? originalColors[index] : 'rgba(0,0,0,0)';
    });

    const nodeTexts = graphData.nodes.map(node => {
      return visibleNodes.includes(node) ? node : '';
    });

    nodeTrace.marker.color = nodeColors;
    nodeTrace.text = nodeTexts;

    // Update edges to only show between visible nodes
    const edgeX = [];
    const edgeY = [];
    const edgeHoverX = [];
    const edgeHoverY = [];
    const edgeHoverText = [];

    if (graphData.edges && Array.isArray(graphData.edges)) {
      graphData.edges.forEach(edge => {
        const normalizedEdge = normalizeEdge(edge);
        if (!normalizedEdge) return;
        
        const [node1, node2] = normalizedEdge;
        
        if (visibleNodes.includes(node1) && visibleNodes.includes(node2)) {
          if (graphData.positions && graphData.positions[node1] && graphData.positions[node2]) {
            const [x0, y0] = graphData.positions[node1];
            const [x1, y1] = graphData.positions[node2];
            
            edgeX.push(x0, x1, null);
            edgeY.push(y0, y1, null);
            
            edgeHoverX.push((x0 + x1) / 2);
            edgeHoverY.push((y0 + y1) / 2);
            edgeHoverText.push(`<b>${node1} ←→ ${node2}</b><br>Relationship: <i>related</i>`);
          }
        }
      });
    }

    updatedPlotData[0].x = edgeX;
    updatedPlotData[0].y = edgeY;
    updatedPlotData[1].x = edgeHoverX;
    updatedPlotData[1].y = edgeHoverY;
    updatedPlotData[1].hovertext = edgeHoverText;

    setPlotData(updatedPlotData);
    setIsHighlighted(false);
  }, [visibleNodes, graphData, originalColors]);

  const handlePlotClick = useCallback((data) => {
    if (!data.points || data.points.length === 0) return;

    const point = data.points[0];
    const traceName = point.data.name;

    if (traceName === 'Entities') {
      const clickedNodeIndex = point.pointIndex;
      const clickedNode = graphData.nodes[clickedNodeIndex];

      if (isHighlighted) {
        // Reset highlight
        const updatedPlotData = [...plotData];
        const nodeTrace = updatedPlotData[2];
        nodeTrace.marker.color = graphData.nodes.map((node, index) => {
          return visibleNodes.includes(node) ? originalColors[index] : 'rgba(0,0,0,0)';
        });
        setPlotData(updatedPlotData);
        setIsHighlighted(false);
      } else {
        // Highlight connected nodes
        const connectedNodes = graphData.adjacency && graphData.adjacency[clickedNode] ? graphData.adjacency[clickedNode] : [];
        const updatedPlotData = [...plotData];
        const nodeTrace = updatedPlotData[2];
        
        const nodeColors = originalColors.map((color, index) => {
          const hex = color;
          const r = parseInt(hex.slice(1, 3), 16);
          const g = parseInt(hex.slice(3, 5), 16);
          const b = parseInt(hex.slice(5, 7), 16);
          return `rgba(${r},${g},${b},0.3)`;
        });

        // Highlight clicked node
        const clickedIndex = graphData.nodes.indexOf(clickedNode);
        if (clickedIndex !== -1) {
          nodeColors[clickedIndex] = originalColors[clickedIndex];
        }

        // Highlight connected nodes
        connectedNodes.forEach(node => {
          const index = graphData.nodes.indexOf(node);
          if (index !== -1) {
            nodeColors[index] = originalColors[index];
          }
        });

        nodeTrace.marker.color = nodeColors;
        setPlotData(updatedPlotData);
        setIsHighlighted(true);
      }
    }
  }, [graphData, plotData, originalColors, visibleNodes, isHighlighted]);

  const handlePlotDoubleClick = useCallback(() => {
    if (isHighlighted) {
      // Reset highlight
      const updatedPlotData = [...plotData];
      const nodeTrace = updatedPlotData[2];
      nodeTrace.marker.color = graphData.nodes.map((node, index) => {
        return visibleNodes.includes(node) ? originalColors[index] : 'rgba(0,0,0,0)';
      });
      setPlotData(updatedPlotData);
      setIsHighlighted(false);
    }
  }, [graphData, plotData, originalColors, visibleNodes, isHighlighted]);

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div style={{ 
        color: '#aaa', 
        textAlign: 'center', 
        padding: '40px 20px',
        fontStyle: 'italic'
      }}>
        No graph data available
      </div>
    );
  }

  return (
    <Plot
      data={plotData}
      layout={{
        title: {
          text: 'Extracted Entities Graph',
          font: { size: 20, color: 'white' }
        },
        showlegend: false,
        hovermode: 'closest',
        margin: { b: 40, l: 40, r: 40, t: 60 },
        height: 550,
        annotations: [{
          text: 'Red: People • Teal: Organizations • Blue: Locations • Green: Products<br><i>Click on nodes or edges to highlight connections • Use controls to show/hide nodes</i>',
          showarrow: false,
          xref: 'paper',
          yref: 'paper',
          x: 0.5,
          y: -0.12,
          xanchor: 'center',
          yanchor: 'bottom',
          font: { color: 'white', size: 11 }
        }],
        xaxis: { showgrid: false, zeroline: false, showticklabels: false },
        yaxis: { showgrid: false, zeroline: false, showticklabels: false },
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: { color: 'white' }
      }}
      config={{
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        toImageButtonOptions: {
          format: 'png',
          filename: 'entity_graph',
          height: 550,
          width: 800,
          scale: 2
        }
      }}
      style={{ width: '100%', height: '550px' }}
      onClick={handlePlotClick}
      onDoubleClick={handlePlotDoubleClick}
    />
  );
};

export default EntityGraph;