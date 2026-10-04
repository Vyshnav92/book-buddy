# Book Buddy: Project Documentation

Author: Vaishnav  
Task: Sayone Tech Full Stack (Fresher) coding task

This document explains what I built, how the parts fit together, why I made the choices I did, and what is still missing. For setup steps and the feature list, see the [README](../README.md).

## 1. Overview

Book Buddy is a reading tracker. You add books, update your progress page by page, watch the stats change, and write a review when you finish a book. If the review is detailed, an AI workflow turns it into a three-line blurb that stays on the book's card.

I kept the scope small on purpose: the four required features first, a working prototype early, then the AI feature, then Docker.

## 2. Requirements coverage

| Requirement from the task | Status | Where |
|---|---|---|
| Add books with title, author, genre, status | Done | `POST /api/books`, add-book form |
| Update reading progress | Done | `PATCH /api/books/<id>`, number box and progress bar on each card |
| View reading stats (% completed, books by genre) | Done | `GET /api/stats`, stat cards and genre bars |
| Personal notes or ratings for completed books | Done (both) | Star rating and notes box on completed cards |
| Frontend in React | Done | `frontend/` (Vite) |
| Backend in Python | Done | Flask, `backend/app.py` |
| SQLite or PostgreSQL | Done | SQLite via Flask-SQLAlchemy |
| Optional AI: summary from user notes | Done | n8n workflow with `gpt-4o-mini` |
| Optional: deployment | Partly | Dockerised and runs locally; not hosted online |
| Optional: user login | Not done | |
| Optional: ISBN import | Not done | |
| Optional: graph of reading over time | Not done | Stats show a bar breakdown by genre, not a time graph |
| Optional: AI book reviews | Not done | |

## 3. Architecture

```
React frontend -- /api requests --> Flask backend
                                      |
                                      +-- SQLAlchemy --> SQLite
                                      |                 backend/instance/books.db
                                      |
                                      +-- For reviews of 100+ characters:
                                          n8n webhook --> OpenAI gpt-4o-mini
                                          summary returns to Flask and is saved
```

In development, React (port 5173) and Flask (port 5000) run separately, and CORS is enabled in Flask. In Docker, the React app is built into static files and Flask serves them, so everything lives at one address (http://localhost:5000) and the frontend uses the relative path `/api`.

## 4. Tech stack and why

- **React with Vite:** the task requires React, and Vite gives a quick dev server and a simple build. I used plain CSS to keep the styling easy to follow.
- **Flask:** the Python framework I'm most comfortable with. For a handful of endpoints it is all that's needed.
- **SQLite with Flask-SQLAlchemy:** no database server to install, and the `Book` model is a normal Python class.
- **n8n:** I already know it, and it keeps the AI prompt and model outside the app code, so it can be changed without touching Flask.
- **Docker:** so a reviewer can run the whole project without installing Python or Node.

## 5. Database

One table, `book`:

| Column | Type | Notes |
|---|---|---|
| `id` | integer | primary key |
| `title` | string(200) | required |
| `author` | string(200) | required |
| `genre` | string(100) | defaults to "Other" |
| `status` | string(20) | `reading`, `completed` or `wishlist` |
| `total_pages` | integer | defaults to 0 |
| `current_page` | integer | defaults to 0 |
| `rating` | integer | 1 to 5, empty until rated |
| `notes` | text | the user's review |
| `ai_summary` | text | AI blurb, empty if not generated |
| `created_at` | datetime | set when the book is added |
| `finished_at` | datetime | set once, when the book becomes completed |

The progress percentage is not stored. It is calculated from `current_page` and `total_pages` each time a book is sent to the frontend. The tables are created on startup with `db.create_all()`; I did not add a migrations tool for a project this small.

## 6. API

All routes are under `/api`.

- `GET /health`: returns `{"status": "ok"}`.
- `GET /books`: all books, newest first. `?status=reading|completed|wishlist` filters by status.
- `POST /books`: body with `title` and `author` (required), plus optional `genre`, `status`, `total_pages`. Returns the new book with `201`. Missing title or author, or an invalid status, returns `400`.
- `PATCH /books/<id>`: send only the fields you want to change (`title`, `author`, `genre`, `status`, `total_pages`, `current_page`, `rating`, `notes`). Two things happen automatically: reaching the last page sets the status to `completed`, and `finished_at` is stamped the first time a book is completed. An unknown id returns `404`.
- `DELETE /books/<id>`: removes a book, returns `204`.
- `GET /stats`: returns the shape below.

```json
{
  "total": 5,
  "by_status": { "reading": 2, "completed": 2, "wishlist": 1 },
  "by_genre": { "Self-help": 2, "Fiction": 3 },
  "percent_completed": 40
}
```

## 7. Frontend

The UI is one page, built from a few pieces in `src/App.jsx`:

- **App:** holds the state (`books`, `form`, `filter`, `stats`) and every API call. `loadBooks()` fetches the books and the stats together, and it runs on page load and after every change, so the screen never shows stale numbers.
- **Stats area:** four stat cards (total, reading, completed, % completed) and a bar per genre.
- **Add-book form:** a controlled form that POSTs to the API.
- **Filter tabs:** All, Reading, Completed, Wishlist. Filtering is done in the browser on the list that is already loaded.
- **BookCard:** progress bar and page input, plus (for completed books) the star rating, notes box, a Save button that shows "Saving..." while the AI runs, and the AI summary box.

The API address is `http://127.0.0.1:5000/api` in development and `/api` in the production build (decided with `import.meta.env.PROD`).

## 8. The AI feature

**What it does:** when a completed book's review is saved with 100 or more characters, the app produces a short blurb like:

```
Verdict: Practical and useful, but the last third drags.
Best for: Students and people starting a new job who want simple routines.
Skip if: You've already read a lot on productivity.
```

**Flow:**

1. The user saves rating and notes. Flask saves them to the database first.
2. If the notes are 100+ characters, Flask POSTs `rating` and `notes` to the n8n webhook (timeout 30 seconds).
3. The n8n workflow has three nodes: **Webhook** → **Basic LLM Chain** (OpenAI `gpt-4o-mini`) → **Respond to Webhook**, which returns `{ "summary": "..." }`.
4. Flask stores the summary in `ai_summary` and returns the updated book. If the notes are shorter than 100 characters, any old summary is cleared.

**The prompt** asks for a fixed three-line format under 40 words, using only the notes, without copying the user's sentences, and without mentioning the book's title or author. My first version asked for a "2-3 sentence summary" and the model mostly repeated my notes back, so I changed it to a strict format with a word limit.

**Why I kept it safe:**
- The model never receives the title or author, only the rating and notes, so it can't make up facts about a book, and a test title like "test1" works fine.
- The notes are saved before the AI is called. If n8n is down or slow, the function returns nothing and the card simply shows no summary.
- Short notes skip the AI call. A one-line note doesn't need summarising, and it saves credits.
- The webhook URL lives in `backend/.env` (ignored by Git and Docker). `backend/.env.example` shows the format. The workflow export in `docs/n8n-workflow.json` contains no credentials.

**Other AI ideas I considered:** book recommendations and a completion-date prediction. I chose the notes summary because it depends only on what the user wrote, so it can't suggest books that don't exist.

## 9. Docker

One multi-stage `Dockerfile` at the repo root:

1. **Stage 1** (Node 22) runs `npm ci` and `npm run build` to produce the static React files.
2. **Stage 2** (Python 3.12 slim) installs the backend requirements plus gunicorn, copies the backend and the built frontend, and runs as a non-root user.

gunicorn runs with one worker and four threads, which suits SQLite, and a 60-second timeout so the AI call has room. A health check calls `/api/health`. `.dockerignore` keeps `.env`, the local database, `node_modules` and `venv` out of the image, so secrets are never baked in. Data is kept in a named volume mounted at `/app/backend/instance`.

For this to work in one container, three small changes were needed in the app: Flask serves the built frontend, the frontend uses a relative API path in production, and `db.create_all()` runs on import (gunicorn doesn't run the `__main__` block).

### Docker DNS Issue

Book Buddy may start normally in Docker while AI summaries fail because the container cannot resolve external domains. This can happen when Docker DNS is not working correctly.

#### Symptoms

- The app loads, and `backend/.env` is loaded correctly.
- AI summaries work when Flask runs locally but fail in Docker.
- DNS checks inside the container may show `Temporary failure in name resolution`.

#### Fix

Start the container with explicit DNS servers:

```bash
docker run -d \
  --name book-buddy \
  -p 5000:5000 \
  --dns 8.8.8.8 \
  --dns 1.1.1.1 \
  --env-file backend/.env \
  -v book-buddy-data:/app/backend/instance \
  book-buddy
```

The `--dns` options provide resolvers so the container can reach external services such as the n8n Cloud webhook.

#### Quick check

Check DNS resolution inside the container:

```bash
docker exec book-buddy getent hosts google.com
```

An IP address means DNS resolution is working. To check access to n8n:

```bash
docker exec book-buddy python -c "import requests; print(requests.get('https://vyshnav92.app.n8n.cloud', timeout=10).status_code)"
```

A response such as `200` confirms the container can reach n8n. If the app works locally and Docker DNS is the only issue, fix the container's DNS configuration first; Flask and n8n do not need configuration changes.

## 10. Git

I committed after each working step, so the history reads as the build order. Commit messages follow a simple prefix style: `feat:` for features, `chore:` for setup, `docs:` for documentation. Secrets are never committed: `.env` is in `.gitignore`, and `.env.example` is committed instead.

## 11. Decisions and trade-offs

- **Prototype first:** I built add, list and progress update end to end before touching stats, notes or AI, so there was always a working app.
- **Stats on the server:** the backend counts books and returns one small object, so the frontend only displays numbers.
- **Filtering in the browser:** the list is small, so filtering the loaded books avoids extra requests. The API also supports `?status=` for larger lists.
- **Both notes and ratings:** the task says notes or ratings. I did both because the notes feed the AI feature.
- **Simple schema changes:** I added the `ai_summary` column by recreating the development database, since there was only test data. A real app would use migrations.
- **No frontend framework extras:** no router, state library or CSS framework. It is one page and the state is small.

## 12. Known limitations and next steps

Honest list of what's missing:

- No user login, so there is one shared list.
- No automated tests. Everything was tested by hand (checklist below).
- Title, author and total pages can't be edited after adding a book.
- If the API is unreachable, the page shows no error message.
- All frontend code is in `App.jsx`. It would be cleaner split into separate component files, with the API calls in their own module.
- The AI call happens inside the save request, so saving a long review takes a few seconds.

What I'd do next: split the frontend into components, add a delete button and an error banner, add backend tests with pytest, then user login and a reading-over-time graph.

## 13. Manual test checklist

1. Add a book with a total page count. It appears as a card and the stats update.
2. Set progress to part of the book: the bar and percentage change.
3. Set progress to the last page: the status becomes `completed` and the review section appears.
4. Click each filter tab: only matching books show, and an empty tab shows a message.
5. Save a rating and a review of 100+ characters: "Saving..." appears, then the AI summary box.
6. Refresh the page: rating, notes and summary are still there.
7. Shorten the review below 100 characters and save: the summary disappears, the notes stay.
8. Docker: build, run, add a book, run `docker restart book-buddy`: the book is still there.

## 14. Development log

1. **Repo and Git setup:** created the repo with a README, `.gitignore` and this docs folder.
2. **Flask skeleton:** a minimal app with a health route to confirm the backend runs.
3. **Database and API:** the `Book` model and the add, list, update and delete routes, with auto-complete at the last page.
4. **React scaffold:** created the frontend with Vite.
5. **First UI:** add-book form, book cards with a progress bar, and progress update. This was the working prototype.
6. **Filter tabs:** All, Reading, Completed, Wishlist.
7. **Stats:** `/api/stats` on the backend, with stat cards and genre bars on the frontend.
8. **Notes and ratings:** star rating and notes box on completed books.
9. **n8n workflow:** webhook, AI chain and response nodes, tuned the prompt until the summary was short instead of a copy of the notes, and exported to `docs/n8n-workflow.json`.
10. **Summary in the backend:** the webhook URL in `.env`, a new `ai_summary` column, save-first-then-summarise logic in the PATCH route.
11. **Summary in the UI:** a prompt for detailed reviews, a "Saving..." button state and the AI summary box.
12. **Docker:** multi-stage Dockerfile, `.dockerignore`, and the small changes that let Flask serve the built frontend.
