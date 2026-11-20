import os
from flask import Flask, render_template_string, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

# Demo user store. Passwords are stored hashed, never as plain text.
USERS = {
    "deepak": generate_password_hash("python123"),
}

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
  .card .sub { color: var(--muted); margin: 8px 0 28px; }

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
  .btn {
    width: 100%; padding: 14px; font: inherit; font-weight: 700; color: #fff;
    background: var(--ink); border: 0; border-radius: 10px; cursor: pointer;
    transition: transform .15s, background .2s;
  }
  .btn:hover { background: #0b2e2f; }
  .btn:active { transform: scale(.98); }
  .btn:focus-visible, .toggle:focus-visible { outline: 3px solid var(--mint); outline-offset: 2px; }
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

LOGIN_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sign in</title>
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
      <form class="card" method="post" action="">
        <h2>Sign in</h2>
        <p class="sub">Enter your details to continue.</p>

        {% if error %}<div class="error" role="alert">{{ error }}</div>{% endif %}

        <div class="field">
          <label for="username">Username</label>
          <input type="text" id="username" name="username" value="{{ username }}" autocomplete="username" required autofocus>
        </div>

        <div class="field">
          <label for="password">Password</label>
          <input type="password" id="password" name="password" autocomplete="current-password" required>
          <button type="button" class="toggle" onclick="togglePassword(this)">Show</button>
        </div>

        <button class="btn" type="submit">Sign in</button>
        <p class="hint">Demo account: <b>deepak</b> / <b>python123</b></p>
      </form>
    </main>
  </div>

  <script>
    function togglePassword(btn) {
      const input = document.getElementById("password");
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.textContent = show ? "Hide" : "Show";
    }
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
  <title>Dashboard</title>
  """ + STYLE + """
</head>
<body>
  <main class="panel" style="min-height:100vh">
    <div class="welcome">
      <div class="badge">{{ user[0]|upper }}</div>
      <h2>Hi, {{ user|capitalize }}</h2>
      <p class="sub">You're signed in.</p>
      <a class="btn" href="{{ url_for('logout') }}" style="padding:14px 28px; width:auto">Sign out</a>
    </div>
  </main>
</body>
</html>
"""

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session and request.method == "GET":
        return redirect(url_for("dashboard"))

    error, username = None, ""
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        if username in USERS and check_password_hash(USERS[username], password):
            session["user"] = username
            return redirect(url_for("dashboard"))
        error = "Wrong username or password. Check both and try again."
    return render_template_string(LOGIN_PAGE, error=error, username=username)


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template_string(DASHBOARD_PAGE, user=session["user"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
