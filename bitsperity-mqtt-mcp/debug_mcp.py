#!/usr/bin/env python3
"""
Debug Script für MCP Verbindung
Simuliert exakt was Cursor macht und zeigt detaillierte Logs
"""

import subprocess
import json
import time
import sys

def test_mcp_connection():
    """Test MCP connection exactly like Cursor does"""
    
    print("🔍 MCP Connection Debug Test")
    print("=" * 50)
    
    # Exakt der gleiche Command wie in Cursor mcp.json
    cmd = [
        "ssh", 
        "umbrel@umbrel.fritz.box",
        "sudo", "docker", "exec", "-i", 
        "bitsperity-mqtt-mcp",
        "python", "src/simple_mcp_server.py"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        # Start process
        print("📡 Starting MCP process...")
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0  # Unbuffered
        )
        
        print(f"✅ Process started (PID: {proc.pid})")
        
        # Test 1: Basic initialization
        print("\n🧪 Test 1: Process initialization")
        time.sleep(2)  # Wait for startup
        
        if proc.poll() is not None:
            print(f"❌ Process died early! Return code: {proc.poll()}")
            stderr = proc.stderr.read()
            print(f"STDERR: {stderr}")
            return False
        
        print("✅ Process is running")
        
        # Test 2: Send tools/list request (wie Cursor das macht)
        print("\n🧪 Test 2: tools/list request")
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        request_json = json.dumps(request) + "\n"
        print(f"📤 Sending: {request_json.strip()}")
        
        # Send request
        proc.stdin.write(request_json)
        proc.stdin.flush()
        
        # Wait for response
        print("⏳ Waiting for response...")
        
        response_line = None
        stderr_lines = []
        
        # Read with timeout
        import select
        
        ready, _, _ = select.select([proc.stdout, proc.stderr], [], [], 10.0)
        
        if proc.stdout in ready:
            response_line = proc.stdout.readline()
            print(f"📥 Raw response: {response_line.strip()}")
            
            try:
                response = json.loads(response_line.strip())
                print(f"✅ Valid JSON response")
                print(f"📋 Response keys: {list(response.keys())}")
                
                if "result" in response and "tools" in response["result"]:
                    tools = response["result"]["tools"]
                    print(f"✅ Found {len(tools)} tools")
                    for tool in tools[:3]:  # Show first 3
                        print(f"   - {tool['name']}: {tool['description'][:50]}...")
                else:
                    print(f"❌ No tools in response: {response}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response: {e}")
                print(f"   Raw: {response_line}")
        
        if proc.stderr in ready:
            stderr_line = proc.stderr.readline()
            if stderr_line:
                print(f"🚨 STDERR: {stderr_line.strip()}")
        
        # Test 3: Check if process is still alive
        print("\n🧪 Test 3: Process health")
        if proc.poll() is None:
            print("✅ Process still running")
        else:
            print(f"❌ Process died! Return code: {proc.poll()}")
        
        # Cleanup
        print("\n🧹 Cleanup")
        proc.terminate()
        proc.wait(timeout=5)
        print("✅ Process terminated")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_with_mongodb():
    """Compare with working MongoDB MCP"""
    
    print("\n" + "=" * 50)
    print("🔄 Comparing with MongoDB MCP")
    print("=" * 50)
    
    # MongoDB MCP Command
    cmd = [
        "ssh", 
        "umbrel@umbrel.fritz.box",
        "sudo", "docker", "exec", "-i", 
        "bitsperity-mongodb-mcp_mcp-server_1",
        "python", "src/simple_mcp_server.py"
    ]
    
    print(f"MongoDB Command: {' '.join(cmd)}")
    
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        request_json = json.dumps(request) + "\n"
        proc.stdin.write(request_json)
        proc.stdin.flush()
        
        response_line = proc.stdout.readline()
        print(f"📥 MongoDB response: {response_line.strip()[:100]}...")
        
        proc.terminate()
        proc.wait(timeout=5)
        
    except Exception as e:
        print(f"❌ MongoDB test error: {e}")

if __name__ == "__main__":
    success = test_mcp_connection()
    compare_with_mongodb()
    
    if success:
        print("\n✅ MCP connection test completed successfully")
        print("If this works but Cursor doesn't, the issue is in Cursor configuration")
    else:
        print("\n❌ MCP connection test failed")
        print("Fix the MCP server issues first") 