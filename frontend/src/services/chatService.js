import api from './api';

export const chatService = {
  async listConversations(params = {}) {
    const response = await api.get('/conversations', { params });
    return response.data;
  },

  async createConversation(data = {}) {
    const response = await api.post('/conversations', data);
    return response.data;
  },

  async getConversation(id) {
    const response = await api.get(`/conversations/${id}`);
    return response.data;
  },

  async updateConversation(id, title) {
    const response = await api.put(`/conversations/${id}`, { title });
    return response.data;
  },

  async deleteConversation(id) {
    await api.delete(`/conversations/${id}`);
    return true;
  },

  async sendMessage(conversationId, content) {
    const response = await api.post(`/conversations/${conversationId}/messages`, { content });
    return response.data;
  },
};

export default chatService;
