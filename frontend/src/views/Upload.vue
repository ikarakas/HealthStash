<template>
  <div class="upload">
    <h1>Upload Health Record</h1>
    
    <form @submit.prevent="handleUpload" class="upload-form">
      <div class="form-group">
        <label for="file">Select File</label>
        <input
          id="file"
          type="file"
          @change="handleFileSelect"
          accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.dcm,.xls,.xlsx,.csv"
          required
        />
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
        <label for="date">Service Date</label>
        <input
          id="date"
          v-model="formData.service_date"
          type="date"
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
import axios from 'axios'

const selectedFile = ref(null)
const loading = ref(false)
const error = ref('')
const success = ref(false)

const formData = ref({
  title: '',
  category: '',
  description: '',
  provider_name: '',
  service_date: ''
})

const handleFileSelect = (event) => {
  selectedFile.value = event.target.files[0]
  if (selectedFile.value && !formData.value.title) {
    formData.value.title = selectedFile.value.name.replace(/\.[^/.]+$/, '')
  }
}

const handleUpload = async () => {
  error.value = ''
  success.value = false
  loading.value = true
  
  try {
    const data = new FormData()
    data.append('file', selectedFile.value)
    data.append('title', formData.value.title)
    data.append('category', formData.value.category)
    if (formData.value.description) data.append('description', formData.value.description)
    if (formData.value.provider_name) data.append('provider_name', formData.value.provider_name)
    if (formData.value.service_date) data.append('service_date', formData.value.service_date)
    
    await axios.post('/api/files/upload', data, {
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
      service_date: ''
    }
    document.getElementById('file').value = ''
    
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

input[type="file"] {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
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