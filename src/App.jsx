import React, { useState, useEffect } from "react";
import Home from "./pages/home.jsx";
import "./App.css";

const App = () => {
  const [message, setMessage] = useState("Connecting...");
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // 백엔드 연결 체크 (타임아웃 설정)
    const checkBackend = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000); // 3초 타임아웃

        const res = await fetch("http://127.0.0.1:8000/", {
          signal: controller.signal
        });
        clearTimeout(timeoutId);

        const data = await res.json();
        setMessage(data.message || "Connected");
      } catch (err) {
        console.warn("백엔드 연결 실패 (계속 진행):", err);
        setMessage("백엔드 연결 실패 (오프라인 모드)");
      } finally {
        // 백엔드 연결 실패해도 페이지는 표시
        setIsReady(true);
      }
    };

    // 즉시 페이지 표시하고 백그라운드에서 백엔드 체크
    setIsReady(true);
    checkBackend();
  }, []);

  // 페이지를 즉시 표시
  return <Home backendMessage={message} />;
};

export default App;
