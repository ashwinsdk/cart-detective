# Rule: Zero Emojis and Zero Unicode Dashes

## Scope
Applies to all source code, comments, documentation, UI strings, commit messages, and script outputs in this repository.

## Requirements
1. **No Emojis**: Never use emoji symbols or pictographs in any file or commit message.
2. **No Em Dashes or En Dashes**: Never use unicode characters `\u2014` (em dash) or `\u2013` (en dash). Replace with commas, colons, or periods.
3. **Automated Verification**: Run `python3 scripts/check_compliance.py` before every commit.
4. **Third-Party Data**: Scraped text containing emojis or dashes is sanitized upon display as documented in `docs/DECISIONS.md`.
