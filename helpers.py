from cs50 import SQL
from flask import redirect, render_template, session
from functools import wraps
import random

db = SQL("sqlite:///profession.db")


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function



def brand():
    if session.get("user_id") is None:  # Default brand in navbar
        return False
    else:
        questionnaire = db.execute("SELECT * FROM questionnaire WHERE user_id = ?", session["user_id"]) 

        try:
            questionnaire = questionnaire[0]
        
        except IndexError:
            return False
        
        else:
            return questionnaire["profession"].capitalize() # Brand in navbar
        
        
def randpic():
    inspirations = db.execute("SELECT * FROM inspiration WHERE user_id = ?", session["user_id"])
    
    if inspirations:
        rand = random.randrange(0, len(inspirations))  # Random pic from inspiration
        pic = inspirations[rand]["picture"]

        return pic
    
    else:
        return False # There is no pics in inspirations