import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import HumanBodyDiagram from '@/components/HumanBodyDiagram.vue'

describe('HumanBodyDiagram', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(HumanBodyDiagram, {
      props: {
        records: []
      }
    })
  })

  it('renders correctly', () => {
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('displays body parts', () => {
    const bodyParts = wrapper.findAll('[data-body-part]')
    expect(bodyParts.length).toBeGreaterThan(0)
  })

  it('highlights body parts with associated records', async () => {
    const recordsWithBodyParts = [
      {
        id: 1,
        title: 'Heart Checkup',
        body_part: 'heart',
        category: 'cardiology'
      },
      {
        id: 2,
        title: 'Lung X-Ray',
        body_part: 'lungs',
        category: 'pulmonology'
      }
    ]

    await wrapper.setProps({ records: recordsWithBodyParts })

    const heartElement = wrapper.find('[data-body-part="heart"]')
    const lungsElement = wrapper.find('[data-body-part="lungs"]')

    expect(heartElement.classes()).toContain('has-records')
    expect(lungsElement.classes()).toContain('has-records')
  })

  it('emits body-part-click event when clicking on a body part', async () => {
    const heartElement = wrapper.find('[data-body-part="heart"]')
    await heartElement.trigger('click')

    expect(wrapper.emitted('body-part-click')).toBeTruthy()
    expect(wrapper.emitted('body-part-click')[0][0]).toBe('heart')
  })

  it('shows tooltip on hover', async () => {
    const records = [
      {
        id: 1,
        title: 'Heart Checkup',
        body_part: 'heart',
        record_date: '2024-01-15'
      }
    ]

    await wrapper.setProps({ records })

    const heartElement = wrapper.find('[data-body-part="heart"]')
    await heartElement.trigger('mouseenter')

    const tooltip = wrapper.find('.body-part-tooltip')
    expect(tooltip.exists()).toBe(true)
    expect(tooltip.text()).toContain('Heart Checkup')
  })

  it('filters records by selected body part', async () => {
    const records = [
      { id: 1, body_part: 'heart' },
      { id: 2, body_part: 'lungs' },
      { id: 3, body_part: 'heart' }
    ]

    await wrapper.setProps({ records })

    const heartElement = wrapper.find('[data-body-part="heart"]')
    await heartElement.trigger('click')

    expect(wrapper.emitted('filter-records')).toBeTruthy()
    expect(wrapper.emitted('filter-records')[0][0]).toEqual({
      body_part: 'heart',
      records: [records[0], records[2]]
    })
  })

  it('handles view toggle between front and back', async () => {
    const toggleButton = wrapper.find('[data-test="view-toggle"]')
    expect(wrapper.vm.currentView).toBe('front')

    await toggleButton.trigger('click')
    expect(wrapper.vm.currentView).toBe('back')

    await toggleButton.trigger('click')
    expect(wrapper.vm.currentView).toBe('front')
  })

  it('displays correct severity indicators', async () => {
    const records = [
      {
        id: 1,
        body_part: 'heart',
        severity: 'high',
        category: 'urgent'
      }
    ]

    await wrapper.setProps({ records })

    const heartElement = wrapper.find('[data-body-part="heart"]')
    expect(heartElement.classes()).toContain('severity-high')
  })

  it('handles zoom controls', async () => {
    const zoomInButton = wrapper.find('[data-test="zoom-in"]')
    const zoomOutButton = wrapper.find('[data-test="zoom-out"]')
    const resetButton = wrapper.find('[data-test="zoom-reset"]')

    const initialScale = wrapper.vm.zoomLevel

    await zoomInButton.trigger('click')
    expect(wrapper.vm.zoomLevel).toBeGreaterThan(initialScale)

    await zoomOutButton.trigger('click')
    await zoomOutButton.trigger('click')
    expect(wrapper.vm.zoomLevel).toBeLessThan(initialScale)

    await resetButton.trigger('click')
    expect(wrapper.vm.zoomLevel).toBe(1)
  })

  it('supports keyboard navigation', async () => {
    const diagram = wrapper.find('.human-body-diagram')
    
    await diagram.trigger('keydown', { key: 'ArrowUp' })
    expect(wrapper.vm.selectedBodyPart).toBeDefined()

    await diagram.trigger('keydown', { key: 'Enter' })
    expect(wrapper.emitted('body-part-click')).toBeTruthy()
  })

  it('displays statistics overlay when enabled', async () => {
    await wrapper.setProps({
      showStatistics: true,
      records: [
        { body_part: 'heart' },
        { body_part: 'heart' },
        { body_part: 'lungs' }
      ]
    })

    const statsOverlay = wrapper.find('.statistics-overlay')
    expect(statsOverlay.exists()).toBe(true)
    expect(statsOverlay.text()).toContain('Heart: 2 records')
    expect(statsOverlay.text()).toContain('Lungs: 1 record')
  })

  it('handles responsive layout', async () => {
    // Mock window resize
    global.innerWidth = 500
    global.dispatchEvent(new Event('resize'))
    await wrapper.vm.$nextTick()

    expect(wrapper.classes()).toContain('mobile-view')

    global.innerWidth = 1024
    global.dispatchEvent(new Event('resize'))
    await wrapper.vm.$nextTick()

    expect(wrapper.classes()).toContain('desktop-view')
  })
})