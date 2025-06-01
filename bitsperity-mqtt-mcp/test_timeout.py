#!/usr/bin/env python3
import subprocess
import json
import select

print("Testing MQTT MCP response timing...")

# Test MQTT MCP
cmd = ['ssh', 'umbrel@umbrel.fritz.box', 'sudo', 'docker', 'exec', '-i', 'bitsperity-mqtt-mcp', 'python', 'src/simple_mcp_server.py']
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

request = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list', 'params': {}}) + '\n'
print(f"Sending: {request.strip()}")

proc.stdin.write(request)
proc.stdin.flush()

print('Request sent, waiting for response...')

# Try to read response with timeout
ready, _, _ = select.select([proc.stdout], [], [], 8.0)

if ready:
    response = proc.stdout.readline()
    print(f'✅ Response received: {response[:200]}...')
else:
    print('❌ No response after 8 seconds!')
    # Check if process is still alive
    if proc.poll() is None:
        print('Process still running')
        # Try to read stderr
        stderr_ready, _, _ = select.select([proc.stderr], [], [], 1.0)
        if stderr_ready:
            stderr = proc.stderr.readline()
            print(f'STDERR: {stderr}')
    else:
        print(f'Process died: {proc.poll()}')

proc.terminate()
proc.wait(timeout=2) 