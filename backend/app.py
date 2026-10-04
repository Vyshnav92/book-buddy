import os
from datetime import datetime
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books.db"
db = SQLAlchemy(app)

VALID_STATUSES = ["reading", "completed", "wishlist"]

load_dotenv()
N8N_SUMMARY_URL = os.getenv("N8N_SUMMARY_URL")
MIN_NOTES_LENGTH = 100


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100), default="Other")
    status = db.Column(db.String(20), default="wishlist")
    total_pages = db.Column(db.Integer, default=0)
    current_page = db.Column(db.Integer, default=0)
    rating = db.Column(db.Integer)
    notes = db.Column(db.Text)
    ai_summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    finished_at = db.Column(db.DateTime)

    def to_dict(self):
        percent = round(self.current_page / self.total_pages * 100) if self.total_pages else 0
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "genre": self.genre,
            "status": self.status,
            "total_pages": self.total_pages,
            "current_page": self.current_page,
            "percent": percent,
            "rating": self.rating,
            "notes": self.notes,
            "ai_summary": self.ai_summary,
            "created_at": self.created_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


def generate_summary(book):
    """Ask the n8n workflow for a short summary of the book's notes.
    Returns the summary text, or None if it can't be generated."""
    if not N8N_SUMMARY_URL:
        return None
    try:
        response = requests.post(
            N8N_SUMMARY_URL,
            json={"rating": book.rating, "notes": book.notes},
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get("summary")
    except (requests.RequestException, ValueError):
        return None


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/books", methods=["GET"])
def list_books():
    status = request.args.get("status")
    query = Book.query
    if status:
        query = query.filter_by(status=status)
    books = query.order_by(Book.created_at.desc()).all()
    return jsonify([b.to_dict() for b in books])


@app.route("/api/books", methods=["POST"])
def add_book():
    data = request.get_json()
    if not data.get("title") or not data.get("author"):
        return jsonify({"error": "title and author are required"}), 400
    status = data.get("status", "wishlist")
    if status not in VALID_STATUSES:
        return jsonify({"error": "invalid status"}), 400
    book = Book(
        title=data["title"],
        author=data["author"],
        genre=data.get("genre", "Other"),
        status=status,
        total_pages=data.get("total_pages", 0),
    )
    db.session.add(book)
    db.session.commit()
    return jsonify(book.to_dict()), 201


@app.route("/api/books/<int:book_id>", methods=["PATCH"])
def update_book(book_id):
    book = db.get_or_404(Book, book_id)
    data = request.get_json()
    for field in ["title", "author", "genre", "status", "total_pages",
                  "current_page", "rating", "notes"]:
        if field in data:
            setattr(book, field, data[field])
    if book.total_pages and book.current_page >= book.total_pages:
        book.status = "completed"
    if book.status == "completed" and not book.finished_at:
        book.finished_at = datetime.now()
    db.session.commit()  # save everything first so the notes are never lost

    if "notes" in data or "rating" in data:
        if book.notes and len(book.notes.strip()) >= MIN_NOTES_LENGTH:
            book.ai_summary = generate_summary(book)
        else:
            book.ai_summary = None
        db.session.commit()

    return jsonify(book.to_dict())


@app.route("/api/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    book = db.get_or_404(Book, book_id)
    db.session.delete(book)
    db.session.commit()
    return "", 204


@app.route("/api/stats")
def stats():
    books = Book.query.all()
    total = len(books)

    by_status = {s: len([b for b in books if b.status == s]) for s in VALID_STATUSES}

    by_genre = {}
    for b in books:
        by_genre[b.genre] = by_genre.get(b.genre, 0) + 1

    percent_completed = round(by_status["completed"] / total * 100) if total else 0

    return jsonify({
        "total": total,
        "by_status": by_status,
        "by_genre": by_genre,
        "percent_completed": percent_completed,
    })


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
