import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  turbopack: {
    // process.cwd() = the directory npm run dev is executed from (client/)
    // This silences the "multiple lockfiles" warning without causing the
    // Turbopack panic that __dirname caused on Windows/OneDrive paths.
    root: process.cwd(),
  },
};

export default nextConfig;
