"""JSONL Session Parser for Claude Code session files.

Parses JSONL files stored in ~/.claude/projects/ to extract messages,
tool uses, and session metadata.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ParsedMessage:
    """Represents a parsed message from a Claude Code session."""
    uuid: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    tool_name: Optional[str] = None
    tool_input: Optional[str] = None
    tool_output: Optional[str] = None
    message_type: str = "text"  # "text" or "tool_use"


class SessionParser:
    """Parser for Claude Code JSONL session files."""

    def parse_file(self, file_path: Path) -> list[ParsedMessage]:
        """Parse a JSONL session file and return a list of ParsedMessage objects.

        Args:
            file_path: Path to the JSONL session file.

        Returns:
            List of ParsedMessage objects extracted from the file.
        """
        messages = []
        file_path = Path(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    parsed = self._parse_line(data)
                    if parsed:
                        messages.extend(parsed)
                except json.JSONDecodeError:
                    continue

        return messages

    def _parse_line(self, data: dict) -> Optional[list[ParsedMessage]]:
        """Parse a single line of JSONL data into ParsedMessage objects.

        Args:
            data: Parsed JSON data from a single line.

        Returns:
            List of ParsedMessage objects, or None if the line should be skipped.
        """
        msg_type = data.get("type")

        # Only process user and assistant messages
        if msg_type not in ("user", "assistant"):
            return None

        message = data.get("message", {})
        role = message.get("role", msg_type)
        content = message.get("content")
        uuid = data.get("uuid", "")
        timestamp = data.get("timestamp", "")

        messages = []

        # Handle user messages (content is typically a string)
        if role == "user":
            text_content = content if isinstance(content, str) else ""
            messages.append(ParsedMessage(
                uuid=uuid,
                role=role,
                content=text_content,
                timestamp=timestamp,
                message_type="text"
            ))

        # Handle assistant messages (content is typically a list of blocks)
        elif role == "assistant":
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        block_type = block.get("type")

                        if block_type == "text":
                            messages.append(ParsedMessage(
                                uuid=uuid,
                                role=role,
                                content=block.get("text", ""),
                                timestamp=timestamp,
                                message_type="text"
                            ))

                        elif block_type == "tool_use":
                            tool_input = block.get("input", {})
                            # Convert tool_input to string for easier searching
                            tool_input_str = json.dumps(tool_input) if isinstance(tool_input, dict) else str(tool_input)
                            messages.append(ParsedMessage(
                                uuid=uuid,
                                role=role,
                                content="",
                                timestamp=timestamp,
                                tool_name=block.get("name"),
                                tool_input=tool_input_str,
                                message_type="tool_use"
                            ))

            elif isinstance(content, str):
                # Fallback for string content in assistant messages
                messages.append(ParsedMessage(
                    uuid=uuid,
                    role=role,
                    content=content,
                    timestamp=timestamp,
                    message_type="text"
                ))

        return messages if messages else None

    def get_session_id(self, file_path: Path) -> Optional[str]:
        """Extract the session ID from a JSONL session file.

        The session ID is typically stored in the first message with a sessionId field.

        Args:
            file_path: Path to the JSONL session file.

        Returns:
            The session ID string, or None if not found.
        """
        file_path = Path(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    session_id = data.get("sessionId")
                    if session_id:
                        return session_id
                except json.JSONDecodeError:
                    continue

        return None

    def get_project_path(self, file_path: Path) -> Optional[str]:
        """Extract the project path from a JSONL session file path.

        Claude Code stores sessions in ~/.claude/projects/<encoded_path>/
        This method decodes the project path from the file location.

        Args:
            file_path: Path to the JSONL session file.

        Returns:
            The decoded project path, or None if it cannot be determined.
        """
        file_path = Path(file_path)

        # Expected structure: ~/.claude/projects/<encoded_path>/<session>.jsonl
        parts = file_path.parts

        try:
            # Find the "projects" directory in the path
            projects_idx = parts.index("projects")
            if projects_idx + 1 < len(parts) - 1:
                encoded_path = parts[projects_idx + 1]
                # The path is typically URL-encoded or base64-encoded
                # For now, return the raw encoded path
                # Could be enhanced to decode various encoding schemes
                return encoded_path
        except ValueError:
            pass

        return None
