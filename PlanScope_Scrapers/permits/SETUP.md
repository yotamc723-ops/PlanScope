# Setup Instructions

## Environment Variables

1. **Create a `.env` file** in this directory (`PlanScope_Scrapers/permits/`)

2. **Copy the template:**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` and add your OpenAI API key:**
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

4. **Get your API key from:**
   - Visit: https://platform.openai.com/api-keys
   - Sign in or create an account
   - Create a new API key
   - Copy and paste it into your `.env` file

## Important Notes

- **Never commit `.env` to git** - it contains your secret API key
- The `.env.example` file is safe to commit (it only has a placeholder)
- Make sure `.env` is in your `.gitignore` file

## Verify Setup

After creating `.env`, you can verify it works by running:
```bash
python3 analyze_permits.py
```

If the API key is missing or invalid, you'll see an error message with instructions.

