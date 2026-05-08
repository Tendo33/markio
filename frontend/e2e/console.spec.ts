import { expect, test, type Page, type Route } from '@playwright/test'

const TOKEN_STORAGE_KEY = 'markio_api_token'

function buildJwt(payload: Record<string, unknown>): string {
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url')
  const body = Buffer.from(JSON.stringify(payload)).toString('base64url')
  return `${header}.${body}.signature`
}

function buildValidToken(role: 'user' | 'admin' = 'user'): string {
  return buildJwt({
    sub: `playwright-${role}`,
    role,
    exp: Math.floor(Date.now() / 1000) + 3600,
  })
}

async function seedToken(page: Page, role: 'user' | 'admin' = 'user') {
  const token = buildValidToken(role)
  await page.addInitScript(
    ({ storageKey, storageValue }) => {
      window.localStorage.setItem(storageKey, storageValue)
    },
    { storageKey: TOKEN_STORAGE_KEY, storageValue: token }
  )
  return token
}

function taskRecord(overrides: Record<string, unknown> = {}) {
  return {
    task_id: 'task-e2e-001',
    filename: 'demo.pdf',
    owner_id: 'playwright-user',
    status: 'pending',
    parse_method: 'auto',
    lang: 'ch',
    created_at: '2026-05-07T12:00:00Z',
    started_at: null,
    completed_at: null,
    result: null,
    error_message: null,
    cache_hit: false,
    priority: 0,
    retry_count: 0,
    processing_duration_ms: null,
    ...overrides,
  }
}

function dashboardPayload(overrides: Record<string, unknown> = {}) {
  return {
    stats: {
      pending: 0,
      processing: 0,
      completed: 0,
      failed: 0,
      canceled: 0,
    },
    queue: {
      queued: 0,
      processing: 0,
      workers: 0,
      paused: false,
    },
    success_rate: 0,
    sla: {
      count: 0,
      avg_ms: 0,
      p95_ms: 0,
      max_ms: 0,
    },
    recent_tasks: [],
    updated_at: '2026-05-07T12:00:00Z',
    ...overrides,
  }
}

async function fulfillJson(route: Route, payload: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(payload),
  })
}

async function installStrictApiMock(
  page: Page,
  handler: (route: Route, url: URL) => Promise<boolean> | boolean
) {
  const unexpectedRequests: string[] = []
  await page.route('**/v1/**', async (route) => {
    const url = new URL(route.request().url())
    const handled = await handler(route, url)
    if (handled) {
      return
    }
    unexpectedRequests.push(`${route.request().method()} ${url.pathname}${url.search}`)
    await fulfillJson(
      route,
      {
        error: { message: 'unexpected api request' },
        detail: 'unexpected api request',
      },
      500
    )
  })
  return unexpectedRequests
}

test('shows token banner and does not hit API when no token is configured', async ({ page }) => {
  const apiRequests: string[] = []
  await page.route('**/v1/**', async (route) => {
    apiRequests.push(route.request().url())
    await fulfillJson(route, { error: { message: 'unexpected request' }, detail: 'unexpected request' }, 503)
  })

  await page.goto('/console/tasks')
  await expect(page.getByText('还没有可用的 JWT Token。先在顶部保存 Token，再筛选、翻页和查看任务详情。')).toBeVisible()
  await expect(page.getByText('还没有可用的 JWT Token。先在顶部保存 Token，再查看任务、提交文件或管理队列。')).toBeVisible()

  await page.goto('/console/tasks/task-missing')
  await expect(page.getByText('还没有可用的 JWT Token。先在顶部保存 Token，再查看任务详情和解析结果。')).toBeVisible()

  expect(apiRequests).toEqual([])
})

test('saves token, submits a task, and refreshes dashboard state', async ({ page }) => {
  let dashboardRequests = 0
  let submitRequests = 0

  const unexpectedRequests = await installStrictApiMock(page, async (route, url) => {
    if (url.pathname === '/v1/tasks/dashboard') {
      dashboardRequests += 1
      const payload =
        dashboardRequests >= 2
          ? dashboardPayload({
              stats: {
                pending: 1,
                processing: 0,
                completed: 0,
                failed: 0,
                canceled: 0,
              },
              recent_tasks: [taskRecord()],
            })
          : dashboardPayload()
      await fulfillJson(route, payload)
      return true
    }
    if (url.pathname === '/v1/tasks/submit') {
      submitRequests += 1
      await fulfillJson(route, taskRecord())
      return true
    }
    return false
  })

  await page.goto('/console/tasks/submit')
  await page.locator('input[aria-label="API JWT Token"]').fill(buildValidToken())
  await page.getByRole('button', { name: '保存 API Token' }).click()

  const fileInput = page.locator('#task-submit-file')
  await fileInput.setInputFiles({
    name: 'demo.pdf',
    mimeType: 'application/pdf',
    buffer: Buffer.from('demo pdf payload', 'utf-8'),
  })
  await page.getByRole('button', { name: '提交任务' }).click()

  await expect(page.getByText('任务提交成功')).toBeVisible()
  await expect(page.getByText('"task_id": "task-e2e-001"')).toBeVisible()
  await expect(page.getByText('等待')).toBeVisible()
  await expect(page.locator('nav .font-semibold.text-tertiary')).toHaveText('1')

  expect(submitRequests).toBe(1)
  expect(dashboardRequests).toBeGreaterThanOrEqual(2)
  expect(unexpectedRequests).toEqual([])
})

test('hydrates filters from query params and polls active task lists', async ({ page }) => {
  await seedToken(page)

  let listRequests = 0
  const requestQueries: string[] = []

  const unexpectedRequests = await installStrictApiMock(page, async (route, url) => {
    if (url.pathname === '/v1/tasks/dashboard') {
      await fulfillJson(route, dashboardPayload())
      return true
    }
    if (url.pathname !== '/v1/tasks') {
      return false
    }
    listRequests += 1
    requestQueries.push(url.search)

    const status = url.searchParams.get('status') ?? ''
    const pageSize = url.searchParams.get('page_size') ?? '20'
    const pageNumber = url.searchParams.get('page') ?? '1'
    const isProcessing = status === 'processing'

    const payload = {
      items: isProcessing
        ? [
            taskRecord({
              task_id: `task-processing-${listRequests}`,
              filename: `processing-${listRequests}.pdf`,
              status: 'processing',
            }),
          ]
        : [],
      total: isProcessing ? 11 : 0,
      page: Number(pageNumber),
      page_size: Number(pageSize),
    }
    await fulfillJson(route, payload)
    return true
  })

  await page.goto('/console/tasks?page=2&page_size=10&status=processing')

  await expect(page.locator('#task-status-filter')).toHaveValue('processing')
  await expect(page.locator('#task-page-size-filter')).toHaveValue('10')
  await expect(page.getByRole('cell', { name: 'processing-1.pdf' })).toBeVisible()

  await page.waitForTimeout(5_500)
  expect(listRequests).toBeGreaterThanOrEqual(2)
  expect(requestQueries[0]).toContain('page=2')
  expect(requestQueries[0]).toContain('page_size=10')
  expect(requestQueries[0]).toContain('status=processing')

  await page.locator('#task-status-filter').selectOption('failed')
  await page.locator('#task-page-size-filter').selectOption('50')
  await page.getByRole('button', { name: '应用过滤' }).click()

  await expect(page).toHaveURL(/page=1/)
  await expect(page).toHaveURL(/page_size=50/)
  await expect(page).toHaveURL(/status=failed/)
  expect(unexpectedRequests).toEqual([])
})

test('polls task detail until completion and fetches final result exactly once', async ({ page }) => {
  await seedToken(page)

  let detailRequests = 0
  let includeResultRequests = 0

  const unexpectedRequests = await installStrictApiMock(page, async (route, url) => {
    if (url.pathname === '/v1/tasks/dashboard') {
      await fulfillJson(route, dashboardPayload())
      return true
    }
    if (url.pathname !== '/v1/tasks/task-detail-001') {
      return false
    }

    detailRequests += 1
    const includeResult = url.searchParams.get('include_result') === 'true'
    if (includeResult) {
      includeResultRequests += 1
      await fulfillJson(
        route,
        taskRecord({
          task_id: 'task-detail-001',
          status: 'completed',
          result: '# final markdown',
          started_at: '2026-05-07T12:00:01Z',
          completed_at: '2026-05-07T12:00:07Z',
          processing_duration_ms: 6000,
        })
      )
      return true
    }

    const payload =
      detailRequests < 3
        ? taskRecord({
            task_id: 'task-detail-001',
            status: 'processing',
            started_at: '2026-05-07T12:00:01Z',
          })
        : taskRecord({
            task_id: 'task-detail-001',
            status: 'completed',
            started_at: '2026-05-07T12:00:01Z',
          completed_at: '2026-05-07T12:00:07Z',
          processing_duration_ms: 6000,
        })
    await fulfillJson(route, payload)
    return true
  })

  await page.goto('/console/tasks/task-detail-001')
  await expect(page.getByText('任务详情')).toBeVisible()
  await expect(page.getByText('# final markdown')).toBeVisible({ timeout: 10_000 })

  await page.waitForTimeout(500)
  expect(detailRequests).toBeGreaterThanOrEqual(3)
  expect(includeResultRequests).toBe(1)
  expect(unexpectedRequests).toEqual([])
})

test('clearing token returns the console to the unauthenticated state', async ({ page }) => {
  await seedToken(page)

  let taskListRequests = 0

  const unexpectedRequests = await installStrictApiMock(page, async (route, url) => {
    if (url.pathname === '/v1/tasks/dashboard') {
      await fulfillJson(route, dashboardPayload())
      return true
    }
    if (url.pathname === '/v1/tasks') {
      taskListRequests += 1
      await fulfillJson(route, {
        items: [taskRecord({ task_id: 'task-clear-001', status: 'processing' })],
        total: 1,
        page: 1,
        page_size: 20,
      })
      return true
    }
    return false
  })

  await page.goto('/console/tasks')
  await expect(page.getByRole('cell', { name: 'demo.pdf' })).toBeVisible()

  await page.getByRole('button', { name: '清除 API Token' }).click()

  await expect(page.getByText('当前 JWT Token 无效')).toHaveCount(0)
  await expect(page.getByText('还没有可用的 JWT Token。先在顶部保存 Token，再筛选、翻页和查看任务详情。')).toBeVisible()
  await expect(page.getByText('还没有可用的 JWT Token。先在顶部保存 Token，再查看任务、提交文件或管理队列。')).toBeVisible()
  expect(taskListRequests).toBeGreaterThanOrEqual(1)
  expect(unexpectedRequests).toEqual([])
})
