<template>
  <div class="vitals">
    <h1>Vital Signs</h1>
    
    <div class="vitals-grid">
      <div class="add-vital">
        <h2>Add New Reading</h2>
        <form @submit.prevent="addVital">
          <select v-model="newVital.type" required>
            <option value="">Select vital type</option>
            <option value="heart_rate">Heart Rate</option>
            <option value="blood_pressure_systolic">Blood Pressure (Systolic)</option>
            <option value="blood_pressure_diastolic">Blood Pressure (Diastolic)</option>
            <option value="weight">Weight</option>
            <option value="temperature">Temperature</option>
            <option value="blood_glucose">Blood Glucose</option>
            <option value="oxygen_saturation">Oxygen Saturation</option>
          </select>
          
          <input
            v-model.number="newVital.value"
            type="number"
            step="0.1"
            placeholder="Value"
            required
          />
          
          <input
            v-model="newVital.unit"
            type="text"
            placeholder="Unit (e.g., bpm, kg, °C)"
            required
          />
          
          <input
            v-model="newVital.recorded_at"
            type="datetime-local"
            required
          />
          
          <textarea
            v-model="newVital.notes"
            placeholder="Optional notes"
            rows="2"
          ></textarea>
          
          <button type="submit">Add Reading</button>
        </form>
      </div>
      
      <div class="latest-vitals">
        <h2>Latest Readings</h2>
        <div v-if="latestVitals" class="vital-cards">
          <div v-for="(vital, type) in latestVitals" :key="type" class="vital-card">
            <h4>{{ formatVitalType(type) }}</h4>
            <p class="value">{{ vital.value }} {{ vital.unit }}</p>
            <p class="date">{{ formatDate(vital.recorded_at) }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <div class="vitals-history">
      <div class="history-header">
        <h2>History</h2>
        <button 
          v-if="vitalHistory.length > 0" 
          @click="deleteAllVitals" 
          class="delete-all-btn"
        >
          Delete All
        </button>
      </div>
      <select v-model="selectedVitalType" @change="fetchHistory">
        <option value="">Select vital type</option>
        <option value="all">All</option>
        <option value="heart_rate">Heart Rate</option>
        <option value="blood_pressure_systolic">Blood Pressure (Systolic)</option>
        <option value="blood_pressure_diastolic">Blood Pressure (Diastolic)</option>
        <option value="weight">Weight</option>
        <option value="temperature">Temperature</option>
        <option value="blood_glucose">Blood Glucose</option>
        <option value="oxygen_saturation">Oxygen Saturation</option>
      </select>
      
      <div v-if="vitalHistory.length > 0" class="history-list">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th v-if="selectedVitalType === 'all'">Type</th>
              <th>Value</th>
              <th>Notes</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="vital in vitalHistory" :key="vital.id">
              <td>{{ formatDate(vital.recorded_at) }}</td>
              <td v-if="selectedVitalType === 'all'">{{ formatVitalType(vital.vital_type) }}</td>
              <td>{{ vital.value }} {{ vital.unit }}</td>
              <td>{{ vital.notes || '-' }}</td>
              <td>
                <button @click="deleteVital(vital.id)" class="delete-btn">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// Helper function to get current local datetime string for input
const getCurrentDateTime = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

const newVital = ref({
  type: '',
  value: null,
  unit: '',
  recorded_at: getCurrentDateTime(),
  notes: ''
})

const latestVitals = ref(null)
const vitalHistory = ref([])
const selectedVitalType = ref('')

const addVital = async () => {
  try {
    // Ensure we have valid data
    if (!newVital.value.type || !newVital.value.value || !newVital.value.unit) {
      alert('Please fill in all required fields')
      return
    }
    
    // Convert local datetime to ISO string with proper timezone
    let recordedTime = null
    if (newVital.value.recorded_at) {
      const localDate = new Date(newVital.value.recorded_at)
      recordedTime = localDate.toISOString()
    }
    
    await axios.post('/api/vitals/', {
      vital_type: newVital.value.type,
      value: parseFloat(newVital.value.value),
      unit: newVital.value.unit,
      recorded_at: recordedTime,
      notes: newVital.value.notes || null
    })
    
    // Reset form with current datetime
    newVital.value = {
      type: '',
      value: null,
      unit: '',
      recorded_at: getCurrentDateTime(),
      notes: ''
    }
    
    // Refresh latest vitals
    fetchLatestVitals()
  } catch (error) {
    console.error('Failed to add vital:', error)
  }
}

const fetchLatestVitals = async () => {
  try {
    const response = await axios.get('/api/vitals/latest')
    latestVitals.value = response.data
  } catch (error) {
    console.error('Failed to fetch latest vitals:', error)
  }
}

const fetchHistory = async () => {
  if (!selectedVitalType.value) return
  
  try {
    const params = {}
    // Only add vital_type param if not "all"
    if (selectedVitalType.value !== 'all') {
      params.vital_type = selectedVitalType.value
    }
    
    const response = await axios.get('/api/vitals/', { params })
    vitalHistory.value = response.data
  } catch (error) {
    console.error('Failed to fetch history:', error)
  }
}

const formatVitalType = (type) => {
  return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatDate = (date) => {
  return new Date(date).toLocaleString()
}

const deleteVital = async (vitalId) => {
  if (!confirm('Are you sure you want to delete this vital sign?')) {
    return
  }
  
  try {
    await axios.delete(`/api/vitals/${vitalId}`)
    // Refresh the history
    fetchHistory()
    // Refresh latest vitals
    fetchLatestVitals()
  } catch (error) {
    console.error('Failed to delete vital:', error)
    alert('Failed to delete vital sign')
  }
}

const deleteAllVitals = async () => {
  const typeText = selectedVitalType.value === 'all' 
    ? 'ALL vital signs' 
    : selectedVitalType.value 
      ? `all ${formatVitalType(selectedVitalType.value)} readings`
      : 'all vital signs'
      
  if (!confirm(`Are you sure you want to delete ${typeText}? This action cannot be undone.`)) {
    return
  }
  
  try {
    const params = {}
    if (selectedVitalType.value && selectedVitalType.value !== 'all') {
      params.vital_type = selectedVitalType.value
    }
    
    const response = await axios.delete('/api/vitals/all', { params })
    alert(response.data.message)
    
    // Clear the history
    vitalHistory.value = []
    // Refresh latest vitals
    fetchLatestVitals()
  } catch (error) {
    console.error('Failed to delete vitals:', error)
    alert('Failed to delete vital signs')
  }
}

onMounted(() => {
  fetchLatestVitals()
})
</script>

<style scoped>
.vitals {
  padding: 2rem;
}

h1 {
  color: #2c3e50;
  margin-bottom: 2rem;
}

.vitals-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 3rem;
}

.add-vital,
.latest-vitals {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.add-vital h2,
.latest-vitals h2,
.vitals-history h2 {
  margin-bottom: 1rem;
  color: #2c3e50;
}

.add-vital form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.add-vital input,
.add-vital select,
.add-vital textarea {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.add-vital button {
  padding: 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.vital-cards {
  display: grid;
  gap: 1rem;
}

.vital-card {
  padding: 1rem;
  background: #f7fafc;
  border-radius: 4px;
  border-left: 4px solid #667eea;
}

.vital-card h4 {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.vital-card .value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #2c3e50;
}

.vital-card .date {
  font-size: 0.75rem;
  color: #999;
}

.vitals-history {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.history-header h2 {
  margin: 0;
}

.delete-all-btn {
  padding: 0.5rem 1rem;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.delete-all-btn:hover {
  background: #c82333;
}

.vitals-history select {
  width: 100%;
  padding: 0.5rem;
  margin-bottom: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.delete-btn {
  padding: 0.25rem 0.5rem;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.delete-btn:hover {
  background: #c82333;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

th {
  background: #f7fafc;
  font-weight: 600;
  color: #4a5568;
}

@media (max-width: 768px) {
  .vitals-grid {
    grid-template-columns: 1fr;
  }
}
</style>