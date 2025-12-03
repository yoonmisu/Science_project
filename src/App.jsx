import React, { useState, useEffect, Component } from "react";
import Home from "./pages/home.jsx";
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
    console.error("❌ ErrorBoundary가 에러를 캐치했습니다:", error, errorInfo);
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
  const [message, setMessage] = useState("Connecting...");
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log("🚀 App.jsx: useEffect 실행됨");

    // 백엔드 연결 체크 (간소화)
    const checkBackend = async () => {
      try {
        console.log("📡 백엔드 연결 시도 중...");
        const res = await fetch("http://127.0.0.1:8000/");
        const data = await res.json();
        setMessage(data.message || "Connected");
        console.log("✅ 백엔드 연결 성공:", data.message);
      } catch (err) {
        console.warn("⚠️ 백엔드 연결 실패 (계속 진행):", err.message);
        setMessage("백엔드 연결 실패 (오프라인 모드)");
      } finally {
        // 백엔드 연결 실패해도 페이지는 표시
        setIsReady(true);
        console.log("✅ isReady = true");
      }
    };

    // 즉시 페이지 표시하고 백그라운드에서 백엔드 체크
    setIsReady(true);
    checkBackend();
  }, []);

  console.log("🎨 App.jsx: 렌더링 중... isReady =", isReady, "message =", message);

  // 에러 바운더리 - Home 컴포넌트를 ErrorBoundary로 감싸기
  console.log("🏠 Home 컴포넌트 렌더링 시도 중...");

  return (
    <ErrorBoundary>
      <Home backendMessage={message} />
    </ErrorBoundary>
  );
};

export default App;
