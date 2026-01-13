const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  transpilePackages: ["@monoco-io/kanban-core"],
  experimental: {
    externalDir: true,
  },
  devIndicators: {
    appIsrStatus: false,
    buildActivity: false,
  },
};

module.exports = nextConfig;
