# 🌐 Web Scraping & Data Extraction System

> A Flask-based Web Application that automatically extracts unstructured data from websites and converts it into structured, reusable formats such as **CSV, Excel, JSON, and SQL**.

---

# 📖 Project Overview

The **Web Scraping & Data Extraction System** is a web-based application developed using **Python, Flask, BeautifulSoup, Requests, SQLAlchemy, MySQL, and Bootstrap 5**.

The application allows users to enter a website URL, scrape important information from that webpage, store the extracted data into a MySQL database, and export the collected data into multiple formats.

This project demonstrates web scraping, database management, responsive web development, and software engineering principles.

---

# 🎯 Mission Statement

> Automatically extract and gather unstructured data from websites and transform it into a structured, usable form.

---

# ✨ Features

- Responsive Bootstrap Dashboard
- Website URL Validation
- Automatic HTML Download
- HTML Parsing using BeautifulSoup
- Store Data in MySQL Database
- Search Scraped Websites
- Delete Records
- Pagination Support
- Export Data to:
  - CSV
  - Excel (.xlsx)
  - JSON
  - SQL
- Logging System
- Exception Handling
- Responsive UI
- MVC Architecture
- Repository Pattern
- Flask Blueprints

---

# 🛠 Technology Stack

| Category | Technology |
|----------|------------|
| Programming Language | Python 3.13 |
| Framework | Flask |
| Database | MySQL 9.x |
| ORM | SQLAlchemy |
| HTML Parser | BeautifulSoup 4 |
| HTTP Library | Requests |
| Frontend | HTML5, CSS3, Bootstrap 5 |
| JavaScript | Vanilla JavaScript |
| IDE | Visual Studio Code |

---

# 📂 Project Structure

```
WebScraper_Project/

│
├── app/
│   │
│   ├── controllers/
│   ├── models/
│   ├── repositories/
│   ├── routes/
│   ├── services/
│   ├── templates/
│   ├── static/
│   │
│   ├── utils/
│   ├── logs/
│   └── __init__.py
│
├── config.py
├── requirements.txt
├── run.py
├── README.md
├── output/
└── .env
```

---

# 🏗 System Architecture

```
User

        │

        ▼

Flask Routes

        │

        ▼

Controllers

        │

        ▼

Services

        │

        ▼

Repository

        │

        ▼

SQLAlchemy ORM

        │

        ▼

MySQL Database
```

---

# 🔄 System Workflow

```
User

    │

    ▼

Enter Website URL

    │

    ▼

Download HTML

    │

    ▼

BeautifulSoup Parser

    │

    ▼

Extract Data

    │

    ▼

Store in MySQL

    │

    ▼

Dashboard

    │

    ▼

Export CSV / Excel / JSON / SQL
```

---

# 📊 Extracted Information

The system extracts:

- Website Title
- Meta Description
- HTTP Status
- Total Links
- Internal Links
- External Links
- Total Images
- Image Sources
- Headings (H1–H6)
- Paragraphs
- Tables
- Forms
- Scripts

---

# 💾 Export Formats

The scraped data can be exported into:

- CSV
- Excel (.xlsx)
- JSON
- SQL

Generated files are stored inside:

```
output/
```

---

# ⚙ Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/WebScraper_Project.git
```

---

### Move into Project Folder

```bash
cd WebScraper_Project
```

---

### Create Virtual Environment

```bash
python -m venv .venv
```

---

### Activate Virtual Environment

Windows

```bash
.venv\Scripts\activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

---

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Configure MySQL

Create a database:

```sql
CREATE DATABASE webscraper;
```

Update `.env`

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=webscraper
```

---

### Run Application

```bash
python run.py
```

Open:

```
http://127.0.0.1:5000
```

---

# 📷 Screenshots

Add screenshots here after completing the project.

Example:

```
screenshots/

dashboard.png

history.png

about.png

export.png
```

---

# 📌 Project Modules

### Module 1

Controllers

- Main Controller
- Scraper Controller
- History Controller
- Export Controller

### Module 2

Routes

### Module 3

Services

### Module 4

Repository

### Module 5

Frontend

---

# 📚 Python Libraries Used

- Flask
- Requests
- BeautifulSoup4
- SQLAlchemy
- Flask-SQLAlchemy
- Pandas
- OpenPyXL
- python-dotenv
- PyMySQL

---

# 🔒 Error Handling

The system handles:

- Invalid URLs
- Connection Timeout
- HTTP Errors
- Database Errors
- Missing Elements
- Empty Search Results

---

# 📈 Future Scope

- Multi-threaded Scraping
- Selenium Integration
- Login-Based Website Scraping
- Scheduled Automatic Scraping
- REST API
- User Authentication
- Charts & Analytics
- AI-based Data Classification

---

# 👨‍💻 Developer

**Ayush Yadav**

B.Tech Computer Science Engineering

Fourth Semester Mini Project

---

# 📄 License

This project is developed only for educational purposes.

---

# 🙏 Acknowledgement

I would like to thank my project guide, faculty members, and my institution for their continuous support and guidance throughout the development of this project.

---

# ⭐ Project Summary

| Item | Details |
|------|---------|
| Project Name | Web Scraping & Data Extraction System |
| Type | Web Application |
| Language | Python 3.13 |
| Framework | Flask |
| Database | MySQL |
| Frontend | Bootstrap 5 |
| Output | CSV, Excel, JSON, SQL |
| Architecture | MVC + Repository Pattern |
| IDE | Visual Studio Code |

---