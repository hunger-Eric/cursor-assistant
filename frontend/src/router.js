import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import Providers from './views/Providers.vue'
import Settings from './views/Settings.vue'

const routes = [
  { path: '/', component: Dashboard },
  { path: '/providers', component: Providers },
  { path: '/settings', component: Settings },
]

export default createRouter({ history: createWebHistory(), routes })
