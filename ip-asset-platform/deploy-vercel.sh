#!/bin/bash

# Vercel Quick Deployment Script
# This script helps deploy the IP Asset Platform to Vercel

echo "🚀 Vercel Deployment Script for IP Asset Platform"
echo "================================================="

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed. Installing..."
    npm install -g vercel
fi

# Check if user is logged in
echo "📋 Checking Vercel login status..."
if ! vercel whoami &> /dev/null; then
    echo "🔐 Please login to Vercel:"
    vercel login
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the project
echo "🔨 Building project..."
npm run build

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
vercel

# Ask if this is production deployment
read -p "Is this a production deployment? (y/n): " is_prod

if [ "$is_prod" = "y" ]; then
    echo "🌐 Deploying to production..."
    vercel --prod
else
    echo "✅ Deployment complete! Preview URL provided above."
fi

echo ""
echo "🎉 Deployment Summary:"
echo "- Main Application: Available at the URL above"
echo "- Inference API: https://your-project.vercel.app/api/inference"
echo "- OverLLM API: https://your-project.vercel.app/api/overllm"
echo "- Deployment API: https://your-project.vercel.app/api/deploy"
echo ""
echo "📝 Next Steps:"
echo "1. Add environment variables in Vercel dashboard"
echo "2. Test the inference endpoints"
echo "3. Deploy inference artifacts using the deployment API"
echo ""
echo "📚 See VERCEL_DEPLOYMENT.md for detailed instructions"