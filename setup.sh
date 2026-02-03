#!/bin/bash
# Quick setup script for kali-driver-mcp

set -e

echo "=== Kali Driver MCP Server - Quick Setup ==="
echo

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: UV is not installed"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install dependencies
echo "1. Installing dependencies..."
uv sync
echo "   ✓ Dependencies installed"
echo

# Check if config.yaml exists
if [ ! -f config.yaml ]; then
    echo "2. Creating config.yaml from template..."
    cp config.yaml.example config.yaml
    echo "   ✓ config.yaml created"
    echo
    echo "   ⚠️  IMPORTANT: Edit config.yaml with your VM details:"
    echo "      - vm.host: Your Kali VM IP address"
    echo "      - vm.key_file: Path to your SSH private key"
    echo "      - shared_folder.vm_path: VM mount point"
    echo "      - network.wireless_interface: Your wireless interface"
    echo
else
    echo "2. config.yaml already exists"
    echo "   ✓ Using existing configuration"
    echo
fi

# Test SSH connection
echo "3. Testing SSH connection (optional)..."
read -p "   Do you want to test SSH connection now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f config.yaml ]; then
        VM_HOST=$(grep "host:" config.yaml | awk '{print $2}' | tr -d '"')
        KEY_FILE=$(grep "key_file:" config.yaml | awk '{print $2}' | tr -d '"' | sed "s|~|$HOME|")

        if [ -n "$VM_HOST" ] && [ -n "$KEY_FILE" ]; then
            echo "   Testing connection to $VM_HOST..."
            ssh -i "$KEY_FILE" -o ConnectTimeout=5 root@"$VM_HOST" "echo 'SSH connection successful'" 2>&1
            if [ $? -eq 0 ]; then
                echo "   ✓ SSH connection successful"
            else
                echo "   ✗ SSH connection failed - please check your configuration"
            fi
        fi
    fi
fi
echo

echo "=== Setup Complete ==="
echo
echo "Next steps:"
echo "  1. Edit config.yaml if you haven't already"
echo "  2. Run the server: uv run python -m kali_driver_mcp.server"
echo "  3. Or test with client: uv run python test_client.py"
echo
echo "Documentation:"
echo "  - README.md: Full usage guide"
echo "  - CLAUDE.md: Development guide"
echo "  - TOOLS_REFERENCE.md: Detailed command reference"
echo
