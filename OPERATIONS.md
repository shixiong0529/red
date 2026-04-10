# Red Dragonfly Chatroom Operations Guide

This document is the day-to-day operations checklist for the production site:

- Site: `https://chat.slow.best`
- App service: `red`
- Reverse proxy: `nginx`
- App directory: `/opt/red/current`
- Data directory: `/opt/red/data`

## 1. Quick status checks

```bash
systemctl status red --no-pager
```

Purpose: Check whether the FastAPI chatroom service is running.

```bash
systemctl status nginx --no-pager
```

Purpose: Check whether nginx is running.

```bash
ss -lntp | grep -E ':80|:443|:8000'
```

Purpose: Confirm the expected ports are listening.

## 2. View logs

```bash
journalctl -u red -f
```

Purpose: Tail application logs in real time.

```bash
journalctl -u nginx -f
```

Purpose: Tail nginx logs in real time.

## 3. Restart services

```bash
systemctl restart red
```

Purpose: Restart the chatroom application after code or config changes.

```bash
systemctl reload nginx
```

Purpose: Reload nginx after editing site config without fully stopping it.

```bash
systemctl restart nginx
```

Purpose: Fully restart nginx if reload is not enough.

## 4. Update application code

```bash
cd /opt/red/current
git pull
. .venv/bin/activate
pip install -r requirements.txt
systemctl restart red
```

Purpose: Pull the latest code, refresh dependencies, and restart the app.

## 5. Check production env settings

```bash
cat /opt/red/current/.env
```

Purpose: Verify the app environment values currently in use.

Expected production values:

```env
DATABASE_URL=sqlite:////opt/red/data/red_dragonfly.db
SESSION_COOKIE_NAME=session
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=lax
SESSION_COOKIE_DOMAIN=chat.slow.best
```

## 6. Verify site availability

```bash
curl -I http://chat.slow.best
```

Purpose: Confirm HTTP redirects to HTTPS.

```bash
curl -I https://chat.slow.best/login
```

Purpose: Confirm the HTTPS login page is reachable.

```bash
curl -iL http://chat.slow.best
```

Purpose: Follow the full redirect chain and confirm the final page returns successfully.

## 7. Back up the database

```bash
cp /opt/red/data/red_dragonfly.db /opt/red/data/red_dragonfly.db.bak.$(date +%F-%H%M%S)
```

Purpose: Create a timestamped SQLite backup before risky changes or upgrades.

## 8. Renew the HTTPS certificate

Current certificate details:

- Domain: `chat.slow.best`
- Renewal mode: manual DNS challenge
- Expires: `2026-07-09`

Important:

- This certificate does not renew automatically.
- Renew it before expiry.
- A good reminder date is around `2026-06-25`.

Renewal command:

```bash
certbot certonly --manual --preferred-challenges dns --key-type rsa --cert-name chat.slow.best -d chat.slow.best --force-renewal
```

Purpose: Re-issue the production RSA certificate using DNS TXT verification.

When prompted, add a DNS TXT record:

- Type: `TXT`
- Host record: `_acme-challenge.chat`
- Value: the token printed by certbot

After the TXT record is visible:

```bash
dig TXT _acme-challenge.chat.slow.best +short
```

Purpose: Confirm the DNS challenge record has propagated before continuing certbot.

After certbot succeeds:

```bash
systemctl reload nginx
```

Purpose: Load the renewed certificate into nginx.

Verify the renewed cert:

```bash
curl -Iv https://chat.slow.best
```

Purpose: Confirm certificate verification is successful.

## 9. Common troubleshooting

If the app does not start:

```bash
journalctl -u red -n 100 --no-pager
```

Purpose: Inspect the most recent app startup errors.

If nginx config was edited:

```bash
nginx -t
```

Purpose: Validate nginx syntax before reload or restart.

If HTTPS seems broken:

```bash
echo | openssl s_client -connect chat.slow.best:443 -servername chat.slow.best 2>/dev/null | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

Purpose: Inspect the live certificate served by nginx.

If the browser cannot access HTTPS but the server looks healthy:

- Recheck the lightweight server firewall template.
- Confirm ports `80` and `443` are allowed.
- Test in an incognito window.
- Flush local DNS cache if needed.

## 10. Useful file locations

- App service: `/etc/systemd/system/red.service`
- Nginx site config: `/etc/nginx/sites-available/red`
- TLS cert path: `/etc/letsencrypt/live/chat.slow.best/`
- App env file: `/opt/red/current/.env`
- SQLite DB: `/opt/red/data/red_dragonfly.db`
