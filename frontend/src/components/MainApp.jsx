import { useState, useEffect } from 'react'
import api from '../api'
import '../styles/app.css'

export default function MainApp({ onLogout }) {
  const [activeTab, setActiveTab] = useState('upload')
  const [uploadFile, setUploadFile] = useState(null)
  const [uploadStatus, setUploadStatus] = useState(null)
  const [uploadId, setUploadId] = useState(null)
  const [learningPlan, setLearningPlan] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleFileSelect = (e) => {
    setUploadFile(e.target.files[0])
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!uploadFile) {
      setError('Please select a file')
      return
    }

    setLoading(true)
    setError('')
    try {
      const result = await api.uploadFile(uploadFile)
      setUploadId(result.upload_id)
      setUploadStatus('processing')
      setUploadFile(null)

      // Poll for status every 500ms
      const pollInterval = setInterval(async () => {
        try {
          const status = await api.getUploadStatus(result.upload_id)
          if (status.status === 'done') {
            setUploadStatus('done')
            setUploadId(null)
            clearInterval(pollInterval)
            await loadLearningPlan()
          } else if (status.status === 'error') {
            setUploadStatus('error')
            clearInterval(pollInterval)
          }
        } catch (err) {
          console.error('Error polling upload status:', err)
        }
      }, 500)

      setTimeout(() => clearInterval(pollInterval), 30000) // Stop polling after 30s
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  const loadLearningPlan = async () => {
    try {
      const result = await api.getLearningPlan()
      setLearningPlan(result.plans || [])
    } catch (err) {
      console.error('Error loading learning plan:', err)
    }
  }

  const handleProgress = async (wordId, performance) => {
    try {
      await api.postProgress(wordId, performance)
      await loadLearningPlan()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update progress')
    }
  }

  useEffect(() => {
    if (activeTab === 'plan') {
      loadLearningPlan()
    }
  }, [activeTab])

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>WordMem</h1>
        <button onClick={onLogout}>Logout</button>
      </header>

      <div className="tabs">
        <button
          className={activeTab === 'upload' ? 'active' : ''}
          onClick={() => setActiveTab('upload')}
        >
          Upload
        </button>
        <button
          className={activeTab === 'plan' ? 'active' : ''}
          onClick={() => setActiveTab('plan')}
        >
          Learning Plan
        </button>
      </div>

      <main className="app-content">
        {error && <div className="error">{error}</div>}

        {activeTab === 'upload' && (
          <div className="upload-section">
            <h2>Upload Document</h2>
            <form onSubmit={handleUpload}>
              <input
                type="file"
                onChange={handleFileSelect}
                disabled={loading}
              />
              <button type="submit" disabled={loading || !uploadFile}>
                {loading ? 'Uploading...' : 'Upload'}
              </button>
            </form>
            {uploadStatus === 'processing' && (
              <p className="status">Processing OCR...</p>
            )}
            {uploadStatus === 'done' && (
              <p className="success">Upload complete! Check your learning plan.</p>
            )}
            {uploadStatus === 'error' && (
              <p className="error">Upload failed. Please try again.</p>
            )}
          </div>
        )}

        {activeTab === 'plan' && (
          <div className="plan-section">
            <h2>Learning Plan</h2>
            {learningPlan.length === 0 ? (
              <p>No items to review. Upload a document to get started!</p>
            ) : (
              <div className="word-list">
                {learningPlan.map((item) => (
                  <div key={item.word_id} className="word-card">
                    <div className="word-info">
                      <p>Word ID: {item.word_id}</p>
                      <p>Interval: {item.interval_hours?.toFixed(2) || 0} hours</p>
                      <p>Reviews: {item.review_count || 0}</p>
                    </div>
                    <div className="word-actions">
                      <button
                        onClick={() => handleProgress(item.word_id, 0.5)}
                      >
                        Hard
                      </button>
                      <button
                        onClick={() => handleProgress(item.word_id, 0.75)}
                      >
                        Medium
                      </button>
                      <button
                        onClick={() => handleProgress(item.word_id, 0.95)}
                      >
                        Easy
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
