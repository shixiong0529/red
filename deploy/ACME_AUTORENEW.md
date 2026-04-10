# HTTPS Auto-Renewal Plan for chat.slow.best

Current status:

- The production certificate for `chat.slow.best` is valid.
- It was issued with `certbot --manual --preferred-challenges dns`.
- Manual certificates do not renew automatically.

To solve renewal properly, switch to an API-based DNS challenge flow.

## Recommended approach

Use `acme.sh` with Alibaba Cloud DNS API (`dns_ali`).

Why this approach:

- It supports DNS validation automatically.
- It avoids the HTTP challenge path that previously returned `403`.
- It can renew certificates automatically without manual TXT record updates.

## Prerequisites

Create a RAM user in Alibaba Cloud with permission to manage DNS records for your domain.

Recommended permission scope:

- Only the permissions required to manage Alibaba Cloud DNS records.
- Do not use the Alibaba Cloud root account AccessKey.

You will need:

- `Ali_Key`
- `Ali_Secret`

Alibaba Cloud documents recommend using a RAM user and AccessKey pair for API access.

## 1. Install acme.sh

```bash
curl https://get.acme.sh | sh
source ~/.bashrc
```

Purpose: Install `acme.sh` for the current user and register its cron-based renewal task.

If `source ~/.bashrc` does not work in your shell, log out and log back in.

## 2. Set Alibaba Cloud DNS API credentials

```bash
export Ali_Key="REPLACE_WITH_YOUR_ACCESS_KEY_ID"
export Ali_Secret="REPLACE_WITH_YOUR_ACCESS_KEY_SECRET"
```

Purpose: Give `acme.sh` access to Alibaba Cloud DNS so it can create and remove TXT validation records automatically.

Note:

- `acme.sh` stores these values in its own account config after first use.
- You do not need to keep exporting them forever once issuance succeeds, but keep them in a secure password manager.

## 3. Issue a new RSA certificate automatically

```bash
~/.acme.sh/acme.sh --set-default-ca --server letsencrypt
~/.acme.sh/acme.sh --issue --dns dns_ali -d chat.slow.best --keylength 2048
```

Purpose: Issue a fresh RSA certificate for `chat.slow.best` using Alibaba Cloud DNS API automation.

## 4. Install the certificate to nginx paths

```bash
mkdir -p /etc/letsencrypt/live/chat.slow.best
~/.acme.sh/acme.sh --install-cert -d chat.slow.best \
  --key-file /etc/letsencrypt/live/chat.slow.best/privkey.pem \
  --fullchain-file /etc/letsencrypt/live/chat.slow.best/fullchain.pem \
  --reloadcmd "systemctl reload nginx"
```

Purpose: Copy the renewed certificate files to the same paths nginx already uses, then reload nginx automatically after renewal.

## 5. Test renewal

```bash
~/.acme.sh/acme.sh --renew -d chat.slow.best --force
```

Purpose: Verify the automatic renewal path works before relying on it in production.

Then confirm nginx reloaded successfully:

```bash
systemctl status nginx --no-pager
curl -Iv https://chat.slow.best
```

Purpose: Check nginx health and verify the renewed certificate is being served correctly.

## 6. Keep or remove certbot

You can keep `certbot` installed, but after switching to `acme.sh`, the active renewal workflow should be:

- issuance: `acme.sh --issue --dns dns_ali`
- install: `acme.sh --install-cert`
- renew: handled by `acme.sh` cron job

## 7. Rollback plan

If the automated issuance fails:

- the current certificate remains in place until expiry
- nginx continues serving the currently installed certificate

That means you can test this migration safely before the current certificate expires.
