import os, json
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret-key-for-session"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# JSON 파일 로딩
POSTS_FILE = "posts.json"
GALLERY_FILE = "gallery.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

posts = load_json(POSTS_FILE)
gallery = load_json(GALLERY_FILE)

# -------------------- 라우팅 -------------------- #
@app.route("/")
def index():
    return render_template("index.html")

# 커뮤니티
@app.route("/community", methods=["GET","POST"])
def community():
    if request.method == "POST":
        nickname = request.form.get("nickname")
        title = request.form.get("title")
        content = request.form.get("content")
        if nickname and title and content:
            post = {"nickname": nickname, "title": title, "content": content, "comments": [], "likes": 0}
            posts.append(post)
            save_json(POSTS_FILE, posts)
        return redirect(url_for("community"))
    return render_template("community.html", posts=posts)

# 댓글 추가
@app.route("/community/comment/<int:post_idx>", methods=["POST"])
def comment(post_idx):
    comment_text = request.form.get("comment")
    nickname = request.form.get("nickname")
    if 0 <= post_idx < len(posts) and comment_text and nickname:
        posts[post_idx]["comments"].append({"nickname": nickname, "content": comment_text})
        save_json(POSTS_FILE, posts)
    return redirect(url_for("community"))

# 좋아요
@app.route("/community/like/<int:post_idx>")
def like(post_idx):
    if 0 <= post_idx < len(posts):
        posts[post_idx]["likes"] += 1
        save_json(POSTS_FILE, posts)
    return redirect(url_for("community"))

# 팬아트 갤러리
@app.route("/gallery", methods=["GET","POST"])
def gallery_page():
    if request.method == "POST":
        nickname = request.form.get("nickname")
        file = request.files.get("image")
        if nickname and file:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            gallery.append({"nickname": nickname, "filename": filename})
            save_json(GALLERY_FILE, gallery)
        return redirect(url_for("gallery_page"))
    return render_template("gallery.html", gallery=gallery)

# -------------------- 실행 -------------------- #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
