<template>
  <div class="mobile-upload">
    <h1>📱 Mobile Upload</h1>
    
    <div class="upload-sections">
      <!-- QR Code Section -->
      <div class="qr-section">
        <h2>Scan to Upload from Mobile</h2>
        <div class="qr-container">
          <canvas ref="qrCanvas"></canvas>
        </div>
        <p class="qr-info">
          Scan this QR code with your mobile device to access the upload page
        </p>
        <div class="upload-url">
          <span>{{ uploadUrl }}</span>
          <button @click="copyUrl" class="copy-btn">📋 Copy</button>
        </div>
      </div>
      
      <!-- Mobile Token Section -->
      <div class="token-section">
        <h2>Temporary Upload Token</h2>
        <div class="token-container">
          <div class="token-display">
            <code>{{ uploadToken }}</code>
            <button @click="regenerateToken" class="refresh-btn">🔄</button>
          </div>
          <p class="token-info">
            Token expires in: <strong>{{ tokenExpiry }}</strong>
          </p>
        </div>
        <div class="instructions">
          <h3>How to use:</h3>
          <ol>
            <li>Scan the QR code or visit the URL on your mobile device</li>
            <li>Enter the upload token when prompted</li>
            <li>Select and upload your health records</li>
            <li>Files will appear in your Records section</li>
          </ol>
        </div>
      </div>
      
      <!-- Recent Mobile Uploads -->
      <div class="recent-uploads">
        <h2>Recent Mobile Uploads</h2>
        <div v-if="recentUploads.length === 0" class="no-uploads">
          No mobile uploads yet
        </div>
        <div v-else class="upload-list">
          <div v-for="upload in recentUploads" :key="upload.id" class="upload-item">
            <span class="upload-name">{{ upload.name }}</span>
            <span class="upload-time">{{ formatTime(upload.timestamp) }}</span>
            <span class="upload-device">{{ upload.device }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import QRCode from 'qrcode'
import api from '../services/axios'

const qrCanvas = ref(null)
const uploadToken = ref('')
const tokenExpiryTime = ref(null)
const recentUploads = ref([])
const copied = ref(false)
const currentTime = ref(Date.now())
const serverIP = ref('')

const uploadUrl = computed(() => {
  // If we have a server-provided IP, use that
  if (serverIP.value && uploadToken.value) {
    return `${serverIP.value}/m/${uploadToken.value}`
  }
  
  // Otherwise, try to construct URL based on current location
  const origin = window.location.origin
  const host = window.location.hostname
  
  // If running on localhost, try to use a more accessible address
  if (host === 'localhost' || host === '127.0.0.1') {
    // This will be replaced by server-provided IP
    const port = window.location.port
    const protocol = window.location.protocol
    // Fallback to a common local network pattern
    return `${protocol}//192.168.1.100${port ? ':' + port : ''}/m/${uploadToken.value}`
  }
  
  return `${origin}/m/${uploadToken.value}`
})

const tokenExpiry = computed(() => {
  if (!tokenExpiryTime.value) return '...'
  const now = currentTime.value // Use reactive current time
  const diff = tokenExpiryTime.value - now
  if (diff <= 0) return 'Expired'
  
  const minutes = Math.floor(diff / 60000)
  const seconds = Math.floor((diff % 60000) / 1000)
  return `${minutes}m ${seconds}s`
})

let expiryInterval = null

const generateToken = async () => {
  try {
    const response = await api.post('/mobile/generate-token')
    uploadToken.value = response.data.token
    tokenExpiryTime.value = Date.now() + (response.data.expires_in * 1000)
    
    // Use server-provided URL if available
    if (response.data.upload_url) {
      serverIP.value = response.data.upload_url.replace(/\/m\/.*$/, '')
    }
    
    // Generate QR code after URL is set
    await new Promise(resolve => setTimeout(resolve, 100)) // Small delay to ensure computed prop updates
    
    if (qrCanvas.value) {
      await QRCode.toCanvas(qrCanvas.value, uploadUrl.value, {
        width: 256,
        margin: 2,
        color: {
          dark: '#1a202c',
          light: '#ffffff'
        }
      })
    }
  } catch (error) {
    console.error('Failed to generate token:', error)
  }
}

const regenerateToken = () => {
  generateToken()
}

const copyUrl = async () => {
  try {
    await navigator.clipboard.writeText(uploadUrl.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (error) {
    console.error('Failed to copy:', error)
  }
}

const fetchRecentUploads = async () => {
  try {
    const response = await api.get('/mobile/recent-uploads')
    recentUploads.value = response.data.uploads || []
  } catch (error) {
    console.error('Failed to fetch uploads:', error)
  }
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return 'Just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  return date.toLocaleDateString()
}

onMounted(() => {
  generateToken()
  fetchRecentUploads()
  
  // Update token expiry every second
  expiryInterval = setInterval(() => {
    currentTime.value = Date.now() // Update reactive current time
    if (tokenExpiryTime.value && currentTime.value >= tokenExpiryTime.value) {
      generateToken()
    }
  }, 1000)
  
  // Refresh uploads every 30 seconds
  setInterval(fetchRecentUploads, 30000)
})

onUnmounted(() => {
  if (expiryInterval) {
    clearInterval(expiryInterval)
  }
})
</script>

<style scoped>
.mobile-upload {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

h1 {
  color: #1a202c;
  margin-bottom: 2rem;
  font-size: 2rem;
}

.upload-sections {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 2rem;
}

/* QR Section */
.qr-section {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.qr-section h2 {
  color: #2d3748;
  margin-bottom: 1.5rem;
  font-size: 1.25rem;
}

.qr-container {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
}

.qr-info {
  text-align: center;
  color: #64748b;
  margin-bottom: 1rem;
}

.upload-url {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: #f1f5f9;
  border-radius: 8px;
  font-family: monospace;
  font-size: 0.875rem;
}

.upload-url span {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.copy-btn {
  padding: 0.375rem 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.copy-btn:hover {
  background: #5a67d8;
}

/* Token Section */
.token-section {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.token-section h2 {
  color: #2d3748;
  margin-bottom: 1.5rem;
  font-size: 1.25rem;
}

.token-container {
  margin-bottom: 1.5rem;
}

.token-display {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8fafc;
  border: 2px dashed #cbd5e0;
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.token-display code {
  flex: 1;
  font-size: 1.5rem;
  font-weight: bold;
  color: #667eea;
  letter-spacing: 0.1em;
  text-align: center;
}

.refresh-btn {
  padding: 0.5rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  cursor: pointer;
  transition: transform 0.3s;
}

.refresh-btn:hover {
  transform: rotate(180deg);
}

.token-info {
  text-align: center;
  color: #64748b;
  font-size: 0.875rem;
}

.token-info strong {
  color: #ef4444;
}

.instructions {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e2e8f0;
}

.instructions h3 {
  color: #2d3748;
  margin-bottom: 1rem;
  font-size: 1rem;
}

.instructions ol {
  margin-left: 1.5rem;
  color: #64748b;
  line-height: 1.8;
}

/* Recent Uploads */
.recent-uploads {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.recent-uploads h2 {
  color: #2d3748;
  margin-bottom: 1.5rem;
  font-size: 1.25rem;
}

.no-uploads {
  text-align: center;
  padding: 2rem;
  color: #94a3b8;
  background: #f8fafc;
  border-radius: 8px;
  border: 2px dashed #e2e8f0;
}

.upload-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.upload-item {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 1rem;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 8px;
  transition: background 0.2s;
}

.upload-item:hover {
  background: #f1f5f9;
}

.upload-name {
  font-weight: 500;
  color: #2d3748;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upload-time {
  color: #64748b;
  font-size: 0.875rem;
}

.upload-device {
  color: #94a3b8;
  font-size: 0.875rem;
}
</style>