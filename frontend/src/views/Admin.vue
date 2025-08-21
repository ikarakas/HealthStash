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
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.username }}</td>
              <td>{{ user.email }}</td>
              <td>{{ user.role }}</td>
              <td>{{ formatStorage(user.storage_used_mb) }} / {{ formatStorage(user.storage_quota_mb) }}</td>
              <td>
                <button @click="resetPassword(user.id)">Reset Password</button>
                <button @click="deleteUser(user.id)" class="danger">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div class="backup-section">
        <h2>Backup Management</h2>
        <button @click="createBackup">Create Backup Now</button>
        
        <div v-if="backups.length > 0" class="backup-list">
          <div v-for="backup in backups" :key="backup.id" class="backup-item">
            <span>{{ formatDate(backup.created_at) }}</span>
            <span>{{ backup.status }}</span>
            <button v-if="backup.status === 'completed'" @click="restoreBackup(backup.id)">
              Restore
            </button>
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
</style>