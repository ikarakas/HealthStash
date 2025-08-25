<!--
  MIT License
  Copyright (c) 2025 Ilker M. KARAKAS
  HealthStash - Privacy-First Personal Health Data Vault
-->
<template>
  <div class="timeline-container">
    <div class="timeline-controls">
      <button @click="zoomOut" :disabled="zoomLevel <= 0" class="zoom-btn">
        🔍➖ Zoom Out
      </button>
      <span class="zoom-indicator">{{ zoomLevelText }}</span>
      <button @click="zoomIn" :disabled="zoomLevel >= 2" class="zoom-btn">
        🔍➕ Zoom In
      </button>
      <button @click="centerToToday" class="center-btn">
        📍 Today
      </button>
    </div>
    
    <div class="timeline-wrapper" ref="timelineWrapper" @wheel="handleWheel" @mousedown="startDragging">
      <canvas ref="timelineCanvas" class="timeline-canvas"></canvas>
      <div class="timeline-tooltip" v-if="hoveredRecord" :style="tooltipStyle">
        <div class="tooltip-title">{{ hoveredRecord.title }}</div>
        <div class="tooltip-date">{{ formatDate(hoveredRecord.service_date) }}</div>
        <div class="tooltip-category">{{ formatCategory(hoveredRecord.category) }}</div>
        <div v-if="hoveredRecord.provider_name" class="tooltip-provider">
          Provider: {{ hoveredRecord.provider_name }}
        </div>
      </div>
    </div>
    
    <div class="timeline-legend">
      <div v-for="(color, category) in categoryColors" :key="category" class="legend-item">
        <span class="legend-color" :style="{ backgroundColor: color }"></span>
        <span class="legend-label">{{ formatCategory(category) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { format, startOfYear, endOfYear, startOfMonth, endOfMonth, differenceInDays, differenceInMonths, differenceInYears, addDays, addMonths, addYears, isWithinInterval, parseISO } from 'date-fns'

const props = defineProps({
  records: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['record-click'])

const timelineWrapper = ref(null)
const timelineCanvas = ref(null)
const hoveredRecord = ref(null)
const tooltipStyle = ref({})

const zoomLevel = ref(1)
const panOffset = ref(0)
const isDragging = ref(false)
const dragStartX = ref(0)
const dragStartOffset = ref(0)

const canvasWidth = ref(1200)
const canvasHeight = ref(400)

const categoryColors = {
  lab_results: '#4CAF50',
  imaging: '#2196F3',
  clinical_notes: '#FF9800',
  prescriptions: '#9C27B0',
  vaccinations: '#00BCD4',
  personal_notes: '#FFC107',
  vital_signs: '#E91E63',
  other: '#607D8B'
}

const zoomLevelText = computed(() => {
  switch(zoomLevel.value) {
    case 0: return 'Years'
    case 1: return 'Months'
    case 2: return 'Days'
    default: return 'Months'
  }
})

const timeRange = computed(() => {
  const now = new Date()
  const recordsWithDates = props.records.filter(r => r.service_date)
  
  if (recordsWithDates.length === 0) {
    return {
      start: startOfYear(addYears(now, -5)),
      end: endOfYear(now),
      span: 5 * 365
    }
  }
  
  const dates = recordsWithDates.map(r => new Date(r.service_date))
  const minDate = new Date(Math.min(...dates))
  const maxDate = new Date(Math.max(...dates))
  
  let start, end, span
  
  switch(zoomLevel.value) {
    case 0: // Years view
      start = startOfYear(addYears(minDate, -1))
      end = endOfYear(addYears(maxDate, 1))
      span = differenceInDays(end, start)
      break
    case 1: // Months view
      start = startOfMonth(addMonths(minDate, -6))
      end = endOfMonth(addMonths(maxDate, 6))
      span = differenceInDays(end, start)
      break
    case 2: // Days view
      start = addDays(minDate, -30)
      end = addDays(maxDate, 30)
      span = differenceInDays(end, start)
      break
  }
  
  return { start, end, span }
})

const visibleRange = computed(() => {
  const { start, end, span } = timeRange.value
  const pixelsPerDay = canvasWidth.value / span
  const offsetDays = panOffset.value / pixelsPerDay
  
  return {
    start: addDays(start, offsetDays),
    end: addDays(end, offsetDays)
  }
})

function formatCategory(category) {
  return category
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatDate(date) {
  if (!date) return 'No date'
  const parsedDate = typeof date === 'string' ? parseISO(date) : date
  return format(parsedDate, 'MMM d, yyyy')
}

function drawTimeline() {
  const canvas = timelineCanvas.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  
  canvas.width = canvasWidth.value * dpr
  canvas.height = canvasHeight.value * dpr
  canvas.style.width = canvasWidth.value + 'px'
  canvas.style.height = canvasHeight.value + 'px'
  
  ctx.scale(dpr, dpr)
  ctx.clearRect(0, 0, canvasWidth.value, canvasHeight.value)
  
  // Draw background
  ctx.fillStyle = '#f5f5f5'
  ctx.fillRect(0, 0, canvasWidth.value, canvasHeight.value)
  
  // Draw grid and labels
  drawTimeGrid(ctx)
  
  // Draw records
  drawRecords(ctx)
}

function drawTimeGrid(ctx) {
  const { start, end, span } = timeRange.value
  const { start: visStart, end: visEnd } = visibleRange.value
  
  ctx.strokeStyle = '#e0e0e0'
  ctx.fillStyle = '#666'
  ctx.font = '12px system-ui'
  
  let intervals = []
  
  switch(zoomLevel.value) {
    case 0: // Years
      const startYear = visStart.getFullYear()
      const endYear = visEnd.getFullYear()
      for (let year = startYear; year <= endYear; year++) {
        intervals.push({
          date: new Date(year, 0, 1),
          label: year.toString()
        })
      }
      break
      
    case 1: // Months
      let currentMonth = new Date(visStart.getFullYear(), visStart.getMonth(), 1)
      while (currentMonth <= visEnd) {
        intervals.push({
          date: currentMonth,
          label: format(currentMonth, 'MMM yyyy')
        })
        currentMonth = addMonths(currentMonth, 1)
      }
      break
      
    case 2: // Days
      const daysToShow = Math.min(60, differenceInDays(visEnd, visStart))
      const dayInterval = Math.max(1, Math.floor(daysToShow / 20))
      let currentDay = new Date(visStart)
      while (currentDay <= visEnd) {
        intervals.push({
          date: currentDay,
          label: format(currentDay, 'MMM d')
        })
        currentDay = addDays(currentDay, dayInterval)
      }
      break
  }
  
  intervals.forEach(({ date, label }) => {
    const x = getXPosition(date)
    if (x >= 0 && x <= canvasWidth.value) {
      // Draw vertical line
      ctx.beginPath()
      ctx.moveTo(x, 50)
      ctx.lineTo(x, canvasHeight.value - 50)
      ctx.stroke()
      
      // Draw label
      ctx.save()
      ctx.translate(x, 40)
      ctx.textAlign = 'center'
      ctx.fillText(label, 0, 0)
      ctx.restore()
    }
  })
  
  // Draw main timeline
  ctx.strokeStyle = '#333'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(0, canvasHeight.value / 2)
  ctx.lineTo(canvasWidth.value, canvasHeight.value / 2)
  ctx.stroke()
  ctx.lineWidth = 1
}

function drawRecords(ctx) {
  const recordsWithDates = props.records
    .filter(r => r.service_date)
    .sort((a, b) => new Date(a.service_date) - new Date(b.service_date))
  
  const centerY = canvasHeight.value / 2
  const layerHeight = 30
  const layers = assignLayers(recordsWithDates)
  
  recordsWithDates.forEach((record, index) => {
    const x = getXPosition(new Date(record.service_date))
    
    if (x >= -20 && x <= canvasWidth.value + 20) {
      const layer = layers[index]
      const y = centerY + (layer % 2 === 0 ? -1 : 1) * (Math.floor(layer / 2) + 1) * layerHeight
      
      // Draw connection line
      ctx.strokeStyle = '#ccc'
      ctx.beginPath()
      ctx.moveTo(x, centerY)
      ctx.lineTo(x, y)
      ctx.stroke()
      
      // Draw record circle
      const color = categoryColors[record.category] || categoryColors.other
      ctx.fillStyle = color
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 2
      
      ctx.beginPath()
      ctx.arc(x, y, 8, 0, Math.PI * 2)
      ctx.fill()
      ctx.stroke()
      
      // Store position for hover detection
      record._x = x
      record._y = y
    }
  })
}

function assignLayers(records) {
  const layers = []
  const layerEndTimes = []
  
  records.forEach((record, index) => {
    const x = getXPosition(new Date(record.service_date))
    let assignedLayer = -1
    
    for (let i = 0; i < layerEndTimes.length; i++) {
      if (x - layerEndTimes[i] > 20) {
        assignedLayer = i
        break
      }
    }
    
    if (assignedLayer === -1) {
      assignedLayer = layerEndTimes.length
      layerEndTimes.push(x)
    } else {
      layerEndTimes[assignedLayer] = x
    }
    
    layers[index] = assignedLayer
  })
  
  return layers
}

function getXPosition(date) {
  const { start, span } = timeRange.value
  const daysSinceStart = differenceInDays(date, start)
  return (daysSinceStart / span) * canvasWidth.value + panOffset.value
}

function handleWheel(event) {
  event.preventDefault()
  
  if (event.ctrlKey || event.metaKey) {
    // Zoom with Ctrl/Cmd + wheel
    if (event.deltaY < 0) {
      zoomIn()
    } else {
      zoomOut()
    }
  } else {
    // Pan with wheel
    panOffset.value -= event.deltaX || event.deltaY
    drawTimeline()
  }
}

function startDragging(event) {
  isDragging.value = true
  dragStartX.value = event.clientX
  dragStartOffset.value = panOffset.value
  
  document.addEventListener('mousemove', drag)
  document.addEventListener('mouseup', stopDragging)
}

function drag(event) {
  if (!isDragging.value) return
  
  const deltaX = event.clientX - dragStartX.value
  panOffset.value = dragStartOffset.value + deltaX
  drawTimeline()
}

function stopDragging() {
  isDragging.value = false
  document.removeEventListener('mousemove', drag)
  document.removeEventListener('mouseup', stopDragging)
}

function zoomIn() {
  if (zoomLevel.value < 2) {
    zoomLevel.value++
    drawTimeline()
  }
}

function zoomOut() {
  if (zoomLevel.value > 0) {
    zoomLevel.value--
    drawTimeline()
  }
}

function centerToToday() {
  panOffset.value = 0
  drawTimeline()
}

function handleMouseMove(event) {
  const rect = timelineCanvas.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  const recordsWithDates = props.records.filter(r => r.service_date && r._x && r._y)
  
  let foundRecord = null
  for (const record of recordsWithDates) {
    const distance = Math.sqrt(Math.pow(x - record._x, 2) + Math.pow(y - record._y, 2))
    if (distance <= 10) {
      foundRecord = record
      break
    }
  }
  
  if (foundRecord) {
    hoveredRecord.value = foundRecord
    tooltipStyle.value = {
      left: `${foundRecord._x}px`,
      top: `${foundRecord._y - 10}px`,
      transform: 'translate(-50%, -100%)'
    }
    timelineCanvas.value.style.cursor = 'pointer'
  } else {
    hoveredRecord.value = null
    timelineCanvas.value.style.cursor = isDragging.value ? 'grabbing' : 'grab'
  }
}

function handleClick(event) {
  if (hoveredRecord.value) {
    emit('record-click', hoveredRecord.value)
  }
}

function handleResize() {
  if (timelineWrapper.value) {
    canvasWidth.value = timelineWrapper.value.clientWidth
    drawTimeline()
  }
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
  
  if (timelineCanvas.value) {
    timelineCanvas.value.addEventListener('mousemove', handleMouseMove)
    timelineCanvas.value.addEventListener('click', handleClick)
  }
  
  drawTimeline()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  
  if (timelineCanvas.value) {
    timelineCanvas.value.removeEventListener('mousemove', handleMouseMove)
    timelineCanvas.value.removeEventListener('click', handleClick)
  }
})

watch(() => props.records, () => {
  drawTimeline()
}, { deep: true })

watch([zoomLevel, panOffset], () => {
  drawTimeline()
})
</script>

<style scoped>
.timeline-container {
  width: 100%;
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.timeline-controls {
  display: flex;
  gap: 15px;
  align-items: center;
  margin-bottom: 20px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
}

.zoom-btn, .center-btn {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.zoom-btn:hover:not(:disabled), .center-btn:hover {
  background: #0056b3;
}

.zoom-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.zoom-indicator {
  padding: 8px 16px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-weight: 500;
}

.timeline-wrapper {
  position: relative;
  width: 100%;
  height: 400px;
  overflow: hidden;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fafafa;
}

.timeline-canvas {
  cursor: grab;
  user-select: none;
}

.timeline-canvas:active {
  cursor: grabbing;
}

.timeline-tooltip {
  position: absolute;
  background: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 10px;
  border-radius: 6px;
  pointer-events: none;
  z-index: 1000;
  min-width: 200px;
  font-size: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
}

.tooltip-title {
  font-weight: bold;
  margin-bottom: 5px;
  font-size: 14px;
}

.tooltip-date {
  margin-bottom: 3px;
  opacity: 0.9;
}

.tooltip-category {
  color: #ffd700;
  font-size: 11px;
  margin-bottom: 3px;
}

.tooltip-provider {
  font-size: 11px;
  opacity: 0.8;
}

.timeline-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1px solid #ddd;
}

.legend-label {
  font-size: 13px;
  color: #555;
}
</style>