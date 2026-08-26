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
    description: 'W01D39–50 正式课程，自动衔接历史完成进度。',
    route: '/listening',
    visible: true,
    icon: '🎧'
  },
  {
    id: 'speaking',
    title: '跟读口语',
    description: 'S01D39–50 正式课程，含私有录音、讯飞评分与三次门控。',
    route: '/speaking',
    visible: true,
    icon: '🎙️'
  },
  {
    id: 'parent',
    title: '家长端',
    description: '认证后独立查询 formal/test 历史，并进入隔离的 test 验收。',
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
