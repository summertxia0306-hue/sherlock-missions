import { render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { ErrorBoundary } from './ErrorBoundary'

function Broken(): ReactNode {
  throw new Error('sensitive detail')
}

describe('ErrorBoundary', () => {
  it('renders children normally', () => {
    render(<ErrorBoundary><p>healthy child</p></ErrorBoundary>)
    expect(screen.getByText('healthy child')).toBeInTheDocument()
  })

  it('shows a safe recovery screen after a render error', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    render(<ErrorBoundary><Broken /></ErrorBoundary>)
    expect(screen.getByRole('alert')).toHaveTextContent('请刷新后再试')
    expect(screen.queryByText('sensitive detail')).not.toBeInTheDocument()
    consoleError.mockRestore()
  })
})
