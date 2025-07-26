u# Week 1 Day 1: Modern Development Environment Setup (2025)

> **Status**: Morning Session ✅ COMPLETED (2025-07-26)

## Overview
**Goal**: Establish cutting-edge local development environment with security-first AWS setup  
**Approach**: Modern tooling with trunk-based development  
**Stack**: UV, Ruff, mise, just, LocalStack, Terraform latest  

---

## Day 1 Morning Session: Development Tools & Security Setup

### 1. Modern Development Tools Installation (1 hour)

#### Core Tools
```bash
# Package managers and environment management
curl -LsSf https://astral.sh/uv/install.sh | sh          # UV for Python (10-100x faster)
curl https://mise.run | sh                                # mise for tool version management
cargo install just                                        # just for modern task running

# Infrastructure tools
brew install terraform                                    # Latest stable Terraform
pip install terraform-local                               # tflocal for LocalStack

# Container tools (if not installed)
brew install --cask docker                               # Docker Desktop
brew install localstack                                  # LocalStack CLI
```

#### Tool Configuration
```bash
# Configure mise for project tools (.mise.toml)
cat > .mise.toml << 'EOF'
[tools]
python = "3.13"
node = "20"
terraform = "latest"
aws-cli = "latest"

[env]
UV_CACHE_DIR = ".cache/uv"
DOCKER_BUILDKIT = "1"
EOF

# Activate mise
mise install
mise use
```

### 2. Secure AWS Credentials Setup (1 hour)

#### AWS IAM Best Practices Setup
```bash
# Create secure credentials directory
mkdir -p ~/.aws/credentials.d
chmod 700 ~/.aws/credentials.d

# Create AWS credentials script (NOT storing actual credentials)
cat > scripts/setup-aws-credentials.sh << 'EOF'
#!/bin/bash
# Secure AWS Credentials Setup Script

echo "=== AWS Credentials Security Setup ==="
echo "This script helps you configure AWS credentials securely."
echo ""

# Option 1: AWS SSO (Recommended for organizations)
setup_aws_sso() {
    echo "Setting up AWS SSO..."
    aws configure sso
    echo "AWS_PROFILE=your-sso-profile" >> .env.local
}

# Option 2: Temporary credentials with MFA
setup_temp_credentials() {
    echo "Setting up temporary credentials with MFA..."
    read -p "Enter your MFA device ARN: " MFA_ARN
    read -p "Enter your MFA token: " MFA_TOKEN
    
    # Get temporary credentials
    aws sts get-session-token \
        --serial-number "$MFA_ARN" \
        --token-code "$MFA_TOKEN" \
        --duration-seconds 43200 > ~/.aws/temp-creds.json
    
    # Parse and export credentials
    export AWS_ACCESS_KEY_ID=$(jq -r '.Credentials.AccessKeyId' ~/.aws/temp-creds.json)
    export AWS_SECRET_ACCESS_KEY=$(jq -r '.Credentials.SecretAccessKey' ~/.aws/temp-creds.json)
    export AWS_SESSION_TOKEN=$(jq -r '.Credentials.SessionToken' ~/.aws/temp-creds.json)
    
    # Clean up
    rm ~/.aws/temp-creds.json
}

# Option 3: IAM User with minimal permissions (Development only)
setup_iam_user() {
    echo "Setting up IAM user credentials..."
    echo "NEVER commit these credentials. Use environment variables only!"
    
    # Use aws-vault for secure storage
    brew install aws-vault
    aws-vault add development-profile
}

echo "Choose credential setup method:"
echo "1) AWS SSO (Recommended)"
echo "2) Temporary credentials with MFA"
echo "3) IAM User with aws-vault"
read -p "Enter choice (1-3): " choice

case $choice in
    1) setup_aws_sso ;;
    2) setup_temp_credentials ;;
    3) setup_iam_user ;;
    *) echo "Invalid choice" ;;
esac

echo ""
echo "=== Security Reminders ==="
echo "✓ Never commit AWS credentials to git"
echo "✓ Always use temporary or SSO credentials when possible"
echo "✓ Enable MFA on all AWS accounts"
echo "✓ Use least-privilege IAM policies"
echo "✓ Rotate credentials regularly"
EOF

chmod +x scripts/setup-aws-credentials.sh
```

#### Environment Variables Security
```bash
# Create secure environment template
cat > .env.template << 'EOF'
# AWS Configuration (DO NOT ADD REAL CREDENTIALS HERE)
AWS_PROFILE=                    # Use named profile instead of keys
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1

# LocalStack Configuration (Safe defaults)
LOCALSTACK_HOST=localhost.localstack.cloud
AWS_ACCESS_KEY_ID=test         # LocalStack only
AWS_SECRET_ACCESS_KEY=test     # LocalStack only
AWS_ENDPOINT_URL=http://localhost:4566

# Security settings
ENABLE_SECURITY_SCANNING=true
ROTATE_CREDENTIALS_DAYS=90
EOF

# Create git-ignored local env file
cp .env.template .env.local
echo ".env.local" >> .gitignore
```

### 3. Project Configuration with Modern Tools (1 hour)

#### Initialize just (Modern Make Alternative)
```bash
# Create justfile for project tasks
cat > justfile << 'EOF'
# Modern task runner configuration
set dotenv-load := true
set export := true

# Default recipe to display help
default:
    @just --list

# Development environment setup
setup:
    uv sync --dev
    mise install
    docker-compose pull
    @echo "✅ Development environment ready!"

# Start all services
up:
    docker-compose up -d
    @echo "Waiting for services..."
    sleep 10
    just init-aws

# Initialize LocalStack AWS resources
init-aws:
    ./scripts/init_aws_resources.sh

# Code quality checks (ultra-fast with Ruff)
lint:
    uv run ruff check src/ tests/
    uv run ruff format --check src/ tests/
    uv run mypy src/

# Format code
fmt:
    uv run ruff check --fix src/ tests/
    uv run ruff format src/ tests/

# Run tests
test:
    uv run pytest tests/ -v

# Security scan
security:
    uv run bandit -r src/
    uv run pip-audit
    docker scout cves

# Clean everything
clean:
    docker-compose down -v
    rm -rf .cache/
    uv cache clean
    find . -type d -name __pycache__ -exec rm -rf {} +

# AWS credentials check (no exposure)
check-aws:
    @echo "Checking AWS configuration..."
    @aws sts get-caller-identity > /dev/null 2>&1 && echo "✅ AWS credentials configured" || echo "❌ AWS credentials not configured"
    @echo "Active profile: ${AWS_PROFILE:-default}"
    @test -f ~/.aws/credentials && echo "⚠️  Warning: Found credentials file. Consider using SSO or aws-vault" || echo "✅ No credentials file found (good!)"
EOF
```

#### VS Code Workspace Configuration
```bash
# Create VS Code workspace with 2025 best practices
cat > .vscode/settings.json << 'EOF'
{
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll": true,
        "source.organizeImports": true
    },
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff"
    },
    "python.linting.enabled": false,  // Ruff handles this
    "python.formatting.provider": "none",  // Ruff handles this
    "ruff.enable": true,
    "ruff.lint.enable": true,
    "ruff.format.enable": true,
    "mypy-type-checker.importStrategy": "fromEnvironment",
    
    // Security
    "git.allowNoVerifyCommit": false,
    "files.exclude": {
        "**/.env.local": false,  // Show but track it's there
        "**/*.pyc": true,
        "**/__pycache__": true
    },
    
    // Modern tools
    "terminal.integrated.env.linux": {
        "MISE_SHELL": "bash"
    },
    "terminal.integrated.env.osx": {
        "MISE_SHELL": "zsh"
    }
}
EOF
```

### 4. Trunk-Based Development Setup (30 mins)

#### Git Configuration
```bash
# Configure trunk-based development
git config --local branch.main.mergeoptions "--no-ff"

# Set up commit signing (security best practice)
git config --local commit.gpgsign true

# Configure git aliases for trunk-based flow
git config --local alias.new "checkout -b"
git config --local alias.done "checkout main"
git config --local alias.sync "!git checkout main && git pull --rebase"
git config --local alias.publish "push -u origin HEAD"

# Create pre-push hook for security
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
# Pre-push security checks

echo "Running pre-push security checks..."

# Check for AWS credentials
if git diff --cached --name-only | xargs grep -l "AWS_SECRET\|aws_secret\|AKIA" 2>/dev/null; then
    echo "❌ ERROR: Possible AWS credentials detected in commit!"
    echo "Remove sensitive data before pushing."
    exit 1
fi

# Run security scan
just security || {
    echo "❌ Security scan failed. Fix issues before pushing."
    exit 1
}

echo "✅ Security checks passed"
EOF

chmod +x .git/hooks/pre-push
```

#### Trunk-Based Workflow Documentation
```bash
# Create trunk-based development guide
cat > docs/trunk-based-development.md << 'EOF'
# Trunk-Based Development Workflow

## Overview
We use trunk-based development for faster integration and simpler workflows.

## Workflow

### 1. Start New Work
```bash
git sync                          # Update main
git new feature/my-feature        # Create feature branch
```

### 2. Regular Development
```bash
# Make changes
just fmt                          # Format code
just lint                         # Check quality
just test                         # Run tests

# Commit often
git add -p                        # Stage changes carefully
git commit -m "feat: add new feature"
```

### 3. Integration
```bash
git sync                          # Update main
git rebase main                   # Rebase on latest
just test                         # Verify everything works
git publish                       # Push to origin
```

### 4. Create PR
- Keep PRs small (< 400 lines changed)
- Merge within 24 hours
- Use GitHub's "Squash and merge"

## Branch Protection Rules
- Require PR reviews
- Require status checks (CI/CD)
- Require up-to-date branches
- Enable "Dismiss stale reviews"
EOF
```

### 5. Security Documentation (30 mins)

```bash
# Create comprehensive security guide
cat > docs/aws-security-setup.md << 'EOF'
# AWS Security Configuration Guide

## Credential Management Options

### Option 1: AWS SSO (Recommended)
Best for organizations with AWS SSO enabled.

```bash
# Configure SSO
aws configure sso

# Login
aws sso login --profile your-profile

# Use in commands
AWS_PROFILE=your-profile aws s3 ls
```

### Option 2: AWS Vault (IAM Users)
Secure storage for long-lived credentials.

```bash
# Install
brew install aws-vault

# Add credentials (stored in OS keychain)
aws-vault add my-profile

# Use credentials
aws-vault exec my-profile -- aws s3 ls

# Or export to environment
aws-vault exec my-profile -- just deploy
```

### Option 3: Temporary Credentials
For maximum security with MFA.

```bash
# Get temporary credentials (12 hours)
./scripts/setup-aws-credentials.sh
# Choose option 2 and follow MFA prompts
```

## IAM Best Practices

### Development IAM Policy
Create a limited IAM user for development:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "dynamodb:*",
        "kinesis:*",
        "glue:*",
        "athena:*"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        },
        "StringLike": {
          "aws:userid": "AIDAI*"
        }
      }
    }
  ]
}
```

### Production Deployment Role
Use assume-role for production:

```bash
# .env.production (git-ignored)
DEPLOY_ROLE_ARN=arn:aws:iam::123456789012:role/DataPlatformDeployRole
```

## Security Checklist

- [ ] Enable MFA on AWS root account
- [ ] Enable MFA on IAM users
- [ ] Use temporary credentials when possible
- [ ] Never commit credentials
- [ ] Use least-privilege IAM policies
- [ ] Enable CloudTrail
- [ ] Enable GuardDuty
- [ ] Set up billing alerts
- [ ] Use separate AWS accounts for dev/prod
- [ ] Implement SCPs for organization

## Credential Rotation

Set up automatic reminders:
```bash
# Add to your calendar
- Every 90 days: Rotate IAM user access keys
- Every 30 days: Review IAM policies
- Every 180 days: Audit service accounts
```
EOF
```

## Completed Morning Session Checklist ✅

- [x] Modern tools installed (UV, mise, just)
- [x] AWS credentials securely configured
- [x] Project configuration with justfile
- [x] VS Code workspace optimized
- [x] Trunk-based development setup
- [x] Security documentation complete
- [x] Pre-push hooks configured
- [x] Environment templates created

## Next Steps
Continue with Docker and LocalStack setup in the afternoon session, focusing on:
- Multi-stage Dockerfile with security best practices
- Complete LocalStack AWS service emulation
- Container security scanning integration
- Infrastructure as Code preparation