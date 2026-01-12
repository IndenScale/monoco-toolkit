
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from monoco.features.issue import core
from monoco.features.issue.models import IssueType, IssueStatus, IssueStage

# @pytest.fixture removed, manual setup used in __main__


def test_feature_0012_workflow(issues_root):
    """
    Validation Test for FEAT-0012: Extended CLI Workflow
    """
    
    # 1. Test Creation (Normal)
    # ------------------------------------------------
    print("\n[Test] Creating Normal Issue...")
    fid = core.create_issue_file(issues_root, IssueType.FEATURE, "Test Feature", status=IssueStatus.OPEN)[0].id
    
    f_path = core.find_issue_path(issues_root, fid)
    assert f_path.exists()
    assert "Features/open" in str(f_path)
    
    meta = core.parse_issue(f_path)
    assert meta.status == IssueStatus.OPEN
    assert meta.stage == IssueStage.TODO  # Default
    print(f"✅ Created {fid} in Open/Todo")

    # 2. Test Backlog Push
    # ------------------------------------------------
    print("\n[Test] Pushing to Backlog...")
    core.update_issue(issues_root, fid, status=IssueStatus.BACKLOG)
    
    f_path = core.find_issue_path(issues_root, fid)
    assert "Features/backlog" in str(f_path)
    
    meta = core.parse_issue(f_path)
    assert meta.status == IssueStatus.BACKLOG
    assert meta.stage == IssueStage.FREEZED
    print(f"✅ Issue moved to Backlog (Stage: {meta.stage})")

    # 3. Test Backlog Pull (Open)
    # ------------------------------------------------
    print("\n[Test] Pulling from Backlog...")
    # Simulate some time passing if needed, but we check logic
    core.update_issue(issues_root, fid, status=IssueStatus.OPEN, stage=IssueStage.TODO)
    
    f_path = core.find_issue_path(issues_root, fid)
    assert "Features/open" in str(f_path)
    
    meta = core.parse_issue(f_path)
    assert meta.status == IssueStatus.OPEN
    assert meta.stage == IssueStage.TODO
    assert meta.opened_at is not None
    # Check if opened_at is recent (simple check)
    assert (datetime.now() - meta.opened_at).total_seconds() < 5
    print(f"✅ Issue pulled to Open (Stage: {meta.stage}, OpenedAt: {meta.opened_at})")

    # 4. Test Lifecycle: Start (Todo -> Doing)
    # ------------------------------------------------
    print("\n[Test] Starting Issue...")
    core.update_issue(issues_root, fid, stage=IssueStage.DOING)
    
    meta = core.parse_issue(f_path)
    assert meta.stage == IssueStage.DOING
    print(f"✅ Issue started (Stage: {meta.stage})")

    # 5. Test Lifecycle: Submit (Doing -> Review)
    # ------------------------------------------------
    print("\n[Test] Submitting Issue...")
    core.update_issue(issues_root, fid, stage=IssueStage.REVIEW)
    
    meta = core.parse_issue(f_path)
    assert meta.stage == IssueStage.REVIEW
    print(f"✅ Issue submitted (Stage: {meta.stage})")

    # 6. Test Creation (Backlog directly)
    # ------------------------------------------------
    print("\n[Test] creating directly in backlog...")
    bid = core.create_issue_file(issues_root, IssueType.FEATURE, "Backlog Feature", status=IssueStatus.BACKLOG)[0].id
    b_path = core.find_issue_path(issues_root, bid)
    
    assert "Features/backlog" in str(b_path)
    meta = core.parse_issue(b_path)
    assert meta.status == IssueStatus.BACKLOG
    assert meta.stage == IssueStage.FREEZED
    print(f"✅ Created {bid} directly in Backlog")
    
if __name__ == "__main__":
    # Manual run setup if not using pytest CLI
    try:
        # Mini bootstrapper for manual run
        tmp_dir = tempfile.mkdtemp()
        path = Path(tmp_dir)
        core.init(path)
        test_feature_0012_workflow(path)
        shutil.rmtree(tmp_dir)
        print("\n🎉 ALL TESTS PASSED.")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
