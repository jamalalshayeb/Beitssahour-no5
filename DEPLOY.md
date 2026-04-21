# نشر الموقع — Deploy guide

Campaign site for قائمة البناء والتنمية. Two free-host options are wired.
**Pick one** — skip the other section.

Before either path:
1. **Change the admin password.** Log in at `/admin/login` with `admin` / `admin123`, then update via `/admin/settings` (or change the seed in `seed.py` before first deploy).
2. **Pick a strong SECRET_KEY.** Generate one:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
   You'll paste it as a secret on the host. Don't commit it to git.

---

## Option A — PythonAnywhere (simplest, no credit card)

**Free tier gives you:** `yourusername.pythonanywhere.com`, 1 web app, 512 MB
storage, no cold starts, built-in bash console + file editor. Custom domains
require the $5/mo Hacker plan.

1. **Sign up** at https://www.pythonanywhere.com/registration/register/beginner/
2. In the **Consoles** tab → **Bash**, run:
   ```bash
   git clone https://github.com/<your-username>/<your-repo>.git ~/site
   cd ~/site
   python3.12 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```
3. In the **Web** tab → **Add a new web app** → **Manual configuration**
   → **Python 3.12**.
4. Set:
   - **Source code:** `/home/<username>/site`
   - **Working directory:** `/home/<username>/site`
   - **WSGI configuration file** — click it and replace the contents with:
     ```python
     import sys, os
     path = '/home/<username>/site'
     if path not in sys.path: sys.path.insert(0, path)
     os.environ['SECRET_KEY'] = '<paste-your-generated-key>'
     os.environ['SESSION_COOKIE_SECURE'] = '1'
     from app import app as application
     ```
   - **Virtualenv:** `/home/<username>/site/.venv`
5. Click **Reload**. Your site is live at
   `https://<username>.pythonanywhere.com/`.

### Pushing updates
```bash
# locally
git push
# then in PythonAnywhere Bash console:
cd ~/site && git pull && touch /var/www/<username>_pythonanywhere_com_wsgi.py
```
The `touch` reloads the worker.

---

## Option B — Fly.io (custom domain, Docker-based)

**Free allowance:** ~3 small machines + 3 GB persistent storage + unlimited
HTTPS. Credit card required at sign-up but you won't be charged unless you
exceed the allowance.

1. **Install the CLI:** https://fly.io/docs/hands-on/install-flyctl/
2. **Sign up + log in:**
   ```bash
   fly auth signup   # or: fly auth login
   ```
3. From this directory:
   ```bash
   fly launch --no-deploy --copy-config --name bayt-sahour-list
   ```
   (Accept Dockerfile, skip PostgreSQL, skip Redis.)
4. **Create the persistent volume** for SQLite + uploaded photos:
   ```bash
   fly volumes create site_data --region cdg --size 1
   ```
5. **Set secrets** (not committed):
   ```bash
   fly secrets set SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')"
   ```
6. **Deploy:**
   ```bash
   fly deploy
   ```
   The site will be at `https://bayt-sahour-list.fly.dev/`.
7. **(Optional) custom domain** `www.example.ps`:
   ```bash
   fly certs add www.example.ps
   # Then add the CNAME / A records it prints to your domain registrar.
   ```

### Pushing updates
```bash
git push   # if you're using GitHub Actions — otherwise just:
fly deploy
```

---

## Common troubleshooting

| Symptom | Fix |
|--|--|
| `ModuleNotFoundError: No module named 'flask'` | venv not activated / wrong interpreter on the host |
| Uploaded photos disappear after redeploy | `UPLOAD_DIR` not on a persistent volume — check `fly.toml` mount or PythonAnywhere path |
| 500 error on first hit | Usually `SECRET_KEY` missing — set it as described above |
| Arabic text renders as `□□□` | Browser font fallback — Cairo loads from Google Fonts, check network isn't blocked |

## Making changes after deploy

The `/admin` panel lets volunteers edit candidate CVs/bios/photos and the
program without touching code. For structural changes (new fields, new
pages, new routes), edit code → commit → push → redeploy.
