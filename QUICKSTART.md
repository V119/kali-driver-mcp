# Quick Start Guide

This guide will help you get the Kali Driver MCP Server up and running in 5 minutes.

## ⚠️ Important: Where to Deploy

**The MCP server runs on your HOST machine (宿主机), NOT in the Kali VM!**

```
Your Computer (Host) ← You install and run the MCP server here
      ↓ SSH
Kali Linux VM ← Server connects to this via SSH
```

## Prerequisites Checklist

- [ ] **Host machine:** Python 3.10+ installed
- [ ] **Host machine:** UV package manager installed
- [ ] **Kali VM:** Running and accessible via network
- [ ] **Kali VM:** SSH server enabled
- [ ] Network connection between host and VM

## Step 1: Install UV (if not installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Step 2: Configure Kali VM

In your Kali VM, run these commands:

```bash
# 1. Enable root SSH login
sudo sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# 2. Install wireless tools
sudo apt update && sudo apt install aircrack-ng

# 3. Check your VM's IP address
ip addr show

# 4. Verify shared folder is mounted (if using VirtualBox/VMware)
mount | grep -i vbox  # For VirtualBox
mount | grep -i vmhgfs  # For VMware
```

## Step 3: Setup SSH from Host

On your host machine:

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -f ~/.ssh/kali_vm

# Copy key to VM (replace VM_IP with your VM's IP)
ssh-copy-id -i ~/.ssh/kali_vm.pub root@VM_IP

# Test connection
ssh -i ~/.ssh/kali_vm root@VM_IP
```

## Step 4: Configure the MCP Server

```bash
# Clone/navigate to project directory
cd kali-driver-mcp

# Run setup script
./setup.sh

# OR manually:
# 1. Install dependencies
uv sync

# 2. Create config file
cp config.yaml.example config.yaml

# 3. Edit config.yaml
nano config.yaml  # or your favorite editor
```

**Important config values to change:**
```yaml
vm:
  host: "192.168.56.101"  # Your VM IP
  key_file: "~/.ssh/kali_vm"  # Your SSH key path

shared_folder:
  vm_path: "/mnt/kali-share/driver"  # Your VM mount point

network:
  wireless_interface: "wlan0"  # Your wireless interface name
```

## Step 5: Test the Server

Run the test client:

```bash
uv run python test_client.py
```

Expected output:
```
=== Available Tools ===

kernel_info:
  Description: Get kernel version and configuration information from Kali VM
...

Running example tool calls...

1. Getting kernel information...
Result: {
  "version": "6.x.x-kali",
  ...
}
```

## Step 6: Use with Claude Desktop

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "kali-driver": {
      "command": "uv",
      "args": ["run", "python", "-m", "kali_driver_mcp.server"],
      "cwd": "/full/path/to/kali-driver-mcp"
    }
  }
}
```

Restart Claude Desktop, and you should see the Kali Driver tools available!

## Common Issues

### Issue: "Connection refused"

**Solution:** Check VM is running and IP is correct:
```bash
ping VM_IP
ssh -i ~/.ssh/kali_vm root@VM_IP
```

### Issue: "Shared folder not mounted"

**Solution:** Check VirtualBox/VMware shared folder settings and mount in VM:
```bash
# VirtualBox (if not auto-mounted)
sudo mkdir -p /mnt/kali-share
sudo mount -t vboxsf kali-share /mnt/kali-share

# VMware
sudo mkdir -p /mnt/hgfs/kali-share
sudo mount -t vmhgfs .host:/kali-share /mnt/hgfs/kali-share
```

### Issue: "airmon-ng: command not found"

**Solution:** Install aircrack-ng in VM:
```bash
sudo apt update && sudo apt install aircrack-ng
```

### Issue: "Permission denied (publickey)"

**Solution:** Check SSH key permissions and configuration:
```bash
chmod 600 ~/.ssh/kali_vm
ssh-copy-id -i ~/.ssh/kali_vm.pub root@VM_IP
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Try examples: `uv run python examples.py`
- Check [TOOLS_REFERENCE.md](TOOLS_REFERENCE.md) for detailed command reference
- Read [CLAUDE.md](CLAUDE.md) for development guide

## Getting Help

If you encounter issues:
1. Check the logs (stderr output from server)
2. Verify SSH connection manually
3. Check VM shared folder is accessible
4. Ensure wireless adapter is available in VM
