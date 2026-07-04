## Open Source Release Checklist

Use this checklist before making the repository public or publishing a new release.

### Repository Hygiene

- Confirm `LICENSE` is present and matches the intended license: `GPLv3`
- Confirm `README.md` reflects the current feature set and legal notices
- Confirm `THIRD_PARTY_NOTICES.md` is up to date
- Confirm `.gitignore` excludes local configs, imported resources, logs, and build artifacts
- Confirm no local test data, cache, or generated files are staged

### Sensitive Data Review

- Search for local absolute paths such as `C:\Users\...`
- Search for `steam_path`, local URLs, debug traces, and crash reports
- Search for any token, password, cookie, key, or webhook string
- Search for update endpoints and verify they are intended to be public

### Asset Review

- Remove any bundled media without explicit redistribution permission
- Remove imported resource packs and example configs containing third-party assets
- Remove thumbnails, preview images, and icons if you are not certain of their license
- Verify fonts, audio, videos, and images are either self-created, properly licensed, or excluded

### Branding and Legal Review

- State clearly that the project is not affiliated with `Valve`
- Avoid bundling `Valve` or `Counter-Strike 2` proprietary assets
- Avoid using third-party brand logos in repository assets unless permitted
- Confirm user-imported resources are described as user-responsible in `README.md`

### Dependency Review

- Re-check licenses for the exact versions in `requirements.txt`
- Preserve all required third-party notices
- Verify that binary distribution obligations are satisfied for bundled dependencies

### Release Package Review

- Do not publish `dist/` contents without also making corresponding source available under `GPLv3`
- Do not publish test builds containing personal paths or machine-specific config
- Verify release notes do not mention unsupported legal claims such as "official", "safe from all bans", or similar absolute statements

### Final Git Review

- Run `git status --short`
- Review every staged file manually
- Make sure no files from `imported/`, `configs/`, `thumbnails/`, `dist/`, or `*.log` are included
- Make sure no generated crash reports are included
