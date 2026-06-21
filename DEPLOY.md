# Deploy STS on Ubuntu (IP + Port)

Simple deployment for: **http://95.182.86.121:8000**

No domain or nginx required. The app runs with **Gunicorn** on port **8000**.

---

## One-command deploy (easiest)

SSH into your Ubuntu server, then run:

```bash
curl -fsSL https://raw.githubusercontent.com/memsa771-hub/sts/main/deploy.sh -o deploy.sh
sudo bash deploy.sh
```

Open in browser:

```
http://95.182.86.121:8000
```

---

## Manual steps (same result)

### 1. Connect to server

```bash
ssh root@95.182.86.121
```

(or use your Ubuntu username instead of `root`)

### 2. Run deploy script from repo

```bash
apt update && apt install -y git
git clone https://github.com/memsa771-hub/sts.git
cd sts
sudo bash deploy.sh
```

### 3. Create admin user (first time)

```bash
cd ~/sts
set -a && source .env && set +a
source venv/bin/activate
python manage.py createsuperuser
```

### 4. Open firewall port (if needed)

If your cloud provider has a firewall, allow **TCP 8000**.

On Ubuntu with UFW:

```bash
sudo ufw allow 8000/tcp
sudo ufw reload
```

Also open port **8000** in your VPS/cloud panel (Hetzner, DigitalOcean, etc.).

---

## Update after code changes

On the server:

```bash
cd ~/sts
sudo bash deploy.sh
```

This pulls latest code, runs migrations, collects static files, and restarts the app.

---

## Useful commands

| Action | Command |
|--------|---------|
| Check status | `sudo systemctl status sts` |
| Restart app | `sudo systemctl restart sts` |
| View logs | `sudo journalctl -u sts -f` |
| Stop app | `sudo systemctl stop sts` |

---

## Configuration

Default settings (change in `deploy.sh` if needed):

| Setting | Default |
|---------|---------|
| Server IP | `95.182.86.121` |
| Port | `8000` |
| App folder | `/home/ubuntu/sts` |
| Service name | `sts` |

Custom IP/port example:

```bash
sudo SERVER_IP=95.182.86.121 PORT=8000 bash deploy.sh
```

Environment file location: `/home/ubuntu/sts/.env`

---

## Troubleshooting

**Site not opening?**
1. Run diagnostics: `sudo bash diagnose.sh`
2. Check service: `sudo systemctl status sts`
3. Check logs: `sudo journalctl -u sts -n 50`
4. Test locally on server: `curl -I http://127.0.0.1:8000`
5. If curl works locally but browser fails → **open port 8000 in your VPS cloud panel** (not just UFW)
6. Confirm port is listening: `sudo ss -tlnp | grep 8000`

**Static files/CSS missing?**
```bash
cd ~/sts
set -a && source .env && set +a
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart sts
```

**DisallowedHost error?**
Add your IP to `.env`:
```
DJANGO_ALLOWED_HOSTS=95.182.86.121,localhost,127.0.0.1
```
Then restart: `sudo systemctl restart sts`
