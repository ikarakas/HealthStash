import { defineStore } from 'pinia'
import axios from 'axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    refreshToken: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin'
  },

  actions: {
    async login(username, password) {
      try {
        const formData = new FormData()
        formData.append('username', username)
        formData.append('password', password)
        
        const response = await axios.post('/api/auth/token', formData)
        
        this.token = response.data.access_token
        this.refreshToken = response.data.refresh_token
        
        localStorage.setItem('token', this.token)
        localStorage.setItem('refreshToken', this.refreshToken)
        
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        
        await this.fetchUser()
        
        return true
      } catch (error) {
        console.error('Login failed:', error)
        return false
      }
    },

    async register(userData) {
      try {
        const response = await axios.post('/api/auth/register', userData)
        
        this.token = response.data.access_token
        this.refreshToken = response.data.refresh_token
        
        localStorage.setItem('token', this.token)
        localStorage.setItem('refreshToken', this.refreshToken)
        
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        
        await this.fetchUser()
        
        return true
      } catch (error) {
        console.error('Registration failed:', error)
        return false
      }
    },

    async fetchUser() {
      try {
        const response = await axios.get('/api/users/me')
        this.user = response.data
      } catch (error) {
        console.error('Failed to fetch user:', error)
      }
    },

    async logout() {
      try {
        await axios.post('/api/auth/logout')
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        this.user = null
        this.token = null
        this.refreshToken = null
        
        localStorage.removeItem('token')
        localStorage.removeItem('refreshToken')
        
        delete axios.defaults.headers.common['Authorization']
      }
    },

    async refreshAccessToken() {
      try {
        const response = await axios.post('/api/auth/refresh', {
          refresh_token: this.refreshToken
        })
        
        this.token = response.data.access_token
        this.refreshToken = response.data.refresh_token
        
        localStorage.setItem('token', this.token)
        localStorage.setItem('refreshToken', this.refreshToken)
        
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        
        return true
      } catch (error) {
        console.error('Token refresh failed:', error)
        await this.logout()
        return false
      }
    },

    initializeAuth() {
      const token = localStorage.getItem('token')
      const refreshToken = localStorage.getItem('refreshToken')
      
      if (token) {
        this.token = token
        this.refreshToken = refreshToken
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        this.fetchUser()
      }
    }
  }
})