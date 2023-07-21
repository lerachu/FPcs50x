import os
import datetime
import pytz

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Select names of stock and their shares for user
    rows = db.execute("SELECT name, SUM(shares) AS shares FROM transactions JOIN stocks ON transactions.id_stock = stocks.id WHERE user_id = ? GROUP BY id_stock  HAVING SUM(shares) > 0 ORDER BY name", session["user_id"])
    total_stocks_value = 0   # For counting how mutch all stocks cost
    for row in rows:  # Rows - list of dicts
        row["cur_price"] = lookup(row["name"])["price"]   # Adding current price for each stock in dictionary
        row["total_value"] = row["cur_price"] * row["shares"]  # Adding total value for "shares" many stocks
        row["cur_price"] = usd(row["cur_price"])
        total_stocks_value += row["total_value"]  # Total value of stocks user has
        row["total_value"] = usd(row["total_value"])

    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])  # How much money user has got(cash)
    balance = usd(cash[0]["cash"] + total_stocks_value)
    cash = usd(cash[0]["cash"])

    return render_template("index.html", rows=rows, balance=balance, cash=cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")  # If GET render page
    else:                                   # If POST
        symbol = request.form.get("symbol").upper()  # Get symbol of stock from request
        shares = request.form.get("shares")  # How many shares user wants to buy

        return postbuy(symbol, shares)  # Part for post request

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Select transactions for user
    rows = db.execute("SELECT name, shares, date, price FROM transactions JOIN stocks ON transactions.id_stock = stocks.id WHERE user_id = ?  ORDER BY date", session["user_id"])

    for row in rows:  # Rows - list of dicts
        row["price"] = usd(row["price"])   # Adding dollar sign

    return render_template("history.html", rows=rows)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":       # If GET render page
        return render_template("quote.html")
    else:                            # If POST
        symbol = request.form.get("symbol")   # Get the name(symbol) of the stock
        response = lookup(symbol)          # Looks prices through API

        if not response:            # If stock does not exist (with this symbol)
            return apology("invalid symbol", 400)

        price = usd(response["price"])     # To add dollar sign

        return render_template("quoted.html", response=response, price=price)  # Else show price


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username") # Get username from form
        if not username:                  # If have not provided
            return apology("must provide username", 400)

        rows = db.execute("SELECT * FROM users WHERE username = ?", username) # Check if there is user with this name
        if len(rows) != 0:
            return apology("username already exists", 400)

        password = request.form.get("password")    # Get password out of form
        confirmation = request.form.get("confirmation")  # Get password out of form (second try)
        if not password:  # If form is empty
            return apology("must provide password", 403)
        if password != confirmation:     # If passwords have not matched
            return apology("the passwords do not match", 403)

        db.execute("INSERT INTO users(username, hash) VALUES(?,?)", username, generate_password_hash(password))  # Insert new user into database

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        # Get names of stocks user had transactions with from db
        stocks = db.execute("SELECT name FROM transactions JOIN stocks ON transactions.id_stock = stocks.id WHERE user_id = ? GROUP BY name HAVING SUM(shares) > 0 ORDER BY name", session["user_id"])
        return render_template("sell.html", stocks=stocks)
    else:                                    # If method - POST
        symbol = request.form.get("symbol")   # Get symbol of the stock from form
        shares = request.form.get("shares")    # Get shares from form

        return postsell(symbol, shares)  # Part for post request

@app.route("/buysell", methods=["POST"])
@login_required
def buysell():
    trans_type = request.form.get("buysell")
    shares = request.form.get("shares")
    symbol = request.form.get("stock")

    if trans_type == "buy":
        return postbuy(symbol, shares)
    else:
        return postsell(symbol, shares)


def postbuy(symbol, shares):
    if not symbol or not shares:         # If user have non filled each input
        return apology("Fill each input", 400)

    try:
        shares = int(shares)    # Shares should be integer > 0
        if shares <= 0:
            return apology("Shares should be > 0", 400)
    except ValueError:
        return apology("Shares should be int", 400)

    response = lookup(symbol)     # Looks prices through API
    if not response:
        return apology("No such stock", 400)

    cost = float(response["price"]) * shares   # The cost of all amount of stocks
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])  # How much money user has got

    cash = cash[0]['cash'] - cost  # Can user afford the bargain?
    if cash < 0:
        return apology("Not enough money", 403)
    try:
        db.execute("INSERT INTO stocks (name) VALUES(?)", symbol)  # Insert name of stock in the table if it is not there
    except ValueError:
        pass

    db.execute("INSERT INTO transactions (id_stock, user_id, price, shares, date) VALUES((SELECT id FROM stocks WHERE name = ?), ?, ?, ?, ?)", symbol, session["user_id"], response["price"], shares, datetime.datetime.now(pytz.timezone("US/Eastern")))  # Insert new transaction

    db.execute("UPDATE users SET cash = ? WHERE id = ?",cash, session["user_id"])  # Update user's cash

    return redirect("/")



def postsell(symbol, shares):
    if not shares:                      # If no input
        return apology("Fill share input", 400)

    if not symbol:                      # If no input
        return apology("Fill symbol input", 400)

    try:
        shares = int(shares)          # If not int
    except ValueError:
        return apology("Share - int > 0", 400)

    if shares <= 0:                 # If int <= 0
        return apology("Share - int > 0", 400)

    # How many shares of that(user want to sell) stock user got
    shares_user_got = db.execute("SELECT SUM(shares) AS shares FROM transactions JOIN stocks ON transactions.id_stock = stocks.id WHERE user_id = ? AND name = ? GROUP BY name", session["user_id"], symbol)
    # List of dicts into int
    shares_user_got = shares_user_got[0]["shares"]

    if shares_user_got < shares:   # If user has less shares than he whant to sell
        return apology(f"You have only {shares_user_got} shares", 403)
    else:
        response = lookup(symbol)     # Looks prices through API
        db.execute("INSERT INTO transactions (id_stock, user_id, price, shares, date) VALUES((SELECT id FROM stocks WHERE name = ?), ?, ?, ?, ?)", symbol, session["user_id"], response["price"], -shares, datetime.datetime.now(pytz.timezone("US/Eastern")))  # Insert new transaction

        profit = response["price"] * shares

        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])  # How much money user has got(cash)
        cash = cash[0]["cash"] + profit    # Cash after selling the shares of stock

        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash, session["user_id"])  # Refresh the cash in db

    return redirect("/")