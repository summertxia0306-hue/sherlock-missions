export type ModuleId = 'listening' | 'speaking' | 'parent' | 'vocabulary'

export interface ModuleRegistration {
  id: ModuleId
  title: string
  description: string
  route: string
  visible: boolean
  icon: string
}

const registry: readonly ModuleRegistration[] = [
  {
    id: 'listening',
    title: '听力训练',
    description: '课程将在 P2 迁移，当前入口只用于基础架构验收。',
    route: '/listening',
    visible: true,
    icon: '🎧'
  },
  {
    id: 'speaking',
    title: '跟读口语',
    description: '录音和评分将在 P3 迁移，当前入口只用于基础架构验收。',
    route: '/speaking',
    visible: true,
    icon: '🎙️'
  },
  {
    id: 'parent',
    title: '家长验收',
    description: '认证后可写入隔离的 test 验收记录。',
    route: '/parent',
    visible: true,
    icon: '🔐'
  },
  {
    id: 'vocabulary',
    title: '单词训练',
    description: '预留模块，尚未立项。',
    route: '/vocabulary',
    visible: false,
    icon: '🔤'
  }
]

export function visibleModules(): readonly ModuleRegistration[] {
  return registry.filter((item) => item.visible)
}

export function getModule(id: ModuleId): ModuleRegistration | undefined {
  return registry.find((item) => item.id === id)
}

