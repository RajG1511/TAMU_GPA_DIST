import React, { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

export default function BarChartAvgGpaCourse() {
  const [dept, setDept] = useState("CSCE");
  const [data, setData] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    
    fetch(`${apiBaseUrl}/insights/avg_gpa_top10_by_dept?department=${dept}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch avg_gpa_top10_by_dept");
        return res.json();
      })
      .then((rows) => {
        setData(rows);
        setError("");
      })
      .catch((err) => setError(err.message));
  }, [dept, apiBaseUrl]);

  // Custom Tooltip Component
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const { course_name, avg_gpa } = payload[0].payload;
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
          <p>{`Course: ${course_name}`}</p>
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
        minHeight: "75vh",
        textAlign: "center",
        padding: "1rem",
        width: "100%", // Ensure the container takes the full width of the parent
      }}
    >
      <h4>Avg GPA vs Course by Department</h4>
      <label>
        Dept:
        <input
          style={{ marginLeft: "0.5rem"}}
          value={dept}
          onChange={(e) => setDept(e.target.value)}
        />
      </label>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <div style={{ width: "85%", height: "400px", marginTop: "1rem" }}>
        {/* Responsive Container for dynamic scaling */}
        <ResponsiveContainer>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="course_name" />
            <YAxis domain={[0, 4]} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="avg_gpa" fill="#82ca9d" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
