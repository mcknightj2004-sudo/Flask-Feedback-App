# Comment Manager (Flask)

Flask + SQLite app to store and manage comments (filter, add, edit, delete).
Data can be loaded from `comments.csv` into the database.

Open
Go to: http://127.0.0.1:5000/

API
- GET `/api/comments` (all)
- GET `/api/comments/type/<type>` (filter by type)
- POST `/api/comments` (add)
- PUT `/api/comments/<id>` (update)
- DELETE `/api/comments/<id>` (delete)
- POST `/api/comments/load` (load from `comments.csv`)

## Setup & Run
```bash
pip install -r requirements.txt
python app.py



