// NavBar.jsx
import React from "react";

export default function NavBar({ currentTab, setCurrentTab }) {
  const tabs = ["Insights", "Course Search", "About"];

  return (
    <div style={{
      display: "flex",
      justifyContent: "center",
      gap: "2rem",
      width: "100%",
      padding: "0.5rem 0",
      marginTop: "1rem"
    }}>
      {tabs.map((tab) => (
        <div
          key={tab}
          onClick={() => setCurrentTab(tab)}
          style={{
            cursor: "pointer",
            padding: "0.5rem 1rem",
            border: currentTab === tab ? "2px solid white" : "2px solid transparent"
          }}
        >
          {tab}
        </div>
      ))}
    </div>
  );
}
