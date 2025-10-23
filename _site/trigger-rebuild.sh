#!/usr/bin/env bash
# Force GitHub Pages rebuild by touching a file and pushing

# Add timestamp to trigger rebuild
echo "// GitHub Pages rebuild trigger: $(date)" > .rebuild-trigger

# Add and commit the trigger
git add .rebuild-trigger
git commit -m "Trigger GitHub Pages rebuild - $(date)"

echo "Pushing to trigger rebuild..."
git push origin main

echo "Waiting for rebuild..."
sleep 30

echo "Checking site..."
curl -s "https://ciso-in-a-box.github.io/ciso-in-a-box-site/" | grep -o "Beautiful Jekyll"