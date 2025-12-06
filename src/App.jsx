import React, { useState, useEffect, Component } from "react";
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from "./pages/home.jsx";
import Landing from "./pages/landing.jsx";
import "./App.css";

// Error Boundary 컴포넌트
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ error, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '40px',
          backgroundColor: '#fff3cd',
          border: '2px solid #ffc107',
          borderRadius: '8px',
          margin: '20px',
          fontFamily: 'monospace'
        }}>
          <h1 style={{ color: '#d9534f' }}>⚠️ 렌더링 에러 발생</h1>
          <h2>에러 메시지:</h2>
          <p style={{ color: '#d9534f', fontSize: '16px' }}>
            {this.state.error && this.state.error.toString()}
          </p>
          <h3>Stack Trace:</h3>
          <pre style={{
            backgroundColor: '#f5f5f5',
            padding: '10px',
            overflow: 'auto',
            fontSize: '12px'
          }}>
            {this.state.errorInfo && this.state.errorInfo.componentStack}
          </pre>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '10px 20px',
              backgroundColor: '#5cb85c',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginTop: '20px'
            }}
          >
            페이지 새로고침
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

const App = () => {
  const [backendMessage, setBackendMessage] = useState("백엔드 연결 시도 중...");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        setBackendMessage(data.message || "백엔드에서 메시지를 성공적으로 받음");
      })
      .catch((err) => {
        setBackendMessage("백엔드 연결 실패");
      });
  }, []);

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={<Landing/>}
          />
          <Route
            path="/Home"
            element={<Home backendStatus={backendMessage}/>}
          />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
};

export default App;
