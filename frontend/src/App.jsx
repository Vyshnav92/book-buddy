import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:5000/api";
const EMPTY_FORM = { title: "", author: "", genre: "", status: "wishlist", total_pages: "" };

function BookCard({ book, onUpdate }) {
  const [page, setPage] = useState(book.current_page);

  return (
    <div className="card">
      <h3>{book.title}</h3>
      <p>{book.author}</p>
      <span className="badge">{book.genre}</span> <span className="badge">{book.status}</span>
      <div className="bar">
        <div className="bar-fill" style={{ width: `${book.percent}%` }}></div>
      </div>
      <small>{book.current_page} / {book.total_pages} pages ({book.percent}%)</small>
      <div className="row">
        <input type="number" value={page} onChange={(e) => setPage(e.target.value)} />
        <button onClick={() => onUpdate(book.id, page)}>Update</button>
      </div>
    </div>
  );
}

function App() {
  const [books, setBooks] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [filter, setFilter] = useState("all")

  async function loadBooks() {
    const res = await fetch(`${API}/books`);
    const data = await res.json();
    setBooks(data);
  }

  useEffect(() => {
    loadBooks();
  }, []);

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    await fetch(`${API}/books`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...form,
        genre: form.genre || "Other",
        total_pages: Number(form.total_pages) || 0,
      }),
    });
    setForm(EMPTY_FORM);
    loadBooks();
  }

  async function updateProgress(id, page) {
    await fetch(`${API}/books/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current_page: Number(page) }),
    });
    loadBooks();
  }

  const visibleBooks =
  filter === "all" ? books : books.filter((b) => b.status === filter);

  return (
    <div className="container">
      <h1>Book Buddy</h1>

      <form className="form" onSubmit={handleSubmit}>
        <input name="title" placeholder="Title" value={form.title} onChange={handleChange} required />
        <input name="author" placeholder="Author" value={form.author} onChange={handleChange} required />
        <input name="genre" placeholder="Genre" value={form.genre} onChange={handleChange} />
        <select name="status" value={form.status} onChange={handleChange}>
          <option value="wishlist">Wishlist</option>
          <option value="reading">Reading</option>
          <option value="completed">Completed</option>
        </select>
        <input name="total_pages" type="number" placeholder="Total pages" value={form.total_pages} onChange={handleChange} />
        <button type="submit">Add Book</button>
      </form>

      <div className="tabs">
  {["all", "reading", "completed", "wishlist"].map((tab) => (
    <button
      key={tab}
      className={filter === tab ? "tab active" : "tab"}
      onClick={() => setFilter(tab)}
    >
      {tab}
    </button>
  ))}
</div>

      {visibleBooks.length === 0 && <p>No books here yet.</p>}

<div className="grid">
  {visibleBooks.map((book) => (
    <BookCard key={book.id} book={book} onUpdate={updateProgress} />
  ))}
</div>
    </div>
  );

}

export default App;
