# SSH random 5-digit port rotation

Use this when the user asks to change SSH from 22 to a random 5-digit port and reconnect with the existing private key.

## Safety workflow

Never close the old SSH port before proving the new port accepts a fresh private-key login.

1. Pick an unused random 5-digit port or use the user's chosen 5-digit port.
2. Stage dual-port SSH:

```bash
SSH_NEW_PORT=PORT bash /tmp/rotate_ssh_port.sh
```

This writes `/etc/ssh/sshd_config.d/99-codex-temp-dual-port.conf` with both `Port 22` and `Port PORT`, validates `sshd -t`, restarts sshd, and prints active listeners.

3. From the Codex host, open a **new** SSH session using the same private key:

```powershell
ssh -i C:\path\to\private_key -p PORT root@VPS_IP "echo NEW_SSH_OK; hostname; whoami"
```

4. Only after the new login succeeds, finalize:

```bash
bash /tmp/rotate_ssh_port.sh --finalize PORT
```

This comments active `Port ...` lines in `/etc/ssh/sshd_config` and other drop-ins, removes the temporary dual-port file, writes `/etc/ssh/sshd_config.d/99-codex-ssh-port.conf`, validates config, restarts sshd, and leaves only the new port.

5. Verify from the Codex host:

```powershell
ssh -i C:\path\to\private_key -p PORT root@VPS_IP "echo FINAL_NEW_SSH_OK; ss -tlnp | grep -E ':PORT|:22'"
Test-NetConnection VPS_IP -Port 22
Test-NetConnection VPS_IP -Port PORT
```

Expected:

- New port succeeds.
- Port 22 TCP fails.
- `ss -tlnp` shows only `0.0.0.0:PORT` / `[::]:PORT` for sshd.

## State update

After final verification, update node state:

```bash
python scripts/node_state.py upsert NODE --ssh-port PORT --last-status ssh-port-PORT-verified-domain-subscription-url-ready
```

## Rollback

If the new port fails during staging, reconnect on the old port and remove `/etc/ssh/sshd_config.d/99-codex-temp-dual-port.conf`, then restart sshd. If finalization was completed but a provider firewall blocks the new port, use the VPS provider console to restore a `Port 22` line or revert the timestamped `/etc/ssh/sshd_config.bak.*` backup.
