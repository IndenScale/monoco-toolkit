import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Monoco Toolkit",
  description: "Agent-Native Issue Tracking System",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: "Home", link: "/" },
      { text: "Guide", link: "/guide" },
    ],

    sidebar: [
      {
        text: "Introduction",
        items: [
          { text: "What is Monoco?", link: "/guide" },
          { text: "Getting Started", link: "/getting-started" },
        ],
      },
    ],

    socialLinks: [
      { icon: "github", link: "https://github.com/indenscale/monoco-toolkit" },
    ],

    footer: {
      message: "Released under the MIT License.",
      copyright: "Copyright © 2026-present IndenScale",
    },
  },
  appearance: "dark", // Force dark mode for "Agent-Native" feel
});
