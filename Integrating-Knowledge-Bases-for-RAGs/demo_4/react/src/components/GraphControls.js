import React, { useState, useEffect, useCallback } from 'react';

const GraphControls = ({ entities, graphData, visibleNodes, onVisibilityChange }) => {
  const [checkedTypes, setCheckedTypes] = useState({});
  const [checkedNodes, setCheckedNodes] = useState({});

  const colorMap = {
    'PERSON': '#FF6B6B',
    'ORG': '#4ECDC4',
    'GPE': '#45B7D1',
    'PRODUCT': '#96CEB4'
  };

  // Initialize checked states when entities change
  useEffect(() => {
    if (entities && Object.keys(entities).length > 0) {
      const newCheckedTypes = {};
      const newCheckedNodes = {};

      Object.entries(entities).forEach(([entityType, entityList]) => {
        if (entityList && entityList.length > 0) {
          newCheckedTypes[entityType] = true;
          entityList.forEach(entity => {
            newCheckedNodes[entity] = true;
          });
        }
      });

      setCheckedTypes(newCheckedTypes);
      setCheckedNodes(newCheckedNodes);
    }
  }, [entities]);

  // Update visible nodes when checked states change
  useEffect(() => {
    const newVisibleNodes = Object.entries(checkedNodes)
      .filter(([node, isChecked]) => isChecked)
      .map(([node]) => node);
    
    onVisibilityChange(newVisibleNodes);
  }, [checkedNodes, onVisibilityChange]);

  const handleTypeChange = useCallback((entityType, isChecked) => {
    setCheckedTypes(prev => ({
      ...prev,
      [entityType]: isChecked
    }));

    // Update all nodes of this type
    if (entities[entityType]) {
      setCheckedNodes(prev => {
        const updated = { ...prev };
        entities[entityType].forEach(entity => {
          updated[entity] = isChecked;
        });
        return updated;
      });
    }
  }, [entities]);

  const handleNodeChange = useCallback((nodeName, isChecked) => {
    setCheckedNodes(prev => ({
      ...prev,
      [nodeName]: isChecked
    }));

    // Update entity type checkbox if needed
    const entityType = Object.entries(entities).find(([type, list]) => 
      list.includes(nodeName)
    )?.[0];

    if (entityType) {
      const typeNodes = entities[entityType];
      const checkedTypeNodes = typeNodes.filter(node => 
        node === nodeName ? isChecked : checkedNodes[node]
      );
      
      setCheckedTypes(prev => ({
        ...prev,
        [entityType]: checkedTypeNodes.length > 0
      }));
    }
  }, [entities, checkedNodes]);

  const showAllNodes = useCallback(() => {
    const allTypes = {};
    const allNodes = {};

    Object.entries(entities).forEach(([entityType, entityList]) => {
      if (entityList && entityList.length > 0) {
        allTypes[entityType] = true;
        entityList.forEach(entity => {
          allNodes[entity] = true;
        });
      }
    });

    setCheckedTypes(allTypes);
    setCheckedNodes(allNodes);
  }, [entities]);

  const hideAllNodes = useCallback(() => {
    const noTypes = {};
    const noNodes = {};

    Object.keys(checkedTypes).forEach(type => {
      noTypes[type] = false;
    });
    Object.keys(checkedNodes).forEach(node => {
      noNodes[node] = false;
    });

    setCheckedTypes(noTypes);
    setCheckedNodes(noNodes);
  }, [checkedTypes, checkedNodes]);

  const showOnlyConnected = useCallback(() => {
    if (!graphData || !graphData.adjacency) return;

    const connectedNodes = new Set();
    
    // Find all nodes that have connections
    Object.entries(graphData.adjacency).forEach(([node, connections]) => {
      if (connections.length > 0) {
        connectedNodes.add(node);
        connections.forEach(conn => connectedNodes.add(conn));
      }
    });

    const newCheckedNodes = {};
    const newCheckedTypes = {};

    // Update node checkboxes
    Object.keys(checkedNodes).forEach(node => {
      newCheckedNodes[node] = connectedNodes.has(node);
    });

    // Update type checkboxes
    Object.entries(entities).forEach(([entityType, entityList]) => {
      const hasVisibleNodes = entityList.some(entity => connectedNodes.has(entity));
      newCheckedTypes[entityType] = hasVisibleNodes;
    });

    setCheckedNodes(newCheckedNodes);
    setCheckedTypes(newCheckedTypes);
  }, [graphData, entities, checkedNodes]);

  const hasEntities = entities && Object.keys(entities).length > 0;

  if (!hasEntities) {
    return (
      <div className="node-controls">
        <h2>Graph Controls</h2>
        <div className="empty-entities">
          <p>No controls available yet.</p>
          <p>Extract entities to see graph controls here.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="node-controls">
      <h2>Graph Controls</h2>
      <div id="nodeControlsContainer">
        {/* Entity Type Controls */}
        <div className="control-group">
          <h4>ENTITY TYPES</h4>
          {Object.entries(entities).map(([entityType, entityList]) => {
            if (!entityList || entityList.length === 0) return null;

            return (
              <div key={entityType} className="checkbox-item">
                <input
                  type="checkbox"
                  id={`type_${entityType}`}
                  checked={checkedTypes[entityType] || false}
                  onChange={(e) => handleTypeChange(entityType, e.target.checked)}
                />
                <label htmlFor={`type_${entityType}`}>
                  {entityType} ({entityList.length})
                </label>
                <div 
                  className="node-color-indicator"
                  style={{ backgroundColor: colorMap[entityType] || '#CCCCCC' }}
                />
              </div>
            );
          })}
        </div>

        {/* Individual Nodes Controls */}
        <div className="control-group">
          <h4>INDIVIDUAL NODES</h4>
          <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
            {Object.entries(entities).map(([entityType, entityList]) => {
              if (!entityList || entityList.length === 0) return null;

              return entityList.map((entity, index) => (
                <div key={`${entityType}_${index}`} className="checkbox-item">
                  <input
                    type="checkbox"
                    id={`node_${entity.replace(/\s+/g, '_')}`}
                    checked={checkedNodes[entity] || false}
                    onChange={(e) => handleNodeChange(entity, e.target.checked)}
                  />
                  <label htmlFor={`node_${entity.replace(/\s+/g, '_')}`}>
                    {entity}
                  </label>
                  <div 
                    className="node-color-indicator"
                    style={{ backgroundColor: colorMap[entityType] || '#CCCCCC' }}
                  />
                </div>
              ));
            })}
          </div>
        </div>

        {/* Control Buttons */}
        <div className="control-buttons">
          <button className="control-btn" onClick={showAllNodes}>
            Show All
          </button>
          <button className="control-btn secondary" onClick={hideAllNodes}>
            Hide All
          </button>
          <button className="control-btn" onClick={showOnlyConnected}>
            Connected Only
          </button>
          <button className="control-btn secondary" onClick={() => showAllNodes()}>
            Reset View
          </button>
        </div>
      </div>
    </div>
  );
};

export default GraphControls;