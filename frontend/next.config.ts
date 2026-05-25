import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  distDir: "out",
  // Export each route as <route>/index.html so FastAPI's StaticFiles serves
  // /kanban and /login on direct load / refresh (not just /kanban.html).
  trailingSlash: true,
};

export default nextConfig;
