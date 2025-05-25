#ifndef MDNS_DISCOVERY_H
#define MDNS_DISCOVERY_H

#include <ESPmDNS.h>
#include "../core/Logger.h"

struct BrokerInfo {
    String host;
    int port;
    bool found;
    
    BrokerInfo() : port(1883), found(false) {}
};

class MDNSDiscovery {
private:
    String service_name;
    BrokerInfo discovered_broker;
    unsigned long last_discovery_attempt;
    static const unsigned long DISCOVERY_TIMEOUT = 5000; // 5 Sekunden
    
public:
    MDNSDiscovery();
    
    bool init(const String& hostname);
    BrokerInfo discoverBroker(const String& service_name);
    bool isDiscoveryComplete() const { return discovered_broker.found; }
    
    const BrokerInfo& getBrokerInfo() const { return discovered_broker; }
    
private:
    bool searchForService(const String& service);
};

#endif // MDNS_DISCOVERY_H 