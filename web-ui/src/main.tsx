import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Gallery from "./pages/Gallery";
import Editor from "./pages/Editor";
import NewSprite from "./pages/NewSprite";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Gallery />} />
        <Route path="/edit/:id" element={<Editor />} />
        <Route path="/new" element={<NewSprite />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
