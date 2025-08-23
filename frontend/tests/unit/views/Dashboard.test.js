import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import Dashboard from '@/views/Dashboard.vue'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

vi.mock('axios')

describe('Dashboard', () => {
  let wrapper
  let authStore

  beforeEach(() => {
    wrapper = mount(Dashboard, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              auth: {
                user: {
                  id: 1,
                  email: 'test@example.com',
                  full_name: 'Test User'
                },
                token: 'test-token'
              }
            }
          })
        ],
        stubs: {
          RouterLink: true
        }
      }
    })
    
    authStore = useAuthStore()
  })

  it('renders dashboard correctly', () => {
    expect(wrapper.find('h1').text()).toContain('Dashboard')
    expect(wrapper.find('.welcome-message').text()).toContain('Test User')
  })

  it('displays user statistics', async () => {
    const stats = {
      total_records: 42,
      total_files: 15,
      recent_uploads: 3,
      storage_used: '250 MB'
    }

    axios.get.mockResolvedValue({ data: stats })
    await wrapper.vm.fetchStatistics()
    await flushPromises()

    expect(wrapper.find('[data-test="total-records"]').text()).toContain('42')
    expect(wrapper.find('[data-test="total-files"]').text()).toContain('15')
    expect(wrapper.find('[data-test="storage-used"]').text()).toContain('250 MB')
  })

  it('shows recent activity', async () => {
    const activities = [
      {
        id: 1,
        type: 'upload',
        description: 'Uploaded blood test results',
        timestamp: '2024-01-20T10:00:00Z'
      },
      {
        id: 2,
        type: 'view',
        description: 'Viewed X-ray report',
        timestamp: '2024-01-19T15:30:00Z'
      }
    ]

    axios.get.mockResolvedValue({ data: activities })
    await wrapper.vm.fetchRecentActivity()
    await flushPromises()

    const activityItems = wrapper.findAll('.activity-item')
    expect(activityItems).toHaveLength(2)
    expect(activityItems[0].text()).toContain('blood test results')
  })

  it('displays quick actions', () => {
    const quickActions = wrapper.findAll('.quick-action')
    expect(quickActions.length).toBeGreaterThan(0)
    
    const uploadAction = wrapper.find('[data-test="quick-upload"]')
    expect(uploadAction.exists()).toBe(true)
  })

  it('shows health summary chart', async () => {
    const chartData = {
      labels: ['Lab Results', 'Imaging', 'Prescriptions'],
      data: [10, 5, 8]
    }

    axios.get.mockResolvedValue({ data: chartData })
    await wrapper.vm.fetchChartData()
    await flushPromises()

    const chart = wrapper.find('.health-summary-chart')
    expect(chart.exists()).toBe(true)
  })

  it('handles empty state correctly', async () => {
    axios.get.mockResolvedValue({ data: { total_records: 0 } })
    await wrapper.vm.fetchStatistics()
    await flushPromises()

    const emptyState = wrapper.find('.empty-state')
    expect(emptyState.exists()).toBe(true)
    expect(emptyState.text()).toContain('Get started')
  })

  it('displays upcoming appointments', async () => {
    const appointments = [
      {
        id: 1,
        title: 'Annual Checkup',
        date: '2024-02-01T14:00:00Z',
        doctor: 'Dr. Smith'
      }
    ]

    axios.get.mockResolvedValue({ data: appointments })
    await wrapper.vm.fetchUpcomingAppointments()
    await flushPromises()

    const appointmentCard = wrapper.find('.appointment-card')
    expect(appointmentCard.exists()).toBe(true)
    expect(appointmentCard.text()).toContain('Annual Checkup')
    expect(appointmentCard.text()).toContain('Dr. Smith')
  })

  it('shows medication reminders', async () => {
    const medications = [
      {
        id: 1,
        name: 'Aspirin',
        dosage: '100mg',
        frequency: 'Daily',
        next_dose: '2024-01-20T08:00:00Z'
      }
    ]

    axios.get.mockResolvedValue({ data: medications })
    await wrapper.vm.fetchMedications()
    await flushPromises()

    const medicationCard = wrapper.find('.medication-reminder')
    expect(medicationCard.exists()).toBe(true)
    expect(medicationCard.text()).toContain('Aspirin')
    expect(medicationCard.text()).toContain('100mg')
  })

  it('handles API errors gracefully', async () => {
    axios.get.mockRejectedValue(new Error('Network error'))
    await wrapper.vm.fetchStatistics()
    await flushPromises()

    const errorMessage = wrapper.find('.error-message')
    expect(errorMessage.exists()).toBe(true)
    expect(errorMessage.text()).toContain('Unable to load data')
  })

  it('refreshes data on pull-to-refresh', async () => {
    const fetchSpy = vi.spyOn(wrapper.vm, 'fetchAllData')
    
    await wrapper.find('.dashboard').trigger('touchstart', { touches: [{ clientY: 100 }] })
    await wrapper.find('.dashboard').trigger('touchmove', { touches: [{ clientY: 200 }] })
    await wrapper.find('.dashboard').trigger('touchend')
    
    expect(fetchSpy).toHaveBeenCalled()
  })

  it('navigates to different sections', async () => {
    const uploadButton = wrapper.find('[data-test="navigate-upload"]')
    await uploadButton.trigger('click')
    
    expect(wrapper.vm.$router.push).toHaveBeenCalledWith('/upload')
  })

  it('displays notification badge for new items', async () => {
    axios.get.mockResolvedValue({ 
      data: { 
        new_records: 3,
        unread_messages: 2 
      } 
    })
    
    await wrapper.vm.fetchNotifications()
    await flushPromises()

    const badge = wrapper.find('.notification-badge')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toBe('5')
  })

  it('shows storage usage warning when near limit', async () => {
    axios.get.mockResolvedValue({ 
      data: { 
        storage_used_percent: 92 
      } 
    })
    
    await wrapper.vm.fetchStorageInfo()
    await flushPromises()

    const warning = wrapper.find('.storage-warning')
    expect(warning.exists()).toBe(true)
    expect(warning.text()).toContain('92% of storage used')
  })
})