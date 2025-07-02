# MCP Scheduling Link Discovery Server

A Model Context Protocol (MCP) server that provides scheduling link discovery across Cal.com and Calendly platforms.

## Features

- **Stateless Operation**: No persistent database, all operations are ephemeral per request
- **Multi-platform Support**: Works with both Cal.com and Calendly APIs
- **Bearer Token Authentication**: Secure access using bearer tokens
- **Name & Company Matching**: Intelligent filtering based on user names and company domains

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file or set environment variables:

```bash
# For Cal.com integration
CALCOM_API_KEY=your_calcom_api_key_here
CALCOM_ORG_ID=your_organization_id_here

# For Calendly integration  
CALENDLY_PAT=your_calendly_personal_access_token_here
```

### 3. Run the Server

```bash
python scheduling_mcp_server.py
```

The server will start on `http://0.0.0.0:8086`

## Available Tools

### 1. `search_scheduling_links`

Search for scheduling links on Cal.com or Calendly.

**Parameters:**
- `platform`: Either "calcom" or "calendly"
- `name`: Full name of the person to search for
- `company`: Company name to match against

**Example Usage:**
```json
{
  "platform": "calcom",
  "name": "Alice Smith", 
  "company": "Acme Corp"
}
```

**Returns:**
```json
{
  "message": "Found 1 scheduling link(s) for 'Alice Smith' at 'Acme Corp' on calcom",
  "results": [
    {
      "name": "Alice Smith",
      "email": "alice@acme.com",
      "company": "Acme Corp",
      "bookingLinks": [
        "https://cal.com/alice/30min-meeting",
        "https://cal.com/alice/consultation"
      ]
    }
  ]
}
```

### 2. `get_scheduling_config`

Check the configuration status of API credentials.

**Returns:**
```json
{
  "calcom": {
    "api_key_configured": true,
    "org_id_configured": true,
    "ready": true
  },
  "calendly": {
    "pat_configured": false,
    "ready": false
  },
  "instructions": {
    "calcom": "Set CALCOM_API_KEY and CALCOM_ORG_ID environment variables",
    "calendly": "Set CALENDLY_PAT environment variable"
  }
}
```

### 3. `validate`

Returns the validation number for MCP server verification.

## Authentication

The server uses bearer token authentication. Use the token: `scheduling_mcp_token_123`

Include in requests:
```
Authorization: Bearer scheduling_mcp_token_123
```

## API Credential Setup

### Cal.com
1. Go to your Cal.com organization settings
2. Generate an API key
3. Note your organization ID
4. Set `CALCOM_API_KEY` and `CALCOM_ORG_ID`

### Calendly
1. Go to your Calendly integrations settings
2. Generate a Personal Access Token
3. Set `CALENDLY_PAT`

## MCP Compliance

This server follows MCP principles:
- ✅ **Stateless**: No persistent database or state
- ✅ **Ephemeral**: All context is per-request only
- ✅ **Minimal**: Single-file implementation
- ✅ **Serverless Ready**: Can be deployed on serverless platforms
- ✅ **Error Handling**: Proper error responses with status codes

## Deployment

The server can be deployed on:
- Local development environments
- Cloud platforms (AWS Lambda, Google Cloud Functions)
- Container platforms (Docker, Kubernetes)
- Edge computing platforms

## Files

- `scheduling_mcp_server.py`: Main MCP server implementation
- `my_mcp_server.py`: Original MCP server with resume and fetch tools
- `requirements.txt`: Python dependencies
- `README.md`: This documentation

## Error Handling

The server provides detailed error messages for:
- Missing or invalid API credentials
- Invalid input parameters
- API rate limits or failures
- Network connectivity issues

## Development

To run in development mode with auto-reload:

```bash
# Install development dependencies
pip install fastmcp[dev]

# Run with auto-reload
python scheduling_mcp_server.py
```
