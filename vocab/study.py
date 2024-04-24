from flask import Blueprint, app, request, jsonify, render_template, current_app, session, redirect, url_for
import requests
import openai 
import os
from werkzeug.utils import secure_filename
import logging
import re
import datetime
import json

bp = Blueprint('study', __name__, url_prefix='/study')

@bp.before_app_request
def before_request():
    # Set the OpenAI API key for each request
    openai.api_key = current_app.config['OPENAI_API_KEY']

@bp.route('/')
def study_home():
    current_time = datetime.datetime.now()
    supabase = current_app.supabase
    response = supabase.table("user_words")\
        .select('*')\
        .order("next_review_date", desc=False)\
        .limit(1)\
        .execute()

    word = "No word scheduled"  # Default value if no word found
    definition = "No definition available"  # Default value if no definition found

    if response.data:
        word_id = response.data[0]['word_id']
        last_reviewed = response.data[0]['last_reviewed']
        print(f"last reviewed from study_home() is {last_reviewed}")
        review_interval = response.data[0]['review_interval']
        session['word_id'] = word_id
        session['last_reviewed'] = last_reviewed
        session['review_interval'] = review_interval
        word_info = supabase.table("words").select("word, definition").eq("word_id", word_id).execute()
        if word_info.data:
            word = word_info.data[0]['word']
            definition = word_info.data[0]['definition']
            session['target_word'] = word
            session['definition'] = definition

    return render_template('record.html', word=word, definition=definition)


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'flac', 'm4a', 'mp3', 'mp4', 'mpeg', 'mpga', 'oga', 'ogg', 'wav', 'webm'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/process_audio', methods=['POST'])
def process_audio():
    uploads_dir = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)

    audio_file = request.files['audio_data']
    if audio_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    file_extension = audio_file.filename.rsplit('.', 1)[1].lower() if '.' in audio_file.filename else None
    if not allowed_file(audio_file.filename):
        return jsonify({'error': 'Unsupported file format', 'extension': file_extension}), 400

    filename = secure_filename(audio_file.filename)
    filepath = os.path.join(uploads_dir, filename)
    audio_file.save(filepath)

    # Debug: Log file path and extension
    print("File saved:", filepath, "Extension:", file_extension)

    # Assume transcribe_audio and process_definition functions exist
    transcription = transcribe_audio(filepath)
    target_word = request.form.get('target_word')
    if not target_word:
        return jsonify({'error': 'No target word provided'}), 400
    evaluation = process_definition(transcription, target_word)
    score_int, tip_str = parse_evaluation(evaluation)
    last_reviewed = session['last_reviewed']
    print(f"last reviewed from process_audio() is {last_reviewed}")
    review_interval = session['review_interval']
    calculate_next_review(last_reviewed, review_interval, score_int)
    # Clean up: Remove the saved audio file after processing
    os.remove(filepath)
    redirect_url = url_for('study.display_results', transcription=transcription, tip_str=tip_str)
    return jsonify({'redirect': redirect_url})
    #return render_template('results.html', transcription=transcription, evaluation=evaluation)

@bp.route('/results')
def display_results():
    transcription = request.args.get('transcription')
    tip_str = request.args.get('tip_str')
    return render_template('results.html', transcription=transcription, tip_str=tip_str)

def transcribe_audio(audio_file_path):
    # Uses OpenAI's Whisper to transcribe the audio file to text.

    audio_file = open(audio_file_path, "rb")
    try:
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        transcription = response.text 
        logging.info("Transcription:", transcription)
        return transcription
    except Exception as e:
        logging.error("An error occurred during transcription:", str(e))
        return None


def process_definition(transcription, target_word):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Adjusted to use a chat model identifier
            messages=[
                {"role": "system", "content": "You are a helpful assistant who specializes in the english language."},
                {"role": "user", "content": f"How accurate is this definition of the '{target_word}? Rate on a scale from 0 (forgot) to 5 (perfect recall). Reply in the format '[a single int rating], [a string tips to improve my definition]? \"{transcription}\""}
            ]
        )
        evaluation = response.choices[0].message.content
        logging.info(f"Evaluation: {evaluation}")
        logging.info("testing log")
        return evaluation
    except Exception as e:
        logging.error(f"An error occurred during processing: {e}")
        return "An error occurred during evaluation."

def update_db(word_id, performance_rating, review_interval, next_review_date):
    data = {
        "easiness_factor": performance_rating,
        "review_interval": review_interval,
        "next_review_date": next_review_date
    }
    response = current_app.supabase.table("user_words").update(data).eq("word_id", word_id).execute()
    return True


def parse_evaluation(evaluation):
    # Split the evaluation into score and tip
    parts = evaluation.split(',', 1)  # Only split at the first comma
    score_int = int(parts[0].strip()) if len(parts) > 0 else 0
    tip_str = parts[1].strip() if len(parts) > 1 else ""
    return score_int, tip_str

def calculate_next_review(last_reviewed, review_interval, performance_rating):
    # Update the easiness factor, review interval based on the performance
    if performance_rating >= 3:
        # Correct response
        if review_interval == 0:
            review_interval = 1  # Start with 1 day if it's the first review
        elif review_interval == 1:
            review_interval = 6  # Move to approximately a week
        else:
            # Increase interval by a factor (usually 1.5 to 2.5)
            review_interval = round(review_interval * 1.6)
    else:
        # Incorrect response, reset interval
        review_interval = 1

    # Calculate the next review date
    print(f"the last reviewed date is {last_reviewed}")
    print(f"the review_interval is {review_interval}")
    date_format = '%Y-%m-%d'
    y = datetime.datetime.strptime(last_reviewed, date_format).date()
    x = y + datetime.timedelta(days=review_interval)
    next_review_date = x.isoformat()
    word_id = session['word_id']
    update_db(word_id, performance_rating, review_interval, next_review_date)
    return True
    #return next_review_date