import axios from 'axios'

const API_BASE = 'http://localhost:8000/api/v1'

class ApiClient {
  constructor() {
    this.token = localStorage.getItem('access_token')
  }

  setToken(token) {
    this.token = token
    localStorage.setItem('access_token', token)
  }

  getHeaders() {
    return this.token ? { Authorization: `Bearer ${this.token}` } : {}
  }

  async register(email, password, name) {
    const res = await axios.post(`${API_BASE}/users/register`, {
      email,
      password,
      name,
    })
    return res.data
  }

  async login(email, password, name) {
    const res = await axios.post(`${API_BASE}/users/login`, {
      email,
      password,
      name,
    })
    if (res.data.access_token) {
      this.setToken(res.data.access_token)
    }
    return res.data
  }

  async uploadFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    const res = await axios.post(`${API_BASE}/upload`, formData, {
      headers: {
        ...this.getHeaders(),
        'Content-Type': 'multipart/form-data',
      },
    })
    return res.data
  }

  async getUploadStatus(uploadId) {
    const res = await axios.get(`${API_BASE}/upload/${uploadId}`, {
      headers: this.getHeaders(),
    })
    return res.data
  }

  async getLearningPlan() {
    const res = await axios.get(`${API_BASE}/learning/plan`, {
      headers: this.getHeaders(),
    })
    return res.data
  }

  async postProgress(wordId, performance) {
    const res = await axios.post(
      `${API_BASE}/learning/progress`,
      {
        word_id: wordId,
        performance,
      },
      {
        headers: this.getHeaders(),
      }
    )
    return res.data
  }
}

export default new ApiClient()
