from flask import Flask, request, redirect, render_template_string, g
import sqlite3
from datetime import date
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "your_plan.db"
app = Flask(__name__)

PAGE = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Your Plan</title>
<style>
:root{--bg:#f4f7f5;--card:#fff;--ink:#17251e;--muted:#718078;--green:#176b4d;--line:#e2e9e5;--red:#b83b45}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px system-ui,-apple-system,sans-serif}
header{background:var(--green);color:white;padding:24px 18px 20px;border-radius:0 0 24px 24px}
header h1{margin:0;font-size:27px}header p{margin:5px 0 0;opacity:.85}
main{max-width:760px;margin:auto;padding:16px 14px 36px}
.tabs{display:flex;gap:7px;overflow:auto;margin:0 0 16px;padding:3px 0}
.tabs a{white-space:nowrap;text-decoration:none;color:var(--green);background:#e3eee8;border-radius:12px;padding:10px 13px;font-weight:650}
.tabs a.active{background:var(--green);color:white}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:17px;padding:16px;margin-bottom:12px;box-shadow:0 3px 12px #163d2910}
.label{font-size:13px;color:var(--muted)}.amount{font-size:23px;font-weight:750;margin-top:4px;overflow-wrap:anywhere}
h2{font-size:19px;margin:4px 0 14px}h3{font-size:16px;margin:0 0 10px}
form{display:grid;gap:10px}input,select,button{width:100%;font:inherit;border-radius:11px;padding:12px;border:1px solid #d5e0d9;background:white;color:var(--ink)}
button{background:var(--green);color:white;border:0;font-weight:700;cursor:pointer}
.row{display:flex;align-items:center;justify-content:space-between;gap:10px}.muted{color:var(--muted);font-size:13px}
.entry{padding:12px 0;border-bottom:1px solid var(--line)}.entry:last-child{border-bottom:0}
.positive{color:var(--green);font-weight:700}.negative{color:var(--red);font-weight:700}
.progress{height:9px;background:#e6eee9;border-radius:99px;overflow:hidden;margin:10px 0}.progress span{display:block;height:100%;background:var(--green)}
.smallbtn{width:auto;padding:7px 10px;font-size:12px;background:#f8e8e8;color:var(--red)}
@media(min-width:600px){.grid{grid-template-columns:repeat(4,minmax(0,1fr))}.layout{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
</style>
</head>
<body>
<header><h1>Your Plan</h1><p>Your money, organized.</p></header>
<main>
<nav class="tabs">
<a href="/" class="{{ 'active' if tab=='dashboard' else '' }}">Dashboard</a>
<a href="/savings" class="{{ 'active' if tab=='savings' else '' }}">Savings</a>
<a href="/spending" class="{{ 'active' if tab=='spending' else '' }}">Daily Spending</a>
<a href="/income" class="{{ 'active' if tab=='income' else '' }}">Total Income</a>
</nav>
{% if tab=='dashboard' %}
<div class="grid">
<div class="card"><div class="label">Available balance</div><div class="amount">₱{{ '%.2f'|format(income-expenses-saved) }}</div></div>
<div class="card"><div class="label">Total income</div><div class="amount positive">₱{{ '%.2f'|format(income) }}</div></div>
<div class="card"><div class="label">Total spending</div><div class="amount negative">₱{{ '%.2f'|format(expenses) }}</div></div>
<div class="card"><div class="label">Savings deposits</div><div class="amount">₱{{ '%.2f'|format(saved) }}</div></div>
</div>
<div class="layout">
<div class="card"><h2>Quick add</h2>
<form action="/add" method="post">
<select name="kind" required><option value="income">Income</option><option value="spending">Daily spending</option><option value="saving">Savings deposit</option></select>
<input name="title" placeholder="Description (e.g. salary, lunch)" maxlength="100" required>
<input name="amount" type="number" min="0.01" step="0.01" placeholder="Amount in PHP (₱)" required>
<input name="entry_date" type="date" value="{{ today }}" required>
<button type="submit">Save transaction</button>
</form></div>
<div class="card"><h2>Recent activity</h2>
{% for e in recent %}
<div class="entry"><div class="row"><strong>{{ e.title }}</strong><span class="{{ 'positive' if e.kind in ['income','saving'] else 'negative' }}">{{ '+' if e.kind in ['income','saving'] else '-' }}₱{{ '%.2f'|format(e.amount) }}</span></div>
<div class="muted">{{ e.entry_date }} · {{ {'income':'Income','spending':'Spending','saving':'Savings'}[e.kind] }}</div></div>
{% else %}<p class="muted">No transactions yet. Add your first one above.</p>{% endfor %}
</div></div>
{% elif tab=='savings' %}
<div class="card"><h2>Savings goal</h2>
<form action="/goal" method="post"><label class="label">Target amount (PHP)</label><input name="goal" type="number" min="0" step="0.01" value="{{ '%.2f'|format(goal) }}" required><button>Update savings goal</button></form>
<div class="row" style="margin-top:18px"><span>Saved: ₱{{ '%.2f'|format(saved) }}</span><strong>{{ progress }}%</strong></div><div class="progress"><span style="width:{{ progress }}%"></span></div><div class="muted">Goal: ₱{{ '%.2f'|format(goal) }}</div>
</div>
<div class="card"><h2>Add savings deposit</h2><form action="/add" method="post"><input type="hidden" name="kind" value="saving"><input name="title" placeholder="Savings description" required maxlength="100"><input name="amount" type="number" min="0.01" step="0.01" placeholder="Amount in PHP" required><input name="entry_date" type="date" value="{{ today }}" required><button>Record deposit</button></form></div>
<div class="card"><h2>Savings history</h2>{% for e in entries %}<div class="entry"><div class="row"><strong>{{ e.title }}</strong><span class="positive">+₱{{ '%.2f'|format(e.amount) }}</span></div><div class="muted">{{ e.entry_date }}</div></div>{% else %}<p class="muted">No savings deposits recorded.</p>{% endfor %}</div>
{% else %}
<div class="card"><h2>{{ 'Daily Spending' if tab=='spending' else 'Total Income' }}</h2>
<form action="/add" method="post"><input type="hidden" name="kind" value="{{ 'spending' if tab=='spending' else 'income' }}"><input name="title" placeholder="{{ 'What did you spend on?' if tab=='spending' else 'Income source (salary, business...)' }}" required maxlength="100"><input name="amount" type="number" min="0.01" step="0.01" placeholder="Amount in PHP (₱)" required><input name="entry_date" type="date" value="{{ today }}" required><button>{{ 'Add expense' if tab=='spending' else 'Add income' }}</button></form>
</div>
<div class="card"><div class="row"><h2>{{ 'Spending history' if tab=='spending' else 'Income history' }}</h2><strong>₱{{ '%.2f'|format(expenses if tab=='spending' else income) }}</strong></div>
{% for e in entries %}<div class="entry"><div class="row"><div><strong>{{ e.title }}</strong><div class="muted">{{ e.entry_date }}</div></div><div class="{{ 'negative' if tab=='spending' else 'positive' }}">₱{{ '%.2f'|format(e.amount) }}</div></div><form action="/delete/{{ e.id }}" method="post" style="display:block;margin-top:8px" onsubmit="return confirm('Delete this transaction?')"><button class="smallbtn">Delete</button></form></div>{% else %}<p class="muted">No records yet.</p>{% endfor %}
</div>
{% endif %}
<p class="muted" style="text-align:center;margin-top:20px">Your Plan · Stored locally in your Termux folder</p>
</main></body></html>
"""

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL CHECK(kind IN ('income','spending','saving')),
            title TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            entry_date TEXT NOT NULL
        )""")
        conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value REAL NOT NULL)")
        conn.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('goal',10000)")

def totals():
    rows = db().execute("SELECT kind, COALESCE(SUM(amount),0) total FROM transactions GROUP BY kind").fetchall()
    sums = {r["kind"]: r["total"] for r in rows}
    return sums.get("income",0), sums.get("spending",0), sums.get("saving",0)

def render(tab):
    income, expenses, saved = totals()
    goalrow = db().execute("SELECT value FROM settings WHERE key='goal'").fetchone()
    goal = goalrow["value"] if goalrow else 10000
    progress = min(100, int(saved / goal * 100)) if goal > 0 else 0
    if tab == "dashboard":
        entries = db().execute("SELECT * FROM transactions ORDER BY entry_date DESC,id DESC LIMIT 8").fetchall()
    elif tab == "savings":
        entries = db().execute("SELECT * FROM transactions WHERE kind='saving' ORDER BY entry_date DESC,id DESC").fetchall()
    else:
        kind = "spending" if tab == "spending" else "income"
        entries = db().execute("SELECT * FROM transactions WHERE kind=? ORDER BY entry_date DESC,id DESC", (kind,)).fetchall()
    return render_template_string(PAGE, tab=tab, income=income, expenses=expenses, saved=saved,
        goal=goal, progress=progress, entries=entries, recent=entries if tab=="dashboard" else [],
        today=date.today().isoformat())

@app.route("/")
def dashboard(): return render("dashboard")
@app.route("/savings")
def savings(): return render("savings")
@app.route("/spending")
def spending(): return render("spending")
@app.route("/income")
def income_page(): return render("income")

@app.route("/add", methods=["POST"])
def add():
    kind = request.form.get("kind","")
    title = request.form.get("title","").strip()
    raw_amount = request.form.get("amount","")
    entry_date = request.form.get("entry_date", date.today().isoformat())
    try:
        amount = float(raw_amount)
        date.fromisoformat(entry_date)
        if kind not in ("income","spending","saving") or not title or amount <= 0 or amount > 1_000_000_000:
            raise ValueError
    except (ValueError, TypeError):
        return "Invalid transaction. Please go back and check your details.", 400
    db().execute("INSERT INTO transactions(kind,title,amount,entry_date) VALUES(?,?,?,?)",
                 (kind,title,amount,entry_date))
    db().commit()
    return redirect("/" if request.referrer is None else request.referrer)

@app.route("/goal", methods=["POST"])
def update_goal():
    try:
        goal = float(request.form.get("goal",""))
        if goal < 0 or goal > 1_000_000_000: raise ValueError
    except ValueError:
        return "Invalid savings goal.", 400
    db().execute("INSERT INTO settings(key,value) VALUES('goal',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (goal,))
    db().commit()
    return redirect("/savings")

@app.route("/delete/<int:entry_id>", methods=["POST"])
def delete(entry_id):
    db().execute("DELETE FROM transactions WHERE id=?", (entry_id,))
    db().commit()
    return redirect(request.referrer or "/")

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=False)
