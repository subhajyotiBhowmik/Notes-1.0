import os
import json
import requests
import app
import face_recognition
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, flash, jsonify

app = Flask(__name__)

app.secret_key = b",\xc2\xf0n\xd1'T\x08I\x04P}LW\xe7\xa9\x94p2\xc7/\xe2\x82\\"
app.config['UPLOAD_FOLDER'] = 'uploads/'
DATA_FILE = 'data.json'

uploaded_files = []

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump(uploaded_files, f)

with open(DATA_FILE, 'r') as f:
    uploaded_files = json.load(f)

users = {
    'user1': {'password': 'password1', 'notes_uploaded': 0},
    'user2': {'password': 'password2', 'notes_uploaded': 0}
}  # Mock user data

user_scores = {
    'user1': 0,
    'user2': 0
}  # Mock user scores


@app.route('/')
def index():
    if 'username' in session:
        uploaded = request.args.get('uploaded')
        return render_template('index.html', username=session['username'], files=uploaded_files, uploaded=uploaded)
    return redirect(url_for('login'))


@app.route('/request_notes', methods=['GET', 'POST'])
def request_notes():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        email = request.form['email']
        topic = request.form['topic']
        message = request.form['message']

        # Create a dictionary with the form data
        request_data = {
            'name': name,
            'email': email,
            'topic': topic,
            'message': message
        }

        # Read existing data from the JSON file
        with open('data.json', 'r') as json_file:
            data = json.load(json_file)

        # Append the new request data to the existing data
        data.append(request_data)

        # Write the updated data back to the JSON file
        with open('requests.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)

        # Redirect to confirmation page
        return redirect(url_for('request_confirmation'))

    # Render the request form template
    return render_template('request_form.html')


# Route for the confirmation page
@app.route('/request_confirmation')
def request_confirmation():
    return render_template('request_confirmation.html')

@app.route('/contact_us', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Handle the message (e.g., send email, store in database, etc.)

        flash('Message sent successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('contact_us.html')


@app.route('/download/<filename>')
def download_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


responses = {
    "hello": "Hi there!",
    "how are you?": "I'm good, thank you!",
    "what's your name?": "I'm a chatbot. What's yours?",
    "default": "I'm sorry, I don't understand that."
}

# Function to get the chatbot's response
def get_bot_response(user_message):
    # Convert user message to lowercase
    user_message = user_message.lower()
    # Check if user message exists in responses dictionary
    if user_message in responses:
        return responses[user_message]
    else:
        return responses["default"]

# Define route for chat interface
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        user_message = request.form['user_message']
        bot_response = get_bot_response(user_message)
        return render_template('chat.html', user_message=user_message, bot_response=bot_response)
    return render_template('chat.html')



# Route for displaying nearby colleges and tutors
@app.route('/nearby', methods=['GET'])
def nearby():
    # Render the nearby.html template
    return render_template('nearby.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'username' in session:
        if request.method == 'POST':
            file = request.files['file']
            section = request.form['section']  # Extract section information from the form
            if file and section:
                filename = file.filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                uploaded_files.append({'filename': filename, 'rating': 0, 'section': section, 'username': session[
                    'username']})  # Include section information in the uploaded file entry
                users[session['username']]['notes_uploaded'] += 1
                save_data()
                return redirect(url_for('index', uploaded='done'))
        return render_template('upload.html')
    return redirect(url_for('login'))


@app.route('/rate/<filename>/<int:rating>', methods=['POST'])
def rate_file(filename, rating):
    for file in uploaded_files:
        if file['filename'] == filename:
            file['rating'] = rating
            break
    save_data()
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            if users[username]['password'] == password:
                session['username'] = username
                return redirect(url_for('index'))
            else:
                flash('Incorrect password. Please check your password and try again.', 'error')
        else:
            flash('User does not exist. Please register first.', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username not in users:
            users[username] = {'password': password, 'notes_uploaded': 0}
            user_scores[username] = 0
            save_data()
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/profile')
def profile():
    if 'username' in session:
        username = session['username']
        user_uploaded_notes = [file for file in uploaded_files if file['username'] == username]
        user_score = user_scores[username]
        user_rank = sorted(user_scores.items(), key=lambda x: x[1], reverse=True).index((username, user_score)) + 1
        return render_template('profile.html', username=username, notes=user_uploaded_notes, score=user_score,
                               rank=user_rank)
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(uploaded_files, f)


if __name__ == '__main__':
    app.run(debug=True,port=8000)
