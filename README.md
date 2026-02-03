# Kali Driver MCP Server

MCP (Model Context Protocol) server for debugging network card (NIC) drivers in a Kali Linux virtual machine from the host machine.

## 🏗️ Architecture

**Important: This MCP server runs on the HOST machine, not in the Kali VM.**

```
┌─────────────────────────────────────┐
│      Host Machine (宿主机)           │
│                                     │
│  Claude Desktop / MCP Client        │
│         ↕                           │
│  Kali Driver MCP Server ←──────┐   │
│         │                      │   │
│         │ SSH                  │   │
│         ↓                      │   │
│  Shared Folder ←──────────────┘   │
└──────────────┬──────────────────────┘
               │
               │ Network + Shared Folder
               ↓
┌─────────────────────────────────────┐
│      Kali Linux VM (虚拟机)          │
│                                     │
│  SSH Server (root access)           │
│  airmon-ng, airodump-ng             │
│  Kernel driver build environment    │
│  Shared Folder Mount Point          │
└─────────────────────────────────────┘
```

**Why this architecture?**
- MCP clients (Claude Desktop) run on the host
- Code editors/IDEs work better on the host
- Driver compilation and loading happen in isolated VM
- Remote control via SSH provides flexibility

## 🚀 Quick Start

**想在其他项目中使用这个 MCP 服务？**

查看详细的客户端连接和使用指南：

- **[📖 MCP 客户端使用指南](MCP_CLIENT_GUIDE.md)** - 三种连接方式详解：
  - ✅ Claude Desktop 集成（最简单）
  - ✅ Python 客户端（自动化脚本）
  - ✅ 其他 MCP 工具集成

- **[💻 Python 客户端示例](mcp_client_example.py)** - 可直接运行的完整示例代码

**快速连接（Claude Desktop）**：

1. 安装并配置本服务（见下方 [Installation](#installation)）
2. 编辑 Claude Desktop 配置：
   ```json
   {
     "mcpServers": {
       "kali-driver": {
         "command": "uv",
         "args": ["run", "python", "-m", "kali_driver_mcp.server"],
         "cwd": "/path/to/kali-driver-mcp"
       }
     }
   }
   ```
3. 重启 Claude Desktop，即可使用！

详细步骤请参考 [MCP_CLIENT_GUIDE.md](MCP_CLIENT_GUIDE.md)。

## Features

This MCP server provides 9 tools for network driver development and debugging:

1. **kernel_info** - Retrieve kernel version and configuration
2. **file_ops** - List/browse files in VM shared folder
3. **code_sync** - Verify shared folder is mounted and accessible
4. **driver_compile** - Build drivers using make
5. **driver_load** - Load/unload kernel modules (insmod/rmmod)
6. **log_viewer** - Access kernel logs (dmesg) and system logs
7. **network_info** - Query network interface information
8. **network_monitor** - Start/stop wireless monitor mode (airmon-ng)
9. **packet_capture** - Capture wireless packets (airodump-ng)

## Architecture

- **Async/Await**: High-performance async SSH operations using asyncssh
- **Root SSH**: Direct root access to Kali VM (no sudo needed)
- **Shared Folder**: Code resides in VM shared folder (VirtualBox/VMware/KVM)
- **Kali Tools**: Uses airmon-ng and airodump-ng for wireless operations

## Prerequisites

### Kali VM Setup

1. **Kali VM running** with network access
2. **Root SSH enabled** in `/etc/ssh/sshd_config`:
   ```bash
   PermitRootLogin yes
   # or for key-only:
   PermitRootLogin prohibit-password
   ```
   Then restart SSH: `systemctl restart ssh`

3. **SSH key authentication** (recommended):
   ```bash
   # On host machine
   ssh-keygen -t ed25519 -f ~/.ssh/kali_vm
   ssh-copy-id -i ~/.ssh/kali_vm.pub root@<VM_IP>
   ```

4. **Shared folder mounted** in VM:
   - Configure in VirtualBox/VMware/KVM settings
   - Example VirtualBox: Shared Folders → Add folder → Auto-mount
   - Verify in VM: `mount | grep kali-share`

5. **Wireless tools installed**:
   ```bash
   apt update && apt install aircrack-ng
   ```

6. **Wireless adapter** available in VM (USB passthrough or virtual adapter)

### Host Machine Setup

1. **Python 3.10+** installed
2. **UV package manager** installed:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

## Installation

### Part 1: Setup on Host Machine (宿主机)

This is where the MCP server will run.

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd kali-driver-mcp
   ```

2. **Install UV (if not installed)**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

4. **Generate SSH key for VM access**:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/kali_vm
   ```

5. **Configure the server**:
   ```bash
   cp config.yaml.example config.yaml
   nano config.yaml  # Edit with your VM details
   ```

   Key settings to configure:
   ```yaml
   vm:
     host: "192.168.56.101"  # Your Kali VM IP
     key_file: "~/.ssh/kali_vm"

   shared_folder:
     host_path: "/Users/your-username/kali-share/driver"  # Host path
     vm_path: "/mnt/kali-share/driver"  # VM mount point

   network:
     wireless_interface: "wlan0"  # Your wireless interface in VM
   ```

### Part 2: Setup on Kali VM (虚拟机)

This is where drivers will be compiled and loaded.

1. **Enable root SSH access**:
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Add or modify: PermitRootLogin yes
   sudo systemctl restart ssh
   ```

2. **Copy SSH key from host**:
   ```bash
   # Run this FROM THE HOST MACHINE:
   ssh-copy-id -i ~/.ssh/kali_vm.pub root@<VM_IP>
   ```

3. **Install wireless tools**:
   ```bash
   sudo apt update
   sudo apt install aircrack-ng build-essential linux-headers-$(uname -r)
   ```

4. **Setup shared folder**:

   **For VirtualBox:**
   - In VirtualBox: Settings → Shared Folders → Add folder
   - Name: `kali-share`
   - Path: Your host folder (e.g., `/Users/username/kali-share`)
   - Auto-mount: ✓

   Then in VM:
   ```bash
   sudo mkdir -p /mnt/kali-share
   sudo mount -t vboxsf kali-share /mnt/kali-share
   # Make persistent (add to /etc/fstab):
   echo "kali-share /mnt/kali-share vboxsf defaults 0 0" | sudo tee -a /etc/fstab
   ```

   **For VMware:**
   ```bash
   sudo mkdir -p /mnt/kali-share
   sudo mount -t vmhgfs .host:/kali-share /mnt/kali-share
   ```

5. **Verify shared folder**:
   ```bash
   ls /mnt/kali-share
   mount | grep kali-share
   ```

6. **Create driver directory**:
   ```bash
   mkdir -p /mnt/kali-share/driver
   # Put your driver source code here
   ```

### Part 3: Test the Setup

**From host machine:**

1. **Test SSH connection**:
   ```bash
   ssh -i ~/.ssh/kali_vm root@<VM_IP>
   ```

2. **Test MCP server**:
   ```bash
   cd kali-driver-mcp
   uv run python test_client.py
   ```

3. **If successful, you should see**:
   ```
   === Available Tools ===
   kernel_info: Get kernel version...
   ...
   ```

## Usage

### Running the MCP Server

**Method 1: Direct execution**
```bash
uv run python -m kali_driver_mcp.server
```

**Method 2: Using the installed script**
```bash
uv run kali-driver-mcp
```

**Method 3: With custom config**
```bash
uv run python -m kali_driver_mcp.server --config /path/to/config.yaml
```

### Using with Claude Desktop

Add to Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "kali-driver": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "kali_driver_mcp.server"
      ],
      "cwd": "/path/to/kali-driver-mcp"
    }
  }
}
```

### Testing the Server

Run the included test client:

```bash
uv run python test_client.py
```

This will:
1. Connect to the MCP server
2. List available tools
3. Execute sample tool calls
4. Display results

## Example Workflow

1. **Check kernel version**:
   ```
   Tool: kernel_info
   Args: {"detail_level": "basic"}
   ```

2. **Verify shared folder**:
   ```
   Tool: code_sync
   Args: {}
   ```

3. **Compile driver**:
   ```
   Tool: driver_compile
   Args: {"clean": true, "verbose": true}
   ```

4. **Load driver**:
   ```
   Tool: driver_load
   Args: {
     "operation": "load",
     "module_name": "mydriver",
     "parameters": {"debug": "1"}
   }
   ```

5. **View kernel logs**:
   ```
   Tool: log_viewer
   Args: {
     "source": "dmesg",
     "lines": 50,
     "filter_pattern": "mydriver"
   }
   ```

6. **Start monitor mode**:
   ```
   Tool: network_monitor
   Args: {"operation": "start", "channel": 6}
   ```

7. **Capture packets**:
   ```
   Tool: packet_capture
   Args: {
     "channel": 6,
     "duration": 60,
     "output_prefix": "test_capture"
   }
   ```

8. **Stop monitor mode**:
   ```
   Tool: network_monitor
   Args: {"operation": "stop"}
   ```

## Configuration Reference

See `config.yaml.example` for a complete configuration template.

Key sections:
- **vm**: VM connection details (host, port, auth)
- **shared_folder**: Shared folder paths
- **build**: Compilation settings
- **network**: Wireless interface names and defaults
- **capture**: Packet capture settings
- **logging**: Log viewing defaults

## Development

### Project Structure

```
kali-driver-mcp/
├── pyproject.toml              # UV project configuration
├── config.yaml.example         # Configuration template
├── CLAUDE.md                   # Development guide
├── TOOLS_REFERENCE.md          # Detailed command reference
├── src/
│   └── kali_driver_mcp/
│       ├── server.py           # MCP server entry point
│       ├── config.py           # Configuration loading
│       ├── ssh_manager.py      # SSH connection pool
│       └── tools/              # Tool implementations
└── test_client.py              # Test client
```

### Adding New Tools

1. Create tool implementation in `src/kali_driver_mcp/tools/`
2. Import in `server.py`
3. Add tool definition in `list_tools()`
4. Add handler in `call_tool()`

## Troubleshooting

### SSH Connection Issues

```bash
# Test SSH connection manually
ssh -i ~/.ssh/kali_vm root@<VM_IP>

# Check SSH key permissions
chmod 600 ~/.ssh/kali_vm
```

### Shared Folder Not Mounted

```bash
# In VM, check mount
mount | grep kali-share

# VirtualBox: install Guest Additions
# VMware: install VMware Tools
```

### Monitor Mode Issues

```bash
# In VM, check if airmon-ng is installed
which airmon-ng

# Check wireless interface
iw dev

# Kill interfering processes manually
airmon-ng check kill
```

### Permission Errors

Ensure you're connecting as root:
```yaml
vm:
  username: "root"  # Must be root
```

## Security Notes

- **Never commit** `config.yaml` with real credentials
- Use SSH key authentication instead of passwords
- Only use this in development/testing environments
- The server disables SSH host key checking for convenience

## License

[Your License Here]

## Contributing

[Contributing Guidelines]
