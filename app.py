from flask import (
    Flask,
    redirect,
    request,
    session,
    render_template
)

import requests
import os


app = Flask(
    __name__,
    template_folder="templates"
)


# =========================================
# Flask Security
# =========================================

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "fuzzbot-local-secret-2026"
)


# =========================================
# Discord Application
# =========================================

CLIENT_ID = "1536519357025357844"

CLIENT_SECRET = os.environ.get(
    "DISCORD_CLIENT_SECRET"
)

REDIRECT_URI = (
    "http://127.0.0.1:5000/callback"
)

DISCORD_API = (
    "https://discord.com/api/v10"
)


# =========================================
# Homepage
# =========================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================
# Discord Login
# =========================================

@app.route("/login")
def login():

    discord_url = (
        "https://discord.com/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=identify"
    )

    return redirect(discord_url)


# =========================================
# Discord OAuth2 Callback
# =========================================

@app.route("/callback")
def callback():

    code = request.args.get("code")

    if not code:

        return """
        <h1>Discord Authorization Failed</h1>
        <p>No authorization code was received.</p>
        <a href="/">Return to FuzzBot</a>
        """

    if not CLIENT_SECRET:

        return """
        <h1>Configuration Error</h1>

        <p>
            DISCORD_CLIENT_SECRET is not set.
        </p>

        <a href="/">
            Return to FuzzBot
        </a>
        """

    token_data = {

        "client_id": CLIENT_ID,

        "client_secret": CLIENT_SECRET,

        "grant_type": "authorization_code",

        "code": code,

        "redirect_uri": REDIRECT_URI

    }

    token_response = requests.post(

        f"{DISCORD_API}/oauth2/token",

        data=token_data,

        headers={
            "Content-Type":
            "application/x-www-form-urlencoded"
        }

    )

    token = token_response.json()

    if "access_token" not in token:

        print(
            "Discord token error:",
            token
        )

        return """
        <h1>Discord Authorization Failed</h1>

        <p>
            Discord rejected the authorization.
        </p>

        <a href="/">
            Return to FuzzBot
        </a>
        """

    access_token = token["access_token"]

    user_response = requests.get(

        f"{DISCORD_API}/users/@me",

        headers={
            "Authorization":
            f"Bearer {access_token}"
        }

    )

    user = user_response.json()

    if "id" not in user:

        print(
            "Discord user error:",
            user
        )

        return """
        <h1>Unable to Get Discord User</h1>

        <a href="/">
            Return to FuzzBot
        </a>
        """

    session["user"] = user

    return redirect("/dashboard")


# =========================================
# Dashboard
# =========================================

@app.route("/dashboard")
def dashboard():

    user = session.get("user")

    if not user:

        return redirect("/login")

    username = (
        user.get("global_name")
        or user.get("username")
        or "Discord User"
    )

    return render_template(
        "dashboard.html",
        username=username
    )


# =========================================
# Moderation Page
# =========================================

@app.route("/moderation")
def moderation():

    user = session.get("user")

    if not user:

        return redirect("/login")

    username = (
        user.get("global_name")
        or user.get("username")
        or "Discord User"
    )

    return render_template(
        "moderation.html",
        username=username
    )


# =========================================
# Dashboard → FuzzBot Warn
# =========================================

@app.route(
    "/warn",
    methods=["POST"]
)
def warn_member():

    user = session.get("user")

    if not user:

        return redirect("/login")

    user_id = request.form.get(
        "user_id"
    )

    reason = request.form.get(
        "reason"
    )

    if not user_id or not reason:

        return """
        <h1>Warning Failed</h1>
        <p>Member ID and reason are required.</p>
        <a href="/moderation">
            Back to Moderation
        </a>
        """

    try:

        response = requests.post(

            "http://127.0.0.1:5050/api/warn",

            json={
                "user_id": int(user_id),
                "reason": reason
            },

            timeout=10

        )

        result = response.json()

    except Exception as error:

        print(
            "Could not contact FuzzBot:",
            error
        )

        return """
        <h1>FuzzBot Connection Error</h1>

        <p>
            Make sure FuzzBot is running.
        </p>

        <a href="/moderation">
            Back to Moderation
        </a>
        """

    if result.get("success"):

        return """
        <h1>✅ Warning Sent</h1>

        <p>
            The member has been warned.
        </p>

        <a href="/moderation">
            Back to Moderation
        </a>
        """

    error_message = result.get(
        "error",
        "Unknown error."
    )

    return f"""
    <h1>⚠️ Warning Failed</h1>

    <p>
        {error_message}
    </p>

    <a href="/moderation">
        Back to Moderation
    </a>
    """


# =========================================
# Logout
# =========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================================
# Start Flask Website
# =========================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )