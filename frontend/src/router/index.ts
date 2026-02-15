import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { title: '仪表盘' },
        },
        {
          path: 'tasks',
          name: 'task-list',
          component: () => import('@/views/TaskList.vue'),
          meta: { title: '任务列表' },
        },
        {
          path: 'tasks/submit',
          name: 'task-submit',
          component: () => import('@/views/TaskSubmit.vue'),
          meta: { title: '提交任务' },
        },
        {
          path: 'tasks/:id',
          name: 'task-detail',
          component: () => import('@/views/TaskDetail.vue'),
          meta: { title: '任务详情' },
        },
        {
          path: 'queue',
          name: 'queue-management',
          component: () => import('@/views/QueueManagement.vue'),
          meta: { title: '队列管理' },
        },
      ],
    },
  ],
})

router.afterEach((to) => {
  const suffix = 'Markio Console'
  if (to.meta.title) {
    document.title = `${String(to.meta.title)} - ${suffix}`
    return
  }
  document.title = suffix
})

export default router
