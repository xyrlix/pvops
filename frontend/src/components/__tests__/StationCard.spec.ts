import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StationCard from '../StationCard.vue'

describe('StationCard', () => {
  it('renders station info correctly', () => {
    const station = {
      id: 1,
      name: '测试电站',
      code: 'TEST001',
      capacity_kw: 500,
      location: '上海',
      status: 'active',
      created_at: '2026-06-23T00:00:00Z',
    }

    const wrapper = mount(StationCard, {
      props: { station },
    })

    expect(wrapper.text()).toContain('测试电站')
    expect(wrapper.text()).toContain('上海')
    expect(wrapper.text()).toContain('500')
  })
})
