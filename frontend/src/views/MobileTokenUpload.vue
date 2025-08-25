<template>
  <div class="mobile-token-upload">
    <div class="upload-container">
      <div class="logo">
        <h1>📱 HealthStash</h1>
        <p>Mobile Upload</p>
      </div>
      
      <!-- Token Verification -->
      <div v-if="!tokenVerified" class="token-section">
        <h2>Enter Upload Token</h2>
        <p class="info">Enter the 8-character token from your desktop</p>
        
        <div class="token-input-group">
          <input
            v-model="inputToken"
            type="text"
            placeholder="ABCD1234"
            maxlength="8"
            @input="inputToken = inputToken.toUpperCase()"
            @keyup.enter="verifyToken"
            :disabled="verifying"
          />
          <button @click="verifyToken" :disabled="verifying || inputToken.length !== 8">
            {{ verifying ? '⏳' : '✅' }} Verify
          </button>
        </div>
        
        <div v-if="error" class="error">
          {{ error }}
        </div>
      </div>
      
      <!-- Upload Section -->
      <div v-else class="upload-section">
        <h2>Upload Health Records</h2>
        <p class="success">✅ Token verified successfully!</p>
        
        <div class="file-upload-area" @drop.prevent="handleDrop" @dragover.prevent @dragenter.prevent>
          <input
            ref="fileInput"
            type="file"
            multiple
            accept="image/*,application/pdf,.doc,.docx,.txt"
            @change="handleFileSelect"
            style="display: none"
          />
          
          <div v-if="!uploading" @click="$refs.fileInput.click()" class="upload-prompt">
            <span class="upload-icon">📤</span>
            <p>Tap to select files or drag & drop</p>
            <p class="file-types">Images, PDFs, Documents</p>
          </div>
          
          <div v-else class="uploading-status">
            <span class="spinner">⏳</span>
            <p>Uploading {{ uploadProgress }}%...</p>
          </div>
        </div>
        
        <!-- Selected Files -->
        <div v-if="selectedFiles.length > 0 && !uploading" class="selected-files">
          <h3>Selected Files:</h3>
          <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
            <span>{{ file.name }}</span>
            <button @click="removeFile(index)" class="remove-btn">✕</button>
          </div>
          
          <div class="category-select">
            <label>Category:</label>
            <select v-model="selectedCategory">
              <option value="lab_results">Lab Results</option>
              <option value="imaging">Imaging</option>
              <option value="clinical_notes">Clinical Notes</option>
              <option value="prescriptions">Prescriptions</option>
              <option value="vaccinations">Vaccinations</option>
              <option value="personal_notes">Personal Notes</option>
              <option value="other">Other</option>
            </select>
          </div>
          
          <div class="date-select">
            <label>Service Date: *</label>
            <input v-model="serviceDate" type="date" required />
          </div>
          
          <button @click="uploadFiles" class="upload-btn">
            📤 Upload {{ selectedFiles.length }} file(s)
          </button>
        </div>
        
        <!-- Upload Results -->
        <div v-if="uploadResults.length > 0" class="upload-results">
          <h3>Upload Complete!</h3>
          <div v-for="result in uploadResults" :key="result.name" class="result-item">
            <span :class="{ success: result.success, error: !result.success }">
              {{ result.success ? '✅' : '❌' }} {{ result.name }}
            </span>
          </div>
          <button @click="resetUpload" class="reset-btn">Upload More Files</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const tokenFromUrl = ref(route.params.token || '')
const inputToken = ref('')
const tokenVerified = ref(false)
const verifying = ref(false)
const error = ref('')

const selectedFiles = ref([])
const selectedCategory = ref('other')
const serviceDate = ref(new Date().toISOString().split('T')[0])
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadResults = ref([])

// Auto-verify if token is in URL
onMounted(() => {
  if (tokenFromUrl.value) {
    inputToken.value = tokenFromUrl.value
    verifyToken()
  }
})

const verifyToken = async () => {
  if (inputToken.value.length !== 8) {
    error.value = 'Token must be 8 characters'
    return
  }
  
  verifying.value = true
  error.value = ''
  
  try {
    const response = await axios.post('/api/mobile/verify-token', {
      token: inputToken.value
    })
    
    if (response.data.valid) {
      tokenVerified.value = true
    } else {
      error.value = 'Invalid or expired token'
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Invalid or expired token'
  } finally {
    verifying.value = false
  }
}

const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  selectedFiles.value = [...selectedFiles.value, ...files]
}

const handleDrop = (event) => {
  const files = Array.from(event.dataTransfer.files)
  selectedFiles.value = [...selectedFiles.value, ...files]
}

const removeFile = (index) => {
  selectedFiles.value.splice(index, 1)
}

const uploadFiles = async () => {
  if (selectedFiles.value.length === 0) return
  
  // Validate service date
  if (!serviceDate.value) {
    error.value = 'Service date is required'
    return
  }
  
  uploading.value = true
  uploadProgress.value = 0
  uploadResults.value = []
  
  const totalFiles = selectedFiles.value.length
  let completedFiles = 0
  
  for (const file of selectedFiles.value) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('category', selectedCategory.value)
      formData.append('service_date', serviceDate.value)
      
      await axios.post(`/api/mobile/upload/${inputToken.value}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const fileProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          uploadProgress.value = Math.round(((completedFiles + fileProgress / 100) * 100) / totalFiles)
        }
      })
      
      uploadResults.value.push({ name: file.name, success: true })
      completedFiles++
    } catch (error) {
      console.error('Upload failed:', error)
      uploadResults.value.push({ name: file.name, success: false })
      completedFiles++
    }
  }
  
  uploading.value = false
  selectedFiles.value = []
}

const resetUpload = () => {
  selectedFiles.value = []
  uploadResults.value = []
  uploadProgress.value = 0
}
</script>

<style scoped>
.mobile-token-upload {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-container {
  background: white;
  border-radius: 20px;
  padding: 2rem;
  max-width: 500px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.logo {
  text-align: center;
  margin-bottom: 2rem;
}

.logo h1 {
  font-size: 2rem;
  color: #1a202c;
  margin: 0;
}

.logo p {
  color: #64748b;
  margin-top: 0.5rem;
}

/* Token Section */
.token-section h2 {
  color: #1a202c;
  margin-bottom: 0.5rem;
  font-size: 1.5rem;
}

.info {
  color: #64748b;
  margin-bottom: 1.5rem;
}

.token-input-group {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.token-input-group input {
  flex: 1;
  padding: 1rem;
  font-size: 1.5rem;
  text-align: center;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-family: monospace;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.token-input-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.token-input-group button {
  padding: 1rem 2rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.token-input-group button:hover:not(:disabled) {
  background: #5a67d8;
  transform: translateY(-1px);
}

.token-input-group button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error {
  color: #ef4444;
  padding: 0.75rem;
  background: #fee2e2;
  border-radius: 8px;
  margin-top: 1rem;
}

/* Upload Section */
.upload-section h2 {
  color: #1a202c;
  margin-bottom: 1rem;
}

.success {
  color: #10b981;
  margin-bottom: 1.5rem;
  font-weight: 500;
}

.file-upload-area {
  border: 3px dashed #cbd5e0;
  border-radius: 16px;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #f8fafc;
}

.file-upload-area:hover {
  border-color: #667eea;
  background: #f0f4ff;
}

.upload-prompt {
  cursor: pointer;
}

.upload-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.upload-prompt p {
  margin: 0.5rem 0;
  color: #64748b;
}

.file-types {
  font-size: 0.875rem;
  color: #94a3b8;
}

.uploading-status {
  text-align: center;
}

.spinner {
  font-size: 3rem;
  display: block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Selected Files */
.selected-files {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e2e8f0;
}

.selected-files h3 {
  color: #1a202c;
  margin-bottom: 1rem;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.remove-btn {
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.category-select {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1.5rem 0;
}

.category-select label {
  font-weight: 600;
  color: #1a202c;
}

.category-select select {
  flex: 1;
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  background: white;
}

.upload-btn {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.125rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.upload-btn:hover {
  transform: translateY(-2px);
}

/* Upload Results */
.upload-results {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e2e8f0;
}

.upload-results h3 {
  color: #1a202c;
  margin-bottom: 1rem;
}

.result-item {
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.result-item .success {
  color: #10b981;
}

.result-item .error {
  color: #ef4444;
}

.reset-btn {
  width: 100%;
  padding: 1rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  margin-top: 1rem;
}

.reset-btn:hover {
  background: #059669;
}

/* Mobile Responsive */
@media (max-width: 640px) {
  .upload-container {
    padding: 1.5rem;
    border-radius: 16px;
  }
  
  .logo h1 {
    font-size: 1.5rem;
  }
  
  .token-input-group {
    flex-direction: column;
  }
  
  .token-input-group button {
    width: 100%;
  }
}
</style>