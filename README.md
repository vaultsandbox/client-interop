<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/logo-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/logo-light.svg">
  <img alt="VaultSandbox" src="./assets/logo-dark.svg">
</picture>

> **VaultSandbox is in Public Beta.** Join the journey to 1.0. Share feedback on [GitHub](https://github.com/vaultsandbox/gateway/discussions).


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# client-interop

Cross-SDK integration test suite for VaultSandbox client libraries.

## Overview

This repository orchestrates end-to-end interoperability tests across VaultSandbox SDK implementations to verify that:

1. Inboxes created by SDK-A can be exported and imported by SDK-B
2. Emails encrypted by the server can be decrypted by any SDK
3. All SDKs conform to the VaultSandbox specification

## Supported SDKs

- `client-go` (Go)
- `client-node` (Node.js/TypeScript)
- `client-python` (Python)
- `client-java` (Java)
- `client-dotnet` (.NET)

## Requirements

- Python 3.10+
- Access to SDK repositories (sibling directories by default)
- Running VaultSandbox server
- SMTP access for sending test emails

## Setup

1. **Install test dependencies:**

```bash
make install
```

2. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your values
```

Required environment variables:

| Variable | Description |
|----------|-------------|
| `VAULTSANDBOX_URL` | Server URL (e.g., `https://example.vsx.email`) |
| `VAULTSANDBOX_API_KEY` | Your API key |
| `SMTP_HOST` | SMTP server host (usually same as server) |
| `SMTP_PORT` | SMTP server port (default: 25) |
| `CLIENT_GO_PATH` | Path to client-go repository |
| `CLIENT_NODE_PATH` | Path to client-node repository |
| `CLIENT_PYTHON_PATH` | Path to client-python repository |
| `CLIENT_JAVA_PATH` | Path to client-java repository |
| `CLIENT_DOTNET_PATH` | Path to client-dotnet repository |

3. **Build SDK testhelpers:**

Each SDK needs a `testhelper` CLI. See `plans/` for implementation details.

```bash
# Go - build binary
cd ../client-go && go build -o testhelper ./cmd/testhelper

# Node - install dependencies (testhelper runs via tsx)
cd ../client-node && npm install

# Python - setup venv with SDK installed
cd ../client-python && python3 -m venv .venv && .venv/bin/pip install -e .

# Java - build local SDK jar, install to local Maven repo, and build shaded JAR
cd ../client-java && ./gradlew jar
cd ../client-java && mvn install:install-file -Dfile=build/libs/vaultsandbox-client-<version>.jar -DgroupId=com.vaultsandbox -DartifactId=client -Dversion=<version> -Dpackaging=jar -DgeneratePom=true
cd ../client-java/scripts/testhelper && mvn package

# .NET - build (runs via dotnet run)
cd ../client-dotnet/scripts/Testhelper && dotnet build
```

Or run all SDK builds from this repo:

```bash
make build-testhelpers
```

If Maven cached a previous "not found" error for the local SDK, clear the cache:

```bash
rm -f ~/.m2/repository/com/vaultsandbox/client/*/*.lastUpdated
```

## Usage

Run all tests:

```bash
make test
```

Run with verbose output:

```bash
make test-verbose
```

### Test Levels

Tests can run at different levels to balance speed vs coverage:

| Level | Description | Use Case |
|-------|-------------|----------|
| `smoke` | Quick sanity check - reference SDK (Go) only | CI on every commit |
| `standard` | Balanced coverage - one direction per SDK pair | PR merges (default) |
| `full` | All permutations - both directions for all pairs | Nightly / pre-release |

```bash
make test-smoke     # Quick smoke test (~5 tests)
make test-standard  # Standard coverage (~10 cross-SDK + 5 decrypt tests)
make test-full      # Full matrix (~20 cross-SDK + 5 decrypt tests)
```

**Test counts for 5 SDKs:**

| Level | Cross-SDK Tests | Single-SDK Tests | Total |
|-------|-----------------|------------------|-------|
| smoke | 4 (all → Go) | 1 (Go only) | ~10 |
| standard | 10 (one direction) | 5 (all SDKs) | ~35 |
| full | 20 (both directions) | 5 (all SDKs) | ~45 |

### Run Specific Tests

Run specific test file:

```bash
PYTHONPATH=tests .venv/bin/pytest tests/test_export_import.py -v
```

Run specific test:

```bash
PYTHONPATH=tests .venv/bin/pytest tests/test_email_decrypt.py::TestEmailDecryption::test_decrypt_plain_text -v
```

### Manual Testing with `--keep-inboxes`

To keep inboxes after tests for manual inspection in the web UI:

```bash
make test-verbose KEEP_INBOXES=1
```

Or with a specific test level:

```bash
make test-smoke KEEP_INBOXES=1
```

This will:
- Save inbox export JSON files to `./exports/`
- Skip cleanup so inboxes remain on the server
- Print the email address and export path for each test

You can then import the JSON files into the web UI to inspect the test emails.

To clear saved exports:

```bash
make clean-exports
```

## Tests

### Email Decryption Tests (`test_email_decrypt.py`)

Tests that each SDK can decrypt emails from the server:

| Test | Description |
|------|-------------|
| `test_decrypt_plain_text` | Plain text email decryption |
| `test_decrypt_with_attachment` | Email with attachment |
| `test_decrypt_html_email` | HTML email content |
| `test_decrypt_unicode_content` | Unicode/emoji content |
| `test_decrypt_multiple_emails` | Multiple emails in one inbox |

### Cross-SDK Import Tests (`test_export_import.py`)

Tests that exports from one SDK can be imported by another:

| Test | Description |
|------|-------------|
| `test_cross_sdk_import` | Create inbox with SDK-A, import and read with SDK-B |
| `test_export_format_consistency` | Verify export contains required fields |
| `test_import_idempotency` | Import same inbox multiple times |

## Test Matrix

For 5 SDKs at `--level=full`, the cross-SDK test matrix covers 20 combinations:

| Creator | Importers |
|---------|-----------|
| Go | Node, Python, Java, .NET |
| Node | Go, Python, Java, .NET |
| Python | Go, Node, Java, .NET |
| Java | Go, Node, Python, .NET |
| .NET | Go, Node, Python, Java |

At `--level=standard`, only 10 combinations are tested (one direction per pair).
At `--level=smoke`, only 4 combinations are tested (all SDKs → Go).

## Project Structure

```
client-interop/
├── tests/
│   ├── conftest.py           # Pytest fixtures and --keep-inboxes flag
│   ├── test_export_import.py # Cross-SDK import tests
│   ├── test_email_decrypt.py # Decryption tests
│   └── helpers/
│       ├── sdk_runner.py     # SDK testhelper execution
│       └── smtp.py           # Email sending utilities
├── exports/                  # Saved inbox exports (--keep-inboxes)
├── plans/                    # Testhelper implementation specs
├── .env.example
├── pytest.ini
├── Makefile
└── requirements.txt
```

## Testhelper Interface

Each SDK implements a CLI with these commands:

| Command | Stdin | Stdout | Description |
|---------|-------|--------|-------------|
| `create-inbox` | - | JSON export | Create inbox, return exported JSON |
| `import-inbox` | JSON export | `{"success":true}` | Import inbox from JSON |
| `read-emails` | JSON export | `{"emails":[...]}` | Import inbox, fetch & decrypt emails |
| `cleanup <address>` | - | `{"success":true}` | Delete inbox |

### Export JSON Format

```json
{
  "version": 1,
  "emailAddress": "abc123@example.vsx.email",
  "expiresAt": "2026-01-04T00:00:00.000Z",
  "inboxHash": "...",
  "serverSigPk": "...",
  "secretKey": "...",
  "exportedAt": "2026-01-03T23:00:00.000Z"
}
```

## Related

- [VaultSandbox Gateway](https://github.com/vaultsandbox/gateway) — The server this test suite validates against
- [client-go](https://github.com/vaultsandbox/client-go) — Go SDK
- [client-node](https://github.com/vaultsandbox/client-node) — Node.js/TypeScript SDK
- [client-python](https://github.com/vaultsandbox/client-python) — Python SDK
- [client-java](https://github.com/vaultsandbox/client-java) — Java SDK
- [client-dotnet](https://github.com/vaultsandbox/client-dotnet) — .NET SDK
- [Documentation](https://vaultsandbox.dev) — Full documentation and guides

## Support

- [Discussions](https://github.com/vaultsandbox/gateway/discussions)
- [Issue Tracker](https://github.com/vaultsandbox/client-interop/issues)

## Contributing

See the [contributing guidelines](https://github.com/vaultsandbox/gateway/blob/main/CONTRIBUTING.md) in the main repository.

## License

MIT — see [LICENSE](LICENSE) for details
