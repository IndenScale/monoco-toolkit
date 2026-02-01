"""
Tests for FEAT-0136: Domain Governance Rules and Auto-Inheritance
"""
import textwrap
from monoco.features.issue import core
from monoco.features.issue.linter import check_integrity
from monoco.features.issue.models import IssueType


def create_epic_file(issues_root, epic_id, title, has_domain=False):
    """Helper to create an epic file."""
    epic_path = issues_root / "Epics" / "open" / f"{epic_id}-{title.lower().replace(' ', '-')}.md"
    epic_path.parent.mkdir(parents=True, exist_ok=True)
    
    domains_yaml = "domains:\n  - Core" if has_domain else "domains: []"
    
    content = f"""---
id: {epic_id}
type: epic
status: open
stage: draft
title: {title}
{domains_yaml}
tags:
  - "#{epic_id}"
---

## {epic_id}: {title}

- [ ] Task 1
- [ ] Task 2
"""
    epic_path.write_text(content)
    return epic_path


def test_domain_coverage_rule_triggers_for_large_projects(issues_root):
    """验证大规模项目（Epics > 32 或 Issues > 128）触发 Domain 覆盖率检查。"""
    # 创建 Domain 定义
    domain_dir = issues_root / "Domains"
    domain_dir.mkdir(parents=True, exist_ok=True)
    (domain_dir / "Core.md").write_text("# Core")
    
    # 创建 35 个 Epic（超过 32 的阈值）
    # 其中只有 20 个有 domain（约 57%，低于 75% 要求）
    for i in range(35):
        epic_id = f"EPIC-{i+1:04d}"
        has_domain = i < 20  # 只有前 20 个有 domain
        create_epic_file(issues_root, epic_id, f"Test Epic {i}", has_domain=has_domain)
    
    # 运行 Linter
    diagnostics = check_integrity(issues_root)
    
    # 验证 Domain Governance 错误（项目级别检查，source 为 DomainGovernance）
    governance_errors = [d for d in diagnostics if "Domain Governance: Coverage is too low" in d.message]
    assert len(governance_errors) >= 1, f"Expected Domain Governance error, got: {[d.message for d in diagnostics if 'Governance' in d.message or 'Coverage' in d.message]}"
    assert "At least 75% of Epics must have domains" in governance_errors[0].message


def test_domain_coverage_rule_passes_with_sufficient_coverage(issues_root):
    """验证当 75% 以上的 Epic 有 Domain 时，不触发错误。"""
    # 创建 Domain 定义
    domain_dir = issues_root / "Domains"
    domain_dir.mkdir(parents=True, exist_ok=True)
    (domain_dir / "Core.md").write_text("# Core")
    
    # 创建 35 个 Epic，其中 28 个有 domain（80%，超过 75%）
    for i in range(35):
        epic_id = f"EPIC-{i+1:04d}"
        has_domain = i < 28  # 28 个有 domain
        create_epic_file(issues_root, epic_id, f"Test Epic {i}", has_domain=has_domain)
    
    # 运行 Linter
    diagnostics = check_integrity(issues_root)
    
    # 验证没有 Domain Governance 错误
    governance_errors = [d for d in diagnostics if "Domain Governance: Coverage is too low" in d.message]
    assert len(governance_errors) == 0


def test_child_inherits_parent_domain_logically(issues_root):
    """验证子 Issue 可以逻辑继承父 Epic 的 Domain（不产生错误）。"""
    # 创建 Domain 定义
    domain_dir = issues_root / "Domains"
    domain_dir.mkdir(parents=True, exist_ok=True)
    (domain_dir / "Core.md").write_text("# Core")
    
    # 创建 35 个 Epic 以满足大规模条件
    for i in range(35):
        epic_id = f"EPIC-{i+1:04d}"
        create_epic_file(issues_root, epic_id, f"Test Epic {i}", has_domain=True)
    
    # 创建一个 Feature，parent 是 EPIC-0001（有 domain），但自己没有 domain
    # 这应该通过检查（逻辑继承）
    feature_path = issues_root / "Features" / "open" / "FEAT-0001-child-feature.md"
    feature_path.parent.mkdir(parents=True, exist_ok=True)
    feature_path.write_text(
        """---
id: FEAT-0001
type: feature
status: open
stage: draft
title: Child Feature
parent: EPIC-0001
domains: []
tags:
  - "#EPIC-0001"
  - "#FEAT-0001"
---

## FEAT-0001: Child Feature

- [ ] Task 1
- [ ] Task 2
"""
    )
    
    # 运行 Linter
    diagnostics = check_integrity(issues_root)
    
    # 验证 Feature 没有 Domain Governance 错误（因为继承了父 Epic 的 Domain）
    feature_governance_errors = [
        d for d in diagnostics 
        if "Domain Governance" in d.message and d.source == "FEAT-0001"
    ]
    assert len(feature_governance_errors) == 0


def test_child_without_domain_and_parent_without_domain_fails(issues_root):
    """验证在大规模项目中，子 Issue 和父 Epic 都没有 Domain 时报错。"""
    # 创建 Domain 定义
    domain_dir = issues_root / "Domains"
    domain_dir.mkdir(parents=True, exist_ok=True)
    (domain_dir / "Core.md").write_text("# Core")
    
    # 创建 35 个 Epic，其中 EPIC-0001 没有 domain
    for i in range(35):
        epic_id = f"EPIC-{i+1:04d}"
        # EPIC-0001 (i=0) 没有 domain，其他的有
        has_domain = i > 0
        create_epic_file(issues_root, epic_id, f"Test Epic {i}", has_domain=has_domain)
    
    # 创建一个 Feature，parent 是 EPIC-0001（没有 domain），自己也没有 domain
    feature_path = issues_root / "Features" / "open" / "FEAT-0001-child-feature.md"
    feature_path.parent.mkdir(parents=True, exist_ok=True)
    feature_path.write_text(
        """---
id: FEAT-0001
type: feature
status: open
stage: draft
title: Child Feature
parent: EPIC-0001
domains: []
tags:
  - "#EPIC-0001"
  - "#FEAT-0001"
---

## FEAT-0001: Child Feature

- [ ] Task 1
- [ ] Task 2
"""
    )
    
    # 运行 Linter
    diagnostics = check_integrity(issues_root)
    
    # 验证 Feature 有 Domain Governance 错误
    feature_governance_errors = [
        d for d in diagnostics 
        if "Domain Governance" in d.message and d.source == "FEAT-0001"
    ]
    assert len(feature_governance_errors) >= 1, f"Expected Domain Governance error for FEAT-0001, got: {[(d.source, d.message) for d in diagnostics if 'Governance' in d.message]}"
    assert "Parent 'EPIC-0001' also has no domains" in feature_governance_errors[0].message


def test_small_project_no_strict_domain_check(issues_root):
    """验证小规模项目（Epics <= 32 且 Issues <= 128）不触发严格 Domain 检查。"""
    # 创建 Domain 定义
    domain_dir = issues_root / "Domains"
    domain_dir.mkdir(parents=True, exist_ok=True)
    (domain_dir / "Core.md").write_text("# Core")
    
    # 只创建 5 个 Epic（小规模）
    for i in range(5):
        epic_id = f"EPIC-{i+1:04d}"
        create_epic_file(issues_root, epic_id, f"Test Epic {i}", has_domain=False)
    
    # 运行 Linter
    diagnostics = check_integrity(issues_root)
    
    # 验证没有 Domain Governance 错误（小规模项目不触发）
    governance_errors = [d for d in diagnostics if "Domain Governance" in d.message]
    assert len(governance_errors) == 0
