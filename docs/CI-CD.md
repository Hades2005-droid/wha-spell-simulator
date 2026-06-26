# CI/CD Pipeline Documentation

## Overview
Automated testing, building, and deployment pipeline using GitHub Actions.

## Workflows

### 1. Test Workflow (.github/workflows/test.yml)
Runs on every push and pull request to main/develop branches.

**Jobs:**
- **test**: Runs on Node.js 18.x and 20.x
  - Install dependencies
  - Run linter (warnings allowed)
  - Run test suite
  - Build project

- **coverage**: Generates and uploads coverage reports
  - Runs after test passes
  - Uploads to Codecov

**Triggered by:**
- Push to main or develop
- Pull requests to main or develop

### 2. Build & Deploy Workflow (.github/workflows/build.yml)
Builds and deploys application to GitHub Pages.

**Jobs:**
- **build**: Build application
  - Install dependencies
  - Run build
  - Archive dist/ folder

- **deploy**: Deploy to GitHub Pages (main branch only)
  - Download build artifacts
  - Deploy to gh-pages branch
  - Accessible at: https://[user].github.io/wha-spell-simulator

- **release**: Create GitHub release (on version tags)
  - Builds project
  - Creates release with tag

**Triggered by:**
- Push to main branch
- Push of version tags (v*)
- Manual workflow dispatch

### 3. Linting

Pre-commit linting (when Husky is installed):
```bash
npm install husky --save-dev
npx husky install
npx husky add .husky/pre-commit "npm run lint:fix && npm test"
```

**Skipping checks (not recommended):**
```bash
git commit --no-verify  # Skip pre-commit hook
```

## Local Development Setup

### Prerequisites
- Node.js 18.x or 20.x
- npm or yarn

### Initial Setup
```bash
# Clone repository
git clone https://github.com/[user]/wha-spell-simulator.git
cd wha-spell-simulator

# Install dependencies
npm install

# Install Husky hooks
npx husky install
```

### Development Commands
```bash
# Start dev server
npm start

# Run tests
npm test

# Check linting
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Build for production
npm run build

# Serve production build
npm run preview
```

## Continuous Integration Checks

### Before Merge to Main
1. ✅ All tests pass (174/174)
2. ✅ Linter passes (0 errors)
3. ✅ Build succeeds
4. ✅ Code review approved
5. ✅ Branch is up-to-date

### Deployment Process

**Automatic (main branch):**
1. Push to main triggers test workflow
2. If all checks pass, build workflow runs
3. Build artifacts uploaded
4. Deploy job runs, pushes to gh-pages
5. Live at GitHub Pages URL

**Manual (releases):**
1. Create and push version tag: `git tag v1.0.0 && git push origin v1.0.0`
2. GitHub Actions detects tag
3. Release job builds and creates GitHub release
4. Manual deployment if needed

## Performance Metrics

Monitor these metrics in CI/CD:

- **Build time**: Should be <5 minutes
- **Test time**: Should be <2 minutes
- **Bundle size**: Currently ~200KB uncompressed, ~50KB gzipped
- **Test coverage**: Target 70%+ coverage

## Troubleshooting

### Tests Failing in CI but Passing Locally
- Check Node.js version matches CI matrix
- Ensure all dependencies installed: `rm -rf node_modules && npm ci`
- Check for platform-specific issues (Windows line endings, etc.)

### Build Failing
- Check that all files are committed
- Verify no uncommitted changes affecting build
- Check build logs for specific errors

### Deployment Not Updating
- Verify gh-pages branch exists
- Check GitHub Pages settings in repo
- Clear browser cache or use incognito window

### Pre-commit Hook Not Running
```bash
# Reinstall hooks
npx husky install

# Make hook executable
chmod +x .husky/pre-commit

# Verify hook exists
ls -la .husky/
```

## Best Practices

1. **Commit Messages**: Use conventional commits
   ```
   feat: add new element
   fix: resolve ring detection bug
   docs: update architecture guide
   ```

2. **Branch Naming**: Use descriptive names
   ```
   feature/new-element
   fix/ring-detection
   docs/api-reference
   ```

3. **PRs**: Include description and testing steps

4. **Tags**: Use semantic versioning
   ```
   v1.0.0  # Release
   v1.0.0-beta.1  # Pre-release
   v1.0.0-rc.1  # Release candidate
   ```

## Future Enhancements

- [ ] Performance benchmarking in CI
- [ ] Visual regression testing
- [ ] Automated dependency updates
- [ ] Staging environment deployment
- [ ] Slack/Discord notifications
- [ ] Code quality metrics (SonarQube)
- [ ] Security scanning (Dependabot)

