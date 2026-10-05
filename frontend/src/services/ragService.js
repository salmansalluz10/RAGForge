import api from './api';

export const ragService = {
  async queryRAG({ question, collectionId = null, documentIds = null, topK = null, threshold = null }) {
    const payload = {
      question,
      collection_id: collectionId,
      document_ids: documentIds,
      top_k: topK,
      threshold,
    };
    const response = await api.post('/rag/query', payload);
    return response.data;
  },
};

export default ragService;
