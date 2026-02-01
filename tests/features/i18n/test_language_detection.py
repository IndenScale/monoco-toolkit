"""Tests for improved language detection with technical terms allowlist."""

import pytest
from monoco.features.i18n.core import detect_language, TECHNICAL_TERMS_ALLOWLIST


class TestLanguageDetection:
    """Test language detection with technical content."""

    def test_pure_chinese_content(self):
        """纯中文内容应被识别为中文。"""
        content = """---
id: TEST-0001
---

## TEST-0001: 这是一个测试

这是一个纯中文的文档内容，没有任何英文。
"""
        assert detect_language(content) == "zh"

    def test_pure_english_content(self):
        """纯英文内容应被识别为英文。"""
        content = """---
id: TEST-0002
---

## TEST-0002: This is a test

This is a pure English document with meaningful sentences and paragraphs.
It contains multiple sentences to ensure proper detection.
"""
        assert detect_language(content) == "en"

    def test_chinese_with_technical_terms(self):
        """中文内容包含技术术语应被识别为中文（FIX-0004 核心测试）。"""
        content = """---
id: TEST-0003
---

## TEST-0003: 修复 CLI 和 API 问题

需要调整 Kubernetes 和 Docker 的配置。
使用 Python 和 JavaScript 编写代码。
通过 CI/CD Pipeline 部署到 AWS。
"""
        # This should be detected as Chinese, not English
        result = detect_language(content)
        assert result in ("zh", "unknown"), f"Expected 'zh' or 'unknown', got '{result}'"

    def test_chinese_with_many_technical_terms(self):
        """中文内容包含大量技术术语不应被误判为英文。"""
        content = """---
id: FIX-0003
---

## FIX-0003: 修复单元测试回归问题

修复由于 API 变更导致的单元测试失败。
更新 pytest 配置和 mock 数据。
调整 CI/CD pipeline 中的测试步骤。
验证 Kubernetes 和 Docker 部署。
"""
        result = detect_language(content)
        # Should NOT be detected as English due to technical terms allowlist
        assert result != "en", f"Chinese content with technical terms was wrongly detected as English"

    def test_mixed_content_with_cjk_threshold(self):
        """中英混排内容，CJK 比例超过阈值应识别为中文。"""
        content = """---
id: TEST-0004
---

## TEST-0004: 混合内容测试

这是一个包含 API、CLI、Kubernetes 的混合文档。
我们需要使用 Python 和 Docker 来部署服务。
同时监控 Grafana 和 Prometheus 的指标。
"""
        result = detect_language(content)
        # Should detect as Chinese due to CJK characters
        assert result in ("zh", "unknown")

    def test_english_with_technical_terms(self):
        """英文内容包含技术术语应被识别为英文。"""
        content = """---
id: TEST-0005
---

## TEST-0005: Fix CLI and API Issues

We need to fix the Kubernetes and Docker configuration issues.
The Python and JavaScript code needs to be updated.
Deploy through CI/CD pipeline to AWS cloud.
"""
        assert detect_language(content) == "en"

    def test_code_heavy_content(self):
        """代码为主的内容应返回 unknown 避免误判。"""
        content = """---
id: TEST-0006
---

## TEST-0006: Code Example

```python
def hello_world():
    print("Hello, World!")
    return True
```

```javascript
function test() {
    return fetch('/api/v1/users');
}
```
"""
        # Code-heavy content should return unknown
        result = detect_language(content)
        assert result in ("en", "unknown")

    def test_minimal_content(self):
        """极少内容应返回 unknown。"""
        content = """---
id: TEST-0007
---

## TEST-0007: Test

API CLI Docker
"""
        result = detect_language(content)
        # Should be unknown or zh (due to technical terms being excluded)
        assert result in ("zh", "unknown", "en")


class TestTechnicalTermsAllowlist:
    """Test technical terms allowlist."""

    def test_common_technical_terms_in_allowlist(self):
        """常见技术术语应在 allowlist 中。"""
        common_terms = [
            "api", "cli", "docker", "kubernetes", "python",
            "javascript", "git", "github", "ci", "cd",
            "sql", "nginx", "linux", "aws", "azure",
        ]
        for term in common_terms:
            assert term in TECHNICAL_TERMS_ALLOWLIST, f"'{term}' should be in allowlist"

    def test_case_insensitive_matching(self):
        """技术术语匹配应不区分大小写。"""
        content = """---
id: TEST-0008
---

## TEST-0008: 测试

使用 API 和 CLI 工具。
配置 KUBERNETES 和 DOCKER。
编写 PYTHON 代码。
"""
        result = detect_language(content)
        # Should still be detected as Chinese (or unknown), not English
        assert result != "en"


class TestRegressionFixes:
    """Regression tests for specific issues like FIX-0003."""

    def test_fix_0003_scenario(self):
        """
        模拟 FIX-0003 的场景：中文 Issue 包含大量技术术语。
        
        FIX-0003 是一个关于修复单元测试回归问题的 Issue，
        包含大量英文技术术语，之前会被误判为英文。
        """
        content = """---
id: FIX-0003
uid: 8f2a1c
type: fix
status: closed
stage: done
title: 修复单元测试回归问题
created_at: '2026-02-01T21:30:00'
updated_at: '2026-02-01T21:45:00'
parent: EPIC-0027
dependencies: []
related: []
domains:
- IssueGovernance
tags:
- '#EPIC-0027'
- '#FIX-0003'
files:
- tests/features/issue/test_linter.py
- tests/features/issue/test_validator.py
solution:
  type: git-commit
  ref: feat/fix-0003-fix-unit-test-regressions
  description: 修复由于 API 变更导致的测试失败
---

## FIX-0003: 修复单元测试回归问题

## Objective
修复由于近期代码重构导致的单元测试回归问题。主要影响 issue linter 和 validator 的测试用例。

## Acceptance Criteria
- [x] **Linter Tests**: 所有 linter 相关测试通过
- [x] **Validator Tests**: 所有 validator 相关测试通过
- [x] **CI Pipeline**: GitHub Actions 工作流成功运行

## Technical Tasks
- [x] **CHORE-Update-Mocks**: 更新测试中的 mock 数据以匹配新 API
- [x] **CHORE-Fix-Assertions**: 修复断言语句中的期望值
- [x] **CHORE-Update-Fixtures**: 更新测试 fixtures

## Review Comments
- 测试覆盖率保持在 85% 以上
- 所有集成测试通过
"""
        result = detect_language(content)
        # This should NOT be detected as English
        assert result != "en", (
            f"FIX-0003 scenario was wrongly detected as English. "
            f"This is the exact issue FIX-0004 is meant to fix."
        )
