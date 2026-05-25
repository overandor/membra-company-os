# IP Asset Platform - Cloud Deployment

A Bloomberg Terminal-style file provenance and collateralization system with LLM-powered appraisals, IPFS integration, and Solana blockchain verification.

## 🚀 Cloud Deployment on Render

### Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Push this code to a GitHub repository
3. **API Keys**: Obtain the following API keys:
   - OpenAI API Key (for LLM appraisals)
   - Pinata API Keys (for IPFS pinning)
   - (Optional) AWS credentials for cloud storage

### Step-by-Step Deployment

#### 1. Prepare Your Repository

```bash
git add .
git commit -m "Configure for cloud deployment"
git push origin main
```

#### 2. Set Up Render Web Service

1. Go to Render Dashboard → New → Web Service
2. Connect your GitHub repository
3. Configure the service:
   - **Name**: ip-asset-platform
   - **Environment**: Node
   - **Region**: Choose nearest region
   - **Branch**: main
   - **Runtime**: Node 18 or later
   - **Build Command**: `npm run build`
   - **Start Command**: `npm start`

#### 3. Set Up PostgreSQL Database

1. Go to Render Dashboard → New → PostgreSQL
2. Configure:
   - **Name**: ip-asset-db
   - **Database Name**: ip_assets
   - **User**: ip_asset_user
   - **Plan**: Free tier available

#### 4. Configure Environment Variables

Add these environment variables in your Render web service:

```bash
# Database (Render will auto-set DATABASE_URL)
DATABASE_URL=[Render will provide this]

# NextAuth
NEXTAUTH_SECRET=[Generate a secure random string]
NEXTAUTH_URL=https://ip-asset-platform.onrender.com

# Cloud LLM (OpenAI)
OPENAI_API_KEY=sk-your-openai-api-key
LLM_PROVIDER=openai
LLM_MODEL=gpt-4

# Cloud IPFS (Pinata)
PINATA_API_KEY=your-pinata-api-key
PINATA_SECRET_KEY=your-pinata-secret-key
PINATA_GATEWAY=https://gateway.pinata.cloud/ipfs

# Solana
SOLANA_RPC_URL=https://api.devnet.solana.com

# Node
NODE_ENV=production
```

#### 5. Deploy

Click "Create Web Service" and Render will:
- Build your Next.js application
- Set up the PostgreSQL database
- Deploy to their global infrastructure
- Provide a public URL like: `https://ip-asset-platform.onrender.com`

### 🔑 Getting API Keys

#### OpenAI API Key
1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up and create an API key
3. Add billing information (required for API access)

#### Pinata API Keys
1. Go to [pinata.cloud](https://pinata.cloud)
2. Sign up for free account
3. Navigate to API Keys section
4. Create new API key

#### Generate NextAuth Secret
```bash
openssl rand -base64 32
```

## 📊 API Endpoints

Once deployed, your public URL will expose these endpoints:

### File Appraisal
```bash
POST https://your-app.onrender.com/api/appraise
Content-Type: application/json

{
  "filePath": "example.ts",
  "fileContent": "your file content here",
  "metadata": {
    "fileType": "typescript",
    "fileSize": 1024
  }
}
```

### IPFS Operations
```bash
POST https://your-app.onrender.com/api/ipfs
Content-Type: application/json

{
  "action": "create_passport",
  "filePath": "example.ts",
  "fileMetadata": {...},
  "appraisal": {...}
}
```

### Solana Operations
```bash
POST https://your-app.onrender.com/api/solana
Content-Type: application/json

{
  "action": "create_dna_transaction",
  "fileDNAHash": "abc123",
  "filePath": "example.ts",
  "metadata": {...}
}
```

## 🧪 Testing Cloud Deployment

### Check Service Status
```bash
curl https://your-app.onrender.com/api/appraise
```

### Test LLM Integration
```bash
curl -X POST https://your-app.onrender.com/api/appraise \
  -H "Content-Type: application/json" \
  -d '{
    "filePath": "test.js",
    "fileContent": "console.log(\"Hello World\");",
    "metadata": {"fileType": "javascript", "fileSize": 30}
  }'
```

### Test IPFS Integration
```bash
curl https://your-app.onrender.com/api/ipfs?action=check_connection
```

### Test Solana Integration
```bash
curl https://your-app.onrender.com/api/solana?action=check_connection
```

## 🔧 Configuration Options

### LLM Provider Switching
You can switch between different LLM providers by changing environment variables:

```bash
# OpenAI (default)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4

# For future providers (Anthropic, etc.)
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-opus
```

### Database Migration
After deployment, run database migrations:

```bash
# In Render shell or locally with DATABASE_URL set
npx prisma migrate deploy
```

## 📈 Monitoring & Logs

- **Render Dashboard**: Monitor deployment logs, metrics, and status
- **Application Logs**: View real-time logs in Render dashboard
- **Database**: Monitor PostgreSQL performance in Render dashboard

## 🌐 Access Your Application

After successful deployment, your application will be available at:
```
https://ip-asset-platform.onrender.com
```

## ⚠️ Important Notes

1. **API Keys**: Never commit API keys to GitHub. Use environment variables
2. **Free Tier Limits**: Render free tier has limits on resources and uptime
3. **Database Backups**: Enable automated backups in PostgreSQL settings
4. **Cost Monitoring**: Monitor OpenAI API usage to avoid unexpected charges
5. **SSL Certificates**: Render automatically handles SSL certificates

## 🛠️ Troubleshooting

### Build Failures
- Check build logs in Render dashboard
- Ensure all dependencies are in package.json
- Verify Node.js version compatibility

### Runtime Errors
- Check environment variables are set correctly
- Verify API keys are valid
- Check database connection string

### API Errors
- Verify API keys have necessary permissions
- Check rate limits and quotas
- Review service-specific documentation

## 📞 Support

- Render Documentation: [docs.render.com](https://docs.render.com)
- OpenAI API: [platform.openai.com/docs](https://platform.openai.com/docs)
- Pinata Documentation: [docs.pinata.cloud](https://docs.pinata.cloud)

## 🔄 Updates & Maintenance

To update your deployed application:

```bash
# Make changes locally
git add .
git commit -m "Update features"
git push origin main

# Render will automatically redeploy
```

## 🎉 Success!

Your IP Asset Platform is now publicly accessible with cloud-based:
- ✅ OpenAI LLM integration for file appraisals
- ✅ Pinata IPFS integration for decentralized storage
- ✅ PostgreSQL database for persistent data
- ✅ Solana blockchain integration for provenance
- ✅ Global CDN via Render infrastructure