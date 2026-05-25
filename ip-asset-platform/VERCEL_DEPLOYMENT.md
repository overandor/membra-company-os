# 🚀 Vercel Deployment Guide - Inference & OverLLM Cloud Deployment

Deploy your IP Asset Platform with inference and OverLLM capabilities to Vercel with cloud storage backend.

## 📋 Prerequisites

- [ ] Vercel account (free at vercel.com)
- [ ] GitHub repository with this code
- [ ] OpenAI API key
- [ ] Pinata API keys (free)
- [ ] (Optional) Vercel Postgres database

## ⚡ 5-Minute Vercel Deployment

### 1. Push Code to GitHub

```bash
git add .
git commit -m "Ready for Vercel deployment"
git push origin main
```

### 2. Deploy to Vercel

#### Option A: Via Vercel Dashboard (Recommended)

1. Go to [vercel.com](https://vercel.com) and sign up/login
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. Vercel will auto-detect Next.js configuration
5. Configure project settings:
   - **Framework Preset**: Next.js
   - **Root Directory**: `./` (leave as is)
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `.next` (auto-detected)

6. Click **"Deploy"**

#### Option B: Via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy
vercel
```

### 3. Add Environment Variables

In your Vercel project dashboard:

1. Go to **Settings** → **Environment Variables**
2. Add the following variables:

#### Required Variables:

```bash
NEXTAUTH_SECRET=your-generated-secret
NEXTAUTH_URL=https://your-project.vercel.app
OPENAI_API_KEY=sk-your-openai-key
PINATA_API_KEY=your-pinata-key
PINATA_SECRET_KEY=your-pinata-secret
DATABASE_URL=your-database-connection-string
```

#### Generate NEXTAUTH_SECRET:

```bash
openssl rand -base64 32
```

#### Get Database URL:

**Option A: Vercel Postgres (Recommended)**
1. In Vercel dashboard, go to **Storage** → **Create Database**
2. Select **Postgres**
3. Choose **Hobby Plan (Free)**
4. Copy the `.env.local` connection string as `DATABASE_URL`

**Option B: External PostgreSQL**
Use your existing PostgreSQL connection string

### 4. Redeploy with Environment Variables

After adding environment variables:
1. Go to **Deployments** tab
2. Click **...** on latest deployment → **Redeploy**

## 🌐 Your Public URLs

After deployment, you'll get these public URLs:

- **Main Application**: `https://your-project.vercel.app`
- **Inference API**: `https://your-project.vercel.app/api/inference`
- **OverLLM API**: `https://your-project.vercel.app/api/overllm`
- **Deployment API**: `https://your-project.vercel.app/api/deploy`
- **IPFS API**: `https://your-project.vercel.app/api/ipfs`

## 🧪 Test Your Deployment

### Test Main App:
```bash
curl https://your-project.vercel.app/
```

### Test Inference API:
```bash
curl -X POST https://your-project.vercel.app/api/inference \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms",
    "model": "gpt-4",
    "maxTokens": 500
  }'
```

### Test OverLLM API:
```bash
curl -X POST https://your-project.vercel.app/api/overllm \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze the business potential of a SaaS product",
    "reasoningType": "chain-of-thought",
    "complexity": "medium",
    "outputFormat": "json"
  }'
```

### Test Deployment API:
```bash
# List available pipelines
curl https://your-project.vercel.app/api/deploy?action=list-pipelines

# Deploy a predefined pipeline
curl -X POST https://your-project.vercel.app/api/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "action": "deploy-predefined",
    "pipelineKey": "file-appraisal"
  }'
```

## 📦 Deploy Inference Artifacts to Cloud Storage

### Deploy Custom Artifact:

```bash
curl -X POST https://your-project.vercel.app/api/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "action": "deploy-artifact",
    "artifact": {
      "name": "my-custom-model",
      "type": "model",
      "content": {
        "architecture": "transformer",
        "parameters": "7b",
        "description": "Custom fine-tuned model"
      },
      "metadata": {
        "version": "1.0",
        "author": "your-name"
      }
    }
  }'
```

### Deploy All Predefined Pipelines:

```bash
curl -X POST https://your-project.vercel.app/api/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "action": "deploy-all-pipelines"
  }'
```

This will deploy:
- File Appraisal Pipeline
- Code Review Pipeline  
- Document Analysis Pipeline

Each pipeline gets stored on IPFS via Pinata with a gateway URL.

## 🔧 Vercel-Specific Features

### Edge Functions:
Your APIs are configured as Edge Functions for optimal performance:
- `src/app/api/inference/route.ts` - Edge runtime
- `src/app/api/overllm/route.ts` - Edge runtime
- `src/app/api/deploy/route.ts` - Edge runtime

### Automatic Scaling:
- Vercel automatically scales your functions
- Handles traffic spikes automatically
- Global edge network for low latency

### Zero-Configuration:
- Next.js auto-detected
- Build process optimized
- Static assets optimized

## 💰 Cost Estimate

### Vercel Free Tier:
- **Hobby Plan**: $0/month
- 100GB bandwidth per month
- 6,000 minutes of execution time
- Unlimited deployments

### API Costs:
- **OpenAI**: ~$0.01-0.10 per inference call
- **Pinata Free Tier**: $0/month (1GB storage)
- **Vercel Postgres**: $0/month (Hobby plan)

### Total Cost: $0-20/month depending on usage

## 🚦 Predefined Pipelines

Your deployment includes these ready-to-use inference pipelines:

### 1. File Appraisal Pipeline
- Content quality analysis
- Market demand evaluation
- Valuation calculation

### 2. Code Review Pipeline
- Security analysis
- Quality assessment
- Performance analysis

### 3. Document Analysis Pipeline
- Key point extraction
- Sentiment analysis
- Summarization

## 📊 Monitor Your Deployment

### Vercel Dashboard:
- **Deployments**: View deployment history
- **Logs**: Real-time function logs
- **Analytics**: Traffic and performance metrics
- **Settings**: Environment variables and configuration

### Vercel CLI Monitoring:
```bash
# View logs
vercel logs

# View deployments
vercel ls

# Inspect deployment
vercel inspect [deployment-url]
```

## 🔄 Updates and Redeployment

### Automatic Deployments:
- Push to main branch → Auto-deploys to production
- Push to other branches → Creates preview deployments

### Manual Redeployment:
```bash
vercel --prod
```

### Environment Variables:
- Changes require redeployment
- Use different values for production/preview/development

## 🛠️ Troubleshooting

### Build Failures:
- Check build logs in Vercel dashboard
- Ensure all dependencies are in package.json
- Verify Node.js version compatibility

### Runtime Errors:
- Check function logs for runtime errors
- Verify environment variables are set correctly
- Ensure API keys are valid

### API Timeout Errors:
- Increase `maxDuration` in `vercel.json`
- Optimize your inference logic
- Consider using Vercel's Pro plan for longer timeouts

### Database Connection Issues:
- Verify DATABASE_URL is correct
- Check database is accessible
- Ensure IP whitelisting is configured

## 🎯 Performance Optimization

### Edge Runtime:
- Your APIs use Edge runtime for global performance
- Functions run closer to users worldwide
- Reduced latency for inference calls

### Caching:
- Vercel automatically caches static assets
- Consider caching API responses when appropriate
- Use Vercel's KV store for persistent caching

### CDN:
- Global content delivery network
- Automatic asset optimization
- Image optimization built-in

## 🔒 Security Best Practices

### Environment Variables:
- Never commit API keys to GitHub
- Use Vercel's environment variables
- Rotate keys regularly

### API Security:
- Implement rate limiting
- Add authentication for sensitive endpoints
- Use HTTPS (automatic on Vercel)

### Database Security:
- Use connection pooling
- Implement proper access controls
- Regular backups

## 📈 Scaling Considerations

### When to Upgrade:
- Exceed free tier limits
- Need longer function timeouts
- Require dedicated infrastructure
- Need custom domains

### Vercel Pro Plan:
- $20/month
- 1TB bandwidth
- Unlimited executions
- Priority support
- Team collaboration

## 🎉 Success!

Your inference and OverLLM platform is now live on Vercel!

**Your Public URL**: `https://your-project.vercel.app`

**Key Features**:
- ✅ Edge-based inference API
- ✅ Advanced OverLLM orchestration
- ✅ Cloud artifact deployment
- ✅ IPFS integration via Pinata
- ✅ Global edge network
- ✅ Automatic scaling
- ✅ Zero-downtime deployments

**Next Steps**:
1. Set up custom domain (optional)
2. Configure monitoring alerts
3. Implement rate limiting
4. Add authentication
5. Review usage analytics