import api from './api';

export const searchService = {
  async semanticSearch({ query, collectionId = null, documentIds = null, topK = 5, threshold = null }) {
    const payload = {
      query,
      collection_id: collectionId,
      document_ids: documentIds,
      top_k: topK,
      threshold,
    };
    const response = await api.post('/search', payload);
    return response.data;
  },
};

export default searchService;
