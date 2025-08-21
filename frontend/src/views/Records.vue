<template>
  <div class="records">
    <h1>Health Records</h1>
    
    <div class="filters">
      <select v-model="filters.category" @change="fetchRecords">
        <option value="">All Categories</option>
        <option value="lab_results">Lab Results</option>
        <option value="imaging">Imaging</option>
        <option value="clinical_notes">Clinical Notes</option>
        <option value="prescriptions">Prescriptions</option>
        <option value="vaccinations">Vaccinations</option>
        <option value="personal_notes">Personal Notes</option>
      </select>
      
      <div class="search-container">
        <input
          v-model="filters.search"
          type="text"
          placeholder="Search records..."
          @keyup.enter="fetchRecords"
        />
        <button v-if="filters.search" @click="clearSearch" class="clear-search">✕</button>
      </div>
      
      <select v-model="filters.sortBy" @change="fetchRecords">
        <option value="created_at_desc">Newest First</option>
        <option value="created_at_asc">Oldest First</option>
        <option value="service_date_desc">Service Date (Recent)</option>
        <option value="service_date_asc">Service Date (Oldest)</option>
        <option value="title_asc">Title (A-Z)</option>
        <option value="title_desc">Title (Z-A)</option>
      </select>
      
      <button @click="fetchRecords" class="search-btn">🔍 Search</button>
      
      <div class="view-toggle">
        <button @click="viewMode = 'list'" :class="{ active: viewMode === 'list' }">📋 List</button>
        <button @click="viewMode = 'grid'" :class="{ active: viewMode === 'grid' }">🎴 Grid</button>
        <button @click="viewMode = 'compact'" :class="{ active: viewMode === 'compact' }">📊 Compact</button>
      </div>
    </div>
    
    <div v-if="activeFilters.length > 0" class="active-filters">
      <span class="filter-label">Active filters:</span>
      <span v-for="filter in activeFilters" :key="filter" class="filter-tag">
        {{ filter }}
        <button @click="removeFilter(filter)">✕</button>
      </span>
    </div>
    
    <div class="records-container" :class="viewMode">
      <div v-if="loading" class="loading">Loading records...</div>
      
      <div v-else-if="records.length === 0" class="empty">
        No records found
      </div>
      
      <div v-else-if="viewMode === 'compact'" class="compact-table">
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Category</th>
              <th>Provider</th>
              <th>Service Date</th>
              <th>Upload Date</th>
              <th>Size</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in paginatedRecords" :key="record.id">
              <td class="title-cell">
                <span class="file-icon">{{ getFileIcon(record.file_type) }}</span>
                <span v-if="!record.editingTitle" @dblclick="startEditTitle(record)" class="title-text">
                  {{ record.title }}
                  <button @click="startEditTitle(record)" class="edit-title-btn-compact" title="Edit">✏️</button>
                </span>
                <div v-else class="title-editor-compact">
                  <input 
                    v-model="record.tempTitle" 
                    @keyup.enter="saveTitle(record)"
                    @keyup.esc="cancelEditTitle(record)"
                    class="title-input-compact"
                  />
                  <button @click="saveTitle(record)" class="save-btn-compact">✅</button>
                  <button @click="cancelEditTitle(record)" class="cancel-btn-compact">❌</button>
                </div>
              </td>
              <td>
                <span class="compact-category" :style="getCategoryStyle(record.category)">
                  {{ formatCategory(record.category) }}
                </span>
              </td>
              <td>{{ record.provider_name || '-' }}</td>
              <td>{{ record.service_date ? formatCompactDate(record.service_date) : '-' }}</td>
              <td>{{ record.created_at ? formatCompactDate(record.created_at) : '-' }}</td>
              <td>{{ formatFileSize(record.file_size) }}</td>
              <td class="actions-cell">
                <button @click="downloadRecord(record.id)" class="compact-btn download" title="Download">⬇️</button>
                <button @click="deleteRecord(record.id)" class="compact-btn delete" title="Delete">🗑️</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div v-else class="records-wrapper">
        <div v-for="record in paginatedRecords" :key="record.id" class="record-card" :class="{ 'has-thumbnail': record.has_thumbnail }">
          <!-- Thumbnail Preview -->
          <div v-if="viewMode === 'grid'" class="thumbnail-container">
            <div v-if="record.thumbnail" class="thumbnail">
              <img :src="record.thumbnail" :alt="record.title" />
            </div>
            <button v-else-if="record.has_thumbnail" @click="loadThumbnail(record)" class="load-thumbnail">
              👁️ Load Preview
            </button>
            <div v-else class="no-thumbnail">
              {{ getFileIcon(record.file_type) }}
            </div>
          </div>
          
          <!-- Peek Button for List View -->
          <div v-if="viewMode === 'list' && record.file_type?.startsWith('image/')" class="peek-container">
            <button @click.stop="togglePeek(record)" class="peek-btn" :class="{ active: record.showPeek }">
              {{ record.showPeek ? '🙈' : '👀' }}
            </button>
            <div v-if="record.showPeek" class="peek-preview" @click.stop>
              <button @click="togglePeek(record)" class="close-peek">✕</button>
              <img v-if="record.thumbnail && !record.thumbnailError" :src="record.thumbnail" :alt="record.title" @error="handleImageError(record)" />
              <div v-else-if="record.loadingThumbnail" class="loading-thumbnail">
                <span>⏳ Loading...</span>
              </div>
              <div v-else-if="record.thumbnailError" class="error-state">
                <span>❌ Failed to load image</span>
                <button @click="loadThumbnail(record)" class="retry-btn">Retry</button>
              </div>
              <button v-else @click="loadThumbnail(record)" class="load-image-btn">Load Image</button>
            </div>
          </div>
          
          <div class="record-content">
            <div class="title-section">
              <h3 v-if="!record.editingTitle" @dblclick="startEditTitle(record)">
                {{ record.title }}
                <button @click="startEditTitle(record)" class="edit-title-btn" title="Edit title">✏️</button>
              </h3>
              <div v-else class="title-editor">
                <input 
                  v-model="record.tempTitle" 
                  @keyup.enter="saveTitle(record)"
                  @keyup.esc="cancelEditTitle(record)"
                  ref="titleInput"
                  class="title-input"
                />
                <button @click="saveTitle(record)" class="save-btn" title="Save">✅</button>
                <button @click="cancelEditTitle(record)" class="cancel-btn" title="Cancel">❌</button>
              </div>
            </div>
            
            <!-- Categories with Edit -->
            <div class="categories-section">
              <div v-if="!record.editingCategories" class="category-tags">
                <span v-for="cat in (record.categories || [record.category])" :key="cat" class="category-tag" :style="getCategoryStyle(cat)">
                  {{ formatCategory(cat) }}
                </span>
                <button @click="startEditCategories(record)" class="edit-categories">✏️</button>
              </div>
              <div v-else class="category-editor">
                <select v-model="record.tempCategories" multiple size="4">
                  <option value="lab_results">Lab Results</option>
                  <option value="imaging">Imaging</option>
                  <option value="clinical_notes">Clinical Notes</option>
                  <option value="prescriptions">Prescriptions</option>
                  <option value="vaccinations">Vaccinations</option>
                  <option value="personal_notes">Personal Notes</option>
                  <option value="vital_signs">Vital Signs</option>
                  <option value="other">Other</option>
                </select>
                <div class="category-actions">
                  <button @click="saveCategories(record)">✅ Save</button>
                  <button @click="cancelEditCategories(record)">❌ Cancel</button>
                </div>
              </div>
            </div>
            
            <div class="record-meta">
              <p class="date">📅 Uploaded: {{ formatDate(record.created_at) }}</p>
              <p v-if="record.service_date" class="service-date">🏥 Service: {{ formatDate(record.service_date) }}</p>
              <p v-if="record.provider_name" class="provider">👨‍⚕️ {{ record.provider_name }}</p>
              <p v-if="record.file_size" class="size">💾 {{ formatFileSize(record.file_size) }}</p>
            </div>
            
            <div class="actions">
              <button @click="downloadRecord(record.id)" class="primary">⬇️ Download</button>
              <button @click="deleteRecord(record.id)" class="danger">🗑️ Delete</button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pagination">
        <button @click="currentPage = 1" :disabled="currentPage === 1">⏮️</button>
        <button @click="currentPage--" :disabled="currentPage === 1">◀️</button>
        <span class="page-info">Page {{ currentPage }} of {{ totalPages }}</span>
        <button @click="currentPage++" :disabled="currentPage === totalPages">▶️</button>
        <button @click="currentPage = totalPages" :disabled="currentPage === totalPages">⏭️</button>
        
        <select v-model.number="itemsPerPage" @change="currentPage = 1" class="items-per-page">
          <option :value="10">10 per page</option>
          <option :value="20">20 per page</option>
          <option :value="50">50 per page</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import api from '../services/axios'

const records = ref([])
const loading = ref(false)
const viewMode = ref('list')
const currentPage = ref(1)
const itemsPerPage = ref(20)

const filters = ref({
  category: '',
  search: '',
  sortBy: 'created_at_desc'
})

// Computed properties
const activeFilters = computed(() => {
  const active = []
  if (filters.value.category) active.push(`Category: ${formatCategory(filters.value.category)}`)
  if (filters.value.search) active.push(`Search: "${filters.value.search}"`)
  return active
})

const sortedRecords = computed(() => {
  const sorted = [...records.value]
  const [field, order] = filters.value.sortBy.split('_')
  
  sorted.sort((a, b) => {
    let aVal = field === 'title' ? a.title : (a[field] || '')
    let bVal = field === 'title' ? b.title : (b[field] || '')
    
    if (order === 'desc') {
      return aVal > bVal ? -1 : 1
    } else {
      return aVal < bVal ? -1 : 1
    }
  })
  
  return sorted
})

const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return sortedRecords.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(sortedRecords.value.length / itemsPerPage.value)
})

// Methods
const fetchRecords = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.category) params.category = filters.value.category
    if (filters.value.search) params.search = filters.value.search
    
    const response = await api.get('/records', { params })
    records.value = response.data.records.map(r => ({
      ...r,
      editingCategories: false,
      showPeek: false,
      loadingThumbnail: false,
      tempCategories: r.categories || [r.category]
    }))
    currentPage.value = 1
  } catch (error) {
    console.error('Failed to fetch records:', error)
  } finally {
    loading.value = false
  }
}

const clearSearch = () => {
  filters.value.search = ''
  fetchRecords()
}

const removeFilter = (filter) => {
  if (filter.startsWith('Category:')) {
    filters.value.category = ''
  } else if (filter.startsWith('Search:')) {
    filters.value.search = ''
  }
  fetchRecords()
}

const downloadRecord = async (recordId) => {
  try {
    // First, get the filename from our records
    const record = records.value.find(r => r.id === recordId)
    const fallbackFileName = record?.file_name || 'download'
    
    const response = await api.get(`/files/download/${recordId}`, {
      responseType: 'blob'
    })
    
    // Get content type from response
    const contentType = response.headers['content-type'] || 'application/octet-stream'
    
    // Create blob with correct content type
    const blob = new Blob([response.data], { type: contentType })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // Try to extract filename from Content-Disposition header
    let fileName = fallbackFileName
    const contentDisposition = response.headers['content-disposition']
    if (contentDisposition) {
      // Match filename with or without quotes
      const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition)
      if (matches && matches[1]) {
        fileName = matches[1].replace(/['"]/g, '')
      }
    }
    
    link.setAttribute('download', fileName)
    document.body.appendChild(link)
    link.click()
    
    // Cleanup
    setTimeout(() => {
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    }, 100)
  } catch (error) {
    console.error('Failed to download:', error)
    alert('Failed to download file')
  }
}

const deleteRecord = async (recordId) => {
  if (!confirm('Are you sure you want to delete this record?')) return
  
  try {
    await api.delete(`/files/${recordId}`)
    await fetchRecords()
  } catch (error) {
    console.error('Failed to delete:', error)
  }
}

// Title management
const startEditTitle = (record) => {
  record.editingTitle = true
  record.tempTitle = record.title
  // Focus the input after Vue updates the DOM
  nextTick(() => {
    const input = document.querySelector('.title-input, .title-input-compact')
    if (input) input.focus()
  })
}

const cancelEditTitle = (record) => {
  record.editingTitle = false
  record.tempTitle = record.title
}

const saveTitle = async (record) => {
  if (!record.tempTitle || record.tempTitle.trim() === '') {
    alert('Title cannot be empty')
    return
  }
  
  try {
    await api.patch(`/records/${record.id}/title`, {
      title: record.tempTitle.trim()
    })
    record.title = record.tempTitle.trim()
    record.editingTitle = false
  } catch (error) {
    console.error('Failed to update title:', error)
    alert('Failed to update title')
  }
}

// Category management
const startEditCategories = (record) => {
  record.editingCategories = true
  record.tempCategories = [...(record.categories || [record.category])]
}

const cancelEditCategories = (record) => {
  record.editingCategories = false
  record.tempCategories = record.categories || [record.category]
}

const saveCategories = async (record) => {
  try {
    await api.patch(`/records/${record.id}/categories`, {
      categories: record.tempCategories
    })
    record.categories = record.tempCategories
    record.editingCategories = false
  } catch (error) {
    console.error('Failed to update categories:', error)
    alert('Failed to update categories')
  }
}

const getCategoryStyle = (category) => {
  const colors = {
    lab_results: { bg: '#e3f2fd', color: '#1976d2' },
    imaging: { bg: '#f3e5f5', color: '#7b1fa2' },
    clinical_notes: { bg: '#e8f5e9', color: '#388e3c' },
    prescriptions: { bg: '#fff3e0', color: '#f57c00' },
    vaccinations: { bg: '#fce4ec', color: '#c2185b' },
    personal_notes: { bg: '#f5f5f5', color: '#616161' },
    vital_signs: { bg: '#e0f2f1', color: '#00796b' },
    other: { bg: '#eceff1', color: '#455a64' }
  }
  const style = colors[category] || colors.other
  return {
    backgroundColor: style.bg,
    color: style.color
  }
}

// Thumbnail management
const togglePeek = (record) => {
  // Toggle the peek state
  record.showPeek = !record.showPeek
  
  // If showing peek and no thumbnail loaded yet, load it
  if (record.showPeek && !record.thumbnail && !record.loadingThumbnail) {
    loadThumbnail(record)
  }
}

const loadThumbnail = async (record) => {
  record.loadingThumbnail = true
  record.thumbnailError = false // Reset error state
  
  // Make sure we have a valid record ID
  if (!record.id) {
    console.error('No record ID available')
    record.thumbnailError = true
    record.loadingThumbnail = false
    return
  }
  
  try {
    const response = await api.get(`/records/${record.id}/thumbnail`)
    
    // Log the response for debugging
    console.log('Thumbnail response:', response.data)
    
    // Check if we got a valid response
    if (response.data && response.data.thumbnail) {
      // Validate it's a proper data URL
      if (response.data.thumbnail.startsWith('data:image')) {
        record.thumbnail = response.data.thumbnail
        record.thumbnailError = false
        console.log('Thumbnail loaded successfully')
      } else {
        console.error('Invalid thumbnail format:', response.data.thumbnail.substring(0, 50))
        record.thumbnail = null
        record.thumbnailError = true
      }
    } else {
      console.error('No thumbnail data in response')
      record.thumbnail = null
      record.thumbnailError = true
    }
  } catch (error) {
    console.error('Failed to load thumbnail for record:', record.id, error)
    
    // Check if it's an HTML response (nginx error page)
    if (error.response && error.response.data && typeof error.response.data === 'string' && error.response.data.includes('<!DOCTYPE')) {
      console.error('Received HTML error page instead of JSON - likely a routing issue')
    }
    
    record.thumbnail = null
    record.thumbnailError = true
  } finally {
    record.loadingThumbnail = false
  }
}

const handleImageError = (record) => {
  console.error('Image failed to load for record:', record.id)
  record.thumbnailError = true
  record.thumbnail = null
}

const getFileIcon = (fileType) => {
  if (!fileType) return '📄'
  if (fileType.includes('pdf')) return '📕'
  if (fileType.includes('image')) return '🖼️'
  if (fileType.includes('word') || fileType.includes('doc')) return '📘'
  if (fileType.includes('excel') || fileType.includes('sheet')) return '📊'
  if (fileType.includes('text')) return '📝'
  return '📄'
}

const formatCategory = (category) => {
  if (!category) return ''
  return category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatDate = (date) => {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatCompactDate = (date) => {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

const formatFileSize = (bytes) => {
  if (!bytes) return 'N/A'
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  if (bytes === 0) return '0 Bytes'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

onMounted(() => {
  fetchRecords()
})
</script>

<style scoped>
.records {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

h1 {
  color: #1a202c;
  margin-bottom: 2rem;
  font-size: 2rem;
  font-weight: 600;
}

/* Filters Section */
.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  align-items: center;
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filters select {
  padding: 0.625rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  background: white;
  font-size: 0.95rem;
  transition: all 0.2s;
  cursor: pointer;
  min-width: 150px;
}

.filters select:hover {
  border-color: #cbd5e0;
}

.filters select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-container {
  position: relative;
  flex: 1;
  min-width: 250px;
}

.search-container input {
  width: 100%;
  padding: 0.625rem 2.5rem 0.625rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  transition: all 0.2s;
}

.search-container input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.clear-search {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: background 0.2s;
}

.clear-search:hover {
  background: #dc2626;
}

.search-btn {
  padding: 0.625rem 1.25rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.search-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.view-toggle {
  display: flex;
  gap: 0.5rem;
  margin-left: auto;
}

.view-toggle button {
  padding: 0.5rem 1rem;
  border: 2px solid #e2e8f0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.view-toggle button.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

/* Active Filters */
.active-filters {
  margin-bottom: 1rem;
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.filter-label {
  font-size: 0.875rem;
  color: #64748b;
  font-weight: 500;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  background: #f1f5f9;
  border-radius: 20px;
  font-size: 0.875rem;
  color: #475569;
}

.filter-tag button {
  background: #e2e8f0;
  border: none;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  transition: background 0.2s;
}

.filter-tag button:hover {
  background: #cbd5e0;
}

/* Records Container */
.records-container {
  min-height: 400px;
}

.records-wrapper {
  display: grid;
  gap: 1.5rem;
}

.records-container.list .records-wrapper {
  grid-template-columns: 1fr;
}

.records-container.grid .records-wrapper {
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

/* Record Card */
.record-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.3s;
  position: relative;
}

.record-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.list .record-card {
  display: flex;
  padding: 1.5rem;
  gap: 1.5rem;
}

.grid .record-card {
  display: flex;
  flex-direction: column;
}

/* Thumbnail */
.thumbnail-container {
  width: 100%;
  height: 200px;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-thumbnail {
  font-size: 3rem;
  color: #cbd5e0;
}

.load-thumbnail {
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.load-thumbnail:hover {
  background: #5a67d8;
}

/* Peek Preview */
.peek-container {
  position: relative;
  margin-right: 1rem;
  display: flex;
  align-items: center;
}

.peek-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid #e2e8f0;
  background: white;
  cursor: pointer;
  font-size: 1.25rem;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.peek-btn:hover {
  border-color: #667eea;
  transform: scale(1.1);
}

.peek-btn.active {
  background: #667eea;
  border-color: #667eea;
}

.peek-preview {
  position: absolute;
  top: 50px;
  left: 0;
  z-index: 100;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
  padding: 0.75rem;
  width: 350px;
  height: 350px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.peek-preview img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 8px;
  background: #f8fafc;
}

.close-peek {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #ef4444;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  z-index: 1;
}

.close-peek:hover {
  background: #dc2626;
  transform: scale(1.1);
}

.load-image-btn {
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: background 0.2s;
}

.load-image-btn:hover {
  background: #5a67d8;
}

.loading-thumbnail {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 0.875rem;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  color: #ef4444;
  font-size: 0.875rem;
}

.retry-btn {
  padding: 0.375rem 0.75rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #dc2626;
}

/* Record Content */
.record-content {
  flex: 1;
  padding: 1.5rem;
}

.grid .record-content {
  padding: 1rem;
}

.record-content h3 {
  margin: 0 0 1rem 0;
  color: #1a202c;
  font-size: 1.25rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Title editing */
.title-section {
  margin-bottom: 1rem;
}

.edit-title-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 0.875rem;
  opacity: 0;
  transition: opacity 0.2s;
  padding: 0.25rem;
}

.record-card:hover .edit-title-btn {
  opacity: 0.6;
}

.edit-title-btn:hover {
  opacity: 1 !important;
}

.title-editor {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.title-input {
  flex: 1;
  padding: 0.5rem;
  border: 2px solid #667eea;
  border-radius: 6px;
  font-size: 1.125rem;
  font-weight: 600;
}

.title-input:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.save-btn, .cancel-btn {
  padding: 0.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.save-btn {
  background: #10b981;
  color: white;
}

.save-btn:hover {
  background: #059669;
}

.cancel-btn {
  background: #ef4444;
  color: white;
}

.cancel-btn:hover {
  background: #dc2626;
}

/* Compact view title editing */
.title-text {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.edit-title-btn-compact {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 0.75rem;
  opacity: 0;
  transition: opacity 0.2s;
  padding: 0;
}

tr:hover .edit-title-btn-compact {
  opacity: 0.6;
}

.edit-title-btn-compact:hover {
  opacity: 1 !important;
}

.title-editor-compact {
  display: inline-flex;
  gap: 0.25rem;
  align-items: center;
}

.title-input-compact {
  padding: 0.25rem 0.5rem;
  border: 2px solid #667eea;
  border-radius: 4px;
  font-size: 0.875rem;
  min-width: 200px;
}

.save-btn-compact, .cancel-btn-compact {
  padding: 0.25rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.2s;
}

.save-btn-compact {
  background: #10b981;
}

.cancel-btn-compact {
  background: #ef4444;
}

/* Categories */
.categories-section {
  margin-bottom: 1rem;
}

.category-tags {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.category-tag {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.edit-categories {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.25rem;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.edit-categories:hover {
  opacity: 1;
}

.category-editor select {
  width: 100%;
  padding: 0.5rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.category-actions {
  display: flex;
  gap: 0.5rem;
}

.category-actions button {
  padding: 0.375rem 0.75rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.category-actions button:first-child {
  background: #10b981;
  color: white;
}

.category-actions button:last-child {
  background: #ef4444;
  color: white;
}

/* Record Meta */
.record-meta {
  margin-bottom: 1rem;
}

.record-meta p {
  margin: 0.375rem 0;
  color: #64748b;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Actions */
.actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}

.actions button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.actions button.primary {
  background: #667eea;
  color: white;
}

.actions button.primary:hover {
  background: #5a67d8;
}

.actions button.danger {
  background: #ef4444;
  color: white;
}

.actions button.danger:hover {
  background: #dc2626;
}

/* Pagination */
.pagination {
  margin-top: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.pagination button {
  padding: 0.5rem 0.75rem;
  border: 2px solid #e2e8f0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 1rem;
}

.pagination button:hover:not(:disabled) {
  border-color: #667eea;
  background: #f0f4ff;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  padding: 0.5rem 1rem;
  background: #f8fafc;
  border-radius: 8px;
  font-size: 0.875rem;
  color: #64748b;
  font-weight: 500;
}

.items-per-page {
  padding: 0.5rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  background: white;
  margin-left: auto;
}

/* Loading & Empty States */
.loading,
.empty {
  text-align: center;
  padding: 4rem 2rem;
  color: #64748b;
  font-size: 1.125rem;
}

.empty {
  background: #f8fafc;
  border-radius: 12px;
  border: 2px dashed #e2e8f0;
}

/* Compact Table View */
.compact-table {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.compact-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.compact-table thead {
  background: #f8fafc;
  border-bottom: 2px solid #e2e8f0;
}

.compact-table th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
}

.compact-table tbody tr {
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.2s;
}

.compact-table tbody tr:hover {
  background: #f8fafc;
}

.compact-table td {
  padding: 0.625rem 1rem;
  color: #1e293b;
}

.title-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.file-icon {
  font-size: 1rem;
}

.compact-category {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.actions-cell {
  display: flex;
  gap: 0.25rem;
}

.compact-btn {
  padding: 0.25rem 0.5rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
  background: transparent;
}

.compact-btn:hover {
  transform: scale(1.1);
}

.compact-btn.download:hover {
  background: #e0e7ff;
}

.compact-btn.delete:hover {
  background: #fee2e2;
}
</style>