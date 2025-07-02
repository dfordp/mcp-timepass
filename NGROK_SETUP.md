# Ngrok Setup Guide for MCP Server

## Method 1: Using the Automated Script (Recommended)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the automated script:**
   ```bash
   python start_with_ngrok.py
   ```
   
   Or on Windows, double-click: `start_server.bat`

## Method 2: Manual Setup

### Step 1: Install ngrok

**Option A: Download from ngrok.com**
1. Go to https://ngrok.com/download
2. Download ngrok for Windows
3. Extract to a folder (e.g., `C:\ngrok\`)
4. Add to your PATH environment variable

**Option B: Using Package Manager**
```bash
# Using Chocolatey (Windows)
choco install ngrok

# Using Scoop (Windows)
scoop install ngrok
```

### Step 2: Set up ngrok (Optional but recommended)

1. Sign up at https://ngrok.com (free account)
2. Get your auth token from the dashboard
3. Configure ngrok:
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN_HERE
   ```

### Step 3: Start your MCP server

```bash
python scheduling_mcp_server.py
```

The server will start on `http://localhost:8086`

### Step 4: Start ngrok tunnel (in a new terminal)

```bash
ngrok http 8086
```

## What you'll see:

```
ngrok                                                                                                                                                                                                                              
                                                                                                                                                                                                                                   
Visit http://localhost:4040 to view requests/responses.                                                                                                                                                                          
                                                                                                                                                                                                                                   
Session Status                online                                                                                                                                                                                               
Account                       your-email@example.com (Plan: Free)                                                                                                                                                                 
Version                       3.4.0                                                                                                                                                                                                
Region                        United States (us)                                                                                                                                                                                   
Latency                       45ms                                                                                                                                                                                                 
Web Interface                 http://127.0.0.1:4040                                                                                                                                                                               
Forwarding                    https://abc123.ngrok.io -> http://localhost:8086                                                                                                                                                    
                                                                                                                                                                                                                                   
Connections                   ttl     opn     rt1     rt5     p50     p90                                                                                                                                                          
                              0       0       0.00    0.00    0.00    0.00       
```

## Using the Public URL

Your MCP server is now publicly accessible at the ngrok URL (e.g., `https://abc123.ngrok.io`)

### MCP Client Configuration:

```json
{
  "server_url": "https://abc123.ngrok.io",
  "auth_token": "scheduling_mcp_token_123"
}
```

### API Endpoints:

- **MCP Protocol**: `https://abc123.ngrok.io/mcp`
- **Health Check**: `https://abc123.ngrok.io/health` (if implemented)

## Testing the Connection

You can test your server using curl:

```bash
curl -X POST https://abc123.ngrok.io/mcp \
  -H "Authorization: Bearer scheduling_mcp_token_123" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

## Important Notes

1. **Free ngrok limitations:**
   - URLs change every time you restart ngrok
   - 40 connections/minute limit
   - Session timeout after 8 hours

2. **Security:**
   - Your server is publicly accessible
   - Make sure to keep your bearer token secure
   - Consider using environment variables for sensitive data

3. **Environment Variables:**
   ```bash
   # Set these before starting the server
   set CALCOM_API_KEY=your_api_key_here
   set CALCOM_ORG_ID=your_org_id_here  
   set CALENDLY_PAT=your_pat_here
   ```

## Troubleshooting

**"ngrok not found":**
- Make sure ngrok is installed and in your PATH
- Try using the full path to ngrok.exe

**"Connection refused":**
- Make sure your MCP server is running on port 8086
- Check if the port is already in use

**"Authentication failed":**
- Verify your bearer token: `scheduling_mcp_token_123`
- Check the Authorization header format

**"No API credentials":**
- Set your environment variables for Cal.com/Calendly APIs
- Use the `get_scheduling_config` tool to check status
