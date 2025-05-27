#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append('/app/backend')

from app.core.avahi_mdns import AvahiMDNSServer
from app.models.service import Service

async def test_avahi():
    print("=== Testing Avahi mDNS Integration ===")
    
    server = AvahiMDNSServer()
    print("1. Starting Avahi server...")
    await server.start()
    print(f"   Server running: {server._running}")
    
    if not server._running:
        print("❌ Avahi server failed to start")
        return
    
    print("2. Creating test service...")
    service = Service(
        name="Direct-Test-Service",
        type="test",
        host="192.168.178.124",
        port=8888,
        protocol="TCP",
        tags=["direct", "test"]
    )
    print(f"   Service: {service.name} on {service.host}:{service.port}")
    
    print("3. Registering service with Avahi...")
    result = await server.register_service(service)
    print(f"   Registration result: {result}")
    
    if result:
        print("4. Checking registered services...")
        registered = server.get_registered_services()
        print(f"   Registered services: {registered}")
        
        print("5. Waiting 5 seconds for mDNS propagation...")
        await asyncio.sleep(5)
        
        print("6. Unregistering service...")
        unregister_result = await server.unregister_service(service.service_id)
        print(f"   Unregistration result: {unregister_result}")
    else:
        print("❌ Service registration failed")
    
    print("7. Stopping Avahi server...")
    await server.stop()
    print("=== Test completed ===")

if __name__ == "__main__":
    asyncio.run(test_avahi()) 