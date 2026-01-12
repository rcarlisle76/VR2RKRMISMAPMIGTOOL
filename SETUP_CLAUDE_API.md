# Quick Setup: Claude API for Enhanced Mapping

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `sentence-transformers` (Phase 1: Local semantic matching)
- `anthropic` (Phase 2: Claude API)

## Step 2: Configure Your API Key

### Option A: Edit Config File (Recommended)

1. Run the app once to generate config file
2. Close the app
3. Edit: `C:\Users\%USERNAME%\.salesforce_migration_tool\config.json`

Add these settings:

```json
{
  "use_semantic_matching": true,
  "use_llm_mapping": true,
  "llm_provider": "claude",
  "llm_model": "claude-3-5-sonnet-20241022",
  "claude_api_key": "sk-ant-your-actual-api-key-here"
}
```

### Option B: Start with Phase 1 Only (No API Key Needed)

Default config enables semantic matching without Claude API:

```json
{
  "use_semantic_matching": true,
  "use_llm_mapping": false
}
```

This gives you ~90% accuracy with no API costs!

## Step 3: Get Your Claude API Key

1. Go to: https://console.anthropic.com/
2. Sign in with your account
3. Click **API Keys** in left menu
4. Click **Create Key**
5. Copy the key (starts with `sk-ant-`)
6. Paste into config.json

## Step 4: Test It

1. Launch the app: `python -m src.main`
2. Login to Salesforce
3. Select an object (e.g., Claim__c)
4. Go to "Map Fields" tab
5. Import a CSV file
6. Click "Auto Map"
7. Check logs for AI activity

### Expected Log Output

**With Semantic Matching Only:**
```
INFO - Initializing AI-enhanced mapping service (semantic: True, llm: False)
INFO - Loading semantic embedding model...
INFO - Semantic embedding model loaded successfully
INFO - AI-enhanced auto-mapping: 14 columns (semantic: true, llm: false)
INFO - Mapped: email_addr → Email__c (score: 0.92, method: semantic)
```

**With Claude API:**
```
INFO - Initializing AI-enhanced mapping service (semantic: True, llm: True)
INFO - Claude API client initialized
INFO - AI-enhanced auto-mapping: 14 columns (semantic: true, llm: true)
INFO - Using LLM for 2 difficult mappings
INFO - Mapped: amt → Amount__c (score: 0.95, method: llm)
```

## Troubleshooting

### "sentence-transformers not installed"

```bash
pip install sentence-transformers
```

### "anthropic not installed"

```bash
pip install anthropic
```

### "Authentication failed" (Claude API)

1. Check API key is correct (no extra spaces)
2. Verify billing is active at https://console.anthropic.com/
3. Test API key with curl:
```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

### First mapping is slow

First run downloads the embedding model (~500MB). Subsequent runs are fast.

Model downloads to: `C:\Users\%USERNAME%\.cache\torch\sentence_transformers\`

## Cost Monitoring

Check your Claude API usage:
- Dashboard: https://console.anthropic.com/
- Each mapping operation: ~$0.003 (less than 1 cent)
- 100 mappings: ~$0.30

## Disable AI Features

To go back to basic fuzzy matching:

```json
{
  "use_semantic_matching": false,
  "use_llm_mapping": false
}
```

## Support

- Logs: `C:\Users\%USERNAME%\.salesforce_migration_tool\logs\migration_tool.log`
- Full guide: See `AI_MAPPING_GUIDE.md`
