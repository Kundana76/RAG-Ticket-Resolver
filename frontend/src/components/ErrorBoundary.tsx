import { Component, type ReactNode } from 'react'

interface Props { children: ReactNode }
interface State { hasError: boolean; error: string }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: '' }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error: error.message }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          minHeight: '100vh', background: '#0d0720', padding: 40,
        }}>
          <div style={{
            background: 'rgba(30,16,53,0.9)',
            border: '1px solid rgba(255,23,68,0.3)',
            borderRadius: 12, padding: 32, maxWidth: 500, textAlign: 'center',
          }}>
            <div style={{ fontSize: '2rem', marginBottom: 12 }}>⚠️</div>
            <h2 style={{ color: '#ff6b6b', fontSize: '1.1rem', marginBottom: 8 }}>
              Something went wrong
            </h2>
            <p style={{ color: '#9575cd', fontSize: '0.85rem', marginBottom: 16 }}>
              {this.state.error || 'An unexpected error occurred.'}
            </p>
            <button
              onClick={() => window.location.reload()}
              style={{
                background: '#7B2FBE', color: 'white', border: 'none',
                padding: '10px 24px', borderRadius: 8, cursor: 'pointer',
                fontWeight: 600, fontSize: '0.85rem',
              }}
            >
              Reload Page
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
