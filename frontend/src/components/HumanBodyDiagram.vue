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
          <!-- Hair -->
          <path d="M75 25 Q75 15 85 12 Q92 8 100 8 Q108 8 115 12 Q125 15 125 25 Q125 30 122 35 L120 30 Q115 20 100 20 Q85 20 80 30 L78 35 Q75 30 75 25" 
                fill="#4a4a4a" stroke="#333" stroke-width="1" opacity="0.9"/>
          
          <!-- Head -->
          <g @click="toggleBodyPart('head')" class="body-part" :class="{ selected: isSelected('head') }">
            <ellipse cx="100" cy="40" rx="25" ry="30" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
          </g>
          
          <!-- Eyes -->
          <g @click="toggleBodyPart('eyes')" class="body-part" :class="{ selected: isSelected('eyes') }">
            <!-- Invisible larger hit area -->
            <rect x="80" y="28" width="40" height="14" fill="transparent" stroke="none"/>
            <circle cx="90" cy="35" r="4" fill="#fff" stroke="#333" stroke-width="1"/>
            <circle cx="110" cy="35" r="4" fill="#fff" stroke="#333" stroke-width="1"/>
            <circle cx="90" cy="35" r="2" fill="#333"/>
            <circle cx="110" cy="35" r="2" fill="#333"/>
          </g>
          
          <!-- Glasses (optional visual indicator) -->
          <g @click="toggleBodyPart('glasses')" class="body-part" :class="{ selected: isSelected('glasses') || isSelected('contact_lenses') || isSelected('vision') }">
            <!-- Invisible larger hit area -->
            <rect x="70" y="27" width="60" height="16" fill="transparent" stroke="none"/>
            <path d="M75 35 Q85 33 90 35 T105 35 Q110 33 120 35" 
                  fill="none" stroke="#555" stroke-width="1.5" opacity="0.6"/>
            <circle cx="90" cy="35" r="8" fill="none" stroke="#555" stroke-width="1.5" opacity="0.6"/>
            <circle cx="110" cy="35" r="8" fill="none" stroke="#555" stroke-width="1.5" opacity="0.6"/>
          </g>
          
          <!-- Nose -->
          <g @click="toggleBodyPart('nose')" class="body-part" :class="{ selected: isSelected('nose') }">
            <!-- Invisible larger hit area -->
            <rect x="92" y="36" width="16" height="12" fill="transparent" stroke="none"/>
            <path d="M100 38 L97 45 L100 46 L103 45 Z" fill="#f9c4aa" stroke="#333" stroke-width="1"/>
          </g>
          
          <!-- Mouth/Teeth -->
          <g @click="toggleBodyPart('teeth')" class="body-part" :class="{ selected: isSelected('teeth') || isSelected('dental') }">
            <!-- Invisible larger hit area -->
            <rect x="88" y="48" width="24" height="10" fill="transparent" stroke="none"/>
            <path d="M92 52 Q100 55 108 52" fill="none" stroke="#333" stroke-width="1"/>
            <rect x="94" y="51" width="3" height="2" fill="#fff" stroke="#333" stroke-width="0.5"/>
            <rect x="98" y="51" width="3" height="2" fill="#fff" stroke="#333" stroke-width="0.5"/>
            <rect x="102" y="51" width="3" height="2" fill="#fff" stroke="#333" stroke-width="0.5"/>
          </g>
          
          <!-- Ears -->
          <g @click="toggleBodyPart('ears')" class="body-part" :class="{ selected: isSelected('ears') }">
            <!-- Invisible larger hit areas -->
            <rect x="68" y="32" width="12" height="16" fill="transparent" stroke="none"/>
            <rect x="120" y="32" width="12" height="16" fill="transparent" stroke="none"/>
            <ellipse cx="74" cy="40" rx="5" ry="8" fill="#fdbcb4" stroke="#333" stroke-width="1"/>
            <ellipse cx="126" cy="40" rx="5" ry="8" fill="#fdbcb4" stroke="#333" stroke-width="1"/>
          </g>
          
          <!-- Throat/Neck -->
          <g @click="toggleBodyPart('throat')" class="body-part" :class="{ selected: isSelected('throat') }">
            <rect x="90" y="65" width="20" height="15" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
          </g>
          
          <!-- Chest -->
          <g @click="toggleBodyPart('chest')" class="body-part" :class="{ selected: isSelected('chest') }">
            <rect x="70" y="80" width="60" height="60" rx="5" fill="#e8d5c4" stroke="#333" stroke-width="1.5"/>
          </g>
          
          <!-- Arms -->
          <g @click="toggleBodyPart('left_arm')" class="body-part" :class="{ selected: isSelected('left_arm') }">
            <rect x="45" y="85" width="20" height="80" rx="10" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
          </g>
          
          <g @click="toggleBodyPart('right_arm')" class="body-part" :class="{ selected: isSelected('right_arm') }">
            <rect x="135" y="85" width="20" height="80" rx="10" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
          </g>
          
          <!-- Hands -->
          <g @click="toggleBodyPart('left_hand')" class="body-part" :class="{ selected: isSelected('left_hand') }">
            <circle cx="55" cy="175" r="12" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
          </g>
          <g @click="toggleBodyPart('right_hand')" class="body-part" :class="{ selected: isSelected('right_hand') }">
            <circle cx="145" cy="175" r="12" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
          </g>
          
          <!-- Abdomen -->
          <g @click="toggleBodyPart('abdomen')" class="body-part" :class="{ selected: isSelected('abdomen') }">
            <rect x="70" y="140" width="60" height="50" fill="#e8d5c4" stroke="#333" stroke-width="1.5"/>
          </g>
          
          <!-- Pelvis -->
          <g @click="toggleBodyPart('pelvis')" class="body-part" :class="{ selected: isSelected('pelvis') }">
            <rect x="70" y="190" width="60" height="30" fill="#e8d5c4" stroke="#333" stroke-width="1.5"/>
          </g>
          
          <!-- Legs -->
          <g @click="toggleBodyPart('left_leg')" class="body-part" :class="{ selected: isSelected('left_leg') }">
            <rect x="75" y="220" width="20" height="100" rx="10" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
          </g>
          
          <g @click="toggleBodyPart('right_leg')" class="body-part" :class="{ selected: isSelected('right_leg') }">
            <rect x="105" y="220" width="20" height="100" rx="10" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
          </g>
          
          <!-- Feet -->
          <g @click="toggleBodyPart('left_foot')" class="body-part" :class="{ selected: isSelected('left_foot') }">
            <ellipse cx="85" cy="335" rx="15" ry="20" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
          </g>
          <g @click="toggleBodyPart('right_foot')" class="body-part" :class="{ selected: isSelected('right_foot') }">
            <ellipse cx="115" cy="335" rx="15" ry="20" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
          </g>
        </svg>
        
        <!-- Back View -->
        <svg v-else-if="currentView === 'back'" viewBox="0 0 200 400" class="body-svg">
          <!-- Hair (back) -->
          <path d="M75 25 Q75 15 85 12 Q92 8 100 8 Q108 8 115 12 Q125 15 125 25 Q125 35 120 45 L115 40 Q110 30 100 30 Q90 30 85 40 L80 45 Q75 35 75 25" 
                fill="#4a4a4a" stroke="#333" stroke-width="1" opacity="0.9"/>
          
          <!-- Head back -->
          <g @click="toggleBodyPart('head_back')" class="body-part" :class="{ selected: isSelected('head_back') }">
            <ellipse cx="100" cy="40" rx="25" ry="30" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
          </g>
          
          <g @click="toggleBodyPart('upper_back')" class="body-part" :class="{ selected: isSelected('upper_back') }">
            <rect x="70" y="80" width="60" height="60" rx="5" fill="#e8d5c4" stroke="#333" stroke-width="1.5"/>
          </g>
          
          <g @click="toggleBodyPart('lower_back')" class="body-part" :class="{ selected: isSelected('lower_back') }">
            <rect x="70" y="140" width="60" height="50" fill="#e8d5c4" stroke="#333" stroke-width="1.5"/>
          </g>
          
          <g @click="toggleBodyPart('buttocks')" class="body-part" :class="{ selected: isSelected('buttocks') }">
            <rect x="70" y="190" width="60" height="30" fill="#e8d5c4" stroke="#333" stroke-width="1.5"/>
          </g>
          
          <!-- Back view legs and arms -->
          <g @click="toggleBodyPart('left_arm')" class="body-part" :class="{ selected: isSelected('left_arm') }">
            <rect x="45" y="85" width="20" height="80" rx="10" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
          </g>
          <g @click="toggleBodyPart('right_arm')" class="body-part" :class="{ selected: isSelected('right_arm') }">
            <rect x="135" y="85" width="20" height="80" rx="10" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
          </g>
          <g @click="toggleBodyPart('left_leg')" class="body-part" :class="{ selected: isSelected('left_leg') }">
            <rect x="75" y="220" width="20" height="100" rx="10" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
          </g>
          <g @click="toggleBodyPart('right_leg')" class="body-part" :class="{ selected: isSelected('right_leg') }">
            <rect x="105" y="220" width="20" height="100" rx="10" fill="#fdbcb4" stroke="#333" stroke-width="1.5"/>
          </g>
        </svg>
        
        <!-- Systems View -->
        <div v-else-if="currentView === 'systems'" class="systems-view">
          <div class="search-container">
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Search body areas..."
              class="search-input"
            />
          </div>
          <div class="systems-grid">
            <button v-for="system in filteredSystems" :key="system.id" 
                    @click="toggleBodyPart(system.id)"
                    :class="{ selected: isSelected(system.id) }"
                    class="system-btn">
              <span class="system-icon">{{ system.icon }}</span>
              <span class="system-name">{{ system.name }}</span>
            </button>
          </div>
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
const searchQuery = ref('')

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
  { id: 'glasses', name: 'Glasses/Frames', icon: '👓' },
  { id: 'contact_lenses', name: 'Contact Lenses', icon: '👁‍🗨' },
  { id: 'vision', name: 'Vision/Prescription', icon: '🔍' },
  { id: 'ears', name: 'Ears', icon: '👂' },
  { id: 'nose', name: 'Nose', icon: '👃' },
  { id: 'throat', name: 'Throat', icon: '🗣️' },
  { id: 'dental', name: 'Teeth', icon: '🦷' },
  { id: 'allergy', name: 'Allergy', icon: '🤧' }
]

const filteredSystems = computed(() => {
  if (!searchQuery.value) return bodySystems
  const query = searchQuery.value.toLowerCase()
  return bodySystems.filter(system => 
    system.name.toLowerCase().includes(query) || 
    system.id.toLowerCase().includes(query)
  )
})

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
}

.body-part.selected rect,
.body-part.selected ellipse,
.body-part.selected circle,
.body-part.selected path {
  fill: #ef4444 !important;
  stroke: #dc2626 !important;
  stroke-width: 2.5 !important;
}

.body-part.selected circle[fill="#333"],
.body-part.selected circle[fill="#fff"] {
  stroke: #dc2626 !important;
  stroke-width: 2 !important;
}

.body-part.selected path[fill="none"] {
  fill: none !important;
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

/* Systems View */
.systems-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.search-container {
  padding: 0 1rem;
}

.search-input {
  width: 100%;
  padding: 0.5rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Systems Grid */
.systems-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 0.75rem;
  padding: 0 1rem 1rem;
  max-height: 300px;
  overflow-y: auto;
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