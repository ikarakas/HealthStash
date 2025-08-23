import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('should register a new user', async ({ page }) => {
    await page.click('text=Register')
    
    await page.fill('[name="full_name"]', 'Test User')
    await page.fill('[name="email"]', `test${Date.now()}@example.com`)
    await page.fill('[name="password"]', 'SecurePass123!')
    await page.fill('[name="confirm_password"]', 'SecurePass123!')
    
    await page.click('button[type="submit"]')
    
    await expect(page).toHaveURL('/dashboard')
    await expect(page.locator('text=Welcome, Test User')).toBeVisible()
  })

  test('should login with valid credentials', async ({ page }) => {
    // First register
    const email = `test${Date.now()}@example.com`
    await page.goto('/register')
    await page.fill('[name="full_name"]', 'Login Test')
    await page.fill('[name="email"]', email)
    await page.fill('[name="password"]', 'TestPass123!')
    await page.fill('[name="confirm_password"]', 'TestPass123!')
    await page.click('button[type="submit"]')
    
    // Logout
    await page.click('text=Logout')
    
    // Login
    await page.goto('/login')
    await page.fill('[name="email"]', email)
    await page.fill('[name="password"]', 'TestPass123!')
    await page.click('button[type="submit"]')
    
    await expect(page).toHaveURL('/dashboard')
    await expect(page.locator('text=Welcome, Login Test')).toBeVisible()
  })

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login')
    await page.fill('[name="email"]', 'nonexistent@example.com')
    await page.fill('[name="password"]', 'WrongPassword')
    await page.click('button[type="submit"]')
    
    await expect(page.locator('.error-message')).toContainText('Invalid credentials')
    await expect(page).toHaveURL('/login')
  })

  test('should validate registration form', async ({ page }) => {
    await page.goto('/register')
    
    // Test empty form submission
    await page.click('button[type="submit"]')
    await expect(page.locator('.field-error')).toHaveCount(4)
    
    // Test invalid email
    await page.fill('[name="email"]', 'invalid-email')
    await page.click('button[type="submit"]')
    await expect(page.locator('.field-error')).toContainText('valid email')
    
    // Test password mismatch
    await page.fill('[name="email"]', 'test@example.com')
    await page.fill('[name="password"]', 'Password123!')
    await page.fill('[name="confirm_password"]', 'DifferentPass123!')
    await page.click('button[type="submit"]')
    await expect(page.locator('.field-error')).toContainText('Passwords do not match')
    
    // Test weak password
    await page.fill('[name="password"]', 'weak')
    await page.fill('[name="confirm_password"]', 'weak')
    await page.click('button[type="submit"]')
    await expect(page.locator('.field-error')).toContainText('at least 8 characters')
  })

  test('should handle password reset flow', async ({ page }) => {
    await page.goto('/login')
    await page.click('text=Forgot Password?')
    
    await page.fill('[name="email"]', 'test@example.com')
    await page.click('button[type="submit"]')
    
    await expect(page.locator('.success-message')).toContainText('Password reset email sent')
  })

  test('should maintain session across page refreshes', async ({ page, context }) => {
    // Register and login
    const email = `test${Date.now()}@example.com`
    await page.goto('/register')
    await page.fill('[name="full_name"]', 'Session Test')
    await page.fill('[name="email"]', email)
    await page.fill('[name="password"]', 'TestPass123!')
    await page.fill('[name="confirm_password"]', 'TestPass123!')
    await page.click('button[type="submit"]')
    
    await expect(page).toHaveURL('/dashboard')
    
    // Refresh page
    await page.reload()
    await expect(page).toHaveURL('/dashboard')
    await expect(page.locator('text=Welcome, Session Test')).toBeVisible()
    
    // Navigate to different page and back
    await page.goto('/records')
    await expect(page.locator('h1')).toContainText('Health Records')
    
    await page.goto('/dashboard')
    await expect(page.locator('text=Welcome, Session Test')).toBeVisible()
  })

  test('should logout successfully', async ({ page }) => {
    // Register and login
    const email = `test${Date.now()}@example.com`
    await page.goto('/register')
    await page.fill('[name="full_name"]', 'Logout Test')
    await page.fill('[name="email"]', email)
    await page.fill('[name="password"]', 'TestPass123!')
    await page.fill('[name="confirm_password"]', 'TestPass123!')
    await page.click('button[type="submit"]')
    
    // Logout
    await page.click('text=Logout')
    await expect(page).toHaveURL('/login')
    
    // Try to access protected route
    await page.goto('/dashboard')
    await expect(page).toHaveURL('/login')
  })

  test('should handle concurrent login attempts', async ({ browser }) => {
    const email = `concurrent${Date.now()}@example.com`
    
    // First register the user
    const setupPage = await browser.newPage()
    await setupPage.goto('/register')
    await setupPage.fill('[name="full_name"]', 'Concurrent Test')
    await setupPage.fill('[name="email"]', email)
    await setupPage.fill('[name="password"]', 'TestPass123!')
    await setupPage.fill('[name="confirm_password"]', 'TestPass123!')
    await setupPage.click('button[type="submit"]')
    await setupPage.click('text=Logout')
    await setupPage.close()
    
    // Create multiple pages
    const pages = await Promise.all([
      browser.newPage(),
      browser.newPage(),
      browser.newPage()
    ])
    
    // Login from all pages simultaneously
    const loginPromises = pages.map(async (page) => {
      await page.goto('/login')
      await page.fill('[name="email"]', email)
      await page.fill('[name="password"]', 'TestPass123!')
      await page.click('button[type="submit"]')
      return page
    })
    
    const results = await Promise.all(loginPromises)
    
    // All should successfully login
    for (const page of results) {
      await expect(page).toHaveURL('/dashboard')
      await page.close()
    }
  })
})