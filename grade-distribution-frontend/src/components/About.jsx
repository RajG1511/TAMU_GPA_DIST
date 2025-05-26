import React from "react";

export default function About() {
  return (
    <div
      style={{
        padding: "2rem",
        maxWidth: "900px",
        margin: "0 auto",
        color: "#f0f0f0",
        lineHeight: "1.8",
      }}
    >
      {/* Page Title */}
      <h2
        style={{
          fontSize: "2.5rem",
          marginBottom: "1.5rem",
          textAlign: "center",
          color: "#88ccee",
          fontWeight: "bold",
        }}
      >
        Discover A&M Grade Data Insights
      </h2>

      {/* Introduction */}
      <p style={{ fontSize: "1.2rem", marginBottom: "2rem", textAlign: "justify" }}>
        Welcome to A&M Grade Data Insights, a platform designed with one goal in
        mind: helping Aggies make better decisions about their academic paths.
        This tool offers a deep dive into grade trends, course performance, and
        instructor statistics, all based on historical data. Please Note that the site is being actively updated.
      </p>

      {/* Why Use This Platform */}
      <div
        style={{
          backgroundColor: "#222",
          padding: "1.5rem",
          borderRadius: "8px",
          marginBottom: "2rem",
          boxShadow: "0px 0px 10px rgba(0, 0, 0, 0.5)",
        }}
      >
        <h3 style={{ fontSize: "1.8rem", marginBottom: "1rem", color: "#ffbb54" }}>
          Why A&M Grade Data Insights?
        </h3>
        <ul style={{ listStyleType: "circle", paddingLeft: "1.5rem", fontSize: "1.1rem" }}>
          <li>Gain valuable insights into GPA trends for courses and professors.</li>
          <li>Access detailed grade distribution data from reliable sources.</li>
          <li>Make informed decisions about course registration and academic planning.</li>
        </ul>
      </div>

      {/* How It Works */}
      <div style={{ marginBottom: "2rem" }}>
        <h3 style={{ fontSize: "1.8rem", marginBottom: "1rem", color: "#ffbb54" }}>
          How It Works
        </h3>
        <p style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
          Simply navigate to the <strong>Course Search</strong> tab, type in a
          course, and view detailed trends over time. For broader analysis, check out the{" "}
          <strong>Insights</strong> tab for interactive graphs showing
          department-wide data and comparisons.
        </p>
        <p style={{ fontSize: "1.1rem" }}>
          The data is sourced directly from official grade distribution records and is regularly updated for accuracy.
        </p>
      </div>

      {/* Connect Section */}
      <div
        style={{
          backgroundColor: "#222",
          padding: "1.5rem",
          borderRadius: "8px",
          boxShadow: "0px 0px 10px rgba(0, 0, 0, 0.5)",
        }}
      >
        <h3 style={{ fontSize: "1.8rem", marginBottom: "1rem", color: "#ffbb54" }}>
          Meet the Creator
        </h3>
        <p style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
          A&M Grade Data Insights was created by an Aggie with a passion for data-driven decision-making. The platform is a personal project designed to enhance student success by making grade data accessible and easy to understand.
        </p>
        <p style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
          Have feedback or ideas? Let’s connect!
        </p>
        <p>
          <a
            href="https://github.com/RajG1511"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: "#88ccee",
              textDecoration: "none",
              fontSize: "1.2rem",
              marginRight: "1rem",
            }}
          >
            GitHub
          </a>
          <a
            href="https://www.linkedin.com/in/rajgupta04/"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: "#88ccee",
              textDecoration: "none",
              fontSize: "1.2rem",
            }}
          >
            LinkedIn
          </a>
        </p>
      </div>
    </div>
  );
}
