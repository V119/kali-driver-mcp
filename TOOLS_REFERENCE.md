# MCP Tools Command Reference

This document provides detailed command references for all 9 MCP tools in the kali-driver-mcp server.

**Note:** `{placeholder}` syntax indicates values from `config.yaml`. Never hardcode these values.

---

## 1. Kernel Information Tool

**Purpose:** Get kernel version, configuration, and system information

**Key Commands:**
```bash
uname -r                          # Kernel version
uname -a                          # Full system info
cat /proc/version                 # Detailed version
cat /proc/config.gz | gunzip      # Kernel config
lsmod | wc -l                     # Loaded modules count
```

**Parameters:**
- `detail_level`: "basic" | "full"
- `config_filter`: Optional regex filter

---

## 2. File Operations Tool

**Purpose:** List and browse files in VM

**Key Commands:**
```bash
ls -lah {vm_path}                 # List with details
find {vm_path} -name "*.c"        # Find C files
stat {vm_path}/file.c             # File metadata
cat {vm_path}/file.c              # Read file
grep -r "pattern" {vm_path}       # Search contents
du -sh {vm_path}                  # Directory size
```

**Parameters:**
- `path`: Directory/file path (default: `config.shared_folder.vm_path`)
- `operation`: "list" | "read" | "stat" | "search"
- `filter`: File pattern (e.g., "*.c")
- `recursive`: Boolean

**Returns:** File entries with name, size, permissions, modified time

---

## 3. Code Synchronization Tool

**Purpose:** Verify shared folder is mounted and accessible

**Key Commands:**
```bash
mount | grep kali-share           # Check if mounted
test -d {vm_path} && echo "EXISTS" || echo "NOT_FOUND"
test -w {vm_path} && echo "WRITABLE" || echo "READ_ONLY"
ls -la {vm_path}                  # List contents
test -f {vm_path}/Makefile && echo "READY"
```

**Parameters:** None (reads from config)

**Returns:**
- `status`: "mounted" | "not_mounted"
- `path`: Mount path
- `writable`: Boolean
- `files_count`: Number of files
- `mount_type`: vboxsf/vmhgfs/virtiofs/9p

---

## 4. Driver Compilation Tool

**Purpose:** Compile kernel modules using make

**Key Commands:**
```bash
cd {vm_path} && make -j{make_jobs}              # Parallel build
cd {vm_path} && make clean                      # Clean
cd {vm_path} && make clean && make -j{make_jobs} # Clean + build
cd {vm_path} && make V=1                        # Verbose
cd {vm_path} && make mydriver.ko                # Specific target
cd {vm_path} && make modules_install            # Install to /lib/modules
```

**Parameters:**
- `target`: Optional make target (default: all)
- `clean`: Override config, force clean
- `verbose`: Verbose output

**Config Values:**
- `shared_folder.vm_path`: Source directory
- `build.make_jobs`: Parallel jobs (-j flag)
- `build.clean_before_build`: Auto clean

**Returns:**
- `exit_code`: 0 for success
- `output`: stdout
- `errors`: stderr
- `duration`: Build time (seconds)
- `artifacts`: List of .ko files created

---

## 5. Driver Loading Tool

**Purpose:** Load/unload kernel modules

**Key Commands:**
```bash
# Load module
insmod {vm_path}/mydriver.ko
insmod {vm_path}/mydriver.ko debug=1 param=value

# Unload
rmmod mydriver
rmmod -f mydriver                 # Force

# Check status
lsmod | grep mydriver
modinfo {vm_path}/mydriver.ko     # Module info
modinfo mydriver                  # Loaded module info

# Get parameters
cat /sys/module/mydriver/parameters/*
for param in /sys/module/mydriver/parameters/*; do
  echo "$(basename $param)=$(cat $param)"
done
```

**Parameters:**
- `operation`: "load" | "unload" | "reload" | "info" | "list"
- `module_name`: Module name (without .ko)
- `parameters`: Dict of params (key=value)
- `force`: Force unload

**Config Values:**
- `shared_folder.vm_path`: Module directory

**Returns:**
- `status`: "loaded" | "unloaded" | "error"
- `module_info`: version, description, dependencies, parameters

---

## 6. Log Viewing Tool

**Purpose:** Access kernel and system logs

**Key Commands:**
```bash
# Kernel messages
dmesg                             # All messages
dmesg | tail -n 100               # Last 100 lines
dmesg -T                          # With timestamps
dmesg -w                          # Follow (continuous)
dmesg --level=err                 # Filter by level
dmesg | grep mydriver             # Filter by pattern

# System logs
cat /var/log/syslog
tail -f /var/log/syslog
cat /var/log/kern.log

# Journal
journalctl -b                     # Current boot
journalctl -f                     # Follow
journalctl -k                     # Kernel only
journalctl --since "5 min ago"    # Time filter
```

**Parameters:**
- `source`: "dmesg" | "syslog" | "kern" | "journal"
- `lines`: Number of lines to retrieve
- `follow`: Boolean - continuous monitoring
- `filter`: Regex pattern
- `level`: "error" | "warn" | "info" | "debug"
- `since`: Time filter (e.g., "5 min ago")

**Config Values:**
- `logging.max_lines`: Default line limit
- `logging.default_source`: Default log source

**Returns:** Array of log entries with timestamp and level

---

## 7. Network Interface Info Tool

**Purpose:** Query network interface information

**Key Commands:**
```bash
# Interface status
ip link                           # List all
ip link show eth0                 # Specific interface
ip addr show eth0                 # With addresses
ip -s link show eth0              # With statistics

# Driver information
ethtool eth0                      # All driver info
ethtool -i eth0                   # Driver name/version
ethtool -k eth0                   # Features
ethtool -g eth0                   # Ring buffers

# Interface details
cat /sys/class/net/eth0/operstate # Status
cat /sys/class/net/eth0/address   # MAC address
cat /sys/class/net/eth0/mtu       # MTU
cat /sys/class/net/eth0/speed     # Speed

# Statistics
cat /sys/class/net/eth0/statistics/rx_packets
cat /sys/class/net/eth0/statistics/tx_packets
cat /sys/class/net/eth0/statistics/rx_bytes
cat /sys/class/net/eth0/statistics/tx_bytes

# Wireless info (if applicable)
iw dev eth0 info
iwconfig eth0
```

**Parameters:**
- `interface`: Interface name (e.g., "eth0", "wlan0", or "all")
- `detail_level`: "basic" | "detailed" | "statistics"
- `info_type`: "status" | "driver" | "settings" | "stats"

**Returns:**
- Interface name, status (up/down), MAC address
- IP addresses, driver name/version
- Statistics (packets, bytes, errors)
- MTU, speed, duplex

---

## 8. Network Monitoring Tool

**Purpose:** Start/stop wireless monitor mode

**Key Commands:**
```bash
# Check status
airmon-ng                         # List interfaces

# Check for interfering processes
airmon-ng check
airmon-ng check kill              # Kill interfering processes

# Start monitor mode
airmon-ng start {wireless_interface}
airmon-ng start {wireless_interface} {channel}

# Stop monitor mode
airmon-ng stop {monitor_interface}

# Manual mode change
iw dev {wireless_interface} set monitor none
ip link set {wireless_interface} down
ip link set {wireless_interface} up

# Check mode
iw dev {wireless_interface} info | grep type
iwconfig {wireless_interface} | grep Mode

# Set channel
iw dev {monitor_interface} set channel {channel}
```

**Parameters:**
- `operation`: "start" | "stop"
- `channel`: Optional channel override

**Config Values:**
- `network.wireless_interface`: Physical interface (e.g., "wlan0")
- `network.monitor_interface`: Monitor mode interface (e.g., "wlan0mon")
- `network.default_channel`: Default channel
- `network.kill_processes`: Kill interfering processes

**Returns:**
- `status`: "success" | "failed"
- `monitor_interface`: Monitor mode interface name
- `channel`: Current channel
- `mode`: "managed" | "monitor"
- `killed_processes`: List of stopped processes

---

## 9. Packet Capture Tool

**Purpose:** Capture wireless packets using airodump-ng

**Key Commands:**
```bash
# Basic capture
airodump-ng {monitor_interface}

# Capture on specific channel
airodump-ng -c {channel} {monitor_interface}

# Capture to file
airodump-ng -w {output_dir}/capture {monitor_interface}

# Capture with options
airodump-ng -c {channel} -w {output_dir}/capture --output-format pcap,csv {monitor_interface}

# Capture specific BSSID (AP)
airodump-ng -c {channel} --bssid AA:BB:CC:DD:EE:FF {monitor_interface}

# Band selection
airodump-ng --band bg {monitor_interface}   # 2.4GHz
airodump-ng --band a {monitor_interface}    # 5GHz
airodump-ng --band abg {monitor_interface}  # Both

# Time-limited capture
timeout {duration} airodump-ng -w {output_dir}/capture {monitor_interface}

# Background capture
airodump-ng -w {output_dir}/capture --background 1 {monitor_interface}

# Additional options
airodump-ng --manufacturer {monitor_interface}  # Show OUI
airodump-ng --beacons {monitor_interface}      # Beacons only
airodump-ng --update {interval} {monitor_interface} # Update interval
```

**Analyze Captured Files:**
```bash
# List capture files
ls -lh {output_dir}/capture*.cap
ls -lh {output_dir}/capture*.csv

# Parse CSV
cat {output_dir}/capture-01.csv

# Analyze packets
tcpdump -r {output_dir}/capture-01.cap
tcpdump -r {output_dir}/capture-01.cap | wc -l  # Count packets

# Convert format
tshark -r {output_dir}/capture-01.cap -w {output_dir}/output.pcap
```

**Parameters:**
- `channel`: Optional channel override
- `bssid`: Optional specific AP MAC address
- `duration`: Optional duration override
- `output_prefix`: Filename prefix (default: "capture")

**Config Values:**
- `network.monitor_interface`: Monitor mode interface
- `network.default_channel`: Default channel
- `capture.output_dir`: Output directory for files
- `capture.default_duration`: Default capture time (seconds)
- `capture.output_format`: "pcap" | "csv" | "pcap,csv"
- `capture.update_interval`: Screen update interval
- `capture.band`: "a" (5GHz) | "bg" (2.4GHz) | "abg" (both)

**Returns:**
- `capture_files`: Array of file paths (.cap, .csv)
- `statistics`:
  - `networks_found`: Number of APs discovered
  - `packets_captured`: Total packets
  - `duration`: Actual capture duration
  - `file_sizes`: Size of capture files
- `networks`: Array of discovered networks:
  - `bssid`: MAC address
  - `channel`: Channel number
  - `essid`: Network name
  - `encryption`: Encryption type
  - `signal`: Signal strength (PWR)

---

## Command Execution Notes

### Path Substitution
Always substitute placeholders from config:
- `{vm_path}` → `config.shared_folder.vm_path`
- `{wireless_interface}` → `config.network.wireless_interface`
- `{monitor_interface}` → `config.network.monitor_interface`
- `{channel}` → `config.network.default_channel`
- `{make_jobs}` → `config.build.make_jobs`
- `{output_dir}` → `config.capture.output_dir`
- `{duration}` → `config.capture.default_duration`

### Error Handling
Check command exit codes:
- `exit_code == 0`: Success
- `exit_code != 0`: Failure (parse stderr for error message)

Common errors:
- "Permission denied": Need root privileges
- "No such file": Path incorrect or shared folder not mounted
- "Device busy": Interface already in use
- "No such device": Interface doesn't exist

### Async Execution Pattern
```python
async def execute_command(ssh: SSHManager, command: str) -> tuple[str, str, int]:
    """Execute command via SSH, return (stdout, stderr, exit_code)"""
    result = await ssh.execute(command)
    return result.stdout, result.stderr, result.exit_code
```

### Timeout Values
Recommended timeouts for long-running operations:
- Driver compilation: 300s (5 minutes)
- Packet capture: Use `config.capture.default_duration` + 10s buffer
- Log following: No timeout (user-initiated stop)
- All other commands: 30s

---

## Quick Reference Table

| Tool | Primary Command | Config Values Used | Root Required |
|------|----------------|-------------------|---------------|
| kernel_info | `uname -r` | None | No |
| file_ops | `ls -lah {vm_path}` | `shared_folder.vm_path` | No |
| code_sync | `mount \| grep kali-share` | `shared_folder.vm_path` | No |
| driver_compile | `make -j{make_jobs}` | `shared_folder.vm_path`, `build.*` | No |
| driver_load | `insmod {vm_path}/driver.ko` | `shared_folder.vm_path` | Yes |
| log_viewer | `dmesg` | `logging.*` | Partial |
| network_info | `ip link` | None | No |
| network_monitor | `airmon-ng start {interface}` | `network.*` | Yes |
| packet_capture | `airodump-ng {monitor_interface}` | `network.*`, `capture.*` | Yes |
