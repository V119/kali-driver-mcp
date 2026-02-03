"""Async SSH connection pool manager."""

import asyncio
import asyncssh
import time
from typing import Optional, Tuple
import logging

from .config import Config
from .logging_config import get_command_logger

logger = logging.getLogger(__name__)


class SSHConnectionError(Exception):
    """SSH connection error."""
    pass


class CommandResult:
    """Result of SSH command execution."""

    def __init__(self, stdout: str, stderr: str, exit_code: int):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code

    @property
    def success(self) -> bool:
        """Check if command succeeded."""
        return self.exit_code == 0


class SSHManager:
    """Manages async SSH connections to Kali VM."""

    def __init__(self, config: Config):
        self.config = config
        self._connection: Optional[asyncssh.SSHClientConnection] = None
        self._lock = asyncio.Lock()
        self.cmd_logger = get_command_logger() if config.logging.log_commands else None

    async def connect(self) -> asyncssh.SSHClientConnection:
        """Get or create SSH connection."""
        async with self._lock:
            # Reuse existing connection if alive
            if self._connection and not self._connection.is_closed():
                return self._connection

            # Create new connection
            try:
                logger.info(f"Connecting to {self.config.vm.host}:{self.config.vm.port}")

                if self.config.vm.auth_method == "key":
                    self._connection = await asyncssh.connect(
                        host=self.config.vm.host,
                        port=self.config.vm.port,
                        username=self.config.vm.username,
                        client_keys=[self.config.vm.key_file],
                        known_hosts=None,  # Disable host key checking for development
                    )
                else:  # password
                    self._connection = await asyncssh.connect(
                        host=self.config.vm.host,
                        port=self.config.vm.port,
                        username=self.config.vm.username,
                        password=self.config.vm.password,
                        known_hosts=None,
                    )

                logger.info("SSH connection established")
                return self._connection

            except Exception as e:
                logger.error(f"Failed to connect to VM: {e}")
                raise SSHConnectionError(f"Failed to connect to VM: {e}")

    async def execute(
        self,
        command: str,
        timeout: Optional[int] = 30,
        check: bool = False,
        needs_root: bool = False
    ) -> CommandResult:
        """
        Execute command on remote VM.

        Args:
            command: Command to execute
            timeout: Command timeout in seconds (None for no timeout)
            check: If True, raise exception on non-zero exit code
            needs_root: If True, execute with root privileges (uses sudo if configured)

        Returns:
            CommandResult with stdout, stderr, and exit code

        Raises:
            SSHConnectionError: If connection fails
            asyncio.TimeoutError: If command times out
            RuntimeError: If check=True and command fails
        """
        conn = await self.connect()

        # Wrap command with sudo if needed
        original_command = command
        if needs_root and self.config.vm.use_sudo:
            command = self._wrap_with_sudo(command)

        # Log command start
        cmd_id = None
        if self.cmd_logger:
            cmd_id = self.cmd_logger.log_command_start(
                command=command,
                timeout=timeout,
                context={
                    "check": check,
                    "needs_root": needs_root,
                    "original_command": original_command if needs_root else None
                }
            )

        start_time = time.time()

        try:
            logger.debug(f"Executing command: {command}")

            # Run command with timeout
            if timeout:
                result = await asyncio.wait_for(
                    conn.run(command, check=False),
                    timeout=timeout
                )
            else:
                result = await conn.run(command, check=False)

            duration = time.time() - start_time

            cmd_result = CommandResult(
                stdout=result.stdout.strip() if result.stdout else "",
                stderr=result.stderr.strip() if result.stderr else "",
                exit_code=result.exit_status or 0
            )

            logger.debug(
                f"Command exit code: {cmd_result.exit_code}, "
                f"stdout length: {len(cmd_result.stdout)}, "
                f"stderr length: {len(cmd_result.stderr)}"
            )

            # Log command completion
            if self.cmd_logger and cmd_id is not None:
                self.cmd_logger.log_command_end(
                    cmd_id=cmd_id,
                    exit_code=cmd_result.exit_code,
                    stdout=cmd_result.stdout,
                    stderr=cmd_result.stderr,
                    duration=duration
                )

            if check and not cmd_result.success:
                raise RuntimeError(
                    f"Command failed with exit code {cmd_result.exit_code}: "
                    f"{cmd_result.stderr or cmd_result.stdout}"
                )

            return cmd_result

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            logger.error(f"Command timed out after {timeout}s: {command}")

            # Log timeout error
            if self.cmd_logger and cmd_id is not None:
                self.cmd_logger.log_command_error(
                    cmd_id=cmd_id,
                    error=asyncio.TimeoutError(f"Command timed out after {timeout}s")
                )
            raise

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Command execution failed: {e}")

            # Log execution error
            if self.cmd_logger and cmd_id is not None:
                self.cmd_logger.log_command_error(cmd_id=cmd_id, error=e)
            raise

    def _wrap_with_sudo(self, command: str) -> str:
        """
        Wrap command with sudo based on configuration.

        Args:
            command: Original command

        Returns:
            Command wrapped with sudo
        """
        vm_config = self.config.vm

        if vm_config.sudo_method == "su":
            # Use sudo su root -c "command"
            # Escape quotes in command
            escaped_command = command.replace('"', '\\"')

            if vm_config.sudo_password:
                # With password: echo password | sudo -S su root -c "command"
                return f'echo "{vm_config.sudo_password}" | sudo -S su root -c "{escaped_command}"'
            else:
                # Without password (NOPASSWD configured)
                return f'sudo su root -c "{escaped_command}"'

        else:  # "command" mode
            # Use sudo command
            if vm_config.sudo_password:
                # With password: echo password | sudo -S command
                return f'echo "{vm_config.sudo_password}" | sudo -S {command}'
            else:
                # Without password (NOPASSWD configured)
                return f'sudo {command}'

    async def close(self):
        """Close SSH connection."""
        if self._connection and not self._connection.is_closed():
            logger.info("Closing SSH connection")
            self._connection.close()
            await self._connection.wait_closed()
            self._connection = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
