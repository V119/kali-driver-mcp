# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based MCP (Model Context Protocol) server for debugging network card (NIC) drivers in a Kali Linux virtual machine from the host machine. The project provides a bridge between the host development environment and the Kali VM, enabling LLM clients to interact with and debug kernel drivers through the standardized MCP interface.

## Core Functionality

The MCP server provides 9 tools for network driver development and debugging:

1. **kernel_info** - Retrieve kernel version and configuration
2. **file_ops** - List/browse files in VM (especially shared folder)
3. **code_sync** - Verify shared folder is mounted and accessible
4. **driver_compile** - Build drivers using make
5. **driver_load** - Load/unload kernel modules (insmod/rmmod)
6. **log_viewer** - Access kernel logs (dmesg) and system logs
7. **network_info** - Query network interface information
8. **network_monitor** - Start/stop monitor mode (airmon-ng)
9. **packet_capture** - Capture wireless packets (airodump-ng)

**Detailed command reference:** See [TOOLS_REFERENCE.md](TOOLS_REFERENCE.md) for complete command lists and parameters for each tool.

## Architecture Decisions

### Implementation Approach: Async High-Performance
- All SSH operations are asynchronous using `asyncssh`
- Supports concurrent execution of multiple operations
- SSH connection pooling for efficient resource management
- Non-blocking I/O for all VM interactions

### Authentication: Direct Root SSH
- MCP server connects to Kali VM as root user via SSH
- Uses SSH key-based authentication (recommended) or password
- No sudo required - all commands run with root privileges
- Simpler command execution (no sudo prefix needed)

### Code Synchronization: Shared Folder
- Driver source code resides in VM shared folder (VirtualBox/VMware/KVM)
- **Paths configured in config.yaml - NEVER hardcoded**
- No file transfer needed - direct access from both host and VM
- Host edits code, VM compiles and loads immediately

### Wireless Tools: Kali-Specific
- **Monitor mode:** `airmon-ng start/stop` (not standard tools)
- **Packet capture:** `airodump-ng` (not tcpdump for wireless)
- Designed for wireless driver development and testing

## Development Environment

**Package Manager:** UV (modern, fast Python package manager)

**Key Dependencies:**
- `mcp` - Official MCP SDK for Python
- `asyncssh` - Async SSH client library
- `pyyaml` - Configuration file parsing

**Commands:**
```bash
# Initialize project
uv init

# Add dependencies
uv add mcp asyncssh pyyaml

# Install and sync
uv sync

# Run server
uv run python -m kali_driver_mcp.server
```

## Project Structure

```
kali-driver-mcp/
├── pyproject.toml              # UV project configuration
├── uv.lock                     # UV lock file
├── config.yaml.example         # Configuration template
├── config.yaml                 # User config (gitignored)
├── CLAUDE.md                   # This file
├── TOOLS_REFERENCE.md          # Detailed command reference
├── src/
│   └── kali_driver_mcp/
│       ├── server.py           # MCP server entry point
│       ├── config.py           # Configuration loading/validation
│       ├── ssh_manager.py      # Async SSH connection pool
│       └── tools/              # MCP tool implementations
│           ├── kernel_info.py
│           ├── file_ops.py
│           ├── code_sync.py
│           ├── driver_compile.py
│           ├── driver_load.py
│           ├── log_viewer.py
│           ├── network_info.py
│           ├── network_monitor.py
│           └── packet_capture.py
└── tests/                      # Unit tests (optional)
```

## Configuration Management

**Critical:** All paths, credentials, and interface names MUST come from `config.yaml`. Never hardcode.

### Configuration File Structure

```yaml
vm:
  host: "192.168.56.101"           # VM IP address
  port: 22
  username: "root"
  auth_method: "key"               # "key" or "password"
  key_file: "~/.ssh/kali_vm"       # SSH private key path
  password: null

shared_folder:
  host_path: "/path/to/host/folder"   # Host machine path
  vm_path: "/mnt/kali-share/driver"   # VM mount point
  verify_mount: true

build:
  make_jobs: 4                     # Parallel make jobs (-j flag)
  clean_before_build: false

network:
  wireless_interface: "wlan0"      # Physical wireless interface
  monitor_interface: "wlan0mon"    # Monitor mode interface
  default_channel: 6
  kill_processes: true             # Kill interfering processes

capture:
  output_dir: "/tmp/captures"      # Capture file directory (in VM)
  default_duration: 60             # Seconds
  output_format: "pcap,csv"        # "pcap", "csv", or "pcap,csv"
  update_interval: 1
  band: "bg"                       # "a" (5GHz), "bg" (2.4GHz), "abg"

logging:
  max_lines: 1000
  default_source: "dmesg"
```

**Implementation:**
- Load config on server startup
- Validate all required fields
- Expand paths (`~` to home directory)
- Pass config object to all tool functions
- Provide `config.yaml.example` in repo (no real credentials)
- Add `config.yaml` to `.gitignore`

## Key Implementation Patterns

### SSH Connection Pool
```python
# Maintain pool of asyncssh connections
# Reuse connections across tool invocations
# Handle connection failures and reconnection
# Graceful shutdown on server exit

class SSHManager:
    async def get_connection(self) -> asyncssh.SSHClientConnection:
        # Return pooled connection
        pass

    async def execute(self, command: str) -> tuple[str, str, int]:
        # Execute command, return (stdout, stderr, exit_code)
        pass
```

### Tool Implementation Pattern
```python
# Each tool is an async function
async def kernel_info_tool(config: Config, ssh: SSHManager) -> dict:
    # Read config values
    # Execute commands via SSH
    # Parse and return structured results
    pass
```

### Configuration Access Pattern
```python
# All tools read from config, never hardcode
vm_path = config.shared_folder.vm_path
interface = config.network.wireless_interface
channel = config.network.default_channel

# Use in command construction
command = f"cd {vm_path} && make -j{config.build.make_jobs}"
```

## Critical Implementation Considerations

1. **Configuration-Driven:** Every path, interface name, credential from config.yaml
2. **Async Everywhere:** All SSH operations must be async (use asyncssh, not paramiko)
3. **Error Handling:** Catch SSH errors, command failures, parse stderr
4. **Command Escaping:** Prevent injection attacks (use shlex.quote or asyncssh escaping)
5. **Timeout Handling:** Set timeouts for long operations (compilation, packet capture)
6. **Connection Pooling:** Reuse SSH connections, don't create new connection per command
7. **Security:** Never commit config.yaml, SSH keys, or passwords to git

## VM Setup Requirements

Before running the MCP server:

1. **Kali VM running** and network accessible
2. **Root SSH enabled:**
   ```bash
   # In /etc/ssh/sshd_config
   PermitRootLogin yes  # or prohibit-password for key-only
   # Then: systemctl restart ssh
   ```
3. **SSH key authentication:**
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/kali_vm
   ssh-copy-id -i ~/.ssh/kali_vm.pub root@192.168.56.101
   ```
4. **Shared folder mounted** in VM:
   - Configure in VirtualBox/VMware/KVM settings
   - Verify: `mount | grep kali-share`
5. **Wireless tools installed:**
   ```bash
   apt update && apt install aircrack-ng
   ```
6. **Wireless adapter available** in VM (USB passthrough or network adapter)

## MCP Client Configuration

To use with Claude Desktop or other MCP clients:

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

## Development Workflow

1. **Create config:**
   ```bash
   cp config.yaml.example config.yaml
   # Edit config.yaml with your VM details
   ```

2. **Test SSH connection:**
   ```bash
   ssh -i ~/.ssh/kali_vm root@192.168.56.101
   ```

3. **Run MCP server:**
   ```bash
   uv run python -m kali_driver_mcp.server
   ```

4. **Test individual tools** (during development):
   ```python
   import asyncio
   from kali_driver_mcp.config import load_config
   from kali_driver_mcp.ssh_manager import SSHManager
   from kali_driver_mcp.tools.kernel_info import kernel_info_tool

   async def test():
       config = load_config()
       ssh = SSHManager(config)
       result = await kernel_info_tool(config, ssh)
       print(result)

   asyncio.run(test())
   ```

## Common Pitfalls to Avoid

- ❌ Hardcoding paths like `/mnt/kali-share/driver`
- ❌ Hardcoding interface names like `wlan0`
- ❌ Using synchronous SSH (paramiko) instead of asyncssh
- ❌ Creating new SSH connection for every command
- ❌ Forgetting to escape user input in shell commands
- ❌ Not handling command failures (non-zero exit codes)
- ❌ Committing config.yaml with real credentials
- ❌ Using tcpdump instead of airodump-ng for wireless capture

## Additional Documentation

- **TOOLS_REFERENCE.md** - Complete command reference for all 9 tools with examples
- **config.yaml.example** - Template configuration file
- **README.md** - User-facing documentation (if created)
