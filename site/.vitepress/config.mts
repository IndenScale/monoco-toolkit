import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Monoco Toolkit",
  description: "Agent-Native Issue Tracking System",
  srcDir: "src",
  base: "/",

  rewrites: {
    "en/:rest*": ":rest*",
  },

  locales: {
    root: {
      label: "English",
      lang: "en",
      themeConfig: {
        nav: [
          { text: "Home", link: "/" },
          { text: "Guide", link: "/guide/" },
          { text: "Reference", link: "/reference/issue/" },
          { text: "Meta", link: "/meta/Manifesto" },
        ],
        sidebar: [
          {
            text: "Guide",
            items: [
              { text: "Get Started", link: "/guide/" },
              { text: "Setup", link: "/guide/setup/" },
              { text: "Best Practices", link: "/guide/workflow" },
            ],
          },
          {
            text: "Reference",
            items: [
              {
                text: "Core Domains",
                items: [
                  { text: "Issue System", link: "/reference/issue/" },
                  { text: "Research (Spike)", link: "/reference/spike/" },
                  { text: "i18n", link: "/reference/i18n/" },
                ],
              },
              {
                text: "Architecture",
                items: [
                  {
                    text: "System Architecture",
                    link: "/reference/architecture",
                  },
                  {
                    text: "Integration Registry",
                    link: "/reference/core-integration-registry",
                  },
                ],
              },
              {
                text: "Extensions",
                link: "/reference/extensions/",
              },
            ],
          },
          {
            text: "Meta",
            items: [
              { text: "Manifesto", link: "/meta/Manifesto" },
              {
                text: "Design Patterns",
                link: "/meta/design/agent-native-design-pattern",
              },
              {
                text: "Process",
                items: [
                  {
                    text: "Release Audit",
                    link: "/meta/process/release_audit",
                  },
                  {
                    text: "PyPI Publishing",
                    link: "/meta/process/pypi-trusted-publishing",
                  },
                ],
              },
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
          { text: "指南", link: "/zh/guide/" },
          { text: "参考", link: "/zh/reference/issue/" },
          { text: "关于", link: "/zh/meta/Manifesto" },
        ],
        sidebar: [
          {
            text: "指南",
            items: [
              { text: "快速开始", link: "/zh/guide/" },
              { text: "安装配置", link: "/zh/guide/setup/" },
              { text: "最佳实践", link: "/zh/guide/workflow" },
            ],
          },
          {
            text: "参考手册",
            items: [
              {
                text: "核心领域",
                items: [
                  { text: "Issue 系统", link: "/zh/reference/issue/" },
                  { text: "Spike 研究", link: "/zh/reference/spike/" },
                  { text: "i18n 国际化", link: "/zh/reference/i18n/" },
                ],
              },
              {
                text: "架构设计",
                items: [
                  { text: "系统架构", link: "/zh/reference/architecture" },
                  {
                    text: "集成注册表",
                    link: "/zh/reference/core-integration-registry",
                  },
                ],
              },
              {
                text: "扩展开发",
                link: "/zh/reference/extensions/",
              },
            ],
          },
          {
            text: "关于项目",
            items: [
              { text: "宣言", link: "/zh/meta/Manifesto" },
              {
                text: "设计模式",
                link: "/zh/meta/design/agent-native-design-pattern",
              },
              {
                text: "流程规范",
                items: [
                  { text: "发布审计", link: "/zh/meta/process/release_audit" },
                  {
                    text: "PyPI 发布",
                    link: "/zh/meta/process/pypi-trusted-publishing",
                  },
                ],
              },
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
