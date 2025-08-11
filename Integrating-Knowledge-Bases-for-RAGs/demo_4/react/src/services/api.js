import axios from 'axios';

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:5000' 
  : '';

export const extractEntities = async (text) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/extract`, {
      text: text
    }, {
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw new Error(error.response?.data?.error || 'Failed to extract entities');
  }
};

export const queryRAG = async (query) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/extract`, {
      query: query
    }, {
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw new Error(error.response?.data?.error || 'Failed to query RAG system');
  }
};