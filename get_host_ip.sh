#!/bin/bash

# Script to get the host machine's IP address for mobile access

echo "Detecting your machine's IP address for mobile access..."
echo ""

# Get the primary network interface IP
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    IP=$(hostname -I | awk '{print $1}')
else
    # Windows or other
    IP=$(hostname -I 2>/dev/null || ipconfig | grep -E "IPv4" | head -1 | awk '{print $NF}')
fi

if [ -z "$IP" ]; then
    echo "Could not detect IP automatically. Please check your network settings."
    echo "You can find your IP address by running:"
    echo "  - On macOS: ifconfig | grep 'inet '"
    echo "  - On Linux: hostname -I"
    echo "  - On Windows: ipconfig"
else
    echo "Your machine's IP address is: $IP"
    echo ""
    echo "To use this IP for mobile uploads, you can either:"
    echo ""
    echo "1. Set it in your .env file:"
    echo "   HOST_IP=$IP"
    echo ""
    echo "2. Or run docker-compose with the environment variable:"
    echo "   HOST_IP=$IP docker-compose up"
    echo ""
    echo "3. Or export it before running docker-compose:"
    echo "   export HOST_IP=$IP"
    echo "   docker-compose up"
fi