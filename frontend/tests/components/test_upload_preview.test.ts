/**
 * 文件名: tests/components/test_upload_preview.test.ts
 * 创建时间: 2026-06-26
 * 作者: TalentSense Team
 * 功能描述: 上传对话框与简历预览测试
 *   - UploadDialog visible 切换 / 取消触发 close
 *   - ResumePreview PDF/图片渲染
 */
import { describe, it, expect, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import UploadDialog from '@/components/resume/UploadDialog.vue'
import ResumePreview from '@/components/resume/ResumePreview.vue'

afterEach(() => {
  // 清理 el-dialog teleport 到 body 的残留
  document.body.innerHTML = ''
})

describe('components/resume/UploadDialog', () => {
  it('visible=false 时不渲染对话框内容', async () => {
    mount(UploadDialog, { props: { visible: false } })
    await flushPromises()
    expect(document.body.textContent || '').not.toContain('RESUME UPLOAD')
  })

  it('visible=true 时渲染对话框（含 eyebrow 与取消按钮）', async () => {
    mount(UploadDialog, { props: { visible: true } })
    await flushPromises()
    const bodyText = document.body.textContent || ''
    expect(bodyText).toContain('RESUME UPLOAD')
    expect(bodyText).toContain('上传简历')
  })

  it('点击取消触发 close 事件', async () => {
    const wrapper = mount(UploadDialog, { props: { visible: true } })
    await flushPromises()
    const cancelBtn = Array.from(document.body.querySelectorAll('button')).find(
      (b) => /取消/.test(b.textContent || ''),
    ) as HTMLButtonElement | undefined
    expect(cancelBtn).toBeTruthy()
    cancelBtn!.click()
    await flushPromises()
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})

describe('components/resume/ResumePreview', () => {
  it('PDF 使用 iframe 渲染', () => {
    const wrapper = mount(ResumePreview, {
      props: { previewUrl: 'http://localhost/a.pdf', fileType: 'pdf' },
    })
    expect(wrapper.find('iframe').exists()).toBe(true)
    expect(wrapper.find('img').exists()).toBe(false)
  })

  it('图片使用 img 渲染', () => {
    const wrapper = mount(ResumePreview, {
      props: { previewUrl: 'http://localhost/a.png', fileType: 'png' },
    })
    expect(wrapper.find('img').exists()).toBe(true)
    expect(wrapper.find('iframe').exists()).toBe(false)
  })

  it('未知类型显示不支持提示', () => {
    const wrapper = mount(ResumePreview, {
      props: { previewUrl: 'http://localhost/a.docx', fileType: 'docx' },
    })
    expect(wrapper.find('.resume-preview__unsupported').exists()).toBe(true)
  })
})

describe('UploadDialog 批量上传', () => {
  it('提示文本应包含批量上传说明', async () => {
    mount(UploadDialog, { props: { visible: true } })
    await flushPromises()
    const bodyText = document.body.textContent || ''
    expect(bodyText).toContain('批量')
    expect(bodyText).toContain('PDF')
  })

  it('el-upload 不应有 limit=1 限制', async () => {
    mount(UploadDialog, { props: { visible: true } })
    await flushPromises()
    const bodyHtml = document.body.innerHTML || ''
    // limit="1" 限制单文件，批量上传时不应存在
    expect(bodyHtml).not.toContain('limit="1"')
  })
})
