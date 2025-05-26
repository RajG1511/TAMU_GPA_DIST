import React, { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";

export default function BarChartAvgGpaDept() {
  const [fullData, setFullData] = useState([]);
  const [filterText, setFilterText] = useState("");
  const [filtered, setFiltered] = useState([]);
  const [error, setError] = useState("");

  // Fetch API Base URL from environment variable
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

  useEffect(() => {
    fetch(`${apiBaseUrl}/insights/avg_gpa_by_department`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch avg_gpa_by_department");
        return res.json();
      })
      .then((rows) => {
        setFullData(rows);
        setFiltered(rows);
        setError("");
      })
      .catch((err) => setError(err.message));
  }, [apiBaseUrl]);

  useEffect(() => {
    if (!filterText) {
      setFiltered(fullData);
    } else {
      const lower = filterText.toLowerCase();
      const filteredRows = fullData.filter((r) =>
        r.department.toLowerCase().includes(lower)
      );
      setFiltered(filteredRows);
    }
  }, [filterText, fullData]);

  // Custom Tooltip Component
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const { department, avg_gpa } = payload[0].payload;
      return (
        <div
          style={{
            background: "rgba(0, 0, 0, 0.75)",
            color: "white",
            padding: "10px",
            borderRadius: "5px",
            fontSize: "14px",
          }}
        >
          <p>{`Department: ${department}`}</p>
          <p>{`Avg GPA: ${avg_gpa.toFixed(2)}`}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "50vh", // Centers vertically
        textAlign: "center", // Centers the title and input field
        padding: "1rem",
      }}
    >
      <h4>Avg GPA vs Department</h4>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <label>
        Search Dept:
        <input
          style={{ marginLeft: "0.5rem" }}
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
        />
      </label>
      <div style={{ width: "100%", height: "400px", marginTop: "0.5rem" }}>
        <ResponsiveContainer>
          <BarChart data={filtered}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="department" />
            <YAxis domain={[0, 4]} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="avg_gpa" fill="#82ca9d" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
