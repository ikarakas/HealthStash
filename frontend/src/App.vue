<template>
  <div id="app">
    <header v-if="isAuthenticated" class="app-header">
      <div class="header-container">
        <router-link to="/dashboard" class="logo-container">
          <img src="@/assets/logo.svg" alt="HealthStash" class="logo" />
        </router-link>
        
        <div class="header-info">
          <div class="user-info">
            <span class="user-icon">👤</span>
            <span class="username">{{ userDisplay }}</span>
          </div>
          <div class="system-info">
            <span class="info-item">⏱️ Uptime: {{ uptime }}</span>
            <span class="info-item">📦 v{{ version }}</span>
          </div>
        </div>
      </div>
    </header>
    
    <nav v-if="isAuthenticated" class="navbar">
      <div class="nav-container">
        <div class="nav-links">
          <router-link to="/dashboard">🏠 Dashboard</router-link>
          <router-link to="/records">📁 Records</router-link>
          <router-link to="/vitals">💓 Vitals</router-link>
          <router-link to="/upload">📤 Upload</router-link>
          <router-link to="/mobile-upload">📱 Mobile Upload</router-link>
          <router-link v-if="isAdmin" to="/admin">⚙️ Admin</router-link>
          <button @click="logout" class="logout-btn">🚪 Logout</button>
        </div>
      </div>
    </nav>
    
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)
const isAdmin = computed(() => authStore.user?.role === 'admin')
const userDisplay = computed(() => {
  if (authStore.user) {
    return authStore.user.full_name || authStore.user.username || authStore.user.email
  }
  return 'Guest'
})

const version = ref('0.0.2')
const startTime = ref(Date.now())
const uptime = ref('0m')

// Update uptime every minute
onMounted(() => {
  const updateUptime = () => {
    const now = Date.now()
    const diff = Math.floor((now - startTime.value) / 1000)
    const days = Math.floor(diff / 86400)
    const hours = Math.floor((diff % 86400) / 3600)
    const minutes = Math.floor((diff % 3600) / 60)
    
    if (days > 0) {
      uptime.value = `${days}d ${hours}h`
    } else if (hours > 0) {
      uptime.value = `${hours}h ${minutes}m`
    } else {
      uptime.value = `${minutes}m`
    }
  }
  
  updateUptime()
  setInterval(updateUptime, 60000) // Update every minute
})

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background-color: #f5f7fa;
  color: #333;
}

/* Header */
.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.header-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-container {
  text-decoration: none;
}

.logo {
  height: 50px;
  width: auto;
}

.header-info {
  display: flex;
  gap: 2rem;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.2);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  backdrop-filter: blur(10px);
}

.user-icon {
  font-size: 1.2rem;
}

.username {
  font-weight: 500;
}

.system-info {
  display: flex;
  gap: 1rem;
}

.info-item {
  font-size: 0.875rem;
  opacity: 0.9;
}

/* Navigation */
.navbar {
  background-color: white;
  padding: 0.75rem 0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  border-bottom: 1px solid #e2e8f0;
}

.nav-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  justify-content: center;
  align-items: center;
}

.nav-links {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.nav-links a {
  color: #4a5568;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: all 0.2s;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.nav-links a:hover {
  background: #f7fafc;
  color: #667eea;
}

.nav-links a.router-link-active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.logout-btn {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.logout-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

main {
  max-width: 1400px;
  margin: 2rem auto;
  padding: 0 1rem;
}
</style>