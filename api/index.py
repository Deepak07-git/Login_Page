import os
import json
import sqlite3
import urllib.request
from flask import Flask, render_template_string, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

# Cloud KV (Upstash / Vercel KV) config
KV_URL = os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL")
KV_TOKEN = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN")

# SQLite config (local disk or /tmp)
DB_PATH = os.environ.get("DB_PATH", "/tmp/users.db" if os.environ.get("VERCEL") else "users.db")


def init_sqlite():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print("SQLite init error:", e)


def sqlite_get(username):
    init_sqlite()
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print("SQLite get error:", e)
        return None


def sqlite_set(username, pw_hash):
    init_sqlite()
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pw_hash))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print("SQLite set error:", e)
        return False


def kv_get(username):
    try:
        url = f"{KV_URL.rstrip('/')}/get/user:{username}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("result")
    except Exception as e:
        print("KV get error:", e)
        return None


def kv_set(username, pw_hash):
    try:
        if kv_get(username):
            return False
        url = f"{KV_URL.rstrip('/')}/set/user:{username}"
        req = urllib.request.Request(
            url,
            data=pw_hash.encode("utf-8"),
            headers={"Authorization": f"Bearer {KV_TOKEN}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status in (200, 201)
    except Exception as e:
        print("KV set error:", e)
        return False


def get_user_hash(username):
    u = username.lower().strip()
    if u == "deepak":
        return generate_password_hash("python123")

    if KV_URL and KV_TOKEN:
        val = kv_get(u)
        if val:
            return val

    return sqlite_get(u)


def create_user(username, password):
    u = username.lower().strip()
    if u == "deepak":
        return False

    pw_hash = generate_password_hash(password)

    if KV_URL and KV_TOKEN:
        return kv_set(u, pw_hash)

    return sqlite_set(u, pw_hash)


STYLE = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --ink: #0f3d3e;
    --mint: #7ae7c7;
    --paper: #f7f8f5;
    --text: #14211f;
    --muted: #5d6b68;
    --line: #d9dfdb;
    --error: #b3261e;
    --success: #0e6245;
  }
  * { box-sizing: border-box; margin: 0; }
  body {
    font-family: "Plus Jakarta Sans", system-ui, sans-serif;
    color: var(--text);
    background: var(--paper);
    min-height: 100vh;
  }
  .page { display: grid; grid-template-columns: 1.1fr 1fr; min-height: 100vh; }

  /* Left: brand panel */
  .brand {
    background: var(--ink);
    color: #fff;
    padding: 56px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
  }
  .brand::before, .brand::after {
    content: "";
    position: absolute;
    border-radius: 50%;
    border: 1.5px solid rgba(122, 231, 199, .35);
  }
  .brand::before { width: 520px; height: 520px; right: -200px; bottom: -180px; }
  .brand::after  { width: 320px; height: 320px; right: -100px; bottom: -80px; background: rgba(122, 231, 199, .08); }
  .logo { font-weight: 800; font-size: 20px; display: flex; align-items: center; gap: 10px; }
  .logo span {
    width: 34px; height: 34px; border-radius: 10px; background: var(--mint); color: var(--ink);
    display: grid; place-items: center; font-weight: 800;
  }
  .brand h1 { font-size: clamp(34px, 4vw, 52px); line-height: 1.1; font-weight: 800; max-width: 440px; }
  .brand p { margin-top: 16px; color: #b9d3cf; max-width: 380px; line-height: 1.6; }
  .brand small { color: #7fa39e; }

  /* Right: form */
  .panel { display: grid; place-items: center; padding: 32px; }
  .card { width: 100%; max-width: 380px; }
  .card h2 { font-size: 30px; font-weight: 800; }
  .card .sub { color: var(--muted); margin: 8px 0 20px; }

  .tabs {
    display: flex;
    background: #e4ece7;
    border-radius: 10px;
    padding: 4px;
    margin-bottom: 22px;
  }
  .tab-btn {
    flex: 1;
    padding: 10px 14px;
    border: 0;
    background: transparent;
    font: inherit;
    font-size: 14px;
    font-weight: 700;
    color: var(--muted);
    border-radius: 8px;
    cursor: pointer;
    transition: all .2s;
  }
  .tab-btn.active {
    background: #fff;
    color: var(--ink);
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
  }

  label { display: block; font-size: 14px; font-weight: 600; margin-bottom: 6px; }
  .field { margin-bottom: 18px; position: relative; }
  input[type=text], input[type=password] {
    width: 100%; padding: 13px 14px; font: inherit; color: var(--text);
    background: #fff; border: 1.5px solid var(--line); border-radius: 10px;
    transition: border-color .2s, box-shadow .2s;
  }
  input:focus { outline: none; border-color: var(--ink); box-shadow: 0 0 0 4px rgba(15, 61, 62, .12); }
  .toggle {
    position: absolute; right: 10px; top: 33px; background: none; border: 0;
    font: inherit; font-size: 13px; font-weight: 600; color: var(--ink); cursor: pointer; padding: 4px 6px;
  }
  .error {
    background: #fdecea; color: var(--error); border-radius: 10px;
    padding: 12px 14px; font-size: 14px; margin-bottom: 18px;
  }
  .success {
    background: #e8f5e9; color: var(--success); border-radius: 10px;
    padding: 12px 14px; font-size: 14px; margin-bottom: 18px;
  }
  .btn {
    width: 100%; padding: 14px; font: inherit; font-weight: 700; color: #fff;
    background: var(--ink); border: 0; border-radius: 10px; cursor: pointer;
    transition: transform .15s, background .2s;
  }
  .btn:hover { background: #0b2e2f; }
  .btn:active { transform: scale(.98); }
  .btn:focus-visible, .toggle:focus-visible, .tab-btn:focus-visible { outline: 3px solid var(--mint); outline-offset: 2px; }
  .hint { margin-top: 20px; font-size: 13px; color: var(--muted); text-align: center; }
  .hint b { color: var(--text); }

  /* Dashboard */
  .welcome { max-width: 420px; text-align: center; }
  .welcome .badge {
    width: 64px; height: 64px; border-radius: 50%; background: var(--mint); color: var(--ink);
    display: grid; place-items: center; font-size: 28px; font-weight: 800; margin: 0 auto 20px;
  }
  .welcome a { display: inline-block; margin-top: 24px; text-decoration: none; }

  @media (max-width: 820px) {
    .page { grid-template-columns: 1fr; }
    .brand { display: none; }
  }
  @media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
"""

AUTH_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sign in / Register - PyPortal</title>
  """ + STYLE + """
</head>
<body>
  <div class="page">
    <aside class="brand">
      <div class="logo"><span>P</span> PyPortal</div>
      <div>
        <h1>Welcome back. Your work is right where you left it.</h1>
        <p>Sign in to pick up your projects, your notes and your progress.</p>
      </div>
      <small>&copy; 2026 PyPortal</small>
    </aside>

    <main class="panel">
      <div class="card">
        <div class="tabs">
          <button type="button" class="tab-btn active" id="tab-login" onclick="switchMode('login')">Sign in</button>
          <button type="button" class="tab-btn" id="tab-register" onclick="switchMode('register')">Register</button>
        </div>

        <form method="post" action="">
          <input type="hidden" name="mode" id="auth-mode" value="{{ mode or 'login' }}">
          <h2 id="form-title">Sign in</h2>
          <p class="sub" id="form-sub">Enter your details to continue.</p>

          {% if error %}<div class="error" role="alert">{{ error }}</div>{% endif %}
          {% if success %}<div class="success" role="status">{{ success }}</div>{% endif %}

          <div class="field">
            <label for="username">Username</label>
            <input type="text" id="username" name="username" value="{{ username }}" autocomplete="username" required autofocus>
          </div>

          <div class="field">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" autocomplete="current-password" required>
            <button type="button" class="toggle" onclick="togglePassword(this, 'password')">Show</button>
          </div>

          <div class="field" id="confirm-field" style="display: none;">
            <label for="confirm_password">Confirm Password</label>
            <input type="password" id="confirm_password" name="confirm_password" autocomplete="new-password">
            <button type="button" class="toggle" onclick="togglePassword(this, 'confirm_password')">Show</button>
          </div>

          <button class="btn" type="submit" id="submit-btn">Sign in</button>

          <p class="hint" id="hint-login">Demo account: <b>deepak</b> / <b>python123</b></p>
          <p class="hint" id="hint-register" style="display: none;">Password must be at least 6 characters.</p>
        </form>
      </div>
    </main>
  </div>

  <script>
    function switchMode(mode) {
      const isRegister = mode === 'register';
      document.getElementById('auth-mode').value = mode;
      document.getElementById('tab-login').classList.toggle('active', !isRegister);
      document.getElementById('tab-register').classList.toggle('active', isRegister);
      document.getElementById('form-title').textContent = isRegister ? 'Create an account' : 'Sign in';
      document.getElementById('form-sub').textContent = isRegister ? 'Enter details to create your account.' : 'Enter your details to continue.';
      document.getElementById('confirm-field').style.display = isRegister ? 'block' : 'none';
      document.getElementById('confirm_password').required = isRegister;
      document.getElementById('submit-btn').textContent = isRegister ? 'Create account' : 'Sign in';
      document.getElementById('hint-login').style.display = isRegister ? 'none' : 'block';
      document.getElementById('hint-register').style.display = isRegister ? 'block' : 'none';
    }

    function togglePassword(btn, inputId) {
      const input = document.getElementById(inputId);
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.textContent = show ? 'Hide' : 'Show';
    }

    // Set initial mode
    switchMode("{{ mode or 'login' }}");
  </script>
</body>
</html>
"""

DASHBOARD_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard - PyPortal</title>
  """ + STYLE + """
</head>
<body>
  <main class="panel" style="min-height:100vh">
    <div class="welcome">
      <div class="badge">{{ user[0]|upper }}</div>
      <h2>Hi, {{ user|capitalize }}</h2>
      <p class="sub">You're signed in.</p>
      <a class="btn" href="/logout" style="padding:14px 28px; width:auto">Sign out</a>
    </div>
  </main>
</body>
</html>
"""

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


@app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def handle_all(path):
    req_path = (
        request.args.get("path")
        or request.headers.get("x-matched-path")
        or request.headers.get("x-forwarded-uri")
        or path
    )
    clean = req_path.replace("api/index", "").strip("/")

    # Logout
    if clean == "logout":
        session.clear()
        return render_template_string(AUTH_PAGE, error=None, success="You have been signed out.", username="", mode="login")

    # Form Submission (Login or Register)
    if request.method == "POST":
        mode = request.form.get("mode", "login")
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        if mode == "register":
            confirm_password = request.form.get("confirm_password", "")
            if len(username) < 3:
                error = "Username must be at least 3 characters long."
                return render_template_string(AUTH_PAGE, error=error, username=username, mode="register")
            if not username.replace("_", "").isalnum():
                error = "Username can only contain letters, numbers, and underscores."
                return render_template_string(AUTH_PAGE, error=error, username=username, mode="register")
            if len(password) < 6:
                error = "Password must be at least 6 characters long."
                return render_template_string(AUTH_PAGE, error=error, username=username, mode="register")
            if password != confirm_password:
                error = "Passwords do not match. Please re-enter."
                return render_template_string(AUTH_PAGE, error=error, username=username, mode="register")

            if not create_user(username, password):
                error = f"Username '{username}' is already taken. Please choose another."
                return render_template_string(AUTH_PAGE, error=error, username=username, mode="register")

            # Registration successful: send user to Sign In tab with a success banner
            return render_template_string(
                AUTH_PAGE,
                error=None,
                success=f"Account created successfully for '{username}'! Please sign in with your password.",
                username=username,
                mode="login",
            )

        else:
            # Sign In mode
            stored_hash = get_user_hash(username)
            if stored_hash and check_password_hash(stored_hash, password):
                session["user"] = username
                return render_template_string(DASHBOARD_PAGE, user=username)
            error = "Wrong username or password. Check both and try again."
            return render_template_string(AUTH_PAGE, error=error, username=username, mode="login")

    # If already logged in, show Dashboard directly
    if "user" in session:
        return render_template_string(DASHBOARD_PAGE, user=session["user"])

    # Initial page load: show Sign In tab
    return render_template_string(AUTH_PAGE, error=None, username="", mode="login")


if __name__ == "__main__":
    init_sqlite()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
