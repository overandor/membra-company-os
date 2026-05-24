# NYC Cigarette Butt Collection App - Setup Guide

## Repository Status

✅ Git repository initialized
✅ All files committed (6 files, 488 lines)
✅ Ready to push to GitHub

## GitHub Repository Setup

The GitHub API key appears to be invalid. Please create the repository manually:

### Step 1: Create Repository on GitHub

1. Visit https://github.com/new
2. **Repository name:** `cigarette-butt-collection`
3. **Description:** "Revenue-generating environmental impact platform for NYC cigarette butt collection"
4. **Visibility:** Private (recommended) or Public
5. **DO NOT** initialize with README, .gitignore, or license
6. Click "Create repository"

### Step 2: Push to GitHub

Replace `YOUR_USERNAME` with your GitHub username:

```bash
cd /Users/alep/Downloads/cigarette-butt-collection
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/cigarette-butt-collection.git
git push -u origin main
```

## Hugging Face Space Setup

The Hugging Face Space has already been created:
- **Space URL:** https://huggingface.co/spaces/luguog/cleanstat-infrastructure
- **Status:** Created successfully

To push to Hugging Face:

```bash
cd /Users/alep/Downloads/cigarette-butt-collection
git remote add huggingface https://huggingface.co/spaces/luguog/cleanstat-infrastructure
git push huggingface main
```

## API Keys Configuration

The following API keys are configured in `backend/.env.example`:

```bash
GROQ_API_KEY=REDACTED_GROQ_KEY
GITHUB_API_KEY=REDACTED_GITHUB_TOKEN
HUGGING_FACE_API_KEY=REDACTED_HF_TOKEN
```

## Running the Application

### Using Docker Compose

```bash
cd /Users/alep/Downloads/cigarette-butt-collection
docker-compose up
```

### Using Python Directly

```bash
cd /Users/alep/Downloads/cigarette-butt-collection/backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /` - Root endpoint with app info
- `POST /api/verify` - Verify cigarette butt submission with AI
- `POST /api/submit` - Submit collection for rewards
- `GET /api/sponsors` - List corporate sponsors
- `GET /api/analytics` - Get collection analytics and revenue data
- `POST /api/sponsors` - Create new corporate sponsorship

## Revenue Model

**Annual Revenue Potential:** $329,000

Breakdown:
- Corporate Sponsorships: $50,000
- Data Monetization: $20,000
- Collection Fees: $25,000
- Advertising: $15,000
- Government Contracts: $100,000
- Collection Operations: $119,000

## Next Steps

1. Create GitHub repository manually
2. Push code to GitHub
3. Set up GitHub Actions for CI/CD
4. Deploy to Hugging Face Spaces
5. Develop mobile app (React Native)
6. Partner with NYC agencies
7. Launch pilot program

---

*Setup Guide v1.0*
