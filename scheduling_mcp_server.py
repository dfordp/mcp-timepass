from typing import Annotated, List, Dict, Any
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp import ErrorData, McpError
from mcp.server.auth.provider import AccessToken
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, TextContent
from pydantic import BaseModel, Field
import httpx
import asyncio
import os
import json
import re
from urllib.parse import quote

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, continue with system environment variables
    pass

TOKEN = "696969"
MY_NUMBER = "918287645453"  # Insert your number {91}{Your number}

# Environment variables for API keys
CALCOM_API_KEY = os.getenv("CALCOM_API_KEY")
CALENDLY_PAT = os.getenv("CALENDLY_PAT")
CALCOM_ORG_ID = os.getenv("CALCOM_ORG_ID")


class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None


class SimpleBearerAuthProvider(BearerAuthProvider):
    """
    A simple BearerAuthProvider that does not require any specific configuration.
    It allows any valid bearer token to access the MCP server.
    """

    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(
            public_key=k.public_key, jwks_uri=None, issuer=None, audience=None
        )
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token,
                client_id="unknown",
                scopes=[],
                expires_at=None,  # No expiration for simplicity
            )
        return None


class SchedulingAPI:
    """
    Handles API interactions with Cal.com and Calendly platforms
    """
    
    @staticmethod
    def extract_domain(company: str) -> str:
        """Extract domain from company name for email matching"""
        # Simple heuristic: convert "Acme Corp" -> "acme.com"
        domain = company.lower()
        domain = re.sub(r'\s+(corp|inc|llc|ltd|company|co)\.?$', '', domain, flags=re.IGNORECASE)
        domain = re.sub(r'\s+', '', domain)
        domain = re.sub(r'[^a-z0-9]', '', domain)
        return f"{domain}.com"
    
    @staticmethod
    def match_name(search_name: str, user_name: str, user_email: str) -> bool:
        """Check if the search name matches the user's name or email"""
        search_words = search_name.lower().split()
        user_name_lower = (user_name or "").lower()
        user_email_lower = (user_email or "").lower()
        
        return all(
            word in user_name_lower or word in user_email_lower
            for word in search_words
        )
    
    @staticmethod
    def match_company(search_company: str, user_email: str, user_company: str = None) -> bool:
        """Check if the search company matches the user's company or email domain"""
        expected_domain = SchedulingAPI.extract_domain(search_company)
        email_domain_match = expected_domain.lower() in (user_email or "").lower()
        
        if user_company:
            company_match = search_company.lower() in user_company.lower()
            return email_domain_match or company_match
        
        return email_domain_match

    @classmethod
    async def search_calcom(cls, name: str, company: str, org_id: str, api_key: str = None) -> List[Dict[str, Any]]:
        """Search Cal.com for users matching name and company"""
        used_api_key = api_key or CALCOM_API_KEY
        
        if not used_api_key:
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message="Cal.com API key not provided. Either set CALCOM_API_KEY environment variable or pass api_key parameter."
                )
            )
        
        if not org_id:
            raise McpError(
                ErrorData(
                    code=INVALID_PARAMS,
                    message="Organization ID is required for Cal.com API calls"
                )
            )

        async with httpx.AsyncClient() as client:
            try:
                # Get organization users
                users_response = await client.get(
                    f"https://api.cal.com/v2/organizations/{org_id}/users",
                    headers={
                        "Authorization": f"Bearer {used_api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=30
                )
                
                if users_response.status_code >= 400:
                    raise McpError(
                        ErrorData(
                            code=INTERNAL_ERROR,
                            message=f"Cal.com API error: {users_response.status_code} - {users_response.text}"
                        )
                    )

                users_data = users_response.json()
                users = users_data.get("data", [])

                # Filter users by name and company
                matched_users = []
                for user in users:
                    if (cls.match_name(name, user.get("name"), user.get("email")) and
                        cls.match_company(company, user.get("email"), user.get("metadata", {}).get("company"))):
                        matched_users.append(user)

                # Get event types for each matched user
                results = []
                for user in matched_users:
                    try:
                        event_types_response = await client.get(
                            f"https://api.cal.com/v2/event-types?userId={user.get('id')}",
                            headers={
                                "Authorization": f"Bearer {used_api_key}",
                                "Content-Type": "application/json"
                            },
                            timeout=30
                        )

                        if event_types_response.status_code == 200:
                            event_types_data = event_types_response.json()
                            event_types = event_types_data.get("data", [])
                            
                            # Generate booking links
                            booking_links = []
                            for event_type in event_types:
                                if event_type.get("slug") and not event_type.get("hidden"):
                                    link = f"https://cal.com/{user.get('username', 'user')}/{event_type['slug']}"
                                    booking_links.append(link)

                            results.append({
                                "name": user.get("name", "Unknown"),
                                "email": user.get("email", ""),
                                "company": user.get("metadata", {}).get("company", company),
                                "bookingLinks": booking_links
                            })
                    except Exception as e:
                        # Continue with other users if one fails
                        print(f"Warning: Failed to fetch event types for user {user.get('id')}: {e}")
                        continue

                return results

            except httpx.HTTPError as e:
                raise McpError(
                    ErrorData(
                        code=INTERNAL_ERROR,
                        message=f"Cal.com API request failed: {str(e)}"
                    )
                )

    @classmethod
    async def search_calendly(cls, name: str, company: str, pat: str = None) -> List[Dict[str, Any]]:
        """Search Calendly for users matching name and company"""
        used_pat = pat or CALENDLY_PAT
        
        if not used_pat:
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message="Calendly Personal Access Token not provided. Either set CALENDLY_PAT environment variable or pass pat parameter."
                )
            )

        async with httpx.AsyncClient() as client:
            try:
                # Get current user info
                user_response = await client.get(
                    "https://api.calendly.com/users/me",
                    headers={
                        "Authorization": f"Bearer {used_pat}",
                        "Content-Type": "application/json"
                    },
                    timeout=30
                )

                if user_response.status_code >= 400:
                    raise McpError(
                        ErrorData(
                            code=INTERNAL_ERROR,
                            message=f"Calendly API error: {user_response.status_code} - {user_response.text}"
                        )
                    )

                user_data = user_response.json()
                organization_uri = user_data["resource"]["current_organization"]

                # Get organization memberships
                memberships_response = await client.get(
                    f"https://api.calendly.com/organization_memberships?organization={quote(organization_uri)}",
                    headers={
                        "Authorization": f"Bearer {used_pat}",
                        "Content-Type": "application/json"
                    },
                    timeout=30
                )

                if memberships_response.status_code >= 400:
                    raise McpError(
                        ErrorData(
                            code=INTERNAL_ERROR,
                            message=f"Calendly memberships API error: {memberships_response.status_code}"
                        )
                    )

                memberships_data = memberships_response.json()
                memberships = memberships_data.get("collection", [])

                # Filter members by name and company
                matched_members = []
                for membership in memberships:
                    user = membership.get("user", {})
                    if (cls.match_name(name, user.get("name"), user.get("email")) and
                        cls.match_company(company, user.get("email"))):
                        matched_members.append(membership)

                # Get event types for each matched member
                results = []
                for membership in matched_members:
                    try:
                        user_uri = membership["user"]["uri"]
                        
                        event_types_response = await client.get(
                            f"https://api.calendly.com/event_types?user={quote(user_uri)}",
                            headers={
                                "Authorization": f"Bearer {used_pat}",
                                "Content-Type": "application/json"
                            },
                            timeout=30
                        )

                        if event_types_response.status_code == 200:
                            event_types_data = event_types_response.json()
                            event_types = event_types_data.get("collection", [])
                            
                            # Generate booking links
                            booking_links = []
                            for event_type in event_types:
                                if (event_type.get("scheduling_url") and 
                                    event_type.get("active", False)):
                                    booking_links.append(event_type["scheduling_url"])

                            results.append({
                                "name": membership["user"].get("name", "Unknown"),
                                "email": membership["user"].get("email", ""),
                                "company": company,  # Calendly doesn't store company info directly
                                "bookingLinks": booking_links
                            })
                    except Exception as e:
                        # Continue with other users if one fails
                        print(f"Warning: Failed to fetch event types for user {membership['user']['uri']}: {e}")
                        continue

                return results

            except httpx.HTTPError as e:
                raise McpError(
                    ErrorData(
                        code=INTERNAL_ERROR,
                        message=f"Calendly API request failed: {str(e)}"
                    )
                )


# Initialize FastMCP server
mcp = FastMCP(
    "Scheduling Link Discovery MCP Server",
    auth=SimpleBearerAuthProvider(TOKEN),
)


@mcp.tool
async def validate() -> str:
    """
    NOTE: This tool must be present in an MCP server used by puch.
    """
    return MY_NUMBER


ServerInfoToolDescription = RichToolDescription(
    description="Get server information including available endpoints and tools.",
    use_when="When you need to know what tools and endpoints are available on this MCP server.",
    side_effects="Returns static server information without making external API calls.",
)


@mcp.tool(description=ServerInfoToolDescription.model_dump_json())
async def get_server_info() -> list[TextContent]:
    """
    Get server information including available endpoints and tools.
    """
    server_info = {
        "name": "Scheduling Link Discovery MCP Server",
        "version": "1.0.0",
        "status": "running",
        "bearer_token": TOKEN,
        "available_tools": [
            "search_scheduling_links - Search for booking links on Cal.com or Calendly",
            "get_scheduling_config - Check API credential configuration status", 
            "get_organization_info - Get organization IDs for Cal.com or Calendly",
            "get_server_info - Get this server information",
            "validate - MCP server validation (returns phone number)"
        ],
        "usage_examples": {
            "search_calcom": {
                "platform": "calcom",
                "name": "John Doe",
                "company": "TechCorp", 
                "org_id": "your_cal_org_id",
                "api_key": "optional_cal_api_key"
            },
            "search_calendly": {
                "platform": "calendly",
                "name": "Jane Smith",
                "company": "AcmeCorp",
                "api_key": "optional_calendly_pat"
            }
        }
    }
    
    return [TextContent(
        type="text",
        text=json.dumps(server_info, indent=2)
    )]


SearchSchedulingToolDescription = RichToolDescription(
    description="Search for scheduling links across Cal.com and Calendly platforms for a specific person and company.",
    use_when="When you need to find booking links for someone at a specific company on Cal.com or Calendly platforms.",
    side_effects="Makes API calls to Cal.com or Calendly to search for users and their available booking links.",
)


@mcp.tool(description=SearchSchedulingToolDescription.model_dump_json())
async def search_scheduling_links(
    platform: Annotated[str, Field(description="Platform to search on: 'calcom' or 'calendly'")],
    name: Annotated[str, Field(description="Full name of the person to search for")],
    company: Annotated[str, Field(description="Company name to match against")],
    org_id: Annotated[str, Field(description="Organization ID (required for Cal.com)", default="")] = "",
    api_key: Annotated[str, Field(description="API key override (optional)", default="")] = "",
) -> list[TextContent]:
    """
    Search for scheduling links on Cal.com or Calendly for a specific person and company.
    
    For Cal.com: org_id is required to specify which organization to search.
    For Calendly: uses the authenticated user's organization automatically.
    """
    
    # Validate platform
    if platform not in ["calcom", "calendly"]:
        raise McpError(
            ErrorData(
                code=INVALID_PARAMS,
                message="Platform must be either 'calcom' or 'calendly'"
            )
        )
    
    # Validate inputs
    if not name or not name.strip():
        raise McpError(
            ErrorData(
                code=INVALID_PARAMS,
                message="Name is required and cannot be empty"
            )
        )
    
    if not company or not company.strip():
        raise McpError(
            ErrorData(
                code=INVALID_PARAMS,
                message="Company is required and cannot be empty"
            )
        )

    try:
        # Search based on platform
        if platform == "calcom":
            # For Cal.com, org_id is required
            if not org_id:
                raise McpError(
                    ErrorData(
                        code=INVALID_PARAMS,
                        message="org_id is required for Cal.com searches. You can find this in your Cal.com dashboard URL: /teams/[ORG_ID]/members"
                    )
                )
            results = await SchedulingAPI.search_calcom(name.strip(), company.strip(), org_id, api_key or None)
        else:  # calendly
            results = await SchedulingAPI.search_calendly(name.strip(), company.strip(), api_key or None)

        # Format results
        if not results:
            response = {
                "message": f"No scheduling links found for '{name}' at '{company}' on {platform}",
                "results": []
            }
        else:
            response = {
                "message": f"Found {len(results)} scheduling link(s) for '{name}' at '{company}' on {platform}",
                "results": results
            }

        return [TextContent(
            type="text",
            text=json.dumps(response, indent=2)
        )]

    except McpError:
        # Re-raise MCP errors as-is
        raise
    except Exception as e:
        raise McpError(
            ErrorData(
                code=INTERNAL_ERROR,
                message=f"Search failed: {str(e)}"
            )
        )


GetSchedulingConfigToolDescription = RichToolDescription(
    description="Get current configuration status for scheduling API credentials.",
    use_when="When you need to check if the required API credentials are configured for Cal.com or Calendly.",
    side_effects="Returns the configuration status without exposing actual credential values.",
)


@mcp.tool(description=GetSchedulingConfigToolDescription.model_dump_json())
async def get_scheduling_config() -> list[TextContent]:
    """
    Get the current configuration status for scheduling API credentials.
    
    Returns information about which credentials are configured without exposing actual values.
    """
    
    config_status = {
        "calcom": {
            "api_key_configured": bool(CALCOM_API_KEY),
            "org_id_configured": bool(CALCOM_ORG_ID),
            "ready": bool(CALCOM_API_KEY and CALCOM_ORG_ID)
        },
        "calendly": {
            "pat_configured": bool(CALENDLY_PAT),
            "ready": bool(CALENDLY_PAT)
        },
        "instructions": {
            "calcom": "Set CALCOM_API_KEY and CALCOM_ORG_ID environment variables OR provide them as parameters",
            "calendly": "Set CALENDLY_PAT environment variable OR provide it as a parameter"
        }
    }
    
    return [TextContent(
        type="text",
        text=json.dumps(config_status, indent=2)
    )]


GetOrgInfoToolDescription = RichToolDescription(
    description="Get organization information for the authenticated user to find organization IDs.",
    use_when="When user needs to find their Cal.com organization ID or Calendly organization details for subsequent searches.",
    side_effects="Makes API calls to retrieve organization information that can be used for scheduling searches.",
)


@mcp.tool(description=GetOrgInfoToolDescription.model_dump_json())
async def get_organization_info(
    platform: Annotated[str, Field(description="Platform: 'calcom' or 'calendly'")],
    api_key: Annotated[str, Field(description="API key or PAT (optional if set in environment)", default="")] = "",
) -> list[TextContent]:
    """
    Get organization information for the authenticated user.
    This helps users find their organization ID for subsequent searches.
    """
    
    if platform not in ["calcom", "calendly"]:
        raise McpError(
            ErrorData(
                code=INVALID_PARAMS, 
                message="Platform must be 'calcom' or 'calendly'"
            )
        )
    
    try:
        if platform == "calcom":
            used_api_key = api_key or CALCOM_API_KEY
            if not used_api_key:
                raise McpError(
                    ErrorData(
                        code=INTERNAL_ERROR,
                        message="Cal.com API key required"
                    )
                )
            
            async with httpx.AsyncClient() as client:
                # Get organizations
                response = await client.get(
                    "https://api.cal.com/v2/organizations",
                    headers={
                        "Authorization": f"Bearer {used_api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=30
                )
                
                if response.status_code >= 400:
                    raise McpError(
                        ErrorData(
                            code=INTERNAL_ERROR,
                            message=f"Cal.com API error: {response.status_code} - {response.text}"
                        )
                    )
                
                data = response.json()
                organizations = data.get("data", [])
                
                org_info = {
                    "platform": "calcom",
                    "organizations": []
                }
                
                for org in organizations:
                    org_info["organizations"].append({
                        "id": org.get("id"),
                        "name": org.get("name"),
                        "slug": org.get("slug"),
                        "description": f"Use org_id='{org.get('id')}' for searches in this organization"
                    })
                
        else:  # calendly
            used_pat = api_key or CALENDLY_PAT
            if not used_pat:
                raise McpError(
                    ErrorData(
                        code=INTERNAL_ERROR,
                        message="Calendly PAT required"
                    )
                )
            
            async with httpx.AsyncClient() as client:
                # Get user info
                user_response = await client.get(
                    "https://api.calendly.com/users/me",
                    headers={
                        "Authorization": f"Bearer {used_pat}",
                        "Content-Type": "application/json"
                    },
                    timeout=30
                )
                
                if user_response.status_code >= 400:
                    raise McpError(
                        ErrorData(
                            code=INTERNAL_ERROR,
                            message=f"Calendly API error: {user_response.status_code} - {user_response.text}"
                        )
                    )
                
                user_data = user_response.json()
                resource = user_data.get("resource", {})
                
                org_info = {
                    "platform": "calendly",
                    "user_name": resource.get("name"),
                    "user_email": resource.get("email"),
                    "organization_uri": resource.get("current_organization"),
                    "description": "Calendly searches use your authenticated organization automatically - no org_id needed"
                }
        
        return [TextContent(
            type="text",
            text=f"Organization information for {platform}:\n\n" + 
                 json.dumps(org_info, indent=2)
        )]
        
    except Exception as e:
        if isinstance(e, McpError):
            raise e
        raise McpError(
            ErrorData(
                code=INTERNAL_ERROR,
                message=f"Error getting organization info: {str(e)}"
            )
        )


async def main():
    """
    Main function to run the MCP server
    """
    print("🚀 Starting Scheduling Link Discovery MCP Server")
    print(f"📍 Server will be available at: http://0.0.0.0:8086")
    print(f"🔑 Bearer Token: {TOKEN}")
    print("📋 MCP Protocol Endpoint:")
    print("   - POST /sse      - MCP protocol endpoint (Server-Sent Events)")
    print("🛠️  Available MCP tools:")
    print("   - search_scheduling_links  - Search Cal.com/Calendly for booking links")
    print("   - get_scheduling_config    - Check API credential status") 
    print("   - get_organization_info    - Get organization IDs")
    print("   - get_server_info          - Get server information")
    print("   - validate                 - MCP validation tool")
    print("💡 Note: Access via MCP client or curl with Bearer token")
    print("=" * 60)
    
    await mcp.run_async(
        "streamable-http",
        host="0.0.0.0",
        port=8086,  # Different port from the original server
    )


if __name__ == "__main__":
    asyncio.run(main())
