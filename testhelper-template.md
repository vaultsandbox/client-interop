# Plan: client-{LANG} testhelper

CLI tool for interoperability testing of the {LANGUAGE} SDK.

## Location

`client-{lang}/scripts/testhelper.{ext}`

## Commands

| Command | Stdin | Stdout | Description |
|---------|-------|--------|-------------|
| `create-inbox` | - | JSON export | Create inbox, return exported JSON |
| `import-inbox` | JSON export | `{"success":true}` | Import inbox from JSON |
| `read-emails` | JSON export | `{"emails":[...]}` | Import inbox, fetch & decrypt emails |
| `cleanup <address>` | - | `{"success":true}` | Delete inbox |

## JSON Schemas

### ExportedInbox (create-inbox output / import-inbox input)

```json
{
  "version": 1,
  "emailAddress": "string",
  "expiresAt": "ISO8601 timestamp",
  "inboxHash": "base64 string",
  "serverSigPk": "base64 string",
  "secretKey": "base64 string",
  "exportedAt": "ISO8601 timestamp"
}
```

### read-emails output

```json
{
  "emails": [
    {
      "id": "string",
      "subject": "string",
      "from": "string",
      "to": ["string"],
      "text": "string",
      "html": "string (optional)",
      "attachments": [
        {
          "filename": "string",
          "contentType": "string",
          "size": 123
        }
      ],
      "receivedAt": "ISO8601 timestamp"
    }
  ]
}
```

## Implementation Requirements

1. **Client initialization**: Read `VAULTSANDBOX_URL` and `VAULTSANDBOX_API_KEY` from environment
2. **JSON keys**: Use camelCase in all JSON output (convert from SDK's native case if needed)
3. **Output**: JSON to stdout, errors to stderr
4. **Exit codes**: 0 for success, non-zero for failure
5. **Stdin handling**: Read full stdin for commands that accept JSON input

## Pseudocode

```
function main():
    command = args[1]

    client = SDK.createClient(
        url=env["VAULTSANDBOX_URL"],
        apiKey=env["VAULTSANDBOX_API_KEY"]
    )

    switch command:
        case "create-inbox":
            inbox = client.createInbox()
            export = inbox.export()
            print(toJSON(export))

        case "import-inbox":
            data = parseJSON(readStdin())
            client.importInbox(data)
            print({"success": true})

        case "read-emails":
            data = parseJSON(readStdin())
            inbox = client.importInbox(data)
            emails = inbox.listEmails()
            print({"emails": formatEmails(emails)})

        case "cleanup":
            address = args[2]
            client.deleteInbox(address)
            print({"success": true})
```

## Codebase Integration

### 1. Update SDK type

In `tests/helpers/sdk_runner.py`, add to the `SDK` literal:

```python
SDK = Literal["go", "node", "python", "java", "dotnet", "{lang}"]
```

### 2. Add command builder

In `SDKRunner._get_command()`, add:

```python
elif self.sdk == "{lang}":
    return ["{run_command}", "{script_path}", command, *args]
```

### 3. Add SDK config

In `get_runners()`, add to `sdk_configs`:

```python
("{lang}", "CLIENT_{LANG}_PATH"),
```

### 4. Environment variable

Set in `.env` or environment:

```bash
CLIENT_{LANG}_PATH=/path/to/client-{lang}
```

## Build & Run

```bash
# Build (if needed)
cd client-{lang}
{build_command}

# Run
{run_command} {script_path} <command>
```

## Test locally

```bash
export VAULTSANDBOX_URL=http://localhost:3000
export VAULTSANDBOX_API_KEY=dev_key

# Create inbox
{run_command} {script_path} create-inbox > /tmp/inbox.json

# Read emails
{run_command} {script_path} read-emails < /tmp/inbox.json

# Cleanup
{run_command} {script_path} cleanup test@inbox.example.com
```

## Checklist

- [ ] Implement testhelper CLI with all 4 commands
- [ ] Update `tests/helpers/sdk_runner.py` (SDK type, command builder, config)
- [ ] Add `CLIENT_{LANG}_PATH` to `.env`
- [ ] Test: `create-inbox` returns valid JSON
- [ ] Test: `read-emails` decrypts emails from other SDKs
- [ ] Test: Full interop test suite passes
