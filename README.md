# Chatribe Backend

A modern real-time chat application backend built with Django, Django Channels, and PostgreSQL.

This repository contains the backend code of the **Chatribe** project, which powers the real-time chat features, user authentication, interest requests, and notifications. It is designed to be scalable, secure, and maintainable with support for WebSockets and JWT-based authentication.

---

## ✨ Features

- Users can register and create accounts easily
- JWT-based secure authentication system
- Users can view and search all other registered users
- Ability to send and receive interest requests
- Real-time chat is enabled once both users accept interest
- Online/offline status tracking
- Unread message indicator
- Real-time chat and interest notifications implemented using WebSockets

---

## 🛠 Tech Stack

- Django – for building the backend and APIs
- PostgreSQL – as the relational database
- Django REST Framework – for creating RESTful APIs
- Django Channels – for handling WebSocket connections
- Daphne – ASGI server to support real-time features
- Redis – used as the channel layer backend for WebSocket handling
- JWT – for secure user authentication

---

## ⚙️ How to Set Up

### Clone the repository

```bash
git clone https://github.com/Shamilnk812/chatribe-chat-application-backend.git
```

### Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate #linux
venv/scripts/activate  # windows
```

### Install the dependencies

```bash
pip install -r requirements.txt
```

### Create a .env file in the root directory and add your environment variables

```bash
SECRET_KEY=your-django-secret-key
DEBUG=True
REDIS_URL=your-redis-url
DATABASE_URL=your-database-url
```

### Apply migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Run the development server using Daphne

```bash
daphne chatribe.asgi:application
```

- Open your browser and go to http://localhost:8000
