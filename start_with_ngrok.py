"""
Script to start MCP server with ngrok tunneling
"""
import asyncio
import subprocess
import time
import sys
from pyngrok import ngrok, conf
import threading

def start_ngrok_tunnel(port, auth_token=None):
    """Start ngrok tunnel for the given port"""
    try:
        # Set auth token if provided
        if auth_token:
            ngrok.set_auth_token(auth_token)
        
        # Start tunnel
        public_url = ngrok.connect(port)
        print(f"\n🌐 Ngrok tunnel started!")
        print(f"📍 Local URL: http://localhost:{port}")
        print(f"🔗 Public URL: {public_url}")
        print(f"📊 Ngrok dashboard: http://localhost:4040")
        print("=" * 50)
        
        return public_url
    except Exception as e:
        print(f"❌ Failed to start ngrok tunnel: {e}")
        print("💡 Make sure ngrok is installed and configured")
        return None

def run_mcp_server():
    """Run the MCP server"""
    try:
        # Import and run the scheduling server
        import scheduling_mcp_server
        asyncio.run(scheduling_mcp_server.main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

def main():
    """Main function to coordinate ngrok and MCP server"""
    print("🚀 Starting MCP Server with Ngrok Tunnel")
    print("=" * 50)
    
    # Configuration
    SERVER_PORT = 8086  # Port for scheduling MCP server
    NGROK_AUTH_TOKEN = None  # Set your ngrok auth token here if you have one
    
    # Start ngrok tunnel
    public_url = start_ngrok_tunnel(SERVER_PORT, NGROK_AUTH_TOKEN)
    
    if public_url:
        print(f"\n📋 Connection Details:")
        print(f"   Bearer Token: scheduling_mcp_token_123")
        print(f"   Endpoints:")
        print(f"     - {public_url}/mcp (MCP endpoint)")
        print(f"     - http://localhost:4040 (ngrok dashboard)")
        print("\n⚡ Starting MCP server...")
        print("   Press Ctrl+C to stop both server and tunnel")
        print("=" * 50)
    
    try:
        # Run the MCP server
        run_mcp_server()
    finally:
        # Clean up ngrok tunnel
        try:
            ngrok.disconnect(public_url)
            ngrok.kill()
            print("\n🔌 Ngrok tunnel closed")
        except:
            pass

if __name__ == "__main__":
    main()
