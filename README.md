# Book Buddy

A small full-stack app for tracking what you read. Add books, update how far you've got, see your reading stats, and write a review when you finish. Long reviews get a short AI-generated blurb (Verdict / Best for / Skip if).

Built for the Sayone Tech Full Stack (Fresher) coding task.

Demo video: add the link here  
Full project documentation: [docs/PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md)

## Features

### Core (from the task)

- Add books with title, author, genre, status (reading / completed / wishlist) and total pages
- Update reading progress by page number. A progress bar shows the percentage, and reaching the last page marks the book as completed automatically
- Filter the list by status: All, Reading, Completed, Wishlist
- Reading stats: total books, books being read, books completed, % completed, and a books-by-genre breakdown
- Star rating (1 to 5) and personal notes for completed books

### AI feature (built in n8n)

- When you save a detailed review (100+ characters) on a completed book, the app sends your notes and rating to an n8n workflow. GPT-4o-mini condenses them into a short blurb that is saved with the book and shown on the card
- The AI only sees your rating and notes, never the book title, so it can't invent details about a book
- If the AI step fails or n8n is not set up, your notes and rating are still saved

### Extras

- Docker setup: one image builds the React app and serves it from Flask
- The n8n workflow is exported in `docs/n8n-workflow.json` so it can be imported and inspected
- A delete endpoint exists in the API (`DELETE /api/books/<id>`), but there is no delete button in the UI yet

## Tech stack

| Part | Choice |
|---|---|
| Frontend | React (Vite), plain CSS |
| Backend | Python, Flask, Flask-SQLAlchemy |
| Database | SQLite |
| AI | n8n Cloud workflow calling OpenAI gpt-4o-mini |
| Packaging | Docker (multi-stage build, gunicorn) |

## Project structure

```text
book-buddy/
├── backend/
│   ├── app.py               # Flask app: Book model, API routes, n8n call
│   ├── requirements.txt
│   └── .env.example         # copy to .env and fill in
├── frontend/
│   └── src/
│       ├── App.jsx          # stats, add-book form, filter tabs, book cards
│       └── App.css
├── docs/
│   ├── PROJECT_DOCUMENTATION.md
│   └── n8n-workflow.json    # AI workflow, importable into n8n
├── Dockerfile
├── .dockerignore
└── README.md
```

## Setup

### Option A: Docker (quickest)

You need Docker installed. From the repo root:

```bash
cp backend/.env.example backend/.env
docker build -t book-buddy .
docker run -d --name book-buddy -p 5000:5000 --env-file backend/.env -v book-buddy-data:/app/backend/instance book-buddy
```

Then open http://localhost:5000

`backend/.env` has to exist, but the AI summary is optional. With the placeholder value the app works normally and just skips summaries. See [AI setup](#ai-setup-optional) to turn them on.

The volume (`-v book-buddy-data:...`) keeps your books when the container is restarted or rebuilt.

To stop and remove it:

```bash
docker rm -f book-buddy
```

If port 5000 is busy, use `-p 8080:5000` and open http://localhost:8080.

If the build can't download npm packages (a Docker DNS/network issue on some machines), try:

```bash
docker build --network=host -t book-buddy .
```

### Option B: Run locally (two terminals)

You need Python 3.10+ and Node.js 20+ (the Docker build uses Python 3.12 and Node 22).

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # optional, see AI setup
python app.py
```

The API runs at http://127.0.0.1:5000. The SQLite database is created automatically in `backend/instance/`.

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the address Vite prints, usually http://localhost:5173. In development the frontend calls the API at http://127.0.0.1:5000/api, so keep the backend running.

## AI setup (optional)

The summary feature needs your own n8n workflow and OpenAI credentials, so it is off until you set this up. Everything else works without it.

1. In n8n (Cloud or self-hosted), go to Workflows → Import from file and choose `docs/n8n-workflow.json`.
2. Open the OpenAI Chat Model node and select your own OpenAI credentials (the model is gpt-4o-mini).
3. Switch the workflow to Active, open the Webhook node and copy the Production URL (not the Test URL).
4. Put it in `backend/.env`:

   ```env
   N8N_SUMMARY_URL=https://your-n8n-host/webhook/book-summary
   ```

5. Restart the backend (or re-run the Docker container with `--env-file backend/.env`).

Try it: set a book's progress to its last page, give it a star rating, write a review of 100+ characters and click **Save notes & rating**. The AI summary box appears after a few seconds.

## API

| Method | Endpoint | What it does |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/books` | List books, newest first. Optional `?status=reading` filter |
| POST | `/api/books` | Add a book (title and author required) |
| PATCH | `/api/books/<id>` | Update any fields (progress, status, rating, notes...). Reaching the last page marks the book completed |
| DELETE | `/api/books/<id>` | Delete a book |
| GET | `/api/stats` | Totals, counts by status and genre, % completed |

More detail, including the data model and the AI flow, is in the [project documentation](docs/PROJECT_DOCUMENTATION.md).

## Known limitations

- No user accounts: it is a single shared list
- No automated tests yet; I tested the flows by hand
- Books can only be deleted through the API, not from the UI
- Genre is free text, so "Self help" and "Self-help" are counted as different genres in the stats
- If the API is unreachable, the UI doesn't show an error message
- Title, author and total pages can't be edited after a book is added

## Author

Vaishnav
