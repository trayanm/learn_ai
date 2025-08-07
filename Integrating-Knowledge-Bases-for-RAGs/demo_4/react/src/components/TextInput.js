import React from 'react';

const TextInput = ({ value, onChange, onSubmit, loading, error }) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(value);
  };

  const defaultText = `Enter text to extract entities and create graph...

Example:
Elon Musk founded SpaceX in 2002. The company is based in California and develops advanced rockets. Tesla was also founded by Elon Musk and produces electric vehicles.

Bellamy is brother of Octavia. They both live in the space station.`;

  return (
    <div className="input-section">
      <h2>Input Text</h2>
      <form onSubmit={handleSubmit}>
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={defaultText}
          disabled={loading}
          className={error ? 'error' : ''}
        />
        {error && <div className="error-message">{error}</div>}
        <button 
          type="submit" 
          disabled={loading || !value.trim()}
          className="submit-btn"
        >
          {loading ? 'Extracting...' : 'Extract Entities'}
        </button>
      </form>
    </div>
  );
};

export default TextInput;