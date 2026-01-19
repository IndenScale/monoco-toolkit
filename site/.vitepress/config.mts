import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Monoco Toolkit",
  description: "Agent-Native Issue Tracking System",
  srcDir: "src",
  base: "/",

  locales: {
    root: {
      label: "English",
      lang: "en",
      themeConfig: {
        nav: [
          { text: "Home", link: "/" },
          { text: "Guide", link: "/guide" },
          { text: "CLI", link: "/tools/cli" },
        ],
        sidebar: [
          {
            text: "Introduction",
            items: [
              { text: "What is Monoco?", link: "/guide" },
              { text: "Architecture", link: "/architecture" },
              {
                text: "Design Patterns",
                link: "/agent-native-design-pattern.md",
              },
            ],
          },
          {
            text: "Tools",
            items: [
              { text: "Issue System", link: "/issue/" },
              { text: "Spike", link: "/spike/" },
              { text: "i18n", link: "/i18n/" },
            ],
          },
        ],
      },
    },
    zh: {
      label: "简体中文",
      lang: "zh-CN",
      link: "/zh/",
      themeConfig: {
        nav: [
          { text: "首页", link: "/zh/" },
          { text: "指南", link: "/zh/guide" },
          { text: "CLI", link: "/zh/tools/cli" },
        ],
        sidebar: [
          {
            text: "介绍",
            items: [
              { text: "什么是 Monoco?", link: "/zh/guide" },
              { text: "架构", link: "/zh/architecture" },
              { text: "设计模式", link: "/zh/agent-native-design-pattern.md" },
            ],
          },
          {
            text: "工具",
            items: [
              { text: "Issue 系统", link: "/zh/issue/" },
              { text: "Spike", link: "/zh/spike/" },
              { text: "i18n", link: "/zh/i18n/" },
            ],
          },
        ],
      },
    },
  },

  themeConfig: {
    // Shared theme config
    socialLinks: [
      { icon: "github", link: "https://github.com/indenscale/monoco-toolkit" },
    ],
    footer: {
      message: "Released under the MIT License.",
      copyright: "Copyright © 2026-present IndenScale",
    },
    search: {
      provider: "local",
    },
  },
  appearance: "dark",
});
