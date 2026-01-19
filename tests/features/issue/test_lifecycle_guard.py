import shutil
import tempfile
from pathlib import Path
from monoco.features.issue import core
from monoco.features.issue.models import (
    IssueType,
    IssueStatus,
    IssueStage,
    IssueSolution,
)


def test_guard_conditions(issues_root):
    """
    Validation Test for FEAT-0013: Lifecycle Guard Conditions
    """

    # Setup: Create a DOING issue
    print("\n[Test] Creating Issue in DOING state...")
    fid = core.create_issue_file(issues_root, IssueType.FEATURE, "Guard Test Feature")[
        0
    ].id
    # Move to DOING
    core.update_issue(issues_root, fid, stage=IssueStage.DOING)

    f_path = core.find_issue_path(issues_root, fid)
    meta = core.parse_issue(f_path)
    assert meta.stage == IssueStage.DOING
    print(f"✅ Issue {fid} is now DOING")

    # 1. Test CLose Guard (Fail)
    # ------------------------------------------------
    print("\n[Test] Attempting direct close from DOING (Should Fail)...")
    try:
        core.update_issue(
            issues_root,
            fid,
            status=IssueStatus.CLOSED,
            solution=IssueSolution.IMPLEMENTED,
        )
        print("❌ FAILED: Should have raised ValueError")
        raise AssertionError("Close Guard Failed")
    except ValueError as e:
        print(f"✅ PASSED: Correctly caught error: {e}")
        assert "Lifecycle Policy" in str(e)
        # assert "Cannot close issue in progress" in str(e) # eclipsed by stricter rule

    # 2. Test Happy Path (Doing -> Review -> Closed)
    # ------------------------------------------------
    print("\n[Test] Transitioning DOING -> REVIEW -> CLOSED...")

    # Complete tasks to satisfy validator
    content = f_path.read_text()
    new_content = content.replace("- [ ]", "- [x]")
    new_content += "\n\n## Review Comments\n\n- [x] Self-Review\n"
    f_path.write_text(new_content)

    # Update to Review
    core.update_issue(issues_root, fid, stage=IssueStage.REVIEW)
    meta = core.parse_issue(f_path)
    assert meta.stage == IssueStage.REVIEW

    # Now Close
    core.update_issue(
        issues_root, fid, status=IssueStatus.CLOSED, solution=IssueSolution.IMPLEMENTED
    )
    f_path = core.find_issue_path(issues_root, fid)  # Re-find after move
    meta = core.parse_issue(f_path)
    assert meta.status == IssueStatus.CLOSED
    assert meta.stage == IssueStage.DONE
    print("✅ PASSED: Happy path closed successfully.")

    # 3. Test Abandon Path (Doing -> Draft -> Closed)
    # ------------------------------------------------
    print("\n[Test] Transitioning DOING -> DRAFT -> CLOSED...")
    # Create new Doing issue
    fid2 = core.create_issue_file(
        issues_root, IssueType.FEATURE, "Abandon Test Feature"
    )[0].id
    core.update_issue(issues_root, fid2, stage=IssueStage.DOING)

    # Back to Draft
    core.update_issue(issues_root, fid2, stage=IssueStage.DRAFT)

    # FIX: Prepare content for Close (Done)
    f_path2 = core.find_issue_path(issues_root, fid2)
    content2 = f_path2.read_text()
    new_content2 = content2.replace("- [ ]", "- [x]")
    new_content2 += "\n\n## Review Comments\n\n- [x] Cancelled\n"
    f_path2.write_text(new_content2)

    # Close
    core.update_issue(
        issues_root, fid2, status=IssueStatus.CLOSED, solution=IssueSolution.WONTFIX
    )

    meta = core.parse_issue(core.find_issue_path(issues_root, fid2))
    assert meta.status == IssueStatus.CLOSED
    print("✅ PASSED: Abandon path closed successfully.")


if __name__ == "__main__":
    try:
        tmp_dir = tempfile.mkdtemp()
        path = Path(tmp_dir)
        core.init(path)
        test_guard_conditions(path)
        shutil.rmtree(tmp_dir)
        print("\n🎉 ALL TESTS PASSED.")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
