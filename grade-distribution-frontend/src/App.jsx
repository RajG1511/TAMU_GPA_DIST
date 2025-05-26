// App.jsx
import React, { useState } from "react";
import NavBar from "./components/NavBar";
import GpaTime from "./components/GpaTime";
import Insights from "./components/Insights";
import About from "./components/About";

export default function App() {
  const [currentTab, setCurrentTab] = useState("Course Search");

  let content;
  if (currentTab === "Insights") {
    content = <Insights />;
  } else if (currentTab === "Course Search") {
    content = <GpaTime />;
  } else if (currentTab === "About") {
    content = <About />;
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        color: "white",
        backgroundColor: "#111",
        display: "flex",
        flexDirection: "column"
      }}
    >
      <h1 style={{ textAlign: "center", margin: "1rem 0" }}>A&M Grade Data Insights</h1>
      <NavBar currentTab={currentTab} setCurrentTab={setCurrentTab} />
      {/* Main content area */}
      <div
        style={{
          flex: 1,               // pushes footer down if you ever add one
          display: "flex",
          justifyContent: "center", 
          // center the content horizontally
          padding: "1rem"
        }}
      >
        <div style={{ width: "90%", maxWidth: "1200px" }}>
          {content}
        </div>
      </div>
    </div>
  );
}
