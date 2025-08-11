import React from 'react';

const EntityList = ({ entities }) => {
  const hasEntities = entities && Object.keys(entities).length > 0;

  if (!hasEntities) {
    return (
      <div className="entities-section">
        <h2>Extracted Entities</h2>
        <div className="empty-entities">
          <p>No entities extracted yet.</p>
          <p>Enter text on the left and click "Extract Entities" to see the results here.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="entities-section">
      <h2>Extracted Entities</h2>
      <div className="entity-types">
        {Object.entries(entities).map(([entityType, entityList]) => {
          if (!entityList || entityList.length === 0) return null;
          
          return (
            <div key={entityType} className="entity-type">
              <strong>{entityType}:</strong>
              <div className="entity-list">
                {entityList.map((entity, index) => (
                  <span key={index} className="entity-item">
                    {entity}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default EntityList;