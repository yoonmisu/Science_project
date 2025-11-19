import React, { useState, useEffect } from "react";
import Home from "./pages/home.jsx";
import "./App.css";

const App = () => {
  const [message, setMessage] = useState("Loading...");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/")
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch((err) => {
        console.error("백엔드 연결 실패:", err);
        setMessage("백엔드 연결 실패");
      });
  }, []);

  return <Home backendMessage={message} />;
};

export default App;
