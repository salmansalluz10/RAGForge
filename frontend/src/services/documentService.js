import api from './api';

export const documentService = {
  async getDocuments(params = {}) {
    const response = await api.get('/documents', { params });
    return response.data;
  },

  async getDocument(id) {
    const response = await api.get(`/documents/${id}`);
    return response.data;
  },

  async uploadDocument(file, collectionId = null, onUploadProgress = null) {
    const formData = new FormData();
    formData.append('file', file);
    if (collectionId) {
      formData.append('collection_id', collectionId);
    }

    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(percentCompleted);
        }
      },
    });
    return response.data;
  },

  async deleteDocument(id) {
    await api.delete(`/documents/${id}`);
    return true;
  },

  async processDocument(id) {
    const response = await api.post(`/documents/${id}/process`);
    return response.data;
  },

  async getDocumentChunks(id) {
    const response = await api.get(`/documents/${id}/chunks`);
    return response.data;
  },
};

export default documentService;
