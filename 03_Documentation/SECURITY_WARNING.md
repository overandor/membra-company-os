# SECURITY WARNING — SECRETS EXPOSED IN CODEBASE

The following credentials are present in plaintext in this repository:

## File: `mac_compute_node/.env`

- `GROQ_API_KEY=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`
- `GATE_API_KEY=57897b69c76df6aa01a1a25b8d9c6bc8`
- `GATE_API_SECRET=ed43f2696c3767685e8470c4ba98ea0f7ea85e9adeb9c3d098182889756d79d9`
- `GITHUB_TOKEN=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`

## What to do RIGHT NOW

1. **Revoke all tokens immediately:**
   - Groq: https://console.groq.com/keys → Delete `gsk_h0VD...`
   - Gate.io: https://www.gate.io/myaccount/api_keys → Delete the API key
   - GitHub: https://github.com/settings/tokens → Delete `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`

2. **Regenerate new keys** and store them OUTSIDE the repo (e.g., macOS Keychain):
   ```bash
   security add-generic-password -s "membra_groq" -a "alep" -w "NEW_KEY_HERE"
   ```

3. **Never commit `.env`** to git:
   ```bash
   echo ".env" >> .gitignore
   echo "**/.env" >> .gitignore
   echo "**/wallets/*.json" >> .gitignore
   git rm --cached mac_compute_node/.env
   ```

4. **Check git history** for leaked secrets:
   ```bash
   git log --all --full-history -- mac_compute_node/.env
   # If pushed anywhere, rotate immediately regardless
   ```

## Also check these files

- `mac_compute_node/05_Config_Files/.env` (also has keys)
- Any `*.json` in `~/.mac_compute_node/wallets/`
- `real_chain.py` may have hardcoded fallbacks

## Bottom line

If this repo has been pushed to GitHub, cloned to another machine, or shared in any way, **these keys are compromised**. Rotate them now.
