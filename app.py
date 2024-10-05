import os
import time
import random
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv(""))

# In-memory storage for chat messages
chat_history = [
    {"role": "assistant", "content": "Hello! I'm the AI-powered Power Apps Bug Tracker Bot. How can I help you today?"}
]

def exponential_backoff(attempt):
    return min(32, 2 ** attempt) + random.random()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '').strip()
        
        if not user_message:
            return jsonify({"response": "Please enter a valid message."}), 400
        
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

if __name__ == '__main__':
    app.run(debug=True)