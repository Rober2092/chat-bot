import os
import time
import random
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from openai import OpenAI
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv(""))

# In-memory storage for chat messages
chat_history = [
    {"role": "assistant", "content": "Hello! I'm the AI-powered Power Apps Bug Tracker Bot. How can I help you today?"}
]

def exponential_backoff(attempt):
    return min(32, 2 ** attempt) + random.random()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.form.get('message', '').strip()
        
        if not user_message:
            return jsonify({"response": "Please enter a valid message."}), 400

        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                user_message += f"\n[Attachment: {filename}]"

        chat_history.append({"role": "user", "content": user_message})
        
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=chat_history
                )
                bot_response = response.choices[0].message.content.strip()
                chat_history.append({"role": "assistant", "content": bot_response})
                return jsonify({"response": bot_response})
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e
                time.sleep(exponential_backoff(attempt))
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"response": "There was an error processing your request. Please try again later."}), 500

@app.route('/history', methods=['GET'])
def get_history():
    try:
        return jsonify(chat_history)
    except Exception as e:
        print(f"Error retrieving chat history: {e}")
        return jsonify([]), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)