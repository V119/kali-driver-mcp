#!/usr/bin/env python3
"""Demonstration script showing command I/O logging functionality."""

import asyncio
from kali_driver_mcp.logging_config import setup_logging, get_command_logger

async def demo_command_logging():
    """Demonstrate command input/output logging."""

    # Setup logging
    setup_logging(
        log_level="DEBUG",
        log_file="logs/demo.log",
        json_format=False,
        enable_console=True
    )

    # Get command logger
    cmd_logger = get_command_logger("demo_commands")

    print("=" * 60)
    print("Command I/O Logging Demonstration")
    print("=" * 60)
    print()

    # Simulate successful command
    print("1. Simulating successful command...")
    cmd_id = cmd_logger.log_command_start("uname -a", timeout=30)

    # Simulate command execution
    await asyncio.sleep(0.1)

    # Log successful completion
    stdout = "Linux kali 6.18.5+kali-arm64 #1 SMP PREEMPT Kali 6.18.5-1kali1 (2026-01-19) aarch64 GNU/Linux"
    stderr = ""
    cmd_logger.log_command_end(cmd_id, exit_code=0, stdout=stdout, stderr=stderr, duration=0.054)

    print()
    print("2. Simulating failed command...")

    # Simulate failed command
    cmd_id = cmd_logger.log_command_start("cat /nonexistent_file", timeout=30)

    await asyncio.sleep(0.1)

    # Log failed completion
    stdout = ""
    stderr = "cat: /nonexistent_file: No such file or directory"
    cmd_logger.log_command_end(cmd_id, exit_code=1, stdout=stdout, stderr=stderr, duration=0.030)

    print()
    print("3. Simulating command with both output and errors...")

    # Simulate command with both stdout and stderr
    cmd_id = cmd_logger.log_command_start("make", timeout=60)

    await asyncio.sleep(0.1)

    # Log completion with both outputs
    stdout = "gcc -o myapp main.c\nLinking..."
    stderr = "main.c:42: error: undefined reference to 'missing_function'\nmake: *** [Makefile:10: myapp] Error 1"
    cmd_logger.log_command_end(cmd_id, exit_code=2, stdout=stdout, stderr=stderr, duration=4.532)

    print()
    print("=" * 60)
    print("Logging complete! Check logs/demo.log for output")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(demo_command_logging())
