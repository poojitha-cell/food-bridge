# 🍲 Food Bridge – Food Donation and Sharing Platform

## 📌 Project Overview
Food Bridge is a web-based food donation platform that connects food donors with people who need food. It helps reduce food waste by allowing donors to share surplus food with receivers.

## ✨ Features
- User Registration and Login
- Separate Donor and Receiver Roles
- Donor Dashboard
- Donate Food
- View Available Food
- Request Food Donations
- Donor Request Approval and Rejection
- Receiver My Requests Page
- PostgreSQL Database Integration

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend |
| Flask | Web Framework |
| HTML | Frontend |
| CSS | Styling |
| PostgreSQL | Database |
| Git & GitHub | Version Control |
| Docker | Containerization |
| GitHub Actions | CI Workflow |
| Render | Cloud Deployment |

## 📂 Project Structure

```text
food-bridge/
│
├── app.py
├── requirements.txt
├── Dockerfile
├── compose.yaml
├── .dockerignore
├── .gitignore
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   ├── donate.html
│   ├── available_food.html
│   ├── donor_requests.html
│   └── my_requests.html
│
├── static/
│   └── style.css
│
├── tests/
│   └── test_app.py
│
└── .github/
    └── workflows/
        └── ci.yml
```

## ⚙️ Run Locally

1. Clone the repository:

```bash
git clone https://github.com/poojitha-cell/food-bridge.git
```

2. Open the project folder:

```bash
cd food-bridge
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure the required environment variables:

```text
DATABASE_URL
SECRET_KEY
```

5. Run the application:

```bash
python app.py
```

Open `http://127.0.0.1:5000/` in your browser.

## 🐳 Docker

Build and run the application using Docker Compose:

```bash
docker compose up --build
```

## ☁️ Deployment

Food Bridge is deployed using Render.

- GitHub is used to store and manage the source code.
- Render hosts the Flask web application.
- Render PostgreSQL stores application data.
- Environment variables are configured securely in Render.

## 🔄 DevOps Workflow

1. Develop the application using Python and Flask.
2. Track source-code changes using Git.
3. Push code to GitHub.
4. Use GitHub Actions for the configured CI workflow.
5. Use Docker to containerize the application.
6. Deploy the application using Render.

## 🎯 Conclusion

Food Bridge provides a simple platform for connecting food donors and receivers. It encourages food sharing, reduces food waste, and demonstrates the use of web development and DevOps technologies.

## 👩‍💻 Author

**Mathsa Poojitha**

GitHub: https://github.com/poojitha-cell
