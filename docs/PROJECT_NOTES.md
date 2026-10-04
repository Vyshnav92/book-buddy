# Project Notes
## Decisions
- Backend: Flask + SQLite (chosen because it's what I know)
- AI feature: summary from notes, built as an n8n workflow
## Progress log
- Step 1: repo initialised
- Step 2: Book model (SQLite via SQLAlchemy) and CRUD API: GET/POST /api/books, PATCH/DELETE /api/books/<id>. Hitting the last page auto-completes a book.
- Step 3: React frontend scaffolded with Vite
- Step 4: First UI: add-book form, book cards with progress bar, and progress update.
- Step 5: Added filter tabs (All/Reading/Completed/Wishlist). Filtering happens in the browser from the already-loaded list, so no extra API call is needed.
- Step 6: Added /api/stats (total, count by status, count by genre, % completed = completed books / total books). Frontend shows stat cards and a books-by-genre bar list; stats refresh every time the book list reloads.
- Step 7: Added star rating (1-5) and personal notes for completed books. Saved through the existing PATCH /api/books/<id> route; no backend change was needed.
- Step 8A: Built n8n Cloud workflow (Webhook -> Basic LLM Chain with gpt-4o-mini -> Respond to Webhook). Condenses the user's notes into a short Verdict / Best for / Skip if blurb under 40 words, using only the notes. Workflow exported to docs/n8n-workflow.json.
- Step 8B: Flask PATCH route saves notes/rating first, then calls the n8n webhook (URL kept in backend/.env, not committed) and stores the result in a new Book.ai_summary column. Notes under 100 characters skip the AI call, and any AI failure leaves the notes saved.
- Step 8C: Review box prompts for a detailed review; the Save button shows "Saving..." while the AI call runs; the card shows an "AI summary" box (Verdict / Best for / Skip if) that persists after refresh.
- Step 9: Docker: single multi-stage Dockerfile (Node builds the React app, Python runs Flask via gunicorn and serves it). Secrets come from --env-file at runtime and are excluded by .dockerignore; SQLite data lives in a named volume.
