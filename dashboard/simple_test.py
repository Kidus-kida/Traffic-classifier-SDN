
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "<h1>Connectivity Test Success!</h1><p>If you can see this, Flask is reachable on port 5001.</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
