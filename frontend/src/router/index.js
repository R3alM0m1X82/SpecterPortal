/**
 * Vue Router configuration for SpecterPortal
 * WITH AUTHENTICATION GUARD
 */
import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import Dashboard from '../views/Dashboard.vue'
import TokensView from '../views/TokensView.vue'
import ImportTokens from '../views/ImportTokens.vue'
import EmailsView from '../views/EmailsView.vue'
import EmailReader from '../views/EmailReader.vue'
import FilesView from '../views/FilesView.vue'
import UsersGroupsView from '../views/UsersGroupsView.vue'
import ApplicationsView from '../views/ApplicationsView.vue'
import DevicesView from '../views/DevicesView.vue'
import RolesView from '../views/RolesView.vue'
import AdminUnitsView from '../views/AdminUnitsView.vue'
import TenantView from '../views/TenantView.vue'
import CAPView from '../views/CAPView.vue'
import SharePointView from '../views/SharePointView.vue'
import TeamsView from '../views/TeamsView.vue'
import VirtualMachinesView from '../views/VirtualMachinesView.vue'
import StorageAccountsView from '../views/StorageAccountsView.vue'
import KeyVaultsView from '../views/KeyVaultsView.vue'
import SQLDatabasesView from '../views/SQLDatabasesView.vue'
import AppServicesView from '../views/AppServicesView.vue'
import AutomationAccountsView from '../views/AutomationAccountsView.vue'
import PermissionsView from '../views/PermissionsView.vue'
import EffectivePermissionsView from '../views/EffectivePermissionsView.vue'
import RoleAssignmentsCompleteView from '../views/RoleAssignmentsCompleteView.vue'
import ExternalUsersView from '../views/ExternalUsersView.vue'
import SearchView from '../views/SearchView.vue'
import AdvancedQueriesView from '../views/AdvancedQueriesView.vue'
import SettingsView from '../views/SettingsView.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/tokens',
    name: 'Tokens',
    component: TokensView,
    meta: { requiresAuth: true }
  },
  {
    path: '/import',
    name: 'Import',
    component: ImportTokens,
    meta: { requiresAuth: true }
  },
  {
    path: '/emails',
    name: 'Emails',
    component: EmailsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/emails/:id',
    name: 'EmailReader',
    component: EmailReader,
    meta: { requiresAuth: true }
  },
  {
    path: '/files',
    name: 'Files',
    component: FilesView,
    meta: { requiresAuth: true }
  },
  {
    path: '/users-groups',
    name: 'UsersGroups',
    component: UsersGroupsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/applications',
    name: 'Applications',
    component: ApplicationsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/devices',
    name: 'Devices',
    component: DevicesView,
    meta: { requiresAuth: true }
  },
  {
    path: '/roles-licenses',
    name: 'Roles',
    component: RolesView,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin-units',
    name: 'AdminUnits',
    component: AdminUnitsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/tenant',
    name: 'Tenant',
    component: TenantView,
    meta: { requiresAuth: true }
  },
  {
    path: '/cap',
    name: 'CAP',
    component: CAPView,
    meta: { requiresAuth: true }
  },
  {
    path: '/external-users',
    name: 'ExternalUsers',
    component: ExternalUsersView,
    meta: { requiresAuth: true }
  },
  {
    path: '/sharepoint',
    name: 'SharePoint',
    component: SharePointView,
    meta: { requiresAuth: true }
  },
  {
    path: '/teams',
    name: 'Teams',
    component: TeamsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/search',
    name: 'Search',
    component: SearchView,
    meta: { requiresAuth: true }
  },
  {
    path: '/advanced-queries',
    name: 'AdvancedQueries',
    component: AdvancedQueriesView,
    meta: { requiresAuth: true }
  },
  // Azure Resources - Separate Views
  {
    path: '/azure/virtual-machines',
    name: 'VirtualMachines',
    component: VirtualMachinesView,
    meta: { requiresAuth: true }
  },
  {
    path: '/azure/storage-accounts',
    name: 'StorageAccounts',
    component: StorageAccountsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/azure/key-vaults',
    name: 'KeyVaults',
    component: KeyVaultsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/azure/sql-databases',
    name: 'SQLDatabases',
    component: SQLDatabasesView,
    meta: { requiresAuth: true }
  },
  {
    path: '/azure/app-services',
    name: 'AppServices',
    component: AppServicesView,
    meta: { requiresAuth: true }
  },
  {
    path: '/azure/automation-accounts',
    name: 'AutomationAccounts',
    component: AutomationAccountsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/azure/permissions',
    name: 'AzurePermissions',
    component: PermissionsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/azure/permissions/effective',
    name: 'EffectivePermissions',
    component: EffectivePermissionsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/azure/permissions/assignments',
    name: 'RoleAssignmentsComplete',
    component: RoleAssignmentsCompleteView,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: SettingsView,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
  
  if (requiresAuth) {
    // Check if user has stored auth
    const hasStoredAuth = !!(
      localStorage.getItem('specter_auth') || 
      sessionStorage.getItem('specter_auth')
    )
    
    if (!hasStoredAuth) {
      // No stored auth, redirect to login
      next({ name: 'Login' })
      return
    }
    
    // Verify session with backend
    try {
      const response = await fetch('http://localhost:5000/api/auth/verify', {
        credentials: 'include'
      })
      
      const data = await response.json()
      
      if (data.success && data.authenticated) {
        // Authenticated, allow navigation
        next()
      } else {
        // Session invalid, clear storage and redirect
        localStorage.removeItem('specter_auth')
        sessionStorage.removeItem('specter_auth')
        next({ name: 'Login' })
      }
    } catch (err) {
      console.error('Auth verification failed:', err)
      next({ name: 'Login' })
    }
  } else {
    // Public route, allow
    next()
  }
})

export default router
