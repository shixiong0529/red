# Red Dragonfly Chatroom Deployment

This project is a single-process FastAPI application with SQLite, Jinja2 templates, static assets, and a WebSocket chat endpoint.

## Recommended target

- OS: Alibaba Cloud ECS with Ubuntu 22.04 LTS or 24.04 LTS
- Region: Wuhan is fine for latency in central China
- Runtime: `systemd + uvicorn + nginx`
- Database: SQLite for early deployment and small-scale use

## Suggested server spec

- 2 vCPU
- 2 GB RAM
- 40 GB ESSD
- Public bandwidth according to your expected traffic

## Ports and security group

Open these ports in the Alibaba Cloud ECS security group:

- `22/tcp` for SSH
- `80/tcp` for HTTP
- `443/tcp` for HTTPS after certificate setup

## 1. Prepare the server

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx
sudo useradd -r -s /usr/sbin/nologin www || true
sudo mkdir -p /opt/red
sudo chown -R $USER:$USER /opt/red
```

## 2. Upload project code

You can use `git clone`, `scp`, or `rsync`.

```bash
cd /opt/red
git clone <your-repo-url> current
cd current
```

If you are not using Git on the server, upload the full project directory to `/opt/red/current`.

## 3. Create the Python environment

```bash
cd /opt/red/current
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 4. Prepare the environment file

```bash
cd /opt/red/current
cp .env.example .env
mkdir -p /opt/red/data
```

Recommended `.env` values for first deployment:

```env
DATABASE_URL=sqlite:////opt/red/data/red_dragonfly.db
SESSION_COOKIE_NAME=session
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=lax
SESSION_COOKIE_DOMAIN=
```

If you later enable HTTPS, change `SESSION_COOKIE_SECURE=false` to `true`.

## 5. First startup test

```bash
cd /opt/red/current
. .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://server-ip:8000` temporarily to check whether the app starts correctly. Stop it with `Ctrl+C` after verification.

## 6. Install the systemd service

```bash
sudo cp /opt/red/current/deploy/red.service /etc/systemd/system/red.service
sudo chown -R www:www /opt/red/current /opt/red/data
sudo systemctl daemon-reload
sudo systemctl enable --now red
sudo systemctl status red
```

Useful commands:

```bash
sudo journalctl -u red -f
sudo systemctl restart red
sudo systemctl stop red
```

## 7. Configure nginx

```bash
sudo cp /opt/red/current/deploy/nginx-red.conf /etc/nginx/sites-available/red
sudo ln -sf /etc/nginx/sites-available/red /etc/nginx/sites-enabled/red
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

After this, open `http://server-ip/`.

## 8. Bind a domain and enable HTTPS

Once your domain resolves to the ECS public IP:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Then update `.env`:

```env
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_DOMAIN=your-domain.com
```

Apply the new settings:

```bash
sudo systemctl restart red
```

## 9. Updating the app

```bash
cd /opt/red/current
git pull
. .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart red
```

## Notes

- SQLite is acceptable for initial deployment, low traffic, or personal/demo use.
- If concurrency grows, move to MySQL or PostgreSQL and set `DATABASE_URL` accordingly.
- The WebSocket endpoint is `/ws/chat`, and the included nginx config already supports upgrade headers.
- The app seeds content on first startup. Make sure the `bak/` directory is present in production.
