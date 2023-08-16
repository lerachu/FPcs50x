import datetime
import pytz

# importing packages
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, brand, randpic

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.globals.update(brand=brand)
app.jinja_env.globals.update(randpic=randpic)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///profession.db")


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
    questionnaire = db.execute("SELECT * FROM questionnaire WHERE user_id = ?", session["user_id"])

    try:
        questionnaire[0]   # If user filled the questionnaire

    except IndexError:
        return redirect("/questionnaire_edit")
    
    else:
        questionnaire = questionnaire[0]
        
        return render_template("index.html", questionnaire=questionnaire)
   

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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")  # Get username from form
        if not username:                  # If have not provided
            return apology("must provide username", 400)

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)  # Check if there is user with this name
        if len(rows) != 0:
            return apology("username already exists", 400)

        password = request.form.get("password")    # Get password out of form
        confirmation = request.form.get("confirmation")  # Get password out of form (second try)
        if not password:  # If form is empty
            return apology("must provide password", 400)
        if password != confirmation:     # If passwords have not matched
            return apology("the passwords do not match", 400)

        db.execute("INSERT INTO users(username, hash) VALUES(?,?)", username,
                   generate_password_hash(password))  # Insert new user into database

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/search")
def search():
    q = request.args.get("q")

    items = db.execute("SELECT * FROM plan WHERE title LIKE ? AND user_id = ? AND completeness = 0", "%" + q + "%", session["user_id"])
    
    return render_template("search.html", items = items) # Render query items 


@app.route("/plan", methods=["GET", "POST"])
@login_required
def plan():
    """Show TO DO plan"""
    if request.method == "GET":
        items = db.execute("SELECT * FROM plan WHERE user_id = ? AND completeness = 0", session["user_id"])

        return render_template("plan.html", items = items)  # TO DO plan
    
    else:                                  
        title = request.form.get("title")    # POST new item 
        link = request.form.get("link")
        description = request.form.get("description")
        comment = request.form.get("comment")
        importance = request.form.get("importance")
        complexity = request.form.get("complexity")
        completeness = 0
        date = datetime.datetime.now(pytz.timezone("US/Eastern"))

        db.execute("INSERT INTO plan (title, link, description, comment, importance, complexity, completeness, user_id, date) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", title, link, description, comment, importance, complexity, completeness, session["user_id"], date)
        return redirect("/plan") 
    

@app.route("/questionnaire", methods=["GET"])
@login_required
def questionnaire():
    """Shows filled in questionnaire (if it is)"""
    questionnaire = db.execute("SELECT name, profession, goal, deadline FROM questionnaire WHERE user_id = ?", session["user_id"]) 
    try:
        questionnaire = questionnaire[0]

    except IndexError:   # If questionnaire is not filled in
        return redirect("/questionnaire_edit")
    
    else:
        return render_template("questionnaire.html", questionnaire=questionnaire)  
    



@app.route("/questionnaire_edit", methods=["GET", "POST"])
@login_required
def questionnaire_edit():
    """Edit questionnaire"""
    if request.method == "GET":
        questionnaire = db.execute("SELECT * FROM questionnaire WHERE user_id = ?", session["user_id"])
        
        try:
            questionnaire = questionnaire[0]   # Check if user filled questionnaire in earlier
            
        except IndexError:
            sendedit = "Send"   # Name for button if user has not filled questionnaire yet
            

        else:
            sendedit = "Save"  # Name for button if user is editing questionnaire 
            questionnaire["chosen_day"], questionnaire["chosen_month"], questionnaire["chosen_year"] = map(int, (questionnaire["deadline"].split("/")))
        
        return render_template("questionnaire_edit.html", days=range(1,32), months=range(1,13), years=range(2023,2050), sendedit=sendedit, questionnaire=questionnaire) 
     
    else:
        name = request.form.get("name")                                 
        profession  = request.form.get("profession") 
        goal = request.form.get("goal")
        day = int(request.form.get("day"))   
        month = int(request.form.get("month"))   
        year = request.form.get("year")  

        questionnaire = db.execute("SELECT * FROM questionnaire WHERE user_id = ?", session["user_id"])

        try:
            questionnaire[0] 

        except IndexError:    # Insert if user filled the questionnaire for the first time
            db.execute("INSERT INTO questionnaire(name, profession, goal, deadline, user_id)  VALUES(?, ?, ?, ?, ?)", name, profession, goal, "{:02d}/{:02d}/{}".format(day, month, year), session["user_id"])   
        
        else:    # Update if user edited questionnaire
            db.execute("UPDATE questionnaire SET name = ?, profession = ?, goal = ?, deadline = ? WHERE user_id = ?", name, profession, goal, "{:02d}/{:02d}/{}".format(day, month, year), session["user_id"])  

        return redirect("/questionnaire")



@app.route("/edit_item", methods=["POST"])
@login_required
def edit_item():
    """Edit item in plan"""                            
    title = request.form.get("title")
    link = request.form.get("link")
    description = request.form.get("description")
    comment = request.form.get("comment")
    importance = request.form.get("importance")
    complexity = request.form.get("complexity")
    id = request.form.get("id")


    completeness = db.execute("SELECT completeness FROM plan WHERE user_id = ? AND id = ?", session["user_id"], id)[0]["completeness"]
    if completeness:   # Find out what item user has edited
        redir = "/done"
    else:
        redir = "/plan"

    db.execute("UPDATE plan SET title = ?, link = ?, description = ?, comment = ?, importance = ?, complexity = ? WHERE user_id = ? AND id = ?", title, link, description, comment, importance, complexity, session["user_id"], id)
    return redirect(redir) 



@app.route("/delete_item", methods=["POST"])
@login_required
def delete_item():
    """Delete item from plan"""                            
    id = request.form.get("id")

    completeness = db.execute("SELECT completeness FROM plan WHERE user_id = ? AND id = ?", session["user_id"], id)[0]["completeness"]
    if completeness:  # Find what item user has deleted to return on right page
        redir = "/done"
    else:
        redir = "/plan"

    db.execute("DELETE FROM plan WHERE user_id = ? AND id = ?", session["user_id"], id)
    return redirect(redir) 



@app.route("/done", methods=["GET", "POST"])
@login_required
def done():
    """Show DONE plan"""
    if request.method == "GET":
        items = db.execute("SELECT * FROM plan WHERE user_id = ? AND completeness = 1", session["user_id"])

        return render_template("done.html", items = items)  
    
    else:                                  
        title = request.form.get("title")   # Add new DONE item
        link = request.form.get("link")
        description = request.form.get("description")
        comment = request.form.get("comment")
        importance = request.form.get("importance")
        complexity = request.form.get("complexity")
        completeness = 1
        date = datetime.datetime.now(pytz.timezone("US/Eastern"))

        db.execute("INSERT INTO plan (title, link, description, comment, importance, complexity, completeness, user_id, date) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", title, link, description, comment, importance, complexity, completeness, session["user_id"], date)
        return redirect("/done") 
    

@app.route("/change_completeness", methods=["POST"])
@login_required
def change_completeness():
    """Srom TO DO to DONE and vise versa"""                            
    
    id = request.form.get("id")
    completeness = int(request.form.get("completeness"))

    if completeness:
        completeness = 0
        redir = "/done"

    else:
        completeness = 1
        redir = "/plan"

    date = datetime.datetime.now(pytz.timezone("US/Eastern"))

    db.execute("UPDATE plan SET completeness = ?, date = ? WHERE user_id = ? AND id = ?", completeness, date, session["user_id"], id)
    
    return redirect(redir)  


@app.route("/statistics", methods=["GET"])
@login_required
def statistics():
    """Show statistic of completion of the plan"""
    statistics = db.execute("SELECT complexity, importance, completeness FROM plan WHERE user_id = ?", session["user_id"]) 
    done = 0
    todo = 0

    for statistic in statistics:
        if statistic["completeness"] == 1:
            if statistic["importance"] == 1:
                done += statistic["complexity"]
            else:
                done += 0.5 * statistic["complexity"]
        else:
            if statistic["importance"] == 1:
                todo += statistic["complexity"]
            else:
                todo += 0.5 * statistic["complexity"]

    try:
        progress = done / (done + todo) * 100
    except ZeroDivisionError:  # Haven't done any item yet
        progress = 0

    items_completed = db.execute("SELECT complexity, importance, date FROM plan WHERE user_id = ? and completeness = 1 ORDER BY date", session["user_id"]) 
    
    progress_history = []  # History of the progress
    progress_cur = 0
    for items in items_completed:
        if items["importance"] == 1:
            progress_cur += items["complexity"] / (done + todo) * 100
            progress_item = {"date": items["date"], "progress": progress_cur}
            progress_history.append(progress_item)
        else:
            progress_cur += 0.5 * items["complexity"] / (done + todo) * 100
            progress_item = {"date": items["date"], "progress": progress_cur}
            progress_history.append(progress_item)

    print(progress_history)

    return render_template("statistics.html", progress=progress, progress_history=progress_history)
            

@app.route("/inspiration", methods=["GET", "POST"])
@login_required
def inspiration():
    """Show pictures"""
    if request.method == "GET":
        inspirations = db.execute("SELECT * FROM inspiration WHERE user_id = ?", session["user_id"])

        return render_template("inspiration.html", inspirations=inspirations)  
    
    else:                                  
        img = request.form.get("img")   # Adding new item
        link = request.form.get("link")
        comment = request.form.get("comment")

        db.execute("INSERT INTO inspiration (picture, link, comment, user_id) VALUES(?, ?, ?, ?)", img, link, comment, session["user_id"])
        return redirect("/inspiration") 


@app.route("/edit_inspiration", methods=["POST"])
@login_required
def edit_inspiration():
    """Edit item"""                            
    img = request.form.get("img")
    link = request.form.get("link")
    comment = request.form.get("comment")
    id = request.form.get("id")

    db.execute("UPDATE inspiration SET picture = ?, link = ?, comment = ? WHERE user_id = ? AND id = ?", img, link, comment, session["user_id"], id)
    return redirect("/inspiration") 



@app.route("/delete_inspiration", methods=["POST"])
@login_required
def delete_inspiration():
    """Edit item"""                            
    id = request.form.get("id")

    db.execute("DELETE FROM inspiration WHERE user_id = ? AND id = ?", session["user_id"], id)
    return redirect("/inspiration") 