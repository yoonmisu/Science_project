import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from "./pages/home.jsx";
import Landing from "./pages/landing.jsx";
import "./App.css";

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
        console.error("백엔드 연결 실패:", err);
        setBackendMessage("🚨 백엔드 연결 실패 (URL/서버 상태 확인 필요)");
      });
  }, []);

  return (
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
  );
};

export default App;