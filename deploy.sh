#!/bin/bash
echo "🚀 Deploying India News Expert..."
git add .
git commit -m "Deploy $(date)"
git push origin main
echo "✅ Check GitHub Actions tab!" 
