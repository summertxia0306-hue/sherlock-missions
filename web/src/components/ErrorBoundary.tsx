import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props { children: ReactNode }
interface State { hasError: boolean }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    if (import.meta.env.DEV) {
      console.error('PWA render error', error.name, info.componentStack)
    }
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <main className="center-card" role="alert">
          <p className="eyebrow">页面暂时出了问题</p>
          <h1>请刷新后再试</h1>
          <button type="button" onClick={() => window.location.reload()}>刷新页面</button>
        </main>
      )
    }
    return this.props.children
  }
}

