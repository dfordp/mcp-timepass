"""
Quick script to check if your API credentials are working
"""
import os
import asyncio
import httpx

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Using system environment variables only.")

# Get credentials
CALCOM_API_KEY = os.getenv("CALCOM_API_KEY")
CALENDLY_PAT = os.getenv("CALENDLY_PAT") 
CALCOM_ORG_ID = os.getenv("CALCOM_ORG_ID")

async def test_calcom():
    """Test Cal.com API credentials"""
    print("🔹 Testing Cal.com API...")
    
    if not CALCOM_API_KEY:
        print("❌ CALCOM_API_KEY not set")
        return False
    
    if not CALCOM_ORG_ID:
        print("❌ CALCOM_ORG_ID not set")
        return False
    
    async with httpx.AsyncClient() as client:
        try:
            # Test API key with organizations endpoint
            response = await client.get(
                "https://api.cal.com/v2/organizations",
                headers={
                    "Authorization": f"Bearer {CALCOM_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                orgs = response.json().get("data", [])
                print(f"✅ Cal.com API key is valid")
                print(f"📊 Found {len(orgs)} organization(s)")
                
                # Check if the specified org ID exists
                org_found = False
                for org in orgs:
                    if org.get("id") == CALCOM_ORG_ID:
                        org_found = True
                        print(f"✅ Organization ID '{CALCOM_ORG_ID}' found: {org.get('name', 'Unnamed')}")
                        break
                
                if not org_found:
                    print(f"❌ Organization ID '{CALCOM_ORG_ID}' not found in your organizations")
                    print("Available organizations:")
                    for org in orgs:
                        print(f"   - ID: {org.get('id')} | Name: {org.get('name', 'Unnamed')}")
                    return False
                
                # Test users endpoint for the organization
                users_response = await client.get(
                    f"https://api.cal.com/v2/organizations/{CALCOM_ORG_ID}/users",
                    headers={
                        "Authorization": f"Bearer {CALCOM_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )
                
                if users_response.status_code == 200:
                    users = users_response.json().get("data", [])
                    print(f"✅ Organization users endpoint working ({len(users)} users)")
                    return True
                else:
                    print(f"❌ Users endpoint failed: {users_response.status_code}")
                    return False
            else:
                print(f"❌ Cal.com API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Cal.com API request failed: {e}")
            return False

async def test_calendly():
    """Test Calendly API credentials"""
    print("\n🔹 Testing Calendly API...")
    
    if not CALENDLY_PAT:
        print("❌ CALENDLY_PAT not set")
        return False
    
    async with httpx.AsyncClient() as client:
        try:
            # Test PAT with user info endpoint
            response = await client.get(
                "https://api.calendly.com/users/me",
                headers={
                    "Authorization": f"Bearer {CALENDLY_PAT}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json().get("resource", {})
                print(f"✅ Calendly PAT is valid")
                print(f"👤 User: {user_data.get('name', 'Unknown')} ({user_data.get('email', 'No email')})")
                
                # Test organization memberships
                org_uri = user_data.get("current_organization")
                if org_uri:
                    memberships_response = await client.get(
                        f"https://api.calendly.com/organization_memberships?organization={org_uri}",
                        headers={
                            "Authorization": f"Bearer {CALENDLY_PAT}",
                            "Content-Type": "application/json"
                        },
                        timeout=10
                    )
                    
                    if memberships_response.status_code == 200:
                        memberships = memberships_response.json().get("collection", [])
                        print(f"✅ Organization memberships endpoint working ({len(memberships)} members)")
                        return True
                    else:
                        print(f"❌ Memberships endpoint failed: {memberships_response.status_code}")
                        return False
                else:
                    print("⚠️  No current organization found")
                    return True  # Still valid, just no org
            else:
                print(f"❌ Calendly API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Calendly API request failed: {e}")
            return False

async def main():
    print("🔍 Checking MCP Scheduling Server API Credentials")
    print("=" * 50)
    
    calcom_ok = await test_calcom()
    calendly_ok = await test_calendly()
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print(f"   Cal.com:  {'✅ Ready' if calcom_ok else '❌ Not Ready'}")
    print(f"   Calendly: {'✅ Ready' if calendly_ok else '❌ Not Ready'}")
    
    if calcom_ok or calendly_ok:
        print("\n🚀 You can start the MCP server now!")
        print("   Run: python scheduling_mcp_server.py")
    else:
        print("\n⚠️  Please configure your API credentials first.")
        print("   See: API_CREDENTIALS_GUIDE.md")

if __name__ == "__main__":
    asyncio.run(main())
