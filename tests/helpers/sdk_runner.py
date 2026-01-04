"""SDK Runner - Executes testhelper commands across different SDK implementations."""

import subprocess
import json
import os
from dataclasses import dataclass
from typing import Literal, Optional

SDK = Literal["go", "node", "python", "java", "dotnet"]


@dataclass
class SDKRunner:
    """Runner for a specific SDK's testhelper CLI."""

    sdk: SDK
    path: str

    def _get_command(self, command: str, args: Optional[list[str]] = None) -> list[str]:
        """Build the command list for the given SDK."""
        args = args or []

        if self.sdk == "go":
            return ["./testhelper", command, *args]
        elif self.sdk == "node":
            return ["npx", "tsx", "scripts/testhelper.ts", command, *args]
        elif self.sdk == "python":
            # Use the SDK's venv Python if it exists
            venv_python = os.path.join(self.path, ".venv", "bin", "python")
            python_cmd = venv_python if os.path.exists(venv_python) else "python"
            return [python_cmd, "scripts/testhelper.py", command, *args]
        elif self.sdk == "java":
            return ["java", "-jar", "scripts/testhelper/target/testhelper-1.0.0.jar", command, *args]
        elif self.sdk == "dotnet":
            return ["dotnet", "run", "--project", "scripts/Testhelper", "--", command, *args]
        else:
            raise ValueError(f"Unknown SDK: {self.sdk}")

    def run(
        self,
        command: str,
        args: Optional[list[str]] = None,
        stdin: Optional[str] = None,
        timeout: int = 30,
    ) -> dict:
        """
        Run a testhelper command and return parsed JSON output.

        Args:
            command: The testhelper command (create-inbox, import-inbox, etc.)
            args: Additional command arguments
            stdin: Optional JSON input to pass via stdin
            timeout: Command timeout in seconds

        Returns:
            Parsed JSON response from the testhelper

        Raises:
            RuntimeError: If the command fails or returns non-JSON output
        """
        cmd = self._get_command(command, args)

        try:
            result = subprocess.run(
                cmd,
                cwd=self.path,
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ},
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"{self.sdk} {command} timed out after {timeout}s")

        if result.returncode != 0:
            raise RuntimeError(
                f"{self.sdk} {command} failed (exit {result.returncode}):\n"
                f"stderr: {result.stderr}\n"
                f"stdout: {result.stdout}"
            )

        if not result.stdout.strip():
            # Some commands may not return output (e.g., cleanup)
            return {"success": True}

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"{self.sdk} {command} returned invalid JSON:\n"
                f"stdout: {result.stdout}\n"
                f"error: {e}"
            )

    def create_inbox(self) -> dict:
        """Create a new inbox and return the export data."""
        return self.run("create-inbox")

    def import_inbox(self, export_data: dict) -> dict:
        """Import an inbox from export data."""
        return self.run("import-inbox", stdin=json.dumps(export_data))

    def read_emails(self, export_data: dict) -> dict:
        """Import inbox and fetch/decrypt all emails."""
        return self.run("read-emails", stdin=json.dumps(export_data))

    def send_email(self, address: str) -> dict:
        """Send a test email to the given address."""
        return self.run("send-email", args=[address])

    def cleanup(self, address: str) -> dict:
        """Delete the inbox for the given address."""
        return self.run("cleanup", args=[address])


def get_runners() -> dict[SDK, SDKRunner]:
    """
    Get runners for all configured SDKs.

    Environment variables required:
        CLIENT_GO_PATH: Path to client-go repository
        CLIENT_NODE_PATH: Path to client-node repository
        CLIENT_PYTHON_PATH: Path to client-python repository
        CLIENT_JAVA_PATH: Path to client-java repository
        CLIENT_DOTNET_PATH: Path to client-dotnet repository
    """
    runners: dict[SDK, SDKRunner] = {}

    sdk_configs: list[tuple[SDK, str]] = [
        ("go", "CLIENT_GO_PATH"),
        ("node", "CLIENT_NODE_PATH"),
        ("python", "CLIENT_PYTHON_PATH"),
        ("java", "CLIENT_JAVA_PATH"),
        ("dotnet", "CLIENT_DOTNET_PATH"),
    ]

    for sdk, env_var in sdk_configs:
        path = os.environ.get(env_var)
        if path:
            # Resolve relative paths from the current working directory
            if not os.path.isabs(path):
                path = os.path.abspath(path)
            runners[sdk] = SDKRunner(sdk, path)

    return runners


def get_available_sdks() -> list[SDK]:
    """Return list of SDKs that have paths configured."""
    return list(get_runners().keys())
