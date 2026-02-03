# Sudo and Privilege Escalation Guide

This document explains the different ways to handle root privileges in Kali Driver MCP Server.

## Three Privilege Escalation Methods

The MCP server supports three methods for obtaining root privileges:

### Method 1: Direct Root SSH (Default - Recommended)

**Configuration:**
```yaml
vm:
  username: "root"
  auth_method: "key"
  key_file: "~/.ssh/kali_vm"
  use_sudo: false  # Not needed
```

**VM Setup:**
```bash
# In /etc/ssh/sshd_config:
PermitRootLogin yes
# Or for key-only:
PermitRootLogin prohibit-password

sudo systemctl restart ssh
```

**Pros:**
- Simplest configuration
- No sudo password needed
- Direct command execution

**Cons:**
- Requires enabling root SSH (security consideration)
- Not recommended for production

**Best for:** Development and testing environments

---

### Method 2: Sudo Su Root (New!)

**Configuration:**
```yaml
vm:
  username: "kali"          # Regular user
  auth_method: "key"
  key_file: "~/.ssh/kali_vm"
  use_sudo: true            # Enable sudo
  sudo_method: "su"         # Use sudo su root
  sudo_password: null       # Or your sudo password
```

**VM Setup:**

**Option A: NOPASSWD (Recommended)**
```bash
# Add to /etc/sudoers or create /etc/sudoers.d/kali
kali ALL=(ALL) NOPASSWD: /bin/su
```

**Option B: With Password**
```yaml
vm:
  sudo_password: "your-sudo-password"
```

**How it works:**
- Wraps every root command with `sudo su root -c "command"`
- With NOPASSWD: `sudo su root -c "insmod mydriver.ko"`
- With password: `echo "password" | sudo -S su root -c "insmod mydriver.ko"`

**Pros:**
- Don't need to enable root SSH
- Single sudo escalation per command
- More secure than root SSH

**Cons:**
- Slightly more complex
- Requires sudo configuration
- May need password in config (security risk)

**Best for:** When root SSH is disabled for security

---

### Method 3: Sudo Per Command

**Configuration:**
```yaml
vm:
  username: "kali"
  auth_method: "key"
  key_file: "~/.ssh/kali_vm"
  use_sudo: true
  sudo_method: "command"    # Sudo each command
  sudo_password: null       # Or your sudo password
```

**VM Setup:**

**Option A: NOPASSWD for Specific Commands**
```bash
# /etc/sudoers.d/kali-driver-mcp
kali ALL=(ALL) NOPASSWD: /sbin/insmod, /sbin/rmmod, /sbin/modprobe
kali ALL=(ALL) NOPASSWD: /usr/sbin/airmon-ng, /usr/sbin/airodump-ng
kali ALL=(ALL) NOPASSWD: /usr/sbin/tcpdump
kali ALL=(ALL) NOPASSWD: /bin/dmesg
```

**Option B: NOPASSWD for All**
```bash
# /etc/sudoers.d/kali-driver-mcp
kali ALL=(ALL) NOPASSWD: ALL
```

**Option C: With Password**
```yaml
vm:
  sudo_password: "your-sudo-password"
```

**How it works:**
- Prefixes each root command with `sudo`
- With NOPASSWD: `sudo insmod mydriver.ko`
- With password: `echo "password" | sudo -S insmod mydriver.ko"`

**Pros:**
- Fine-grained control over which commands can run
- Most secure option
- No root SSH needed

**Cons:**
- Requires listing all commands in sudoers
- May miss some commands (causes failures)
- More complex sudoers configuration

**Best for:** Production environments with strict security

---

## Comparison Matrix

| Feature | Direct Root SSH | Sudo Su Root | Sudo Per Command |
|---------|----------------|--------------|------------------|
| **Security** | Low | Medium | High |
| **Complexity** | Low | Medium | High |
| **Setup Time** | Quick | Medium | Longer |
| **Root SSH Required** | Yes | No | No |
| **Password in Config** | No (with key) | Optional | Optional |
| **Fine-grained Control** | No | No | Yes |
| **Recommended For** | Development | General Use | Production |

---

## Configuration Examples

### Example 1: Development Setup (Method 1)

```yaml
vm:
  host: "192.168.56.101"
  username: "root"
  auth_method: "key"
  key_file: "~/.ssh/kali_vm"
  use_sudo: false
```

No VM changes needed beyond enabling root SSH.

### Example 2: Secure Development (Method 2)

```yaml
vm:
  host: "192.168.56.101"
  username: "kali"
  auth_method: "key"
  key_file: "~/.ssh/kali_vm"
  use_sudo: true
  sudo_method: "su"
  sudo_password: null
```

VM setup:
```bash
# /etc/sudoers.d/kali-driver-mcp
kali ALL=(ALL) NOPASSWD: /bin/su
```

### Example 3: Production Setup (Method 3)

```yaml
vm:
  host: "192.168.56.101"
  username: "kali"
  auth_method: "key"
  key_file: "~/.ssh/kali_vm"
  use_sudo: true
  sudo_method: "command"
  sudo_password: null
```

VM setup:
```bash
# /etc/sudoers.d/kali-driver-mcp
kali ALL=(ALL) NOPASSWD: /sbin/insmod
kali ALL=(ALL) NOPASSWD: /sbin/rmmod
kali ALL=(ALL) NOPASSWD: /sbin/modprobe
kali ALL=(ALL) NOPASSWD: /usr/sbin/airmon-ng
kali ALL=(ALL) NOPASSWD: /usr/sbin/airodump-ng
kali ALL=(ALL) NOPASSWD: /usr/sbin/tcpdump
kali ALL=(ALL) NOPASSWD: /bin/dmesg
```

---

## Testing Your Configuration

### Test 1: Check User

```bash
ssh kali@192.168.56.101 "whoami"
# Should output: kali
```

### Test 2: Check Sudo Works

```bash
ssh kali@192.168.56.101 "sudo whoami"
# Should output: root (or ask for password)
```

### Test 3: Check Sudo Su Works

```bash
ssh kali@192.168.56.101 'sudo su root -c "whoami"'
# Should output: root
```

### Test 4: Run MCP Test

```bash
cd kali-driver-mcp
uv run python test_client.py
```

---

## Troubleshooting

### Error: "sudo: a password is required"

**Solution:** Either:
1. Add password to config: `sudo_password: "your-password"`
2. Configure NOPASSWD in /etc/sudoers

### Error: "sudo: no tty present"

**Solution:** Add to /etc/sudoers:
```
Defaults:kali !requiretty
```

### Error: "sudo: command not found in secure_path"

**Solution:** Use full paths in config or add to sudo secure_path:
```
Defaults secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
```

### Commands Still Fail with Sudo

**Check logs:**
```bash
tail -f logs/kali-driver-mcp.log
# Look for actual command being executed
```

**Enable DEBUG:**
```yaml
logging:
  level: "DEBUG"
```

---

## Security Best Practices

1. **Never commit passwords to git**
   - Use environment variables
   - Or prompt for password at runtime

2. **Use SSH keys instead of passwords**
   ```yaml
   auth_method: "key"
   ```

3. **Limit sudo to specific commands** (Method 3)
   - Don't use `ALL=(ALL) NOPASSWD: ALL`

4. **Use strong SSH key passphrases**
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/kali_vm
   # Enter a strong passphrase
   ```

5. **Restrict SSH access by IP**
   ```bash
   # /etc/ssh/sshd_config
   AllowUsers kali@192.168.56.1
   ```

6. **Audit sudo usage**
   ```bash
   # /etc/sudoers
   Defaults logfile=/var/log/sudo.log
   ```

---

## Migration Guide

### Migrating from Root SSH to Sudo Su

1. **Update config.yaml:**
   ```yaml
   username: "kali"  # Change from "root"
   use_sudo: true
   sudo_method: "su"
   ```

2. **Setup sudoers in VM:**
   ```bash
   echo "kali ALL=(ALL) NOPASSWD: /bin/su" | sudo tee /etc/sudoers.d/kali-driver-mcp
   ```

3. **Test:**
   ```bash
   uv run python test_client.py
   ```

4. **Optional: Disable root SSH:**
   ```bash
   # /etc/ssh/sshd_config
   PermitRootLogin no
   sudo systemctl restart ssh
   ```

---

## FAQ

**Q: Which method should I use?**
A: For development, use Method 1 (Direct Root SSH). For production or shared VMs, use Method 2 or 3.

**Q: Do I need to store my sudo password in the config?**
A: No, if you configure NOPASSWD in /etc/sudoers.

**Q: Can I use password authentication instead of SSH keys?**
A: Yes, but SSH keys are more secure and recommended.

**Q: Will existing code/configs break?**
A: No, the default (use_sudo: false with root user) maintains backward compatibility.

**Q: Can I switch between methods?**
A: Yes, just update config.yaml and restart the server.

**Q: What happens if a command doesn't need root?**
A: It runs normally without sudo prefix (only root commands are wrapped).

---

For more information, see:
- [README.md](README.md) - Full documentation
- [CLAUDE.md](CLAUDE.md) - Development guide
- [config.yaml.example](config.yaml.example) - Configuration template
