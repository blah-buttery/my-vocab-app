import functools
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from flask import current_app as app

bp = Blueprint("auth", __name__, url_prefix="/auth")

def login_required(view):
    """View decorator that redirects anonymous users to the login page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped_view

@bp.before_app_request
def load_logged_in_user():
    """Load the user object from Supabase into ``g.user`` if a user id is stored in the session."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        response = app.supabase.table("users").select("*").eq("user_id", user_id).execute()
        g.user = response.data[0] if response.data else None

@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        error = None

        # Check if any fields are empty
        if not username:
            error = "Username is required."
        elif not email:
            error = "Email is required."
        elif not password:
            error = "Password is required."

        # Check if username or email already exists in the database
        if error is None:
            response_username = app.supabase.table("users").select("user_id").eq("username", username).execute()
            response_email = app.supabase.table("users").select("user_id").eq("email", email).execute()
            
            if response_username.data:
                error = f"User {username} is already registered."
            elif response_email.data:
                error = f"Email {email} is already in use."

        # Insert new user data into the database
        if error is None:
            hashed_password = generate_password_hash(password)
            app.supabase.table("users").insert({
                "username": username, 
                "email": email, 
                "password_hash": hashed_password
            }).execute()
            return redirect(url_for("auth.login"))

        flash(error)
    
    return render_template("auth/register.html")

@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None

        response = app.supabase.table("users").select("*").eq("username", username).execute()
        user = response.data[0] if response.data else None

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user["password_hash"], password):
            error = "Incorrect password."

        if error is None:
            session.clear()
            session["user_id"] = user["user_id"]
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")

@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
