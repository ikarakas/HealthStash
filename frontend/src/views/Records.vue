<template>
  <div class="records">
    <h1>Health Records</h1>
    
    <div class="filters">
      <select v-model="filters.category">
        <option value="">All Categories</option>
        <option value="lab_results">Lab Results</option>
        <option value="imaging">Imaging</option>
        <option value="clinical_notes">Clinical Notes</option>
        <option value="prescriptions">Prescriptions</option>
        <option value="vaccinations">Vaccinations</option>
        <option value="personal_notes">Personal Notes</option>
      </select>
      
      <input
        v-model="filters.search"
        type="text"
        placeholder="Search records..."
      />
      
      <button @click="fetchRecords">Search</button>
    </div>
    
    <div class="records-list">
      <div v-if="loading" class="loading">Loading records...</div>
      
      <div v-else-if="records.length === 0" class="empty">
        No records found
      </div>
      
      <div v-else>
        <div v-for="record in records" :key="record.id" class="record-card">
          <h3>{{ record.title }}</h3>
          <p class="category">{{ formatCategory(record.category) }}</p>
          <p class="date">{{ formatDate(record.service_date) }}</p>
          <p v-if="record.provider_name" class="provider">Provider: {{ record.provider_name }}</p>
          <div class="actions">
            <button @click="downloadRecord(record.id)">Download</button>
            <button @click="deleteRecord(record.id)" class="danger">Delete</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const records = ref([])
const loading = ref(false)
const filters = ref({
  category: '',
  search: ''
})

const fetchRecords = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.category) params.category = filters.value.category
    if (filters.value.search) params.search = filters.value.search
    
    const response = await axios.get('/api/records', { params })
    records.value = response.data.records
  } catch (error) {
    console.error('Failed to fetch records:', error)
  } finally {
    loading.value = false
  }
}

const downloadRecord = async (recordId) => {
  try {
    const response = await axios.get(`/api/files/download/${recordId}`)
    // Handle file download
    console.log('Download:', response.data)
  } catch (error) {
    console.error('Failed to download:', error)
  }
}

const deleteRecord = async (recordId) => {
  if (!confirm('Are you sure you want to delete this record?')) return
  
  try {
    await axios.delete(`/api/files/${recordId}`)
    await fetchRecords()
  } catch (error) {
    console.error('Failed to delete:', error)
  }
}

const formatCategory = (category) => {
  return category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatDate = (date) => {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString()
}

onMounted(() => {
  fetchRecords()
})
</script>

<style scoped>
.records {
  padding: 2rem;
}

h1 {
  color: #2c3e50;
  margin-bottom: 2rem;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.filters select,
.filters input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.filters input {
  flex: 1;
}

.filters button {
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.records-list {
  display: grid;
  gap: 1rem;
}

.record-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.record-card h3 {
  margin-bottom: 0.5rem;
}

.category {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: #e0e7ff;
  color: #4c51bf;
  border-radius: 4px;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.date,
.provider {
  color: #666;
  font-size: 0.875rem;
}

.actions {
  margin-top: 1rem;
  display: flex;
  gap: 0.5rem;
}

.actions button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.actions button:first-child {
  background: #667eea;
  color: white;
}

.actions button.danger {
  background: #e74c3c;
  color: white;
}

.loading,
.empty {
  text-align: center;
  padding: 2rem;
  color: #666;
}
</style>