from flask import Flask, request, render_template, redirect, url_for
import sqlite3
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
import speech_recognition as sr

app = Flask(__name__)

# Home page route
@app.route('/')
def home():
    return render_template('login.html')

# Login route
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if verify_user(username, password):
        return redirect(url_for('welcome', username=username))
    else:
        return render_template('login.html', error="Invalid username or password")

# Welcome page route
@app.route('/welcome')
def welcome():
    username = request.args.get('username')
    return render_template('home.html', username=username)

# Verify user function
def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users_data WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return False
    return row[0] == password

# Speech recognition route with error handling
@app.route('/speech', methods=['POST'])
def recognize_speech_from_mic():
    fs = 44100  # Sample rate
    seconds = 5  # Duration of recording

    # Get the username from the request
    username = request.form.get('username')

    if username is None:
        return render_template('home.html', error="Username is missing.")

    print("Recording...")
    try:
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')  # Change channels to 1 for mono
        sd.wait()  # Wait until recording is finished
        print("Recording complete.")
    except Exception as e:
        print(f"Error during recording: {e}")
        return render_template('home.html', error="Error during recording. Please try again.", username=username)

    # Save the recording to a WAV file
    wav.write("output.wav", fs, myrecording)  # Save as WAV file

    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile('output.wav')

    try:
        with audio_file as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)

        # Save transcription to the database
        save_transcription(username, text)

        return render_template('home.html', speech_text=text, username=username)
    except sr.UnknownValueError:
        return render_template('home.html', error="Sorry, I could not understand the audio.", username=username)
    except sr.RequestError as e:
        return render_template('home.html', error=f"Could not request results from Google Speech Recognition service; {e}", username=username)

# Create users_data table if it doesn't exist
def create_users_data_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Create user_logs table if it doesn't exist
def create_user_logs_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        log_message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

# Save new user and log the action
def save_new_user(username, email, password):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users_data (username, email, password) VALUES (?, ?, ?)', 
                       (username, email, password))
        cursor.execute('INSERT INTO user_logs (username, log_message) VALUES (?, ?)', 
                       (username, 'Account created'))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving new user: {e}")
        return False

def create_transcription_logs_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transcription_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        transcription TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("transcription log table created")
    conn.commit()
    conn.close()

def save_transcription(username, transcription):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO transcription_logs (username, transcription) VALUES (?, ?)', 
                       (username, transcription))
        print(f"transcription saved {transcription} by {username}")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving transcription: {e}")

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password == confirm_password:
            if save_new_user(username, email, password):
                return redirect(url_for('home'))
            else:
                return render_template('register.html', error="Error creating account.")
        else:
            return render_template('register.html', error="Passwords do not match.")
    return render_template('register.html')

if __name__ == '__main__':
    create_users_data_table()
    create_user_logs_table()
    app.run(debug=True)
