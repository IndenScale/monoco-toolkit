const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["@monoco/kanban-core"],
  outputFileTracingRoot: path.join(__dirname, "../../../"),
  experimental: {
    externalDir: true,
  },
};

module.exports = nextConfig;
