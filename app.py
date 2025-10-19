from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "AREXMADO 공식 Flask 사이트입니다!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
