<template>
  <div class="upload">
    <h1>Upload Health Record</h1>
    
    <form @submit.prevent="handleUpload" class="upload-form">
      <div class="form-group">
        <label for="file">Select File</label>
        <div
          class="file-drop-zone"
          :class="{ 'dragging': isDragging, 'has-file': selectedFile }"
          @drop="handleDrop"
          @dragover="handleDragOver"
          @dragenter="handleDragEnter"
          @dragleave="handleDragLeave"
        >
          <input
            id="file"
            type="file"
            @change="handleFileSelect"
            accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.dcm,.xls,.xlsx,.csv"
            required
            ref="fileInput"
          />
          <div class="drop-zone-content">
            <svg v-if="!selectedFile" class="upload-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            <p v-if="!selectedFile" class="drop-text">
              Drop your file here or <span class="browse-link">browse</span>
            </p>
            <p v-else class="file-name">
              📄 {{ selectedFile.name }}
              <button type="button" @click.prevent="clearFile" class="clear-file">✕</button>
            </p>
          </div>
        </div>
      </div>
      
      <div class="form-group">
        <label for="title">Title</label>
        <input
          id="title"
          v-model="formData.title"
          type="text"
          placeholder="Document title"
          required
        />
      </div>
      
      <div class="form-group">
        <label for="category">Category</label>
        <select id="category" v-model="formData.category" required>
          <option value="">Select category</option>
          <option value="lab_results">Lab Results</option>
          <option value="imaging">Imaging</option>
          <option value="clinical_notes">Clinical Notes</option>
          <option value="prescriptions">Prescriptions</option>
          <option value="vaccinations">Vaccinations</option>
          <option value="personal_notes">Personal Notes</option>
          <option value="other">Other</option>
        </select>
      </div>
      
      <div class="form-group">
        <label for="description">Description</label>
        <textarea
          id="description"
          v-model="formData.description"
          rows="3"
          placeholder="Optional description"
        ></textarea>
      </div>
      
      <div class="form-group">
        <label for="provider">Provider Name</label>
        <input
          id="provider"
          v-model="formData.provider_name"
          type="text"
          placeholder="Healthcare provider name"
        />
      </div>
      
      <div class="form-group">
        <label for="date">Service Date *</label>
        <input
          id="date"
          v-model="formData.service_date"
          type="date"
          required
        />
      </div>
      
      <div v-if="error" class="error">
        {{ error }}
      </div>
      
      <div v-if="success" class="success">
        File uploaded successfully!
      </div>
      
      <button type="submit" :disabled="loading || !selectedFile">
        {{ loading ? 'Uploading...' : 'Upload File' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../services/axios'

const selectedFile = ref(null)
const loading = ref(false)
const error = ref('')
const success = ref(false)
const isDragging = ref(false)
const fileInput = ref(null)

const formData = ref({
  title: '',
  category: '',
  description: '',
  provider_name: '',
  service_date: new Date().toISOString().split('T')[0]
})

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  processFile(file)
}

const processFile = (file) => {
  if (!file) return
  
  // Check file type
  const allowedExtensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.dcm', '.xls', '.xlsx', '.csv']
  const fileName = file.name.toLowerCase()
  const isAllowed = allowedExtensions.some(ext => fileName.endsWith(ext))
  
  if (!isAllowed) {
    error.value = 'File type not allowed. Please select a valid file.'
    return
  }
  
  selectedFile.value = file
  if (!formData.value.title) {
    formData.value.title = file.name.replace(/\.[^/.]+$/, '')
  }
  error.value = ''
}

const handleDrop = (event) => {
  event.preventDefault()
  isDragging.value = false
  
  const files = event.dataTransfer.files
  if (files.length > 0) {
    processFile(files[0])
    // Update the file input
    if (fileInput.value) {
      const dataTransfer = new DataTransfer()
      dataTransfer.items.add(files[0])
      fileInput.value.files = dataTransfer.files
    }
  }
}

const handleDragOver = (event) => {
  event.preventDefault()
}

const handleDragEnter = (event) => {
  event.preventDefault()
  isDragging.value = true
}

const handleDragLeave = (event) => {
  event.preventDefault()
  // Only set isDragging to false if we're leaving the drop zone entirely
  if (!event.currentTarget.contains(event.relatedTarget)) {
    isDragging.value = false
  }
}

const clearFile = () => {
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  formData.value.title = ''
}

const handleUpload = async () => {
  error.value = ''
  success.value = false
  loading.value = true
  
  // Validate service_date is provided
  if (!formData.value.service_date) {
    error.value = 'Service date is required'
    loading.value = false
    return
  }
  
  try {
    const data = new FormData()
    data.append('file', selectedFile.value)
    data.append('title', formData.value.title)
    data.append('category', formData.value.category)
    if (formData.value.description) data.append('description', formData.value.description)
    if (formData.value.provider_name) data.append('provider_name', formData.value.provider_name)
    data.append('service_date', formData.value.service_date)
    
    await api.post('/files/upload', data, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    success.value = true
    
    // Reset form
    selectedFile.value = null
    formData.value = {
      title: '',
      category: '',
      description: '',
      provider_name: '',
      service_date: new Date().toISOString().split('T')[0]
    }
    if (fileInput.value) {
      fileInput.value.value = ''
    }
    
    setTimeout(() => {
      success.value = false
    }, 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Upload failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.upload {
  padding: 2rem;
  max-width: 600px;
  margin: 0 auto;
}

h1 {
  color: #2c3e50;
  margin-bottom: 2rem;
}

.upload-form {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: #555;
  font-weight: 500;
}

input[type="text"],
input[type="date"],
select,
textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.file-drop-zone {
  position: relative;
  border: 2px dashed #cbd5e0;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  background: #f7fafc;
  transition: all 0.3s ease;
  cursor: pointer;
}

.file-drop-zone:hover {
  border-color: #667eea;
  background: #edf2f7;
}

.file-drop-zone.dragging {
  border-color: #667eea;
  background: #e9efff;
  transform: scale(1.02);
}

.file-drop-zone.has-file {
  border-color: #48bb78;
  background: #f0fff4;
}

.file-drop-zone input[type="file"] {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  opacity: 0;
  cursor: pointer;
}

.drop-zone-content {
  pointer-events: none;
}

.upload-icon {
  color: #667eea;
  margin-bottom: 1rem;
}

.drop-text {
  color: #4a5568;
  font-size: 1rem;
  margin: 0;
}

.browse-link {
  color: #667eea;
  text-decoration: underline;
  font-weight: 500;
}

.file-name {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: #2d3748;
  font-weight: 500;
  margin: 0;
}

.clear-file {
  pointer-events: auto;
  background: #e53e3e;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  transition: background 0.3s;
}

.clear-file:hover {
  background: #c53030;
}

textarea {
  resize: vertical;
}

button {
  width: 100%;
  padding: 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s;
}

button:hover:not(:disabled) {
  background: #5a67d8;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  padding: 0.75rem;
  background: #fee;
  color: #c53030;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.success {
  padding: 0.75rem;
  background: #c6f6d5;
  color: #22543d;
  border-radius: 4px;
  margin-bottom: 1rem;
}
</style>