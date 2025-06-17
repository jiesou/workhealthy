import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import MonitorsOverview from './views/MonitorsOverview.vue'
import Settings from './views/Settings.vue'
import History from './views/History.vue'
import FaceSignin from './views/FaceSignin.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/monitors-overview',
      name: 'monitors-overview',
      component: MonitorsOverview
    },
    {
      path: '/settings',
      name: 'settings',
      component: Settings
    },
    {
      path: '/history',
      name: 'history',
      component: History
    },
    {
      path: '/face-signin',
      name: 'face-signin',
      component: FaceSignin
    }
  ]
})

export default router 