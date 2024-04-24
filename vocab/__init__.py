import os
from flask import Flask, jsonify, render_template, current_app
from supabase import create_client, Client
import logging

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile('config.py', silent=True)
    
    supabase_url = app.config['SUPABASE_URL']
    supabase_key = app.config['SUPABASE_KEY']
    app.supabase = create_client(supabase_url, supabase_key)

    # Log to a file in production
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    @app.route('/')
    def index():
        # Use the Supabase client within your route
        supabase = app.supabase 
        #result = supabase.table('users').select('*').execute()
        return render_template('base.html')

    from . import auth
    from . import study
    from . import words

    app.register_blueprint(auth.bp)
    app.register_blueprint(study.bp)
    app.register_blueprint(words.bp)

    app.add_url_rule("/", endpoint="index")

    return app
