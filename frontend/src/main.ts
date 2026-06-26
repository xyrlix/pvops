import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import '@/styles/theme.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { initTheme } from '@/composables/useTheme'

import App from './App.vue'
import router from './router'

// SPA fallback for GitHub Pages (see public/404.html): when 404.html
// redirects here, restore the originally requested URL before the
// router boots so Vue Router renders the right view.
{
  const redirect = sessionStorage.getItem('pvops:redirect')
  if (redirect) {
    sessionStorage.removeItem('pvops:redirect')
    history.replaceState(null, '', redirect)
  }
}

initTheme()

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
