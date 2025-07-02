# How to Get Cal.com Organization ID and Calendly Personal Access Token

## 🔹 Cal.com Setup

### Step 1: Get Cal.com API Key

1. **Sign in to Cal.com**
   - Go to https://app.cal.com
   - Log in to your account

2. **Navigate to API Settings**
   - Click on your profile (top right)
   - Go to **Settings** → **Developer** → **API Keys**
   - Or directly visit: https://app.cal.com/settings/developer/api-keys

3. **Create New API Key**
   - Click **"Create New API Key"**
   - Give it a name (e.g., "MCP Scheduling Server")
   - Copy the generated API key (starts with `cal_`)
   - **Save this immediately** - you won't see it again!

### Step 2: Get Organization ID

**Method 1: From URL (Easiest)**
1. Go to your Cal.com dashboard
2. Click on **"Teams"** or **"Organization"** in the sidebar
3. Look at the URL - it will be something like:
   ```
   https://app.cal.com/teams/[ORG_ID]/members
   ```
   The `ORG_ID` part is your organization ID

**Method 2: From API Call**
```bash
# Replace YOUR_API_KEY with your actual API key
curl -X GET "https://api.cal.com/v2/organizations" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

**Method 3: From Account Settings**
1. Go to **Settings** → **Organizations**
2. Click on your organization
3. The ID will be visible in the organization details

---

## 🔹 Calendly Setup

### Step 1: Get Personal Access Token (PAT)

1. **Sign in to Calendly**
   - Go to https://calendly.com
   - Log in to your account

2. **Navigate to Integrations**
   - Click on your profile (top right)
   - Go to **Account Settings** → **Integrations**
   - Or directly visit: https://calendly.com/integrations

3. **Find API & Webhooks**
   - Look for **"API & Webhooks"** section
   - Click **"Generate new token"** or **"Create Personal Access Token"**

4. **Create Token**
   - Give it a name (e.g., "MCP Scheduling Server")
   - Select the required scopes (usually all are fine for development)
   - Click **"Create Token"**
   - **Copy the token immediately** - you won't see it again!

### Alternative Method: Direct API Access

1. Go directly to: https://calendly.com/integrations/api_webhooks
2. Click **"Create Personal Access Token"**
3. Follow the steps above

---

## 🔹 Setting Environment Variables

### Windows (PowerShell)
```powershell
# Set temporarily (for current session)
$env:CALCOM_API_KEY="cal_your_api_key_here"
$env:CALCOM_ORG_ID="your_org_id_here"
$env:CALENDLY_PAT="your_personal_access_token_here"

# Set permanently (recommended)
[Environment]::SetEnvironmentVariable("CALCOM_API_KEY", "cal_your_api_key_here", "User")
[Environment]::SetEnvironmentVariable("CALCOM_ORG_ID", "your_org_id_here", "User")
[Environment]::SetEnvironmentVariable("CALENDLY_PAT", "your_personal_access_token_here", "User")
```

### Windows (Command Prompt)
```cmd
# Set temporarily
set CALCOM_API_KEY=cal_your_api_key_here
set CALCOM_ORG_ID=your_org_id_here
set CALENDLY_PAT=your_personal_access_token_here

# Set permanently
setx CALCOM_API_KEY "cal_your_api_key_here"
setx CALCOM_ORG_ID "your_org_id_here"
setx CALENDLY_PAT "your_personal_access_token_here"
```

### Using .env File (Recommended for Development)

Create a `.env` file in your project root:

```bash
# Cal.com Configuration
CALCOM_API_KEY=cal_your_api_key_here
CALCOM_ORG_ID=your_org_id_here

# Calendly Configuration
CALENDLY_PAT=your_personal_access_token_here
```

Then install python-dotenv and load it:
```bash
pip install python-dotenv
```

---

## 🔹 Testing Your Configuration

### Test Cal.com API
```bash
curl -X GET "https://api.cal.com/v2/organizations/YOUR_ORG_ID/users" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

### Test Calendly API
```bash
curl -X GET "https://api.calendly.com/users/me" \
  -H "Authorization: Bearer YOUR_PAT" \
  -H "Content-Type: application/json"
```

### Test with Your MCP Server
```bash
python scheduling_mcp_server.py
```

Then call the config tool:
```bash
curl -X POST http://localhost:8086 \
  -H "Authorization: Bearer 696969" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_scheduling_config",
      "arguments": {}
    }
  }'
```

---

## 🔹 Important Security Notes

1. **Never commit API keys to version control**
2. **Use environment variables or .env files**
3. **Regularly rotate your tokens**
4. **Use minimal required permissions**
5. **Monitor API usage in your dashboards**

---

## 🔹 Troubleshooting

**"Invalid API Key" Error:**
- Make sure you copied the full key including any prefixes
- Check that the key hasn't expired
- Verify you're using the correct API endpoint

**"Organization not found" Error:**
- Double-check your organization ID
- Make sure your API key has access to that organization
- Try listing organizations first to find the correct ID

**"Invalid token" Error (Calendly):**
- Ensure the PAT is correctly copied
- Check token hasn't been revoked
- Verify you have the required permissions

**Environment Variables Not Loading:**
- Restart your terminal/IDE after setting permanent variables
- Check spelling of variable names
- Use `echo $CALCOM_API_KEY` (Linux/Mac) or `echo %CALCOM_API_KEY%` (Windows) to verify

---

## 🔹 Rate Limits

**Cal.com:**
- 100 requests per minute (free tier)
- 1000 requests per minute (paid plans)

**Calendly:**
- 100,000 requests per day
- 1000 requests per minute

Monitor your usage to avoid hitting limits during development.
