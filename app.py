from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Replace with your secret key

# Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Helper Functions
def load_json(file_name):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            return json.load(f)
    return []

def save_json(file_name, data):
    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)

# Load/Save Posts
def load_posts():
    return load_json("blog_data.json")

def save_posts(posts):
    save_json("blog_data.json", posts)

# Load/Save Users
def load_users():
    return load_json("user_data.json")

def save_users(users):
    save_json("user_data.json", users)

# Routes
@app.route('/')
def home():
    posts = load_posts()
    categories = set(post.get('category', 'Uncategorized') for post in posts)  # Default to 'Uncategorized' if 'category' is missing
    search_query = request.args.get('search', '').lower()
    filtered_posts = [post for post in posts if search_query in post['title'].lower() or search_query in post['content'].lower()]
    return render_template("index.html", posts=filtered_posts, categories=categories)

@app.route("/post/<int:post_id>")
def view_post(post_id):
    posts = load_posts()
    post = next((post for post in posts if post['id'] == post_id), None)
    if not post:
        return "Post not found", 404
    post['views'] = post.get('views', 0) + 1
    save_posts(posts)
    return render_template("view_post.html", post=post)

@app.route("/create", methods=["GET", "POST"])
def create_post():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        category = request.form["category"]
        image = request.files["image"]

        if image:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        else:
            image_filename = None

        posts = load_posts()
        new_post = {
            "id": len(posts) + 1,
            "title": title,
            "content": content,
            "category": category,
            "image": image_filename,
            "likes": 0,
            "views": 0
        }
        posts.append(new_post)
        save_posts(posts)
        return redirect(url_for("home"))

    return render_template("create_post.html")

@app.route("/like/<int:post_id>")
def like_post(post_id):
    posts = load_posts()
    post = next((post for post in posts if post['id'] == post_id), None)
    if post:
        post['likes'] += 1
        save_posts(posts)
    return redirect(url_for("view_post", post_id=post_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users = load_users()
        user = next((u for u in users if u["username"] == username and u["password"] == password), None)

        if user:
            session["user"] = username
            return redirect(url_for("home"))
        else:
            return "Invalid credentials", 401

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

@app.route("/admin")
def admin_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    posts = load_posts()
    return render_template("admin_dashboard.html", posts=posts)

@app.route("/delete/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    if "user" not in session:
        return redirect(url_for("login"))

    posts = load_posts()
    posts = [post for post in posts if post['id'] != post_id]
    save_posts(posts)
    return redirect(url_for("admin_dashboard"))

# Run the App
if __name__ == "__main__":
    app.run(debug=True)
