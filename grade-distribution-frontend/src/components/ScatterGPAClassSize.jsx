import React, { useEffect, useState } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export default function ScatterGpaClassSize() {
  const [data, setData] = useState([]);
  const [error, setError] = useState("");

  // Fetch API Base URL from environment variable
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

  useEffect(() => {
    fetch(`${apiBaseUrl}/insights/scatter_gpa_class_size`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch scatter_gpa_class_size");
        return res.json();
      })
      .then((rows) => {
        // rows: {section_id, avg_gpa, avg_class_size}
        // rename them for Recharts
        const chartData = rows.map((r) => ({
          x: r.avg_class_size,
          y: r.avg_gpa,
        }));
        setData(chartData);
        setError("");
      })
      .catch((err) => setError(err.message));
  }, [apiBaseUrl]);

  // Get dynamic axis scaling
  const xDomain = [
    0,
    data.length > 0 ? Math.max(...data.map((d) => d.x)) + 5 : 50, // Add padding
  ];
  const yDomain = [
    0,
    data.length > 0 ? Math.max(...data.map((d) => d.y)) + 0.5 : 4, // Add padding
  ];

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "50vh", // Center vertically
        textAlign: "center",
        padding: "1rem",
      }}
    >
      <h4>Avg GPA vs Class Size (200 data points)</h4>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <div style={{ width: "100%", height: "400px" }}>
        <ResponsiveContainer>
          <ScatterChart>
            <CartesianGrid />
            <XAxis
              type="number"
              dataKey="x"
              name="Class Size"
              domain={xDomain} // Dynamically scale the x-axis
            />
            <YAxis
              type="number"
              dataKey="y"
              name="GPA"
              domain={yDomain} // Dynamically scale the y-axis
            />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} />
            <Legend />
            <Scatter name="Sections" data={data} fill="#8884d8" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
