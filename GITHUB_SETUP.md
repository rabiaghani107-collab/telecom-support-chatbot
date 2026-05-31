# 🚀 GitHub Setup Guide — Push TelcoBot to GitHub

This guide walks you through creating a GitHub repository and pushing the TelcoBot project to it.

---

## Step 1: Create a New GitHub Repository

1. Go to [https://github.com/new](https://github.com/new)
2. Fill in the details:
   - **Repository name:** `telecom-support-chatbot`
   - **Description:** `AI-powered customer support chatbot for TelcoMax using LangChain + LangGraph`
   - **Visibility:** Choose **Public** or **Private** (your preference)
   - ⚠️ **Do NOT** check "Add a README file" (we already have one)
   - ⚠️ **Do NOT** add `.gitignore` or license (we already have them)
3. Click **"Create repository"**

> After creating, GitHub will show you a page with setup instructions. You'll need the repository URL from that page (it looks like `https://github.com/YOUR_USERNAME/telecom-support-chatbot.git`).

---

## Step 2: Connect Your Local Repository to GitHub

Open a terminal, navigate to the project folder, and run these commands:

```bash
# Navigate to the project directory
cd /path/to/telecom_support_chatbot

# Add GitHub as the remote origin (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/telecom-support-chatbot.git

# Verify the remote was added
git remote -v
```

You should see output like:
```
origin  https://github.com/YOUR_USERNAME/telecom-support-chatbot.git (fetch)
origin  https://github.com/YOUR_USERNAME/telecom-support-chatbot.git (push)
```

---

## Step 3: Push to GitHub

```bash
# Push all commits to GitHub (first time — sets upstream branch)
git push -u origin main
```

GitHub will prompt you for authentication. You have two options:

### Option A: Personal Access Token (Recommended)
1. Go to [GitHub Settings → Developer Settings → Personal Access Tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Give it a descriptive name (e.g., `telecom-chatbot-push`)
4. Select scope: **`repo`** (Full control of private repositories)
5. Click **"Generate token"** and **copy it immediately** (you won't see it again)
6. When Git asks for your password, paste the **token** instead of your GitHub password

### Option B: GitHub CLI
```bash
# Install GitHub CLI (if not already installed)
# macOS:  brew install gh
# Ubuntu: sudo apt install gh
# Windows: winget install GitHub.cli

# Authenticate
gh auth login

# Then push
git push -u origin main
```

---

## Step 4: Verify the Push

1. Go to `https://github.com/YOUR_USERNAME/telecom-support-chatbot`
2. You should see all your files, including:
   - `README.md` (rendered beautifully with Mermaid diagrams)
   - `app.py`
   - `agents/`, `tools/`, `config/`, `data/`, `knowledge_base/`
   - `screenshots/` (with all 7 screenshots)
   - `demo_video.mp4`

---

## Quick Reference — All Commands in One Block

```bash
# ── Run these commands in order ──────────────────────────────

# 1. Navigate to project
cd /path/to/telecom_support_chatbot

# 2. Connect to GitHub (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/telecom-support-chatbot.git

# 3. Push to GitHub
git push -u origin main

# ── That's it! ──────────────────────────────────────────────
```

---

## Making Future Changes

After the initial push, use this workflow for any future updates:

```bash
# 1. Make your changes to files

# 2. Stage changes
git add -A

# 3. Commit with a message
git commit -m "Describe what you changed"

# 4. Push to GitHub
git push
```

---

## Troubleshooting

### "remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/telecom-support-chatbot.git
```

### "Authentication failed"
- Make sure you're using a **Personal Access Token**, not your GitHub password
- Ensure the token has the **`repo`** scope
- If using 2FA, you **must** use a token

### "src refspec main does not match any"
```bash
# Check your current branch name
git branch
# If it shows 'master' instead of 'main':
git branch -m master main
git push -u origin main
```

### "failed to push some refs"
```bash
# If GitHub has files you don't have locally (e.g., you checked "Add README"):
git pull origin main --allow-unrelated-histories
git push -u origin main
```
