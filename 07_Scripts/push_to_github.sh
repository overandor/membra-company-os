#!/bin/bash
# ============================================================
# GITHUB PUSH SCRIPT
# Initializes git repo, commits all code, pushes to GitHub
# ============================================================

set -e

REPO_NAME="laptop-asset-tokenization"
GITHUB_USER=""  # Will be prompted
REPO_DESCRIPTION="Tokenized laptop software assets — $47.5M appraised value | 370K LOC | 100+ systems"

echo "============================================"
echo "GITHUB DEPLOYMENT — Laptop Asset Tokenization"
echo "============================================"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "ERROR: git is not installed. Install it first:"
    echo "  brew install git"
    exit 1
fi

# Configure git if not already
if [ -z "$(git config --global user.name)" ]; then
    echo ""
    echo "Git not configured. Enter your details:"
    read -p "GitHub username: " GITHUB_USER
    read -p "GitHub email: " GITHUB_EMAIL
    
    git config --global user.name "$GITHUB_USER"
    git config --global user.email "$GITHUB_EMAIL"
    echo "[✓] Git configured for $GITHUB_USER"
else
    GITHUB_USER=$(git config --global user.name)
    echo "[✓] Using git user: $GITHUB_USER"
fi

# Navigate to Downloads
cd /Users/alep/Downloads

# Initialize git if not already
if [ ! -d ".git" ]; then
    echo ""
    echo "[1] Initializing git repository..."
    git init
    echo "[✓] Git repo initialized"
else
    echo "[✓] Git repo already exists"
fi

# Ensure .gitignore exists
if [ ! -f ".gitignore" ]; then
    echo "ERROR: .gitignore not found. Run tokenization setup first."
    exit 1
fi

# Stage all files
echo ""
echo "[2] Staging files (respecting .gitignore)..."
git add .

# Show what will be committed
echo ""
echo "[3] Files to be committed:"
git status --short | head -50
FILE_COUNT=$(git status --short | wc -l | tr -d ' ')
echo "    ... and more (total: ~$FILE_COUNT files)"

# Commit
echo ""
echo "[4] Creating commit..."
COMMIT_MSG="Initial commit: Laptop Asset Tokenization

- 100+ trading systems, AI agents, and projects
- 370,361 lines of Python
- Appraised at \$47,503,000 (post-deployment)
- ERC-20 + SPL token contracts included
- Full cryptographic proofs generated

Token: \$LAT (Laptop Asset Token)
Valuation: COCOMO II + DCF + DeFi Comparables"

git commit -m "$COMMIT_MSG"
echo "[✓] Committed"

# Check if GitHub CLI is available
if command -v gh &> /dev/null; then
    echo ""
    echo "[5] GitHub CLI detected. Creating repository..."
    
    # Check if authenticated
    if gh auth status &> /dev/null; then
        # Create repo
        gh repo create "$REPO_NAME" \
            --description "$REPO_DESCRIPTION" \
            --public \
            --source . \
            --remote origin \
            --push
        
        echo "[✓] Repository created and pushed to GitHub"
        echo ""
        echo "Repository: https://github.com/$GITHUB_USER/$REPO_NAME"
    else
        echo "GitHub CLI not authenticated. Run: gh auth login"
        echo "Then re-run this script."
        
        # Add remote manually
        echo ""
        echo "Adding remote origin..."
        git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git" 2>/dev/null || true
        echo "Remote added. Push manually with:"
        echo "  git push -u origin main"
    fi
else
    echo ""
    echo "[5] GitHub CLI not found. Manual steps:"
    echo "  1. Create repo at: https://github.com/new"
    echo "     Name: $REPO_NAME"
    echo "  2. Then run:"
    echo "     git remote add origin https://github.com/$GITHUB_USER/$REPO_NAME.git"
    echo "     git branch -M main"
    echo "     git push -u origin main"
    
    # Add remote anyway
    git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git" 2>/dev/null || true
fi

echo ""
echo "============================================"
echo "DEPLOYMENT COMPLETE"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Verify repo: https://github.com/$GITHUB_USER/$REPO_NAME"
echo "  2. Deploy token: python tokenization/deploy_solana_token.py"
echo "  3. Add liquidity on Raydium/Uniswap"
echo "  4. Update token metadata with GitHub URL"
