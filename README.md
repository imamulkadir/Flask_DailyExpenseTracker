# 💰 Flask Daily Expense Tracker

A lightweight personal expense tracking web app built with **Flask**, featuring category management, analytics, CSV export, and a clean UI — all powered by simple JSON file storage. Perfect for daily budgeting without any database setup!

---

## 📸 Features

- 📝 Add, edit, and delete daily expenses
- 📊 View summaries by day, week, or month
- 📂 Export expenses to CSV
- 📈 Visualize expenses with charts
- 🗂 Manage custom categories
- 📁 JSON-based data storage (no DB required)

---

## 📁 Project Structure

```
Flask_DailyExpencseTracker/
├── app.py                 # Main Flask app
├── templates/             # HTML templates (Jinja2)
│   ├── index.html
│   ├── summary.html
│   ├── analytics.html
│   ├── edit_expense.html
│   └── categories.html
├── static/                # Optional static files (CSS/JS)
├── expenses.json          # Auto-generated file to store expense data
├── categories.json        # Auto-generated file to store category list
├── requirements.txt       # Python dependencies
└── README.md              # Project info and instructions
```

---

## 🚀 Installation & Run Instructions

> 🐍 Python 3.8+ required  
> 💻 Works on Windows, macOS, and Linux

```bash
# 1. Clone the repository
git clone https://github.com/imamulkadir/Flask_DailyExpenseTracker.git
cd Flask_DailyExpenseTracker

# 2. (Optional but recommended) Create a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the Flask app
python app.py

# 5. Open your browser and visit:
http://127.0.0.1:5000
```

---

## 🧪 Demo Features

- Add an expense (with category and amount)
- View today’s and recent expenses
- Summary filter: today, this week, or this month
- Analytics page with daily/monthly charts
- Manage categories (add/delete)
- Export all data to CSV

---

## 📦 Requirements

All dependencies are listed in `requirements.txt`, including:

```
Flask==2.3.3
itsdangerous==2.1.2
Jinja2==3.1.3
Werkzeug==2.3.7
MarkupSafe==2.1.5
```

---

## 📌 Notes

- All data is saved in `expenses.json` and `categories.json` in the project root.
- No database or user login system (designed for single-user use).
- Charts use Chart.js via CDN in the templates (no extra config needed).

---

## ✨ Future Improvements

- User authentication (multi-user support)
- Dark mode UI
- Budget limits & alerts
- PWA support for mobile access

---

## 🧑‍💻 Author

Made with ❤️ by [Imamul Kadir](https://github.com/imamulkadir)

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).
