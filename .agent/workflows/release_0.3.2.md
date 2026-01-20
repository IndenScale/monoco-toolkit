---
description: Release Toolkit version 0.3.2 - tag main and publish
---

1. Create a release chore issue
   ```bash
   monoco issue create chore -t "Release Toolkit v0.3.2"
   ```
2. Set the project version
   // turbo
   ```bash
   python Toolkit/scripts/set_version.py 0.3.2
   ```
3. Run release validation checks
   // turbo
   ```bash
   Toolkit/scripts/run_release_checks.sh 0.3.2
   ```
4. Commit version changes and push to `main`
   ```bash
   git add .
   git commit -m "chore: bump version to 0.3.2"
   git push origin main
   ```
5. Create and push git tag `v0.3.2`
   // turbo
   ```bash
   git tag -a v0.3.2 -m "Release Toolkit v0.3.2"
   git push origin v0.3.2
   ```
6. Close the release issue with solution
   ```bash
   monoco issue close <ISSUE_ID> --solution "Released version 0.3.2 with tag v0.3.2"
   ```

*Note*: Replace `<ISSUE_ID>` with the actual ID returned from step 1.
