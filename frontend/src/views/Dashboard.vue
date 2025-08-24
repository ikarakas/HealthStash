<!--
  MIT License
  Copyright (c) 2025 Ilker M. KARAKAS
  HealthStash - Privacy-First Personal Health Data Vault
-->
<template>
  <div class="dashboard">
    <h1>Welcome to HealthStash</h1>
    
    <div class="stats-grid">
      <div class="stat-card">
        <h3>Total Records</h3>
        <p class="stat-value">{{ stats.totalRecords }}</p>
      </div>
      
      <div class="stat-card">
        <h3>Storage Used</h3>
        <p class="stat-value">{{ formatStorage(stats.storageUsed) }}</p>
        <div class="progress-bar">
          <div 
            class="progress-fill" 
            :style="`width: ${stats.storagePercentage}%`"
          ></div>
        </div>
      </div>
      
      <div class="stat-card">
        <h3>Recent Uploads</h3>
        <p class="stat-value">{{ stats.recentUploads }}</p>
      </div>
      
      <div class="stat-card">
        <h3>Last Backup</h3>
        <p class="stat-value">{{ formatDate(stats.lastBackup) }}</p>
      </div>
    </div>
    
    <div class="quick-actions">
      <h2>Quick Actions</h2>
      <div class="action-buttons">
        <router-link to="/upload" class="action-btn">
          Upload File
        </router-link>
        <router-link to="/vitals" class="action-btn">
          Add Vital Sign
        </router-link>
        <router-link to="/records" class="action-btn">
          View Records
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/axios'

const stats = ref({
  totalRecords: 0,
  storageUsed: 0,
  storageQuota: 5000,
  storagePercentage: 0,
  recentUploads: 0,
  lastBackup: null
})

const fetchStats = async () => {
  try {
    const response = await api.get('/records/stats')
    const data = response.data
    
    stats.value = {
      totalRecords: Object.values(data.categories).reduce((a, b) => a + b, 0),
      storageUsed: data.storage.used_mb,
      storageQuota: data.storage.quota_mb,
      storagePercentage: data.storage.percentage,
      recentUploads: data.recent_uploads.length,
      lastBackup: new Date()
    }
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

const formatStorage = (mb) => {
  if (mb < 1024) {
    return `${mb.toFixed(1)} MB`
  }
  return `${(mb / 1024).toFixed(2)} GB`
}

const formatDate = (date) => {
  if (!date) return 'Never'
  return new Date(date).toLocaleDateString()
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.dashboard {
  padding: 2rem;
}

h1 {
  color: #2c3e50;
  margin-bottom: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-card h3 {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #2c3e50;
}

.progress-bar {
  margin-top: 1rem;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #667eea;
  transition: width 0.3s;
}

.quick-actions h2 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.action-btn {
  padding: 1rem 2rem;
  background: #667eea;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  transition: background 0.3s;
}

.action-btn:hover {
  background: #5a67d8;
}
</style>