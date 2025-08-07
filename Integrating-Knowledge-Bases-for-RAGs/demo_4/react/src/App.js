import React, { useState, useCallback } from 'react';
import TextInput from './components/TextInput';
import EntityList from './components/EntityList';
import EntityGraph from './components/EntityGraph';
import GraphControls from './components/GraphControls';
import { extractEntities } from './services/api';

function App() {
  const [inputText, setInputText] = useState('');
  const [entities, setEntities] = useState({});
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [visibleNodes, setVisibleNodes] = useState([]);

  const handleTextSubmit = useCallback(async (text) => {
    if (!text.trim()) return;

    setLoading(true);
    setError('');

    try {
      const response = await extractEntities(text);
      setEntities(response.entities);
      setGraphData(response.graph);
      
      // Initialize visible nodes with all nodes
      if (response.graph && response.graph.nodes) {
        setVisibleNodes(response.graph.nodes);
      }
    } catch (err) {
      setError('Failed to extract entities. Please try again.');
      console.error('Error extracting entities:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleVisibilityChange = useCallback((newVisibleNodes) => {
    setVisibleNodes(newVisibleNodes);
  }, []);

  const navigateToRAG = () => {
    // Navigate to main RAG system
    window.location.href = '/';
  };

  return (
    <div className="app">
      <div className="container">
        <div className="navigation">
          <button onClick={navigateToRAG} className="nav-link">
            ← Back to RAG System
          </button>
        </div>
        
        <h1>Entity Extraction and Graph Visualization</h1>
        
        {/* Graph Section - Full Width at Top */}
        <div className="graph-section">
          <h2>Entity Graph</h2>
          <div className="graph-container">
            {graphData && graphData.nodes && graphData.nodes.length > 0 ? (
              <EntityGraph 
                graphData={graphData} 
                visibleNodes={visibleNodes}
              />
            ) : (
              <div className="empty-state">
                <h3>No Graph Generated Yet</h3>
                <p>Enter text below and click "Extract Entities" to see the interactive graph visualization</p>
              </div>
            )}
          </div>
        </div>
        
        {/* Bottom Grid - Input, Entities, and Controls */}
        <div className="bottom-grid">
          <TextInput 
            value={inputText}
            onChange={setInputText}
            onSubmit={handleTextSubmit}
            loading={loading}
            error={error}
          />
          
          <EntityList entities={entities} />
          
          <GraphControls 
            entities={entities}
            graphData={graphData}
            visibleNodes={visibleNodes}
            onVisibilityChange={handleVisibilityChange}
          />
        </div>
      </div>
    </div>
  );
}

export default App;