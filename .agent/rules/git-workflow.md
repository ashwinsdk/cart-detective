# Rule: Git and Release Workflow

## Scope
Applies to all branches, commits, merges, and releases in this repository.

## Requirements
1. **Branching**:
   - `main` is the primary trunk branch.
   - Each phase is developed on a branch named `phase/<number>-<short-name>` (for example, `phase/0-scaffold`).
2. **Merging**:
   - Once all automated tests and linting succeed, merge the phase branch into `main` via fast-forward or squash merge.
3. **Commit Messages**:
   - Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`.
   - Imperative mood, plain text, lowercase prefix.
   - Zero emojis and zero em/en dashes in commit headers and descriptions.
4. **Pushing to Origin**:
   - Push to `origin main` after completing and merging each phase.
   - If authentication fails, report the needed command or token clearly without attempting arbitrary retries.
