import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useCopilotStore = defineStore('copilot', () => {
  const isOpen = ref(false)
  const context = ref<Record<string, any> | undefined>(undefined)

  const open = (ctx?: Record<string, any>) => {
    context.value = ctx
    isOpen.value = true
  }

  const close = () => {
    isOpen.value = false
  }

  const toggle = () => {
    isOpen.value = !isOpen.value
  }

  return { isOpen, context, open, close, toggle }
})
