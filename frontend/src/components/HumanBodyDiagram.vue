<template>
  <div class="body-diagram-container">
    <div class="body-selector">
      <div class="view-toggle">
        <button @click="currentView = 'front'" :class="{ active: currentView === 'front' }">Front</button>
        <button @click="currentView = 'back'" :class="{ active: currentView === 'back' }">Back</button>
        <button @click="currentView = 'systems'" :class="{ active: currentView === 'systems' }">Systems</button>
      </div>
      
      <div class="body-svg-wrapper">
        <!-- Front View -->
        <svg v-if="currentView === 'front'" viewBox="0 0 200 400" class="body-svg">
          <!-- Head -->
          <g @click="toggleBodyPart('head')" class="body-part" :class="{ selected: isSelected('head') }">
            <ellipse cx="100" cy="40" rx="25" ry="30" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
            <text x="100" y="45" text-anchor="middle" class="label">Head</text>
          </g>
          
          <!-- Neck -->
          <rect @click="toggleBodyPart('neck')" :class="{ selected: isSelected('neck') }"
                x="90" y="65" width="20" height="15" fill="#fdbcb4" stroke="#333" stroke-width="1.5" class="body-part"/>
          
          <!-- Chest -->
          <g @click="toggleBodyPart('chest')" class="body-part" :class="{ selected: isSelected('chest') }">
            <rect x="70" y="80" width="60" height="60" rx="5" fill="#e8d5c4" stroke="#333" stroke-width="1.5"/>
            <text x="100" y="115" text-anchor="middle" class="label">Chest</text>
          </g>
          
          <!-- Arms -->
          <g @click="toggleBodyPart('left_arm')" class="body-part" :class="{ selected: isSelected('left_arm') }">
            <rect x="45" y="85" width="20" height="80" rx="10" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
            <text x="55" y="125" text-anchor="middle" class="label-small">L Arm</text>
          </g>
          
          <g @click="toggleBodyPart('right_arm')" class="body-part" :class="{ selected: isSelected('right_arm') }">
            <rect x="135" y="85" width="20" height="80" rx="10" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
            <text x="145" y="125" text-anchor="middle" class="label-small">R Arm</text>
          </g>
          
          <!-- Hands -->
          <circle @click="toggleBodyPart('left_hand')" :class="{ selected: isSelected('left_hand') }"
                  cx="55" cy="175" r="12" fill="#fdbcb4" stroke="#333" stroke-width="1.5" class="body-part"/>
          <circle @click="toggleBodyPart('right_hand')" :class="{ selected: isSelected('right_hand') }"
                  cx="145" cy="175" r="12" fill="#fdbcb4" stroke="#333" stroke-width="1.5" class="body-part"/>
          
          <!-- Abdomen -->
          <g @click="toggleBodyPart('abdomen')" class="body-part" :class="{ selected: isSelected('abdomen') }">
            <rect x="70" y="140" width="60" height="50" fill="#e8d5c4" stroke="#333" stroke-width="1.5"/>
            <text x="100" y="170" text-anchor="middle" class="label">Abdomen</text>
          </g>
          
          <!-- Pelvis -->
          <g @click="toggleBodyPart('pelvis')" class="body-part" :class="{ selected: isSelected('pelvis') }">
            <rect x="70" y="190" width="60" height="30" fill="#e8d5c4" stroke="#333" stroke-width="1.5"/>
            <text x="100" y="210" text-anchor="middle" class="label">Pelvis</text>
          </g>
          
          <!-- Legs -->
          <g @click="toggleBodyPart('left_leg')" class="body-part" :class="{ selected: isSelected('left_leg') }">
            <rect x="75" y="220" width="20" height="100" rx="10" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
            <text x="85" y="270" text-anchor="middle" class="label-small">L Leg</text>
          </g>
          
          <g @click="toggleBodyPart('right_leg')" class="body-part" :class="{ selected: isSelected('right_leg') }">
            <rect x="105" y="220" width="20" height="100" rx="10" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
            <text x="115" y="270" text-anchor="middle" class="label-small">R Leg</text>
          </g>
          
          <!-- Feet -->
          <ellipse @click="toggleBodyPart('left_foot')" :class="{ selected: isSelected('left_foot') }"
                   cx="85" cy="335" rx="15" ry="20" fill="#fdbcb4" stroke="#333" stroke-width="1.5" class="body-part"/>
          <ellipse @click="toggleBodyPart('right_foot')" :class="{ selected: isSelected('right_foot') }"
                   cx="115" cy="335" rx="15" ry="20" fill="#fdbcb4" stroke="#333" stroke-width="1.5" class="body-part"/>
        </svg>
        
        <!-- Back View -->
        <svg v-else-if="currentView === 'back'" viewBox="0 0 200 400" class="body-svg">
          <!-- Similar structure but for back view -->
          <g @click="toggleBodyPart('head_back')" class="body-part" :class="{ selected: isSelected('head_back') }">
            <ellipse cx="100" cy="40" rx="25" ry="30" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
            <text x="100" y="45" text-anchor="middle" class="label">Head</text>
          </g>
          
          <g @click="toggleBodyPart('upper_back')" class="body-part" :class="{ selected: isSelected('upper_back') }">
            <rect x="70" y="80" width="60" height="60" rx="5" fill="#e8d5c4" stroke="#333" stroke-width="1.5"/>
            <text x="100" y="115" text-anchor="middle" class="label">Upper Back</text>
          </g>
          
          <g @click="toggleBodyPart('lower_back')" class="body-part" :class="{ selected: isSelected('lower_back') }">
            <rect x="70" y="140" width="60" height="50" fill="#e8d5c4" stroke="#333" stroke-width="1.5"/>
            <text x="100" y="170" text-anchor="middle" class="label">Lower Back</text>
          </g>
          
          <g @click="toggleBodyPart('buttocks')" class="body-part" :class="{ selected: isSelected('buttocks') }">
            <rect x="70" y="190" width="60" height="30" fill="#e8d5c4" stroke="#333" stroke-width="1.5"/>
            <text x="100" y="210" text-anchor="middle" class="label">Buttocks</text>
          </g>
        </svg>
        
        <!-- Systems View -->
        <div v-else-if="currentView === 'systems'" class="systems-grid">
          <button v-for="system in bodySystems" :key="system.id" 
                  @click="toggleBodyPart(system.id)"
                  :class="{ selected: isSelected(system.id) }"
                  class="system-btn">
            <span class="system-icon">{{ system.icon }}</span>
            <span class="system-name">{{ system.name }}</span>
          </button>
        </div>
      </div>
      
      <!-- Selected Parts Display -->
      <div v-if="selectedParts.length > 0" class="selected-parts">
        <h4>Selected Areas:</h4>
        <div class="parts-list">
          <span v-for="part in selectedParts" :key="part" class="part-tag">
            {{ formatPartName(part) }}
            <button @click="removeBodyPart(part)" class="remove-btn">✕</button>
          </span>
        </div>
        <button @click="clearAll" class="clear-all-btn">Clear All</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  readonly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const currentView = ref('front')
const selectedParts = ref([...props.modelValue])

const bodySystems = [
  { id: 'nervous_system', name: 'Nervous', icon: '🧠' },
  { id: 'cardiovascular', name: 'Heart/Blood', icon: '❤️' },
  { id: 'respiratory', name: 'Lungs', icon: '🫁' },
  { id: 'digestive', name: 'Digestive', icon: '🍽️' },
  { id: 'skeletal', name: 'Bones', icon: '🦴' },
  { id: 'muscular', name: 'Muscles', icon: '💪' },
  { id: 'immune', name: 'Immune', icon: '🛡️' },
  { id: 'endocrine', name: 'Hormones', icon: '⚗️' },
  { id: 'urinary', name: 'Urinary', icon: '💧' },
  { id: 'reproductive', name: 'Reproductive', icon: '👶' },
  { id: 'skin', name: 'Skin', icon: '🤚' },
  { id: 'eyes', name: 'Eyes', icon: '👁️' },
  { id: 'ears', name: 'Ears', icon: '👂' },
  { id: 'dental', name: 'Teeth', icon: '🦷' }
]

const isSelected = (part) => {
  return selectedParts.value.includes(part)
}

const toggleBodyPart = (part) => {
  if (props.readonly) return
  
  const index = selectedParts.value.indexOf(part)
  if (index > -1) {
    selectedParts.value.splice(index, 1)
  } else {
    selectedParts.value.push(part)
  }
  emit('update:modelValue', selectedParts.value)
}

const removeBodyPart = (part) => {
  if (props.readonly) return
  
  const index = selectedParts.value.indexOf(part)
  if (index > -1) {
    selectedParts.value.splice(index, 1)
  }
  emit('update:modelValue', selectedParts.value)
}

const clearAll = () => {
  if (props.readonly) return
  selectedParts.value = []
  emit('update:modelValue', selectedParts.value)
}

const formatPartName = (part) => {
  return part.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

watch(() => props.modelValue, (newVal) => {
  selectedParts.value = [...newVal]
}, { deep: true })
</script>

<style scoped>
.body-diagram-container {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

.body-selector {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.view-toggle {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  justify-content: center;
}

.view-toggle button {
  padding: 0.5rem 1rem;
  border: 2px solid #e2e8f0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.view-toggle button:hover {
  background: #f8fafc;
}

.view-toggle button.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.body-svg-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.body-svg {
  width: 100%;
  max-width: 250px;
  height: auto;
}

.body-part {
  cursor: pointer;
  transition: all 0.2s;
}

.body-part:hover {
  opacity: 0.8;
  transform: scale(1.05);
}

.body-part.selected {
  fill: #ef4444 !important;
  stroke: #dc2626 !important;
  stroke-width: 2.5 !important;
}

.label {
  font-size: 10px;
  font-weight: 600;
  pointer-events: none;
  fill: #333;
}

.label-small {
  font-size: 8px;
  font-weight: 500;
  pointer-events: none;
  fill: #333;
}

/* Systems Grid */
.systems-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 0.75rem;
  padding: 1rem;
}

.system-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.system-btn:hover {
  background: #f8fafc;
  transform: translateY(-2px);
}

.system-btn.selected {
  background: #fee2e2;
  border-color: #ef4444;
}

.system-icon {
  font-size: 1.5rem;
}

.system-name {
  font-size: 0.75rem;
  font-weight: 500;
  text-align: center;
}

/* Selected Parts Display */
.selected-parts {
  border-top: 1px solid #e2e8f0;
  padding-top: 1rem;
}

.selected-parts h4 {
  margin: 0 0 0.75rem 0;
  color: #475569;
  font-size: 0.875rem;
  font-weight: 600;
}

.parts-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.part-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.75rem;
  background: #fee2e2;
  color: #dc2626;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 500;
}

.remove-btn {
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 10px;
}

.clear-all-btn {
  padding: 0.375rem 0.75rem;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-all-btn:hover {
  background: #e5e7eb;
}
</style>