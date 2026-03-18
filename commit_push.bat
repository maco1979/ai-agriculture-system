@echo off
cd /d d:\1.6\1.5
git add ai-agriculture-system/
git commit -m "fix(frontend): remove Supabase dependencies"
git push origin clean-deploy-v2
