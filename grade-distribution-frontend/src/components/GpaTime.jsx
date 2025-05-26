import React, { useEffect, useState, useRef } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from "recharts";

const BACKEND = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";

export default function GpaTime() {
  const [courseName, setCourseName] = useState("ENGR-102");
  const [rawData, setRawData] = useState([]);
  const [error, setError] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const containerRef = useRef(null);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handler = e => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Fetch GPA trends on courseName change
  useEffect(() => {
    if (!courseName) return;
    fetch(`${BACKEND}/grades/trends?course_name=${courseName}`)
      .then(res => {
        if (!res.ok) throw new Error(res.status);
        return res.json();
      })
      .then(setRawData)
      .catch(e => setError(e.toString()));
  }, [courseName]);

  // Fetch autocomplete suggestions
  useEffect(() => {
    if (!courseName) {
      setSuggestions([]);
      return;
    }
    fetch(`${BACKEND}/courses?prefix=${courseName}&limit=10`)
      .then(res => res.ok ? res.json() : [])
      .then(list => {
        setSuggestions(list);
        setShowSuggestions(true);
      })
      .catch(() => setSuggestions([]));
  }, [courseName]);

  // Build Recharts data
  const chartData = [];
  rawData.forEach(r => {
    const term = `${r.year} ${r.semester}`;
    let row = chartData.find(d => d.term === term);
    if (!row) {
      row = { term };
      chartData.push(row);
    }
    row[r.instructor_name] = r.avg_gpa;
  });
  const instructors = [...new Set(rawData.map(d => d.instructor_name))];
  const colors = [
    "#8884d8", "#82ca9d", "#FFBB28", "#FF8042", "#8dd1e1",
    "#d0ed57", "#a4de6c", "#ffc658", "#f06292", "#ba68c8"
  ];

  return (
    <div ref={containerRef} style={{ position: "relative", padding: "1rem" }}>
      <h2>Course Search</h2>
      <p>Enter a course like <em>ENGR-102</em></p>

      <div style={{ position: "relative", width: 300 }}>
        <input
          type="text"
          placeholder="e.g. ENGR-102"
          value={courseName}
          onChange={e => setCourseName(e.target.value.toUpperCase())}
          onFocus={() => setShowSuggestions(true)}
          style={{
            width: "100%",
            padding: "8px",
            fontSize: "1rem",
            boxSizing: "border-box",
            background: "#222",
            color: "#fff",
            border: "1px solid #444",
            borderRadius: 4
          }}
        />
        {showSuggestions && suggestions.length > 0 && (
          <ul style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            maxHeight: 150,
            overflowY: "auto",
            background: "#222",
            border: "1px solid #444",
            borderTop: "none",
            margin: 0,
            padding: 0,
            listStyle: "none",
            zIndex: 1000
          }}>
            {suggestions.map(s => (
              <li
                key={s}
                onMouseDown={e => {
                  e.preventDefault();
                  setCourseName(s);
                  setShowSuggestions(false);
                }}
                style={{
                  padding: "8px",
                  cursor: "pointer",
                  borderBottom: "1px solid #444",
                  color: "#ddd"
                }}
                onMouseEnter={e => (e.currentTarget.style.background = "#333")}
                onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
              >
                {s}
              </li>
            ))}
          </ul>
        )}
      </div>

      {error && <p style={{ color: "red", marginTop: 8 }}>Error: {error}</p>}

      <div style={{ width: "100%", height: 500, marginTop: 24 }}>
        <ResponsiveContainer>
          <LineChart
            data={chartData}
            margin={{ top: 20, right: 200, bottom: 60, left: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#444" />
            <XAxis
              dataKey="term"
              angle={-45}
              textAnchor="end"
              height={60}
              tick={{ fill: "#ccc" }}
            />
            <YAxis domain={["dataMin", "dataMax"]} tick={{ fill: "#ccc" }} />
            <Tooltip
              contentStyle={{ backgroundColor: "#222", border: "none" }}
              labelStyle={{ color: "#fff" }}
              itemStyle={{ color: "#fff" }}
            />
            <Legend
              layout="vertical"
              align="right"
              verticalAlign="top"
              wrapperStyle={{
                top: 0,
                right: 0,
                width: 180,
                maxHeight: 400,
                overflowY: "auto",
                color: "#fff"
              }}
            />
            {instructors.map((instr, i) => (
              <Line
                key={instr}
                dataKey={instr}
                stroke={colors[i % colors.length]}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
