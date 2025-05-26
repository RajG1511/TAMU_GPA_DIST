import React from "react";
import BarChartAvgGpaCourse from "./BarChartAvgGpaCourse";
import PieChartDeptProportion from "./PieChartDeptProportion";
import ScatterGpaClassSize from "./ScatterGPAClassSize";
import BarChartAvgGpaDept from "./BarChartAvgGpaDept";

export default function Insights() {
  return (
    <div
      style={{
        padding: "2rem",
        backgroundColor: "#121212", // Dark background for a modern look
        color: "white",
        fontFamily: "'Roboto', sans-serif",
        lineHeight: "1.5",
      }}
    >
      <h2 style={{ textAlign: "center", marginBottom: "2rem", fontSize: "2rem" }}>
        Insights
      </h2>
      
      {/* Graph 1 */}
      <div
        style={{
          borderRadius: "8px",
          backgroundColor: "#1f1f1f",
          padding: "1.5rem",
          marginBottom: "2rem",
          boxShadow: "0 4px 8px rgba(0, 0, 0, 0.5)",
        }}
      >
        <BarChartAvgGpaCourse />
      </div>

      {/* Graph 2 */}
      <div
        style={{
          borderRadius: "8px",
          backgroundColor: "#1f1f1f",
          padding: "1.5rem",
          marginBottom: "2rem",
          boxShadow: "0 4px 8px rgba(0, 0, 0, 0.5)",
        }}
      >
        <PieChartDeptProportion />
      </div>

      {/* Graph 3 */}
      <div
        style={{
          borderRadius: "8px",
          backgroundColor: "#1f1f1f",
          padding: "1.5rem",
          marginBottom: "2rem",
          boxShadow: "0 4px 8px rgba(0, 0, 0, 0.5)",
        }}
      >
        <ScatterGpaClassSize />
      </div>

      {/* Graph 4 */}
      <div
        style={{
          borderRadius: "8px",
          backgroundColor: "#1f1f1f",
          padding: "1.5rem",
          marginBottom: "2rem",
          boxShadow: "0 4px 8px rgba(0, 0, 0, 0.5)",
        }}
      >
        <BarChartAvgGpaDept />
      </div>
    </div>
  );
}
