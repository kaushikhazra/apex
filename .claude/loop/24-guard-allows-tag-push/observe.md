# Observe

1. `python -m unittest plugins/e-spec/hooks/scripts/test_protected_branch_guard.py -v` — all pass.
2. The hook run as a subprocess against a real git repo on `main` with a real tag (mocked git is not enough).

| AC | Check |
|----|-------|
| 1 | `TestTagPush.test_tag_push_allowed`, `..._in_powershell`; real repo: `v1.0`, `refs/tags/v1.0`, `--tags` exit 0 |
| 2 | `TestTagPush.test_branch_push_blocked`; real repo: bare, `origin`, `main`, `HEAD` exit 2 |
| 3 | `TestTagPush.test_tag_and_branch_blocked`; real repo: `v1.0 main` exit 2 |
| 4 | `TestTagPush.test_guard_off_allows_branch_push`; `TestBranchGuardOptOut` |
| 5 | each case above is a test; suite 28 of 28 including `test_master_write_src_blocked` (mock fixed) |
