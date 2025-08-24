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
                <button 
                  v-if="user.role !== 'admin'" 
                  @click="updateUserRole(user.id, 'admin')" 
                  class="promote"
                  title="Promote to Admin"
                >
                  👑 Make Admin
                </button>
                <button 
                  v-else-if="user.role === 'admin' && user.id !== currentUserId" 
                  @click="updateUserRole(user.id, 'user')" 
                  class="demote"
                  title="Remove Admin Rights"
                >
                  👤 Make User
                </button>
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
            <span>Type</span>
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
            <div class="backup-type">
              <span class="type-badge" :class="backup.source === 'automatic' ? 'type-auto' : 'type-manual'">
                {{ backup.source === 'automatic' ? '🤖 Auto' : '👤 Manual' }}
              </span>
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
          
          <div class="password-field">
            <div class="password-input-wrapper">
              <input 
                v-model="newUser.password" 
                :type="showPassword ? 'text' : 'password'"
                placeholder="Password" 
                required
                @input="checkPasswordStrength(newUser.password)"
              />
              <button type="button" class="password-toggle" @click="togglePasswordVisibility">
                {{ showPassword ? '👁️' : '👁️‍🗨️' }}
              </button>
            </div>
            
            <div class="password-actions">
              <button type="button" class="generate-btn" @click="generatePassword">
                🔐 Generate Strong Password
              </button>
              <button 
                v-if="newUser.password" 
                type="button" 
                class="copy-btn"
                @click="copyPassword"
              >
                {{ copiedPassword ? '✓ Copied!' : '📋 Copy' }}
              </button>
            </div>
            
            <div v-if="passwordStrength" class="password-strength">
              <span class="strength-label">Strength:</span>
              <span :class="['strength-indicator', `strength-${passwordStrength}`]">
                {{ passwordStrength.charAt(0).toUpperCase() + passwordStrength.slice(1) }}
              </span>
            </div>
            
            <div class="password-requirements">
              <small>Requirements:</small>
              <ul>
                <li :class="{ met: newUser.password.length >= 12 }">At least 12 characters</li>
                <li :class="{ met: /[A-Z]/.test(newUser.password) }">One uppercase letter</li>
                <li :class="{ met: /[a-z]/.test(newUser.password) }">One lowercase letter</li>
                <li :class="{ met: /[0-9]/.test(newUser.password) }">One number</li>
                <li :class="{ met: /[^A-Za-z0-9]/.test(newUser.password) }">One special character</li>
              </ul>
            </div>
          </div>
          
          <button type="submit" class="create-user-btn">Create User</button>
          <button type="button" class="cancel-btn" @click="showCreateUser = false">Cancel</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../services/axios'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const stats = ref({})
const users = ref([])
const backups = ref([])
const showCreateUser = ref(false)
const backupSystemStatus = ref(null)

// Get current user ID from auth store
const currentUserId = computed(() => authStore.user?.id)

const newUser = ref({
  email: '',
  username: '',
  full_name: '',
  password: ''
})

const showPassword = ref(false)
const passwordStrength = ref('')
const copiedPassword = ref(false)

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
  // Validate all fields are filled
  if (!newUser.value.email || !newUser.value.username || 
      !newUser.value.full_name || !newUser.value.password) {
    alert('Please fill in all fields')
    return
  }
  
  // Validate email format
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(newUser.value.email)) {
    alert('Please enter a valid email address')
    return
  }
  
  // Validate password strength
  if (newUser.value.password.length < 12) {
    alert('Password must be at least 12 characters long')
    return
  }
  
  try {
    await api.post('/admin/users', newUser.value)
    showCreateUser.value = false
    newUser.value = { email: '', username: '', full_name: '', password: '' }
    passwordStrength.value = ''
    showPassword.value = false
    await fetchUsers()
    alert('User created successfully')
  } catch (error) {
    console.error('Failed to create user:', error)
    let errorMessage = 'Failed to create user'
    
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.response?.status === 400) {
      errorMessage = 'User with this email or username already exists'
    } else if (error.response?.status === 401) {
      errorMessage = 'You are not authorized to create users'
    } else if (error.response?.status === 403) {
      errorMessage = 'Admin privileges required'
    } else if (error.message) {
      errorMessage = error.message
    }
    
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

const updateUserRole = async (userId, newRole) => {
  const action = newRole === 'admin' ? 'promote to admin' : 'demote to regular user'
  if (!confirm(`Are you sure you want to ${action} this user?`)) return
  
  try {
    await api.put(`/admin/users/${userId}/role`, { role: newRole })
    await fetchUsers()
    alert(`User role updated to ${newRole}`)
  } catch (error) {
    console.error('Failed to update user role:', error)
    const errorMessage = error.response?.data?.detail || 'Failed to update user role'
    alert(`Error: ${errorMessage}`)
  }
}

const createBackup = async () => {
  try {
    const response = await api.post('/backup/create')
    const message = response.data.message || 'Backup initiated successfully'
    const details = response.data.includes ? `\nIncludes: ${response.data.includes.join(', ')}` : ''
    alert(message + details)
    
    // Refresh backup list after a short delay to show the new backup
    setTimeout(() => fetchBackups(), 2000)
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
  if (!date) return '—'
  try {
    const d = new Date(date)
    if (isNaN(d.getTime())) return '—'
    return d.toLocaleString()
  } catch (error) {
    return '—'
  }
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
  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffMinutes < 5) return 'Just now'
  if (diffMinutes < 60) return `${diffMinutes} minutes ago`
  if (diffHours === 1) return '1 hour ago'
  if (diffHours < 24) return `${diffHours} hours ago`
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 14) return 'Last week'
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
  if (diffDays < 60) return 'Last month'
  return `${Math.floor(diffDays / 30)} months ago`
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

const generatePassword = () => {
  const length = 16
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  const lowercase = 'abcdefghijklmnopqrstuvwxyz'
  const numbers = '0123456789'
  const symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?'
  
  const allChars = uppercase + lowercase + numbers + symbols
  let password = ''
  
  password += uppercase.charAt(Math.floor(Math.random() * uppercase.length))
  password += lowercase.charAt(Math.floor(Math.random() * lowercase.length))
  password += numbers.charAt(Math.floor(Math.random() * numbers.length))
  password += symbols.charAt(Math.floor(Math.random() * symbols.length))
  
  for (let i = 4; i < length; i++) {
    password += allChars.charAt(Math.floor(Math.random() * allChars.length))
  }
  
  password = password.split('').sort(() => Math.random() - 0.5).join('')
  
  newUser.value.password = password
  checkPasswordStrength(password)
}

const checkPasswordStrength = (password) => {
  if (!password) {
    passwordStrength.value = ''
    return
  }
  
  let strength = 0
  
  if (password.length >= 12) strength++
  if (password.length >= 16) strength++
  if (/[a-z]/.test(password)) strength++
  if (/[A-Z]/.test(password)) strength++
  if (/[0-9]/.test(password)) strength++
  if (/[^A-Za-z0-9]/.test(password)) strength++
  
  if (strength <= 2) passwordStrength.value = 'weak'
  else if (strength <= 4) passwordStrength.value = 'medium'
  else passwordStrength.value = 'strong'
}

const copyPassword = async () => {
  try {
    await navigator.clipboard.writeText(newUser.value.password)
    copiedPassword.value = true
    setTimeout(() => {
      copiedPassword.value = false
    }, 2000)
  } catch (error) {
    console.error('Failed to copy password:', error)
  }
}

const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
}

const fetchBackupStatus = async () => {
  try {
    const response = await api.get('/backup/status')
    backupSystemStatus.value = response.data
  } catch (error) {
    console.error('Failed to fetch backup status:', error)
  }
}

onMounted(() => {
  fetchStats()
  fetchUsers()
  fetchBackups()
  fetchBackupStatus()
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

button.promote {
  background: linear-gradient(135deg, #ffd700 0%, #ffb347 100%);
  color: #333;
  font-weight: 600;
}

button.promote:hover {
  background: linear-gradient(135deg, #ffcc00 0%, #ff9f00 100%);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.3);
}

button.demote {
  background: #6c757d;
  color: white;
}

button.demote:hover {
  background: #5a6268;
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
  grid-template-columns: 2fr 1fr 1.2fr 1fr 1fr 1.5fr;
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
  grid-template-columns: 2fr 1fr 1.2fr 1fr 1fr 1.5fr;
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

/* Enhanced Password Field Styles */
.password-field {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.password-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.password-input-wrapper input {
  padding-right: 2.5rem;
}

.password-toggle {
  position: absolute;
  right: 0.5rem;
  background: transparent;
  border: none;
  padding: 0.25rem;
  cursor: pointer;
  font-size: 1.2rem;
  margin: 0;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.password-toggle:hover {
  opacity: 1;
}

.password-actions {
  display: flex;
  gap: 0.5rem;
}

.generate-btn,
.copy-btn {
  flex: 1;
  padding: 0.5rem 0.75rem;
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin: 0;
}

.generate-btn:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.copy-btn:hover {
  background: #10b981;
  color: white;
  border-color: #10b981;
}

.password-strength {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f9fafb;
  border-radius: 6px;
}

.strength-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.strength-indicator {
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.strength-weak {
  background: #fee2e2;
  color: #dc2626;
}

.strength-medium {
  background: #fef3c7;
  color: #d97706;
}

.strength-strong {
  background: #d1fae5;
  color: #059669;
}

.password-requirements {
  background: #f9fafb;
  padding: 0.75rem;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.password-requirements small {
  display: block;
  color: #6b7280;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.password-requirements ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.password-requirements li {
  font-size: 0.75rem;
  color: #9ca3af;
  padding-left: 1.25rem;
  position: relative;
}

.password-requirements li::before {
  content: '✗';
  position: absolute;
  left: 0;
  color: #ef4444;
}

.password-requirements li.met {
  color: #059669;
}

.password-requirements li.met::before {
  content: '✓';
  color: #059669;
}

.create-user-btn {
  width: 100%;
  padding: 0.75rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 0.5rem;
}

.create-user-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.cancel-btn {
  width: 100%;
  padding: 0.75rem;
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin: 0;
}

.cancel-btn:hover {
  background: #e5e7eb;
}

/* Backup Type Badge Styles */
.backup-type {
  display: flex;
  align-items: center;
}

.type-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.625rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.type-auto {
  background: #e0f2fe;
  color: #0369a1;
  border: 1px solid #7dd3fc;
}

.type-manual {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fde68a;
}
</style>