# Cycle 1

**Saw:** `protected_branch_guard.py` blocked every `git push` while HEAD was `main`/`master`; push args were never read. `test_master_write_src_blocked` failed because the test mock returned the branch name for `rev-parse --show-toplevel`.

**Did:** added `is_tag_only_push` (remote + refspec parse; a name counts as a tag only if git confirms `refs/tags/<name>` and no branch shares it; unknown blocks). Fixed the mock (`show-ref`, `--show-toplevel`). Added `TestTagPush`. e-spec 1.3.0 -> 1.3.1, README row.

**Result:** 5 of 5 criteria hold. Suite 28/28. Real-repo run 9/9. Develop push left allowed, as before (owner ruling).

**Accepted, not fixed:** only the first `|` segment is parsed (existing behaviour); `git push` chained after `&&` is judged on the same tokens, which can only over-block.
