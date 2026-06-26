import { create } from 'zustand'

export interface Notification {
  id: string
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  read: boolean
  created_at: string
}

interface UIState {
  sidebarOpen: boolean
  sidebarCollapsed: boolean
  notifications: Notification[]
  unreadCount: number
  theme: 'dark'
  pageTitle: string
}

interface UIActions {
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setSidebarCollapsed: (collapsed: boolean) => void
  addNotification: (notification: Omit<Notification, 'id' | 'read' | 'created_at'>) => void
  markNotificationRead: (id: string) => void
  markAllNotificationsRead: () => void
  clearNotifications: () => void
  setPageTitle: (title: string) => void
}

type UIStore = UIState & UIActions

export const useUIStore = create<UIStore>((set, get) => ({
  // State
  sidebarOpen: true,
  sidebarCollapsed: false,
  notifications: [
    {
      id: '1',
      title: 'Prediction Complete',
      message: 'Your granite sample analysis is ready',
      type: 'success',
      read: false,
      created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    },
    {
      id: '2',
      title: 'Dataset Ready',
      message: 'Your uploaded dataset has been processed',
      type: 'info',
      read: false,
      created_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    },
    {
      id: '3',
      title: 'Report Generated',
      message: 'Basalt analysis report is ready for download',
      type: 'success',
      read: true,
      created_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
    },
  ],
  unreadCount: 2,
  theme: 'dark',
  pageTitle: 'Dashboard',

  // Actions
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

  addNotification: (notification) => {
    const newNotif: Notification = {
      ...notification,
      id: Date.now().toString(),
      read: false,
      created_at: new Date().toISOString(),
    }
    set((state) => ({
      notifications: [newNotif, ...state.notifications],
      unreadCount: state.unreadCount + 1,
    }))
  },

  markNotificationRead: (id) => {
    set((state) => {
      const notifications = state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      )
      return {
        notifications,
        unreadCount: notifications.filter((n) => !n.read).length,
      }
    })
  },

  markAllNotificationsRead: () => {
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    }))
  },

  clearNotifications: () => set({ notifications: [], unreadCount: 0 }),

  setPageTitle: (title) => set({ pageTitle: title }),
}))
