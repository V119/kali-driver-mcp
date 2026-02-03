#!/usr/bin/env python3
"""
Log viewer and analyzer for Kali Driver MCP Server.

This tool helps analyze and debug MCP server logs.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def parse_json_log(line: str) -> Optional[dict]:
    """Parse a JSON log line."""
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def parse_text_log(line: str) -> Optional[dict]:
    """Parse a text log line."""
    # Basic parsing for text logs
    # Format: timestamp - logger - level - message
    parts = line.split(" - ", 3)
    if len(parts) >= 4:
        return {
            "timestamp": parts[0],
            "logger": parts[1],
            "level": parts[2],
            "message": parts[3],
        }
    return None


def filter_commands(log_file: Path, output_file: Optional[Path] = None):
    """Extract all SSH command logs."""
    commands = []

    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Try JSON format first
            log_entry = parse_json_log(line)
            if not log_entry:
                log_entry = parse_text_log(line)

            if not log_entry:
                continue

            # Check if this is a command log
            message = log_entry.get("message", "")
            if "[CMD-" in message:
                # Extract command ID
                if "Starting command" in message:
                    cmd_info = {
                        "type": "start",
                        "message": message,
                        "timestamp": log_entry.get("timestamp"),
                    }
                    if log_entry.get("extra"):
                        cmd_info.update(log_entry["extra"])
                    commands.append(cmd_info)

                elif "Completed with exit code" in message:
                    cmd_info = {
                        "type": "complete",
                        "message": message,
                        "timestamp": log_entry.get("timestamp"),
                    }
                    if log_entry.get("extra"):
                        cmd_info.update(log_entry["extra"])
                    commands.append(cmd_info)

                elif "Command failed" in message:
                    cmd_info = {
                        "type": "error",
                        "message": message,
                        "timestamp": log_entry.get("timestamp"),
                    }
                    if log_entry.get("extra"):
                        cmd_info.update(log_entry["extra"])
                    commands.append(cmd_info)

    # Print or save results
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(commands, f, indent=2)
        print(f"Extracted {len(commands)} command logs to {output_file}")
    else:
        print(f"\n=== SSH Commands ({len(commands)} entries) ===\n")
        for cmd in commands:
            print(f"[{cmd.get('timestamp', 'N/A')}] {cmd.get('message', '')}")
            if cmd.get('command'):
                print(f"  Command: {cmd['command'][:80]}...")
            if cmd.get('exit_code') is not None:
                print(f"  Exit Code: {cmd['exit_code']}")
            if cmd.get('duration_seconds'):
                print(f"  Duration: {cmd['duration_seconds']}s")
            print()


def filter_tools(log_file: Path, output_file: Optional[Path] = None):
    """Extract all MCP tool logs."""
    tools = []

    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Try JSON format first
            log_entry = parse_json_log(line)
            if not log_entry:
                log_entry = parse_text_log(line)

            if not log_entry:
                continue

            # Check if this is a tool log
            message = log_entry.get("message", "")
            if "[TOOL-" in message:
                tool_info = {
                    "message": message,
                    "timestamp": log_entry.get("timestamp"),
                }
                if log_entry.get("extra"):
                    tool_info.update(log_entry["extra"])
                tools.append(tool_info)

    # Print or save results
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(tools, f, indent=2)
        print(f"Extracted {len(tools)} tool logs to {output_file}")
    else:
        print(f"\n=== MCP Tools ({len(tools)} entries) ===\n")
        for tool in tools:
            print(f"[{tool.get('timestamp', 'N/A')}] {tool.get('message', '')}")
            if tool.get('tool_name'):
                print(f"  Tool: {tool['tool_name']}")
            if tool.get('arguments'):
                print(f"  Arguments: {tool['arguments']}")
            if tool.get('duration_seconds'):
                print(f"  Duration: {tool['duration_seconds']}s")
            print()


def filter_errors(log_file: Path):
    """Extract all errors from log."""
    errors = []

    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Try JSON format first
            log_entry = parse_json_log(line)
            if not log_entry:
                log_entry = parse_text_log(line)

            if not log_entry:
                continue

            # Check if this is an error
            level = log_entry.get("level", "")
            if level in ["ERROR", "CRITICAL"]:
                errors.append(log_entry)

    print(f"\n=== Errors ({len(errors)} entries) ===\n")
    for error in errors:
        print(f"[{error.get('timestamp', 'N/A')}] {error.get('message', '')}")
        if error.get("exception"):
            exc = error["exception"]
            print(f"  Exception: {exc.get('type')} - {exc.get('message')}")
        print()


def show_stats(log_file: Path):
    """Show statistics about the log file."""
    stats = {
        "total_lines": 0,
        "commands": 0,
        "tools": 0,
        "errors": 0,
        "warnings": 0,
        "levels": {},
    }

    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            stats["total_lines"] += 1

            # Try to parse
            log_entry = parse_json_log(line)
            if not log_entry:
                log_entry = parse_text_log(line)

            if not log_entry:
                continue

            # Count by level
            level = log_entry.get("level", "UNKNOWN")
            stats["levels"][level] = stats["levels"].get(level, 0) + 1

            # Count errors and warnings
            if level == "ERROR":
                stats["errors"] += 1
            elif level == "WARNING":
                stats["warnings"] += 1

            # Count commands and tools
            message = log_entry.get("message", "")
            if "[CMD-" in message:
                stats["commands"] += 1
            if "[TOOL-" in message:
                stats["tools"] += 1

    print("\n=== Log Statistics ===\n")
    print(f"Total Lines: {stats['total_lines']}")
    print(f"Commands: {stats['commands']}")
    print(f"Tools: {stats['tools']}")
    print(f"Errors: {stats['errors']}")
    print(f"Warnings: {stats['warnings']}")
    print("\nBy Level:")
    for level, count in sorted(stats["levels"].items()):
        print(f"  {level}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Kali Driver MCP Server logs"
    )
    parser.add_argument(
        "logfile",
        type=Path,
        help="Path to log file"
    )
    parser.add_argument(
        "--commands",
        action="store_true",
        help="Show SSH command logs"
    )
    parser.add_argument(
        "--tools",
        action="store_true",
        help="Show MCP tool logs"
    )
    parser.add_argument(
        "--errors",
        action="store_true",
        help="Show error logs"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for extracted logs (JSON format)"
    )

    args = parser.parse_args()

    if not args.logfile.exists():
        print(f"Error: Log file not found: {args.logfile}")
        sys.exit(1)

    # If no specific filter, show stats
    if not (args.commands or args.tools or args.errors or args.stats):
        args.stats = True

    if args.stats:
        show_stats(args.logfile)

    if args.commands:
        filter_commands(args.logfile, args.output)

    if args.tools:
        filter_tools(args.logfile, args.output)

    if args.errors:
        filter_errors(args.logfile)


if __name__ == "__main__":
    main()
