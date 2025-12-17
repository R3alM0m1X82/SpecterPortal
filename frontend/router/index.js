/**
 * Vue Router configuration
 */
import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import TokensView from '../views/TokensView.vue'
import ImportTokens from '../views/ImportTokens.vue'
import EmailsView from '../views/EmailsView.vue'
import EmailReader from '../views/EmailReader.vue'
import FilesView from '../views/FilesView.vue'
import UsersView from '../views/UsersView.vue'
import ApplicationsView from '../views/ApplicationsView.vue'
import DevicesView from '../views/DevicesView.vue'
import GroupsView from '../views/GroupsView.vue'
import TenantView from '../views/TenantView.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/tokens',
    name: 'Tokens',
    component: TokensView
  },
  {
    path: '/import',
    name: 'Import',
    component: ImportTokens
  },
  {
    path: '/emails',
    name: 'Emails',
    component: EmailsView
  },
  {
    path: '/emails/:id',
    name: 'EmailReader',
    component: EmailReader
  },
  {
    path: '/files',
    name: 'Files',
    component: FilesView
  },
  {
    path: '/users',
    name: 'Users',
    component: UsersView
  },
  {
    path: '/applications',
    name: 'Applications',
    component: ApplicationsView
  },
  {
    path: '/devices',
    name: 'Devices',
    component: DevicesView
  },
  {
    path: '/groups',
    name: 'Groups',
    component: GroupsView
  },
  {
    path: '/tenant',
    name: 'Tenant',
    component: TenantView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
