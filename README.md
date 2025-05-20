# 🚀 Simple Game Server

A minimal, lightweight game server built with [FastAPI](https://fastapi.tiangolo.com/), powered by Python 3 and [MongoDB](https://www.mongodb.com/).
---

## 🛠 Features

- User Profile management  
- Authentication (JWT-based)
- Player stat tracking
- REST API with auto-generated docs
- Easily extendable (friends, chat, lobbies, matchmaking)

---

## 🔧 Setup

### 1. Clone the Repo

```bash
git clone https://github.com/jinine/game-server.git
cd game-server
```
### 2. Create and Activate a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
````

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create .env file, set 'your-mongodb-url' to your mongodb url string
```bash
MONGO_URL='your-mongodb-url'
```

### 5. Run the Server

```bash
uvicorn main:app --reload
```

---

## 🧪 API Docs

* Swagger UI → [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc → [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧾 License
MIT -  free to modify, build on and deploy commercially

---

## 💬 Contact / Contribution
Made with ❤️ by Tristan Engen

Feel free to submit an issue! contribution guide will be detailed in a CONTRIBUTION.md file at a future date.

