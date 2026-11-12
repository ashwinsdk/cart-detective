# Skill: Git Branching, Commits, and Release Management

- **Name**: git-and-release
- **Description**: Strict git operations, conventional commit authoring, clean branch merges, and release verification.

## When to Use
Use this skill when initializing phase branches, committing code changes, merging into main, pushing to remote, and tagging releases.

## Step by Step Procedure
1. Create a dedicated branch for the current phase:
   ```bash
   git checkout -b phase/<number>-<short-name>
   ```
2. Verify all quality gates succeed prior to staging files.
3. Check status: `git status` to ensure only intended files are tracked.
4. Author concise conventional commit messages:
   - Format: `feat: <description>`, `fix: <description>`, `docs: <description>`, `chore: <description>`, `test: <description>`.
   - Never use emojis or dashes in commit messages.
5. Merge into `main` using fast-forward or squash merge:
   ```bash
   git checkout main
   git merge --ff-only phase/<number>-<short-name>
   ```
6. Push to `origin main`:
   ```bash
   git push origin main
   ```
7. If push fails due to authentication or credentials, halt and provide the exact token or command needed.

## Code Patterns
```bash
# Correct commit message examples
git commit -m "docs: add starter files and pipeline specifications"
git commit -m "feat: implement token bucket rate limiter in fetcher"
git commit -m "test: add mock fixtures for amazon json ld extraction"
```

## Pitfalls
- Adding decorative emojis to commit messages (like sparkles or rockets).
- Using em dashes or en dashes in commit bodies.
- Committing unstaged temporary files, `.env`, or `.sqlite` databases.

## Done Checklist
- [ ] Phase branch follows naming convention `phase/<number>-<short-name>`.
- [ ] Conventional commit format verified.
- [ ] No emojis or dashes in commit message.
- [ ] Merged cleanly into main.
- [ ] Pushed to origin.
