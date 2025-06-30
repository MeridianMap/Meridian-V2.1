import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI.
    return { hasError: true, error: error };
  }

  componentDidCatch(error, errorInfo) {
    // You can also log the error to an error reporting service
    console.error("Uncaught error:", error, errorInfo);
    this.setState({ errorInfo: errorInfo });
  }

  render() {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      return (
        <div style={{ padding: '20px', background: '#ffe6e6', border: '1px solid #ff0000', borderRadius: '5px' }}>
          <h2>Something went wrong!</h2>
          <p>A JavaScript error occurred in the application.</p>
          <details style={{ whiteSpace: 'pre-wrap' }}>
            <summary>Error Details (click to expand)</summary>
            <br />
            <strong>Error:</strong> {this.state.error && this.state.error.toString()}
            <br /><br />
            <strong>Stack Trace:</strong>
            <br />
            {this.state.errorInfo && this.state.errorInfo.componentStack ? 
              this.state.errorInfo.componentStack : 
              'Stack trace not available'
            }
          </details>
          <button 
            onClick={() => window.location.reload()} 
            style={{ marginTop: '10px', padding: '5px 10px' }}
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
