# FTP Upload Plan

Codex prepares a local package under `dist/ai_accel_paper/`. It does not upload the package.

## Build Package

```bash
just build-dist-package
```

## Suggested Upload Shape

Upload the contents of `dist/ai_accel_paper/` to:

```text
https://ftp.kotori9.dev/ai_accel_paper/
```

Example using `lftp`, with credentials supplied outside the repository:

```bash
lftp -u "$FTP_USER","$FTP_PASS" ftp.kotori9.dev <<'EOF'
mirror -R dist/ai_accel_paper /ai_accel_paper
bye
EOF
```

After upload, verify that `manifest.json` and `checksums.sha256` are reachable and match the local package.

The package can list Windows serial ports before any FPGA run:

```powershell
python install.py --local . --list-ports
```
