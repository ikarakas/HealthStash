import { test, expect } from '@playwright/test'
import path from 'path'

test.describe('Health Records Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    const email = `test${Date.now()}@example.com`
    await page.goto('/register')
    await page.fill('[name="full_name"]', 'Records Test')
    await page.fill('[name="email"]', email)
    await page.fill('[name="password"]', 'TestPass123!')
    await page.fill('[name="confirm_password"]', 'TestPass123!')
    await page.click('button[type="submit"]')
    
    await page.goto('/records')
  })

  test('should create a new health record', async ({ page }) => {
    await page.click('text=Add New Record')
    
    await page.fill('[name="title"]', 'Blood Test Results')
    await page.selectOption('[name="record_type"]', 'lab_result')
    await page.selectOption('[name="category"]', 'laboratory')
    await page.fill('[name="record_date"]', '2024-01-20')
    await page.fill('[name="description"]', 'Annual blood work checkup')
    
    await page.click('button:has-text("Save")')
    
    await expect(page.locator('.success-toast')).toContainText('Record created successfully')
    await expect(page.locator('.record-card:has-text("Blood Test Results")')).toBeVisible()
  })

  test('should upload file to health record', async ({ page }) => {
    // Create a record first
    await page.click('text=Add New Record')
    await page.fill('[name="title"]', 'X-Ray Report')
    await page.selectOption('[name="record_type"]', 'imaging')
    await page.fill('[name="record_date"]', '2024-01-20')
    await page.click('button:has-text("Save")')
    
    // Upload file
    await page.click('.record-card:has-text("X-Ray Report")')
    await page.click('text=Upload File')
    
    const fileInput = await page.locator('input[type="file"]')
    await fileInput.setInputFiles(path.join(__dirname, 'fixtures', 'test-document.pdf'))
    
    await expect(page.locator('.file-upload-progress')).toBeVisible()
    await expect(page.locator('.file-item:has-text("test-document.pdf")')).toBeVisible()
  })

  test('should filter health records', async ({ page }) => {
    // Create multiple records
    const records = [
      { title: 'Blood Test', type: 'lab_result', category: 'laboratory' },
      { title: 'X-Ray', type: 'imaging', category: 'radiology' },
      { title: 'Prescription', type: 'prescription', category: 'pharmacy' }
    ]
    
    for (const record of records) {
      await page.click('text=Add New Record')
      await page.fill('[name="title"]', record.title)
      await page.selectOption('[name="record_type"]', record.type)
      await page.selectOption('[name="category"]', record.category)
      await page.fill('[name="record_date"]', '2024-01-20')
      await page.click('button:has-text("Save")')
    }
    
    // Filter by type
    await page.selectOption('[name="filter_type"]', 'lab_result')
    await expect(page.locator('.record-card')).toHaveCount(1)
    await expect(page.locator('.record-card:has-text("Blood Test")')).toBeVisible()
    
    // Filter by category
    await page.selectOption('[name="filter_type"]', '')
    await page.selectOption('[name="filter_category"]', 'radiology')
    await expect(page.locator('.record-card')).toHaveCount(1)
    await expect(page.locator('.record-card:has-text("X-Ray")')).toBeVisible()
    
    // Search
    await page.selectOption('[name="filter_category"]', '')
    await page.fill('[name="search"]', 'Prescription')
    await expect(page.locator('.record-card')).toHaveCount(1)
    await expect(page.locator('.record-card:has-text("Prescription")')).toBeVisible()
  })

  test('should edit health record', async ({ page }) => {
    // Create a record
    await page.click('text=Add New Record')
    await page.fill('[name="title"]', 'Original Title')
    await page.selectOption('[name="record_type"]', 'lab_result')
    await page.fill('[name="record_date"]', '2024-01-20')
    await page.click('button:has-text("Save")')
    
    // Edit the record
    await page.click('.record-card:has-text("Original Title")')
    await page.click('text=Edit')
    
    await page.fill('[name="title"]', 'Updated Title')
    await page.fill('[name="description"]', 'Updated description')
    await page.click('button:has-text("Update")')
    
    await expect(page.locator('.success-toast')).toContainText('Record updated successfully')
    await expect(page.locator('.record-card:has-text("Updated Title")')).toBeVisible()
    await expect(page.locator('.record-card:has-text("Original Title")')).not.toBeVisible()
  })

  test('should delete health record', async ({ page }) => {
    // Create a record
    await page.click('text=Add New Record')
    await page.fill('[name="title"]', 'To Be Deleted')
    await page.selectOption('[name="record_type"]', 'lab_result')
    await page.fill('[name="record_date"]', '2024-01-20')
    await page.click('button:has-text("Save")')
    
    // Delete the record
    await page.click('.record-card:has-text("To Be Deleted")')
    await page.click('text=Delete')
    
    // Confirm deletion
    await page.click('button:has-text("Confirm Delete")')
    
    await expect(page.locator('.success-toast')).toContainText('Record deleted successfully')
    await expect(page.locator('.record-card:has-text("To Be Deleted")')).not.toBeVisible()
  })

  test('should export health records', async ({ page }) => {
    // Create some records
    for (let i = 1; i <= 3; i++) {
      await page.click('text=Add New Record')
      await page.fill('[name="title"]', `Record ${i}`)
      await page.selectOption('[name="record_type"]', 'lab_result')
      await page.fill('[name="record_date"]', '2024-01-20')
      await page.click('button:has-text("Save")')
    }
    
    // Export as PDF
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('text=Export Records'),
      page.click('text=Export as PDF')
    ])
    
    expect(download.suggestedFilename()).toContain('health-records')
    expect(download.suggestedFilename()).toContain('.pdf')
  })

  test('should share health record with another user', async ({ page, browser }) => {
    // Create a record
    await page.click('text=Add New Record')
    await page.fill('[name="title"]', 'Shared Record')
    await page.selectOption('[name="record_type"]', 'lab_result')
    await page.fill('[name="record_date"]', '2024-01-20')
    await page.click('button:has-text("Save")')
    
    // Share the record
    await page.click('.record-card:has-text("Shared Record")')
    await page.click('text=Share')
    
    await page.fill('[name="share_email"]', 'doctor@example.com')
    await page.selectOption('[name="permission"]', 'read')
    await page.fill('[name="expires_at"]', '2024-12-31')
    await page.click('button:has-text("Share Record")')
    
    await expect(page.locator('.success-toast')).toContainText('Record shared successfully')
    await expect(page.locator('.shared-users')).toContainText('doctor@example.com')
  })

  test('should display record timeline', async ({ page }) => {
    // Create records with different dates
    const dates = ['2024-01-10', '2024-01-15', '2024-01-20']
    
    for (const date of dates) {
      await page.click('text=Add New Record')
      await page.fill('[name="title"]', `Record on ${date}`)
      await page.selectOption('[name="record_type"]', 'lab_result')
      await page.fill('[name="record_date"]', date)
      await page.click('button:has-text("Save")')
    }
    
    // Switch to timeline view
    await page.click('text=Timeline View')
    
    const timelineItems = await page.locator('.timeline-item').all()
    expect(timelineItems.length).toBe(3)
    
    // Check chronological order
    const firstItem = await timelineItems[0].textContent()
    expect(firstItem).toContain('2024-01-20')
  })

  test('should handle bulk operations', async ({ page }) => {
    // Create multiple records
    for (let i = 1; i <= 5; i++) {
      await page.click('text=Add New Record')
      await page.fill('[name="title"]', `Bulk Record ${i}`)
      await page.selectOption('[name="record_type"]', 'lab_result')
      await page.fill('[name="record_date"]', '2024-01-20')
      await page.click('button:has-text("Save")')
    }
    
    // Select multiple records
    await page.click('text=Select All')
    
    // Bulk export
    await page.click('text=Bulk Actions')
    await page.click('text=Export Selected')
    
    await expect(page.locator('.success-toast')).toContainText('5 records exported')
  })

  test('should work with body diagram integration', async ({ page }) => {
    // Create a record with body part
    await page.click('text=Add New Record')
    await page.fill('[name="title"]', 'Heart Checkup')
    await page.selectOption('[name="record_type"]', 'consultation')
    await page.selectOption('[name="body_part"]', 'heart')
    await page.fill('[name="record_date"]', '2024-01-20')
    await page.click('button:has-text("Save")')
    
    // Navigate to body diagram
    await page.click('text=Body Diagram')
    
    // Click on heart in diagram
    await page.click('[data-body-part="heart"]')
    
    // Should show related record
    await expect(page.locator('.body-part-records')).toContainText('Heart Checkup')
  })
})