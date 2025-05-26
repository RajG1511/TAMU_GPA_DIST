import React, { useState, useEffect } from "react";
import { PieChart, Pie, Tooltip, Cell } from "recharts";

export default function PieChartDeptProportion() {
  const [data, setData] = useState([]);
  const [error, setError] = useState("");

  // Fetch API Base URL from environment variable
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

  const COLORS = [
    "#0088FE",
    "#00C49F",
    "#FFBB28",
    "#FF8042",
    "#A4DE6C",
    "#d0ed57",
    "#ffc658",
    "#f06292",
    "#ba68c8",
    "#ffd54f",
    "#82ca9d",
  ];

  useEffect(() => {
    fetch(`${apiBaseUrl}/insights/proportion_by_department`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch proportion_by_department");
        return res.json();
      })
      .then((rows) => {
        // Sort descending by count and calculate percentages
        const total = rows.reduce((sum, row) => sum + row.count, 0);
        rows.sort((a, b) => b.count - a.count).forEach((row) => {
          row.percentage = ((row.count / total) * 100).toFixed(1); // Add percentage field
        });
        setData(rows);
        setError("");
      })
      .catch((err) => setError(err.message));
  }, [apiBaseUrl]);

  // Custom Tooltip for Pie Chart
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const { department, count, percentage } = payload[0].payload;
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
          <p>{`Count: ${count}`}</p>
          <p>{`Percentage: ${percentage}%`}</p>
        </div>
      );
    }
    return null;
  };

  // Custom Legend Component
  const CustomLegend = () => (
    <div style={{ maxHeight: "300px", overflowY: "auto", paddingLeft: "20px" }}>
      {data.map((entry, index) => (
        <div key={`legend-item-${index}`} style={{ marginBottom: "8px" }}>
          <span
            style={{
              display: "inline-block",
              width: "12px",
              height: "12px",
              backgroundColor: COLORS[index % COLORS.length],
              marginRight: "8px",
            }}
          ></span>
          {`${entry.department} (${entry.percentage}%)`}
        </div>
      ))}
    </div>
  );

  return (
    <div style={{ padding: "1rem" }}>
      <h4 style={{ textAlign: "center", marginBottom: "1rem" }}>
        Proportion of Courses by Department
      </h4>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
        <PieChart width={400} height={500}>
          <Pie
            data={data}
            dataKey="count"
            nameKey="department"
            cx="50%"
            cy="50%"
            outerRadius={150}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
        <CustomLegend />
      </div>
    </div>
  );
}
