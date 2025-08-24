<!--
  HealthStash - Payment Vault Component
  Copyright (c) 2025 Ilker M. KARAKAS
  Licensed under the MIT License
-->

<template>
  <div class="payment-vault">
    <div class="header-with-action">
      <h1>💰 Invoice & Payment Vault</h1>
      <div class="header-actions">
        <button @click="showSummary = !showSummary" class="summary-toggle-btn">
          {{ showSummary ? '📊 Hide Summary' : '📊 Show Summary' }}
        </button>
        <button @click="showCreateDialog = true" class="create-payment-btn">
          ➕ Add Invoice/Payment
        </button>
      </div>
    </div>

    <!-- Summary Panel -->
    <div v-if="showSummary" class="summary-panel">
      <div class="summary-card">
        <h3>Total Expenses</h3>
        <p class="amount">€{{ summary.total_amount?.toFixed(2) || '0.00' }}</p>
      </div>
      <div class="summary-card">
        <h3>Insurance Paid</h3>
        <p class="amount insurance">€{{ summary.total_insurance_paid?.toFixed(2) || '0.00' }}</p>
      </div>
      <div class="summary-card">
        <h3>Your Responsibility</h3>
        <p class="amount responsibility">€{{ summary.total_patient_responsibility?.toFixed(2) || '0.00' }}</p>
      </div>
      <div class="summary-card">
        <h3>Total Payments</h3>
        <p class="count">{{ summary.total_payments || 0 }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters">
      <select v-model="filters.status" @change="fetchPayments">
        <option value="">All Status</option>
        <option value="pending">Pending</option>
        <option value="paid">Paid</option>
        <option value="partially_paid">Partially Paid</option>
        <option value="disputed">Disputed</option>
        <option value="refunded">Refunded</option>
        <option value="cancelled">Cancelled</option>
      </select>
      
      <input
        v-model="filters.provider"
        type="text"
        placeholder="Provider name..."
        @keyup.enter="fetchPayments"
      />
      
      <input
        v-model="filters.dateFrom"
        type="date"
        placeholder="From date"
        @change="fetchPayments"
      />
      
      <input
        v-model="filters.dateTo"
        type="date"
        placeholder="To date"
        @change="fetchPayments"
      />
      
      <select v-model="filters.sortBy" @change="fetchPayments">
        <option value="expense_date_desc">Expense Date (Recent)</option>
        <option value="expense_date_asc">Expense Date (Oldest)</option>
        <option value="invoice_date_desc">Invoice Date (Recent)</option>
        <option value="invoice_date_asc">Invoice Date (Oldest)</option>
        <option value="amount_desc">Amount (High to Low)</option>
        <option value="amount_asc">Amount (Low to High)</option>
        <option value="created_at_desc">Added (Recent)</option>
      </select>
      
      <button @click="fetchPayments" class="search-btn">🔍 Search</button>
      <button @click="clearFilters" class="clear-btn">Clear</button>
    </div>

    <!-- Payments List -->
    <div class="payments-container">
      <div v-if="loading" class="loading">Loading payments...</div>
      
      <div v-else-if="payments.length === 0" class="empty">
        <p>No payment records found</p>
        <button @click="showCreateDialog = true" class="create-first-btn">
          Add your first invoice/payment
        </button>
      </div>
      
      <div v-else class="payments-grid">
        <div v-for="payment in payments" :key="payment.id" class="payment-card" @click="viewPayment(payment)">
          <div class="payment-header">
            <span class="provider-name">{{ payment.provider_name || 'Unknown Provider' }}</span>
            <span :class="['status-badge', payment.payment_status]">
              {{ formatStatus(payment.payment_status) }}
            </span>
          </div>
          
          <div class="payment-amount">
            <span class="currency">{{ payment.currency }}</span>
            <span class="amount">€{{ payment.amount?.toFixed(2) }}</span>
          </div>
          
          <div class="payment-details">
            <div v-if="payment.invoice_number" class="detail-row">
              <span class="label">Invoice #:</span>
              <span class="value">{{ payment.invoice_number }}</span>
            </div>
            
            <div v-if="payment.expense_date" class="detail-row">
              <span class="label">Service Date:</span>
              <span class="value">{{ formatDate(payment.expense_date) }}</span>
            </div>
            
            <div v-if="payment.health_record" class="detail-row linked">
              <span class="label">📎 Linked to:</span>
              <span class="value">{{ payment.health_record.title }}</span>
            </div>
            
            <div v-if="payment.insurance_paid_amount" class="detail-row">
              <span class="label">Insurance Paid:</span>
              <span class="value">€{{ payment.insurance_paid_amount.toFixed(2) }}</span>
            </div>
            
            <div v-if="payment.patient_responsibility" class="detail-row">
              <span class="label">You Pay:</span>
              <span class="value responsibility">€{{ payment.patient_responsibility.toFixed(2) }}</span>
            </div>
          </div>
          
          <div v-if="payment.files && payment.files.length > 0" class="payment-files">
            <span class="file-count">📄 {{ payment.files.length }} file(s)</span>
          </div>
          
          <div class="payment-actions">
            <button @click.stop="editPayment(payment)" class="edit-btn">✏️ Edit</button>
            <button @click.stop="deletePayment(payment)" class="delete-btn">🗑️ Delete</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Payment Dialog -->
    <div v-if="showCreateDialog || showEditDialog" class="dialog-overlay" @click.self="closeDialogs">
      <div class="dialog">
        <h2>{{ showEditDialog ? 'Edit Payment Record' : 'Add Invoice/Payment' }}</h2>
        
        <form @submit.prevent="savePayment">
          <div class="form-row">
            <div class="form-group">
              <label>Link to Health Record (Optional)</label>
              <select v-model="paymentForm.health_record_id">
                <option value="">-- Not linked --</option>
                <option v-for="record in healthRecords" :key="record.id" :value="record.id">
                  {{ record.title }} - {{ formatDate(record.service_date) }}
                </option>
              </select>
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label>Provider Name *</label>
              <input v-model="paymentForm.provider_name" type="text" required />
            </div>
            
            <div class="form-group">
              <label>Amount *</label>
              <input v-model.number="paymentForm.amount" type="number" step="0.01" required />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label>Invoice Number</label>
              <input v-model="paymentForm.invoice_number" type="text" />
            </div>
            
            <div class="form-group">
              <label>Invoice Date</label>
              <input v-model="paymentForm.invoice_date" type="date" />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label>Service/Expense Date</label>
              <input v-model="paymentForm.expense_date" type="date" />
            </div>
            
            <div class="form-group">
              <label>Payment Status</label>
              <select v-model="paymentForm.payment_status">
                <option value="pending">Pending</option>
                <option value="paid">Paid</option>
                <option value="partially_paid">Partially Paid</option>
                <option value="disputed">Disputed</option>
                <option value="refunded">Refunded</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label>Payment Method</label>
              <select v-model="paymentForm.payment_method">
                <option value="">-- Select --</option>
                <option value="cash">Cash</option>
                <option value="credit_card">Credit Card</option>
                <option value="debit_card">Debit Card</option>
                <option value="insurance">Insurance</option>
                <option value="check">Check</option>
                <option value="wire_transfer">Wire Transfer</option>
                <option value="other">Other</option>
              </select>
            </div>
            
            <div class="form-group">
              <label>Payment Date</label>
              <input v-model="paymentForm.payment_date" type="date" />
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label>Insurance Paid</label>
              <input v-model.number="paymentForm.insurance_paid_amount" type="number" step="0.01" />
            </div>
            
            <div class="form-group">
              <label>Your Responsibility</label>
              <input v-model.number="paymentForm.patient_responsibility" type="number" step="0.01" />
            </div>
          </div>
          
          <div class="form-group">
            <label>Service Description</label>
            <textarea v-model="paymentForm.service_description" rows="2"></textarea>
          </div>
          
          <div class="form-group">
            <label>Notes</label>
            <textarea v-model="paymentForm.notes" rows="2"></textarea>
          </div>
          
          <div v-if="!showEditDialog" class="form-group">
            <label>Upload Files (Invoices/Receipts)</label>
            <input type="file" multiple @change="handleFileSelect" accept=".pdf,.jpg,.jpeg,.png,.gif,.bmp,.tiff" />
            <div v-if="selectedFiles.length > 0" class="selected-files">
              <div v-for="(file, index) in selectedFiles" :key="index" class="selected-file">
                {{ file.name }}
                <button type="button" @click="removeFile(index)">✕</button>
              </div>
            </div>
          </div>
          
          <div class="dialog-actions">
            <button type="button" @click="closeDialogs" class="cancel-btn">Cancel</button>
            <button type="submit" class="save-btn">{{ showEditDialog ? 'Update' : 'Save' }} Payment</button>
          </div>
        </form>
      </div>
    </div>

    <!-- View Payment Dialog -->
    <div v-if="selectedPayment" class="dialog-overlay" @click.self="selectedPayment = null">
      <div class="dialog wide">
        <h2>Payment Details</h2>
        
        <div class="payment-detail-view">
          <div class="detail-section">
            <h3>Provider Information</h3>
            <p><strong>Provider:</strong> {{ selectedPayment.provider_name || 'N/A' }}</p>
            <p v-if="selectedPayment.provider_address"><strong>Address:</strong> {{ selectedPayment.provider_address }}</p>
            <p v-if="selectedPayment.service_description"><strong>Service:</strong> {{ selectedPayment.service_description }}</p>
          </div>
          
          <div class="detail-section">
            <h3>Payment Information</h3>
            <p><strong>Amount:</strong> {{ selectedPayment.currency }} €{{ selectedPayment.amount?.toFixed(2) }}</p>
            <p><strong>Status:</strong> <span :class="['status-badge', selectedPayment.payment_status]">{{ formatStatus(selectedPayment.payment_status) }}</span></p>
            <p v-if="selectedPayment.payment_method"><strong>Method:</strong> {{ formatPaymentMethod(selectedPayment.payment_method) }}</p>
            <p v-if="selectedPayment.invoice_number"><strong>Invoice #:</strong> {{ selectedPayment.invoice_number }}</p>
            <p v-if="selectedPayment.invoice_date"><strong>Invoice Date:</strong> {{ formatDate(selectedPayment.invoice_date) }}</p>
            <p v-if="selectedPayment.expense_date"><strong>Service Date:</strong> {{ formatDate(selectedPayment.expense_date) }}</p>
            <p v-if="selectedPayment.payment_date"><strong>Payment Date:</strong> {{ formatDate(selectedPayment.payment_date) }}</p>
          </div>
          
          <div v-if="selectedPayment.insurance_paid_amount || selectedPayment.patient_responsibility" class="detail-section">
            <h3>Insurance & Responsibility</h3>
            <p v-if="selectedPayment.insurance_claim_number"><strong>Claim #:</strong> {{ selectedPayment.insurance_claim_number }}</p>
            <p v-if="selectedPayment.insurance_paid_amount"><strong>Insurance Paid:</strong> €{{ selectedPayment.insurance_paid_amount.toFixed(2) }}</p>
            <p v-if="selectedPayment.patient_responsibility"><strong>Your Responsibility:</strong> €{{ selectedPayment.patient_responsibility.toFixed(2) }}</p>
          </div>
          
          <div v-if="selectedPayment.health_record" class="detail-section">
            <h3>Linked Health Record</h3>
            <p><strong>Record:</strong> {{ selectedPayment.health_record.title }}</p>
            <p v-if="selectedPayment.health_record.service_date"><strong>Service Date:</strong> {{ formatDate(selectedPayment.health_record.service_date) }}</p>
            <button @click="viewHealthRecord(selectedPayment.health_record.id)" class="view-record-btn">
              View Health Record
            </button>
          </div>
          
          <div v-if="selectedPayment.files && selectedPayment.files.length > 0" class="detail-section">
            <h3>Attached Files</h3>
            <div class="file-list">
              <div v-for="file in selectedPayment.files" :key="file.id" class="file-item">
                <span class="file-name">📄 {{ file.file_name }}</span>
                <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
                <button @click="downloadFile(selectedPayment.id, file.id, file.file_name)" class="download-btn">
                  ⬇️ Download
                </button>
              </div>
            </div>
          </div>
          
          <div v-if="selectedPayment.notes" class="detail-section">
            <h3>Notes</h3>
            <p>{{ selectedPayment.notes }}</p>
          </div>
        </div>
        
        <div class="dialog-actions">
          <button @click="selectedPayment = null" class="close-btn">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '../services/axios'

export default {
  name: 'PaymentVault',
  setup() {
    const route = useRoute()
    const payments = ref([])
    const healthRecords = ref([])
    const loading = ref(false)
    const showCreateDialog = ref(false)
    const showEditDialog = ref(false)
    const selectedPayment = ref(null)
    const showSummary = ref(true)
    const summary = ref({})
    const selectedFiles = ref([])
    
    const filters = ref({
      status: '',
      provider: '',
      dateFrom: '',
      dateTo: '',
      sortBy: 'expense_date_desc',
      health_record_id: ''
    })
    
    const paymentForm = ref({
      health_record_id: '',
      invoice_number: '',
      invoice_date: '',
      expense_date: '',
      amount: '',
      currency: 'EUR',
      payment_status: 'pending',
      payment_method: '',
      payment_date: '',
      provider_name: '',
      provider_address: '',
      service_description: '',
      insurance_claim_number: '',
      insurance_paid_amount: '',
      patient_responsibility: '',
      notes: ''
    })
    
    const fetchPayments = async () => {
      loading.value = true
      try {
        const params = {
          sort_by: filters.value.sortBy
        }
        
        if (filters.value.status) params.status = filters.value.status
        if (filters.value.provider) params.provider = filters.value.provider
        if (filters.value.dateFrom) params.date_from = filters.value.dateFrom
        if (filters.value.dateTo) params.date_to = filters.value.dateTo
        if (filters.value.health_record_id) params.health_record_id = filters.value.health_record_id
        
        const response = await api.get('/payments', { params })
        payments.value = response.data.payments
      } catch (error) {
        console.error('Error fetching payments:', error)
        alert('Error fetching payments')
      } finally {
        loading.value = false
      }
    }
    
    const fetchSummary = async () => {
      try {
        const params = {}
        if (filters.value.dateFrom) params.date_from = filters.value.dateFrom
        if (filters.value.dateTo) params.date_to = filters.value.dateTo
        
        const response = await api.get('/payments/stats/summary', { params })
        summary.value = response.data
      } catch (error) {
        console.error('Error fetching summary:', error)
      }
    }
    
    const fetchHealthRecords = async () => {
      try {
        const response = await api.get('/records')
        healthRecords.value = response.data.records
      } catch (error) {
        console.error('Error fetching health records:', error)
      }
    }
    
    const handleFileSelect = (event) => {
      selectedFiles.value = Array.from(event.target.files)
    }
    
    const removeFile = (index) => {
      selectedFiles.value.splice(index, 1)
    }
    
    const savePayment = async () => {
      try {
        const formData = new FormData()
        
        // Add all form fields
        Object.keys(paymentForm.value).forEach(key => {
          if (paymentForm.value[key] !== '' && paymentForm.value[key] !== null) {
            formData.append(key, paymentForm.value[key])
          }
        })
        
        // Add files if creating new payment
        if (!showEditDialog.value && selectedFiles.value.length > 0) {
          selectedFiles.value.forEach(file => {
            formData.append('files', file)
          })
        }
        
        if (showEditDialog.value) {
          await api.put(`/payments/${paymentForm.value.id}`, formData)
        } else {
          await api.post('/payments', formData)
        }
        
        closeDialogs()
        fetchPayments()
        fetchSummary()
      } catch (error) {
        console.error('Error saving payment:', error)
        alert('Error saving payment')
      }
    }
    
    const editPayment = (payment) => {
      paymentForm.value = { ...payment }
      showEditDialog.value = true
    }
    
    const deletePayment = async (payment) => {
      if (confirm(`Delete payment record for ${payment.provider_name}?`)) {
        try {
          await api.delete(`/payments/${payment.id}`)
          fetchPayments()
          fetchSummary()
        } catch (error) {
          console.error('Error deleting payment:', error)
          alert('Error deleting payment')
        }
      }
    }
    
    const viewPayment = async (payment) => {
      try {
        const response = await api.get(`/payments/${payment.id}`)
        selectedPayment.value = response.data
      } catch (error) {
        console.error('Error fetching payment details:', error)
      }
    }
    
    const downloadFile = async (paymentId, fileId, fileName) => {
      try {
        const response = await api.get(`/payments/${paymentId}/files/${fileId}/download`, {
          responseType: 'blob'
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', fileName)
        document.body.appendChild(link)
        link.click()
        link.remove()
      } catch (error) {
        console.error('Error downloading file:', error)
        alert('Error downloading file')
      }
    }
    
    const viewHealthRecord = (recordId) => {
      window.location.href = `/records#${recordId}`
    }
    
    const closeDialogs = () => {
      showCreateDialog.value = false
      showEditDialog.value = false
      selectedFiles.value = []
      paymentForm.value = {
        health_record_id: '',
        invoice_number: '',
        invoice_date: '',
        expense_date: '',
        amount: '',
        currency: 'EUR',
        payment_status: 'pending',
        payment_method: '',
        payment_date: '',
        provider_name: '',
        provider_address: '',
        service_description: '',
        insurance_claim_number: '',
        insurance_paid_amount: '',
        patient_responsibility: '',
        notes: ''
      }
    }
    
    const clearFilters = () => {
      filters.value = {
        status: '',
        provider: '',
        dateFrom: '',
        dateTo: '',
        sortBy: 'expense_date_desc',
        health_record_id: ''
      }
      fetchPayments()
      fetchSummary()
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return ''
      return new Date(dateString).toLocaleDateString()
    }
    
    const formatStatus = (status) => {
      if (!status) return ''
      return status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
    }
    
    const formatPaymentMethod = (method) => {
      if (!method) return ''
      return method.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
    }
    
    const formatFileSize = (bytes) => {
      if (!bytes) return '0 B'
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(1024))
      return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
    }
    
    onMounted(() => {
      // Check if filtering by health record ID
      const healthRecordId = route.query.health_record_id
      if (healthRecordId) {
        filters.value.health_record_id = healthRecordId
      }
      
      fetchPayments()
      fetchSummary()
      fetchHealthRecords()
    })
    
    return {
      payments,
      healthRecords,
      loading,
      showCreateDialog,
      showEditDialog,
      selectedPayment,
      showSummary,
      summary,
      selectedFiles,
      filters,
      paymentForm,
      fetchPayments,
      handleFileSelect,
      removeFile,
      savePayment,
      editPayment,
      deletePayment,
      viewPayment,
      downloadFile,
      viewHealthRecord,
      closeDialogs,
      clearFilters,
      formatDate,
      formatStatus,
      formatPaymentMethod,
      formatFileSize
    }
  }
}
</script>

<style scoped>
.payment-vault {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header-with-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.summary-toggle-btn,
.create-payment-btn {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
}

.summary-toggle-btn {
  background: #6c757d;
}

.summary-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 10px;
}

.summary-card {
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.summary-card h3 {
  font-size: 14px;
  color: #666;
  margin: 0 0 10px 0;
}

.summary-card .amount {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.summary-card .amount.insurance {
  color: #28a745;
}

.summary-card .amount.responsibility {
  color: #dc3545;
}

.summary-card .count {
  font-size: 32px;
  font-weight: bold;
  color: #007bff;
}

.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filters input,
.filters select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.search-btn,
.clear-btn {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.clear-btn {
  background: #6c757d;
}

.payments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.payment-card {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.payment-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.payment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.provider-name {
  font-weight: bold;
  font-size: 16px;
  color: #333;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
}

.status-badge.pending {
  background: #ffc107;
  color: #333;
}

.status-badge.paid {
  background: #28a745;
  color: white;
}

.status-badge.partially_paid {
  background: #fd7e14;
  color: white;
}

.status-badge.disputed {
  background: #dc3545;
  color: white;
}

.status-badge.refunded {
  background: #17a2b8;
  color: white;
}

.status-badge.cancelled {
  background: #6c757d;
  color: white;
}

.payment-amount {
  font-size: 24px;
  margin: 10px 0;
  color: #007bff;
}

.payment-amount .currency {
  font-size: 16px;
  margin-right: 5px;
}

.payment-details {
  margin: 15px 0;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  margin: 5px 0;
  font-size: 14px;
}

.detail-row.linked {
  background: #e7f3ff;
  padding: 5px;
  border-radius: 4px;
  margin: 8px 0;
}

.detail-row .label {
  color: #666;
}

.detail-row .value {
  color: #333;
  font-weight: 500;
}

.detail-row .value.responsibility {
  color: #dc3545;
  font-weight: bold;
}

.payment-files {
  margin: 10px 0;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.file-count {
  font-size: 14px;
  color: #666;
}

.payment-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.edit-btn,
.delete-btn {
  flex: 1;
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.edit-btn {
  background: #007bff;
  color: white;
}

.delete-btn {
  background: #dc3545;
  color: white;
}

.empty {
  text-align: center;
  padding: 40px;
  color: #666;
}

.create-first-btn {
  margin-top: 20px;
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 8px;
  padding: 20px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.dialog.wide {
  max-width: 800px;
}

.dialog h2 {
  margin: 0 0 20px 0;
  color: #333;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.selected-files {
  margin-top: 10px;
}

.selected-file {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px;
  background: #f8f9fa;
  border-radius: 4px;
  margin: 5px 0;
}

.dialog-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.cancel-btn,
.save-btn,
.close-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn,
.close-btn {
  background: #6c757d;
  color: white;
}

.save-btn {
  background: #28a745;
  color: white;
}

.payment-detail-view {
  display: grid;
  gap: 20px;
}

.detail-section {
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.detail-section h3 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 16px;
}

.detail-section p {
  margin: 5px 0;
  color: #666;
}

.detail-section strong {
  color: #333;
  margin-right: 5px;
}

.view-record-btn {
  margin-top: 10px;
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.file-list {
  display: grid;
  gap: 10px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: white;
  border-radius: 4px;
}

.file-name {
  flex: 1;
  color: #333;
}

.file-size {
  color: #666;
  font-size: 14px;
}

.download-btn {
  padding: 6px 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}
</style>