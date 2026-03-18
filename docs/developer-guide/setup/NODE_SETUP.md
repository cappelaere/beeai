# Node.js Setup with nvm

## Current Setup

- **Node.js Version**: v24.13.1 (LTS)
- **npm Version**: v11.8.0
- **Package Manager**: nvm (Node Version Manager)

## Quick Start

### Using nvm in This Project

```bash
# Load nvm (in new terminal sessions)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Use the project's Node version (reads .nvmrc)
nvm use

# Or automatically (if .nvmrc exists)
cd /path/to/beeai  # nvm will auto-switch if configured
```

### Automatic Version Switching

Add this to your `~/.bashrc` or `~/.zshrc` for automatic version switching:

```bash
# Load nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Auto-switch Node version when entering directory with .nvmrc
autoload -U add-zsh-hook
load-nvmrc() {
  local node_version="$(nvm version)"
  local nvmrc_path="$(nvm_find_nvmrc)"

  if [ -n "$nvmrc_path" ]; then
    local nvmrc_node_version=$(nvm version "$(cat "${nvmrc_path}")")

    if [ "$nvmrc_node_version" = "N/A" ]; then
      nvm install
    elif [ "$nvmrc_node_version" != "$node_version" ]; then
      nvm use
    fi
  elif [ "$node_version" != "$(nvm version default)" ]; then
    echo "Reverting to nvm default version"
    nvm use default
  fi
}
add-zsh-hook chpwd load-nvmrc
load-nvmrc
```

## Installation

### Install nvm (if not installed)

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
```

### Install Node.js LTS

```bash
# Install latest LTS version
nvm install --lts

# Set as default
nvm alias default 24

# Use it
nvm use default
```

## Common Commands

### Version Management

```bash
# List installed versions
nvm ls

# List available versions
nvm ls-remote

# Install specific version
nvm install 24.13.1

# Use specific version
nvm use 24.13.1

# Set default version
nvm alias default 24

# Check current version
node --version
npm --version
```

### Package Management

```bash
# Install dependencies
npm install

# Install package
npm install <package-name>

# Install dev dependency
npm install --save-dev <package-name>

# Update packages
npm update

# Check for outdated packages
npm outdated
```

## Project Dependencies

### Frontend Tests (tests/ directory)

```bash
cd tests

# Install test dependencies
npm install

# Run tests
npm test           # All tests
npm run test:unit  # Unit tests only
npm run test:e2e   # E2E tests only
```

### Test Dependencies

The project uses:
- **Jest** - JavaScript testing framework
- **Playwright** - End-to-end testing
- **jsdom** - DOM testing utilities

See [tests/package.json](../tests/package.json) for complete dependency list.

## Version Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Node.js** | 18.x | 24.x (LTS) |
| **npm** | 9.x | 11.x |

## Troubleshooting

### nvm command not found

**Solution:** Load nvm in your shell:

```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
```

Or add to your `~/.bashrc` or `~/.zshrc`.

### Wrong Node version

**Solution:** Use the version specified in `.nvmrc`:

```bash
nvm use
```

### npm install fails

**Solutions:**

1. **Clear npm cache:**
   ```bash
   npm cache clean --force
   ```

2. **Delete node_modules and reinstall:**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Use specific Node version:**
   ```bash
   nvm use 24
   npm install
   ```

### Permission errors

**Solution:** Never use `sudo` with npm. Use nvm-installed Node:

```bash
# Check Node installation location
which node
# Should be: /Users/patrice/.nvm/versions/node/v24.13.1/bin/node

# If using system Node, switch to nvm version
nvm use default
```

## Benefits of nvm

### ✅ Version Management
- Install multiple Node versions side-by-side
- Switch between versions per project
- Easy upgrades and downgrades

### ✅ No Permission Issues
- No need for `sudo`
- User-level installation
- Clean and isolated

### ✅ Project Consistency
- `.nvmrc` ensures team uses same version
- Automatic version switching
- Reproducible builds

### ✅ Easy Updates
- Simple LTS upgrades
- Test new versions safely
- Rollback if needed

## Migration from Old Node

### Before (v11.12.0)
```bash
$ node --version
v11.12.0

$ npm --version
6.7.0
```

### After (v24.13.1 LTS)
```bash
$ node --version
v24.13.1

$ npm --version
11.8.0
```

### Benefits
- **9+ years newer** - Latest features and security
- **Better performance** - Faster execution
- **Modern syntax** - Latest ECMAScript support
- **Security patches** - Up-to-date security fixes
- **Package compatibility** - Modern packages work correctly

## .nvmrc File

The `.nvmrc` file specifies the Node version for this project:

```
24.13.1
```

**Usage:**
```bash
# Automatically use correct version
cd /path/to/beeai
nvm use
# Now using node v24.13.1
```

## Best Practices

### 1. Always Use nvm
```bash
# Good
nvm use
npm install

# Bad
sudo npm install  # Never use sudo with npm
```

### 2. Check Version Before Development
```bash
# Before starting work
nvm use
node --version  # Should show v24.13.1
```

### 3. Update Regularly
```bash
# Update nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Update Node LTS
nvm install --lts --reinstall-packages-from=current
nvm alias default 24
```

### 4. Use Package Lock
```bash
# Commit package-lock.json
git add package-lock.json
git commit -m "Update dependencies"
```

## Shell Configuration

### For Bash (~/.bashrc)

```bash
# Load nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
```

### For Zsh (~/.zshrc)

```bash
# Load nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
```

## Verification

```bash
# Check nvm is working
command -v nvm

# Check Node version
node --version
# Expected: v24.13.1

# Check npm version
npm --version
# Expected: 11.8.0

# Check installation location
which node
# Expected: /Users/patrice/.nvm/versions/node/v24.13.1/bin/node
```

## Resources

- **nvm Repository**: https://github.com/nvm-sh/nvm
- **Node.js Official**: https://nodejs.org/
- **npm Documentation**: https://docs.npmjs.com/

---

**Status**: ✅ **COMPLETE**

Node.js v24.13.1 (LTS) installed and configured with nvm for the RealtyIQ project.
