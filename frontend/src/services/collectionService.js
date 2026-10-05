import api from './api';

export const collectionService = {
  async listCollections(params = {}) {
    const response = await api.get('/collections', { params });
    return response.data;
  },

  async createCollection(data) {
    const response = await api.post('/collections', data);
    return response.data;
  },

  async getCollection(id) {
    const response = await api.get(`/collections/${id}`);
    return response.data;
  },

  async updateCollection(id, data) {
    const response = await api.put(`/collections/${id}`, data);
    return response.data;
  },

  async deleteCollection(id) {
    await api.delete(`/collections/${id}`);
    return true;
  },

  async addDocument(collectionId, documentId) {
    const response = await api.post(`/collections/${collectionId}/documents`, {
      document_id: documentId,
    });
    return response.data;
  },

  async removeDocument(collectionId, documentId) {
    const response = await api.delete(`/collections/${collectionId}/documents/${documentId}`);
    return response.data;
  },
};

export default collectionService;
