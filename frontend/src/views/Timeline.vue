<!--
  MIT License
  Copyright (c) 2025 Ilker M. KARAKAS
  HealthStash - Privacy-First Personal Health Data Vault
-->
<template>
  <div class="timeline-view">
    <div class="timeline-header">
      <h1>Health Timeline</h1>
      <div class="header-actions">
        <select v-model="filterCategory" @change="filterRecords" class="filter-select">
          <option value="">All Categories</option>
          <option value="lab_results">Lab Results</option>
          <option value="imaging">Imaging</option>
          <option value="clinical_notes">Clinical Notes</option>
          <option value="prescriptions">Prescriptions</option>
          <option value="vaccinations">Vaccinations</option>
          <option value="personal_notes">Personal Notes</option>
          <option value="vital_signs">Vital Signs</option>
          <option value="other">Other</option>
        </select>
        <button @click="exportTimeline" class="export-btn">
          📊 Export View
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">
      Loading your health timeline...
    </div>

    <div v-else-if="!filteredRecords.length" class="no-records">
      <p>No health records found with service dates.</p>
      <p>Start adding records with dates to see your health timeline!</p>
    </div>

    <TimelineVisualization 
      v-else
      :records="filteredRecords" 
      @record-click="handleRecordClick"
    />

    <div v-if="selectedRecord" class="record-details">
      <div class="details-header">
        <h3>{{ selectedRecord.title }}</h3>
        <button @click="selectedRecord = null" class="close-btn">✕</button>
      </div>
      <div class="details-body">
        <div class="detail-row">
          <strong>Date:</strong> {{ formatDate(selectedRecord.service_date) }}
        </div>
        <div class="detail-row">
          <strong>Category:</strong> {{ formatCategory(selectedRecord.category) }}
        </div>
        <div v-if="selectedRecord.provider_name" class="detail-row">
          <strong>Provider:</strong> {{ selectedRecord.provider_name }}
        </div>
        <div v-if="selectedRecord.location" class="detail-row">
          <strong>Location:</strong> {{ selectedRecord.location }}
        </div>
        <div v-if="selectedRecord.description" class="detail-row">
          <strong>Description:</strong>
          <p>{{ selectedRecord.description }}</p>
        </div>
        <div class="detail-actions">
          <button @click="viewFullRecord" class="view-btn">View Full Record</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { format, parseISO } from 'date-fns'
import api from '@/services/axios'
import TimelineVisualization from '@/components/TimelineVisualization.vue'

const router = useRouter()
const records = ref([])
const loading = ref(true)
const filterCategory = ref('')
const selectedRecord = ref(null)

const filteredRecords = computed(() => {
  if (!filterCategory.value) {
    return records.value
  }
  return records.value.filter(r => r.category === filterCategory.value)
})

function formatDate(date) {
  if (!date) return 'No date'
  return format(parseISO(date), 'MMMM d, yyyy')
}

function formatCategory(category) {
  return category
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

async function fetchRecords() {
  try {
    loading.value = true
    const response = await api.get('/records', {
      params: {
        sort_by: 'service_date_desc',
        limit: 1000
      }
    })
    records.value = response.data.records || []
  } catch (error) {
    console.error('Failed to fetch records:', error)
    alert('Failed to load health records. Please try again.')
  } finally {
    loading.value = false
  }
}

function filterRecords() {
  // Filtering is handled by computed property
}

function handleRecordClick(record) {
  selectedRecord.value = record
}

function viewFullRecord() {
  if (selectedRecord.value) {
    router.push({
      name: 'Records',
      query: { id: selectedRecord.value.id }
    })
  }
}

function exportTimeline() {
  const data = filteredRecords.value.map(record => ({
    date: formatDate(record.service_date),
    title: record.title,
    category: formatCategory(record.category),
    provider: record.provider_name || '',
    location: record.location || '',
    description: record.description || ''
  }))
  
  const csv = [
    ['Date', 'Title', 'Category', 'Provider', 'Location', 'Description'],
    ...data.map(row => [
      row.date,
      row.title,
      row.category,
      row.provider,
      row.location,
      row.description
    ])
  ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n')
  
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `health-timeline-${format(new Date(), 'yyyy-MM-dd')}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  fetchRecords()
})
</script>

<style scoped>
.timeline-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.timeline-header h1 {
  font-size: 28px;
  color: #333;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 15px;
  align-items: center;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  cursor: pointer;
}

.export-btn {
  padding: 8px 16px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.export-btn:hover {
  background: #218838;
}

.loading {
  text-align: center;
  padding: 60px 20px;
  font-size: 18px;
  color: #666;
}

.no-records {
  text-align: center;
  padding: 60px 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.no-records p {
  margin: 10px 0;
  color: #666;
  font-size: 16px;
}

.record-details {
  position: fixed;
  right: 20px;
  top: 100px;
  width: 350px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-height: 70vh;
  overflow-y: auto;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #007bff;
  color: white;
  border-radius: 8px 8px 0 0;
}

.details-header h3 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.details-body {
  padding: 20px;
}

.detail-row {
  margin-bottom: 15px;
}

.detail-row strong {
  display: inline-block;
  margin-bottom: 5px;
  color: #555;
}

.detail-row p {
  margin: 5px 0;
  color: #666;
  line-height: 1.5;
}

.detail-actions {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.view-btn {
  width: 100%;
  padding: 10px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.view-btn:hover {
  background: #0056b3;
}

@media (max-width: 768px) {
  .timeline-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }
  
  .record-details {
    position: static;
    width: 100%;
    margin-top: 20px;
  }
}
</style>