# Book Buddy

## Run with Docker

1. Copy `backend/.env.example` to `backend/.env` and set `N8N_SUMMARY_URL` to your n8n production webhook URL (optional; the app works without it, but AI summaries are disabled).
2. Build and run:

   ```bash
   docker build -t book-buddy .
   docker run -d --name book-buddy -p 5000:5000 --env-file backend/.env -v book-buddy-data:/app/backend/instance book-buddy
   ```

3. Open http://localhost:5000
