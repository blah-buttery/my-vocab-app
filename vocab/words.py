from flask import Blueprint, app
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import session
from flask import current_app
import supabase
import requests
from datetime import datetime
import json

import csv
import io
from werkzeug.exceptions import abort

from .auth import login_required

bp = Blueprint("words", __name__, url_prefix="/upload")

@bp.route("/upload", methods=["GET", "POST"])
@login_required
def add_words_to_db():
    user_id = get_current_user_id()
    if request.method == "POST":
        file = request.files.get('file')
        if file and file.filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
            csv_input = csv.reader(stream)
            words = set()
            for row in csv_input:
                word = row[0].strip().lower()
                add_word_to_user(word, user_id)
        return redirect(url_for("index"))
    return render_template("words.html")

def get_current_user_id():
    return session.get('user_id')

def add_word_to_user(word, user_id):
    # Check if the word exists in the `words` table
    supabase = current_app.supabase
    result = supabase.table("words").select("word_id").eq("word", word).execute()
    if result.data:
        word_id = result.data[0]['word_id']
    else:
        # If not, insert the word and get the word_id
        definition = get_def(word)
        insert_result = supabase.table("words").insert({"word": word, "definition": definition}).execute()
        word_id = insert_result.data[0]['word_id']

    # Now add or update the user_word
    user_word = {
        "user_id": user_id,
        "word_id": word_id,
        "last_reviewed": datetime.now().date().isoformat(),
        "review_interval": 0,
        "next_review_date": datetime.now().date().isoformat(),
        "easiness_factor": 2.5,
        "review_history": []
    }
    supabase.table("user_words").insert(user_word).execute()

def get_def(word):
     # Fetch definition from Merriam-Webster API
    mw_api_key = current_app.config['DICTIONARY_KEY']
    url = f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={mw_api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        definition = response.json()[0]['shortdef'][0]
    else:
        definition = "Definition not found."
    return definition

@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))