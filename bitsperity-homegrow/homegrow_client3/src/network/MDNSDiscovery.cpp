#include "MDNSDiscovery.h"

MDNSDiscovery::MDNSDiscovery() : 
    last_discovery_attempt(0) {
}

bool MDNSDiscovery::init(const String& hostname) {
    Logger::info("Initializing mDNS with hostname: " + hostname, "mDNS");
    
    if (!MDNS.begin(hostname.c_str())) {
        Logger::error("Failed to initialize mDNS", "mDNS");
        return false;
    }
    
    Logger::info("mDNS initialized successfully", "mDNS");
    return true;
}

BrokerInfo MDNSDiscovery::discoverBroker(const String& service_name) {
    this->service_name = service_name;
    discovered_broker = BrokerInfo(); // Reset
    last_discovery_attempt = millis();
    
    Logger::info("Starting mDNS discovery for service: " + service_name, "mDNS");
    
    if (searchForService(service_name)) {
        Logger::info("Broker discovered: " + discovered_broker.host + ":" + 
                    String(discovered_broker.port), "mDNS");
    } else {
        Logger::warn("No MQTT broker found via mDNS", "mDNS");
    }
    
    return discovered_broker;
}

bool MDNSDiscovery::searchForService(const String& service) {
    // Suche nach dem Service
    int n = MDNS.queryService(service.c_str(), "tcp");
    
    if (n == 0) {
        Logger::debug("No services found for: " + service, "mDNS");
        return false;
    }
    
    Logger::info("Found " + String(n) + " service(s)", "mDNS");
    
    // Ersten gefundenen Service verwenden
    for (int i = 0; i < n; i++) {
        String hostname = MDNS.hostname(i);
        IPAddress ip = MDNS.IP(i);
        int port = MDNS.port(i);
        
        Logger::debug("Service " + String(i) + ": " + hostname + 
                     " (" + ip.toString() + ":" + String(port) + ")", "mDNS");
        
        // Ersten gültigen Service verwenden
        if (port > 0) {
            discovered_broker.host = ip.toString();
            discovered_broker.port = port;
            discovered_broker.found = true;
            
            // Zusätzliche Informationen loggen
            Logger::info("Selected broker: " + hostname, "mDNS");
            Logger::info("IP: " + discovered_broker.host, "mDNS");
            Logger::info("Port: " + String(discovered_broker.port), "mDNS");
            
            return true;
        }
    }
    
    return false;
} 