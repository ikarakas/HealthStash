<template>
  <div class="admin">
    <h1>Admin Dashboard</h1>
    
    <div class="stats-overview">
      <div class="stat">
        <h3>Total Users</h3>
        <p>{{ stats.users?.total || 0 }}</p>
      </div>
      <div class="stat">
        <h3>Active Users</h3>
        <p>{{ stats.users?.active || 0 }}</p>
      </div>
      <div class="stat">
        <h3>Total Storage</h3>
        <p>{{ formatStorage(stats.storage?.total_used_mb || 0) }}</p>
      </div>
      <div class="stat">
        <h3>Logins (24h)</h3>
        <p>{{ stats.activity?.logins_24h || 0 }}</p>
      </div>
    </div>
    
    <div class="admin-sections">
      <div class="users-section">
        <h2>User Management</h2>
        <button @click="showCreateUser = true">Create New User</button>
        
        <table v-if="users.length > 0">
          <thead>
            <tr>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Storage</th>
              <th>Created</th>
              <th>Last Updated</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.username }}</td>
              <td>{{ user.email }}</td>
              <td>{{ user.role }}</td>
              <td>{{ formatStorage(user.storage_used_mb) }} / {{ formatStorage(user.storage_quota_mb) }}</td>
              <td>{{ formatDate(user.created_at) }}</td>
              <td>{{ formatDate(user.updated_at) }}</td>
              <td>
                <button @click="resetPassword(user.id)">Reset Password</button>
                <button @click="deleteUser(user.id)" class="danger">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div class="backup-section">
        <div class="section-header">
          <h2>Backup Management</h2>
          <button @click="createBackup" class="primary-btn">
            <span class="btn-icon">+</span>
            Create Backup Now
          </button>
        </div>
        
        <div class="backup-stats">
          <div class="backup-stat">
            <div class="stat-icon success">✓</div>
            <div class="stat-details">
              <span class="stat-number">{{ backups.filter(b => b.status === 'completed').length }}</span>
              <span class="stat-label">Successful</span>
            </div>
          </div>
          <div class="backup-stat">
            <div class="stat-icon warning">⚠</div>
            <div class="stat-details">
              <span class="stat-number">{{ backups.filter(b => b.status === 'in_progress').length }}</span>
              <span class="stat-label">In Progress</span>
            </div>
          </div>
          <div class="backup-stat">
            <div class="stat-icon error">✕</div>
            <div class="stat-details">
              <span class="stat-number">{{ backups.filter(b => b.status === 'failed').length }}</span>
              <span class="stat-label">Failed</span>
            </div>
          </div>
          <div class="backup-stat">
            <div class="stat-icon info">📅</div>
            <div class="stat-details">
              <span class="stat-number">{{ getLastBackupTime() }}</span>
              <span class="stat-label">Last Backup</span>
            </div>
          </div>
        </div>
        
        <div v-if="backups.length > 0" class="backup-list">
          <div class="backup-list-header">
            <span>Date & Time</span>
            <span>Status</span>
            <span>Size</span>
            <span>Duration</span>
            <span>Actions</span>
          </div>
          <div v-for="backup in backups" :key="backup.id" class="backup-item" :class="`status-${backup.status}`">
            <div class="backup-date">
              <div class="date-primary">{{ formatBackupDate(backup.created_at) }}</div>
              <div class="date-secondary">{{ formatBackupTime(backup.created_at) }}</div>
            </div>
            <div class="backup-status">
              <span class="status-badge" :class="`badge-${backup.status}`">
                <span v-if="backup.status === 'completed'" class="status-icon">✓</span>
                <span v-else-if="backup.status === 'failed'" class="status-icon">✕</span>
                <span v-else-if="backup.status === 'in_progress'" class="status-icon spinning">⟳</span>
                {{ formatStatus(backup.status) }}
              </span>
              <div v-if="backup.error_message" class="error-message">{{ backup.error_message }}</div>
            </div>
            <div class="backup-size">{{ formatBackupSize(backup.size_mb) }}</div>
            <div class="backup-duration">{{ formatDuration(backup.duration_seconds) }}</div>
            <div class="backup-actions">
              <button v-if="backup.status === 'completed'" @click="restoreBackup(backup.id)" class="action-btn restore">
                <span title="Restore">⟲</span>
              </button>
              <button v-if="backup.status === 'failed'" @click="retryBackup(backup.id)" class="action-btn retry">
                <span title="Retry">↻</span>
              </button>
              <button v-if="backup.status === 'completed'" @click="downloadBackup(backup.id)" class="action-btn download">
                <span title="Download">↓</span>
              </button>
              <button @click="deleteBackup(backup.id)" class="action-btn delete">
                <span title="Delete">🗑</span>
              </button>
            </div>
          </div>
        </div>
        
        <div v-else class="no-backups">
          <div class="empty-state">
            <div class="empty-icon">📦</div>
            <p>No backups found</p>
            <span>Create your first backup to protect your data</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Create User Modal -->
    <div v-if="showCreateUser" class="modal">
      <div class="modal-content">
        <h2>Create New User</h2>
        <form @submit.prevent="handleCreateUser">
          <input v-model="newUser.email" type="email" placeholder="Email" required />
          <input v-model="newUser.username" type="text" placeholder="Username" required />
          <input v-model="newUser.full_name" type="text" placeholder="Full Name" required />
          <input v-model="newUser.password" type="password" placeholder="Password" required />
          <button type="submit">Create User</button>
          <button type="button" @click="showCreateUser = false">Cancel</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/axios'

const stats = ref({})
const users = ref([])
const backups = ref([])
const showCreateUser = ref(false)

const newUser = ref({
  email: '',
  username: '',
  full_name: '',
  password: ''
})

const fetchStats = async () => {
  try {
    const response = await api.get('/admin/stats')
    stats.value = response.data
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

const fetchUsers = async () => {
  try {
    const response = await api.get('/users/')
    users.value = response.data
  } catch (error) {
    console.error('Failed to fetch users:', error)
  }
}

const fetchBackups = async () => {
  try {
    const response = await api.get('/backup/history')
    backups.value = response.data
  } catch (error) {
    console.error('Failed to fetch backups:', error)
  }
}

const handleCreateUser = async () => {
  try {
    const response = await api.post('/admin/users', newUser.value)
    showCreateUser.value = false
    newUser.value = { email: '', username: '', full_name: '', password: '' }
    await fetchUsers()
    alert('User created successfully')
  } catch (error) {
    console.error('Failed to create user:', error)
    const errorMessage = error.response?.data?.detail || 'Failed to create user'
    alert(`Error: ${errorMessage}`)
  }
}

const resetPassword = async (userId) => {
  const newPassword = prompt('Enter new password:')
  if (!newPassword) return
  
  try {
    await api.post(`/admin/users/${userId}/reset-password`, { new_password: newPassword })
    alert('Password reset successfully')
  } catch (error) {
    console.error('Failed to reset password:', error)
  }
}

const deleteUser = async (userId) => {
  if (!confirm('Are you sure you want to delete this user?')) return
  
  try {
    await api.delete(`/users/${userId}`)
    await fetchUsers()
  } catch (error) {
    console.error('Failed to delete user:', error)
  }
}

const createBackup = async () => {
  try {
    const response = await api.post('/backup/create')
    alert(response.data.message || 'Backup initiated successfully')
    await fetchBackups()
  } catch (error) {
    console.error('Failed to create backup:', error)
    const errorMessage = error.response?.data?.detail || 'Failed to create backup'
    alert(`Error: ${errorMessage}`)
  }
}

const restoreBackup = async (backupId) => {
  if (!confirm('Are you sure you want to restore this backup?')) return
  
  try {
    await api.post(`/backup/restore/${backupId}`)
    alert('Backup restored successfully')
  } catch (error) {
    console.error('Failed to restore backup:', error)
  }
}

const formatStorage = (mb) => {
  if (mb < 1024) return `${mb.toFixed(1)} MB`
  return `${(mb / 1024).toFixed(2)} GB`
}

const formatDate = (date) => {
  return new Date(date).toLocaleString()
}

const formatBackupDate = (date) => {
  const d = new Date(date)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const formatBackupTime = (date) => {
  const d = new Date(date)
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

const formatStatus = (status) => {
  const statusMap = {
    'completed': 'Completed',
    'failed': 'Failed',
    'in_progress': 'In Progress',
    'pending': 'Pending'
  }
  return statusMap[status] || status
}

const formatBackupSize = (sizeMb) => {
  if (!sizeMb) return '—'
  if (sizeMb < 1) return `${(sizeMb * 1024).toFixed(0)} KB`
  if (sizeMb < 1024) return `${sizeMb.toFixed(1)} MB`
  return `${(sizeMb / 1024).toFixed(2)} GB`
}

const formatDuration = (seconds) => {
  if (!seconds) return '—'
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes < 60) return `${minutes}m ${remainingSeconds}s`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours}h ${remainingMinutes}m`
}

const getLastBackupTime = () => {
  const completed = backups.value.filter(b => b.status === 'completed')
  if (completed.length === 0) return 'Never'
  // Append 'Z' to indicate UTC if not already present
  const dateStr = completed[0].created_at
  const lastBackup = new Date(dateStr.includes('Z') || dateStr.includes('+') ? dateStr : dateStr + 'Z')
  const now = new Date()
  const diffMs = now - lastBackup
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  if (diffHours < 1) return 'Just now'
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays === 1) return 'Yesterday'
  return `${diffDays} days ago`
}

const retryBackup = async (backupId) => {
  try {
    await api.post(`/backup/retry/${backupId}`)
    alert('Backup retry initiated')
    await fetchBackups()
  } catch (error) {
    console.error('Failed to retry backup:', error)
    alert('Failed to retry backup')
  }
}

const downloadBackup = async (backupId) => {
  try {
    const response = await api.get(`/backup/download/${backupId}`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `backup-${backupId}.tar.gz`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    console.error('Failed to download backup:', error)
    alert('Failed to download backup')
  }
}

const deleteBackup = async (backupId) => {
  if (!confirm('Are you sure you want to delete this backup?')) return
  
  try {
    await api.delete(`/backup/${backupId}`)
    await fetchBackups()
  } catch (error) {
    console.error('Failed to delete backup:', error)
    alert('Failed to delete backup')
  }
}

onMounted(() => {
  fetchStats()
  fetchUsers()
  fetchBackups()
})
</script>

<style scoped>
.admin {
  padding: 2rem;
}

h1 {
  color: #2c3e50;
  margin-bottom: 2rem;
}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat h3 {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.stat p {
  font-size: 2rem;
  font-weight: bold;
  color: #2c3e50;
}

.admin-sections {
  display: grid;
  gap: 2rem;
}

.users-section,
.backup-section {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

h2 {
  margin-bottom: 1rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

th,
td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

button {
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 0.5rem;
}

button.danger {
  background: #e74c3c;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  width: 400px;
}

.modal-content form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.modal-content input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

/* Backup Section Styles */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.primary-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.primary-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-icon {
  font-size: 1.25rem;
  font-weight: bold;
}

.backup-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.backup-stat {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.stat-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 1.25rem;
  font-weight: bold;
}

.stat-icon.success {
  background: #d4edda;
  color: #28a745;
}

.stat-icon.warning {
  background: #fff3cd;
  color: #ffc107;
}

.stat-icon.error {
  background: #f8d7da;
  color: #dc3545;
}

.stat-icon.info {
  background: #d1ecf1;
  color: #17a2b8;
}

.stat-details {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 1.5rem;
  font-weight: bold;
  color: #1e293b;
  line-height: 1;
}

.stat-label {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.backup-list {
  background: #f8fafc;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.backup-list-header {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1fr 1fr 1.5fr;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: #f1f5f9;
  border-bottom: 2px solid #e2e8f0;
  font-weight: 600;
  font-size: 0.875rem;
  color: #475569;
}

.backup-item {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1fr 1fr 1.5fr;
  gap: 1rem;
  padding: 1.25rem;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  transition: all 0.2s ease;
  align-items: center;
}

.backup-item:hover {
  background: #fafbfc;
  transform: translateX(2px);
}

.backup-item:last-child {
  border-bottom: none;
}

.backup-date {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.date-primary {
  font-weight: 600;
  color: #1e293b;
  font-size: 0.9rem;
}

.date-secondary {
  font-size: 0.75rem;
  color: #64748b;
}

.backup-status {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  width: fit-content;
}

.status-icon {
  font-size: 0.875rem;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.badge-completed {
  background: #d4edda;
  color: #155724;
}

.badge-failed {
  background: #f8d7da;
  color: #721c24;
}

.badge-in_progress {
  background: #fff3cd;
  color: #856404;
}

.badge-pending {
  background: #d1ecf1;
  color: #004085;
}

.error-message {
  font-size: 0.75rem;
  color: #dc3545;
  font-style: italic;
  margin-top: 0.25rem;
}

.backup-size {
  font-weight: 500;
  color: #475569;
  font-size: 0.9rem;
}

.backup-duration {
  font-weight: 500;
  color: #475569;
  font-size: 0.9rem;
}

.backup-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 1.1rem;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.action-btn.restore {
  color: #10b981;
}

.action-btn.restore:hover {
  background: #d4edda;
  border-color: #10b981;
}

.action-btn.retry {
  color: #f59e0b;
}

.action-btn.retry:hover {
  background: #fff3cd;
  border-color: #f59e0b;
}

.action-btn.download {
  color: #3b82f6;
}

.action-btn.download:hover {
  background: #dbeafe;
  border-color: #3b82f6;
}

.action-btn.delete {
  color: #ef4444;
}

.action-btn.delete:hover {
  background: #fee2e2;
  border-color: #ef4444;
}

.no-backups {
  padding: 3rem 2rem;
  text-align: center;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.5;
}

.empty-state p {
  font-size: 1.125rem;
  font-weight: 600;
  color: #475569;
  margin: 0;
}

.empty-state span {
  font-size: 0.875rem;
  color: #94a3b8;
}
</style>