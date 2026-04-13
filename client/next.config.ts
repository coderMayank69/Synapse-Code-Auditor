import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  // NOTE: turbopack.root is intentionally omitted.
  // Setting it (with __dirname or process.cwd()) causes a fatal Turbopack
  // panic on Windows paths that contain spaces (e.g. "Synapse Code Auditor").
  // Local dev uses --no-turbopack (webpack) via the dev script instead.
};

export default nextConfig;
