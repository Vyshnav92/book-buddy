# Project Notes
## Decisions
- Backend: Flask + SQLite (chosen because it's what I know)
- AI feature: summary from notes, built as an n8n workflow
## Progress log
- Step 2: repo initialised
- Step 4: Book model (SQLite via SQLAlchemy) and CRUD API: GET/POST /api/books, PATCH/DELETE /api/books/<id>. Hitting the last page auto-completes a book.
- Step 5: React frontend scaffolded with Vite
- Step 6: First UI: add-book form, book cards with progress bar, and progress update.
- Step 7: Added filter tabs (All/Reading/Completed/Wishlist). Filtering happens in the browser from the already-loaded list, so no extra API call is needed.
- Step 8: Added /api/stats (total, count by status, count by genre, % completed = completed books / total books). Frontend shows stat cards and a books-by-genre bar list; stats refresh every time the book list reloads.
- Step 9: Added star rating (1-5) and personal notes for completed books. Saved through the existing PATCH /api/books/<id> route; no backend change was needed.
- Step 10A: Built n8n Cloud workflow (Webhook -> Basic LLM Chain with gpt-4o-mini -> Respond to Webhook). Condenses the user's notes into a short Verdict / Best for / Skip if blurb under 40 words, using only the notes. Workflow exported to docs/n8n-workflow.json.
