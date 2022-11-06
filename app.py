from cs50 import SQL

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session

from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
movies_db=SQL('sqlite:///movies.db')
shows_db=SQL('sqlite:///shows.db')
users_db=SQL('sqlite:///users.db')

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

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

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username").upper():
            return apology("must provide username", 200)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 200)

        # Query database for username
        rows = users_db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username").upper())

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 200)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash('Logged in!')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == 'POST':

        username = request.form.get('username').upper()
        password = request.form.get('password')
        confirmation = request.form.get('confirmation')
        usernames = users_db.execute('SELECT username FROM users WHERE username = ?', username)

        if not username:
            return apology('must provide username', 400)
        elif not password:
            return apology('must provide password', 400)
        elif len(password) < 8:
            return apology('password should be atleast 8 characters long')
        elif not confirmation:
            return apology('confirm your password', 400)
        elif password != confirmation:
            return apology('password and confirm password must be same', 400)
        elif usernames:
            return apology('username already exists', 400)
        hashed_pass = generate_password_hash(password)
        users_db.execute('INSERT INTO users (username,hash) VALUES(?,?)', username, hashed_pass)
        rows = users_db.execute("SELECT id FROM users WHERE username = ?", username)
        session["user_id"] = rows[0]['id']
        flash('Registered!')
        return redirect('/')

    return render_template('register.html')

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route('/')
@login_required
def index():
    username = users_db.execute('SELECT username FROM users WHERE id = ?',session['user_id'])[0]['username']
    return render_template('index.html',username=username)

@app.route('/search',methods=['POST','GET'])
@login_required
def search():
    if request.method == 'POST':
        title = request.form.get('search')
        shows = shows_db.execute("SELECT * FROM shows WHERE title LIKE ? ORDER BY year DESC LIMIT 50", "%" + title + "%")
        movies = movies_db.execute("SELECT * FROM movies WHERE title LIKE ? ORDER BY year DESC LIMIT 50", "%" + title + "%")
        username = users_db.execute('SELECT username FROM users WHERE id = ?',session['user_id'])[0]['username']
        user_shows = users_db.execute("SELECT * FROM profiles WHERE title LIKE ? AND type='Show' AND username= ? ","%" + title + "%",username)
        user_movies = users_db.execute("SELECT * FROM profiles WHERE title LIKE ? AND type='Movie' AND username= ? ","%" + title + "%",username)
        return render_template("results.html", shows=shows,movies=movies,user_shows=user_shows,user_movies=user_movies,username=username)
    return redirect('/')

@app.route('/add',methods=['POST'])
@login_required
def add():
    username = users_db.execute('SELECT username FROM users WHERE id = ?',session['user_id'])[0]['username']
    show_id = request.form.get('show_id')
    movie_id = request.form.get('movie_id')
    rating = request.form.get('rating')
    if show_id:
        show_info = shows_db.execute("SELECT * FROM shows WHERE id = ?",show_id)[0]
        users_db.execute('INSERT INTO profiles (username,title,type,rating,year) VALUES (?,?,?,?,?)',username,show_info['title'],'Show',rating,show_info['year'])
        flash('Added to your List!')
        return redirect('/')
    if movie_id:
        movie_info = movies_db.execute("SELECT * FROM movies WHERE id = ?",movie_id)[0]
        users_db.execute('INSERT INTO profiles (username,title,type,rating,year) VALUES (?,?,?,?,?)',username,movie_info['title'],'Movie',rating,movie_info['year'])
        flash('Added to your List!')
        return redirect('/')

@app.route('/movies',methods=['GET','POST'])
@login_required
def movies():
    username = users_db.execute('SELECT username FROM users WHERE id = ?',session['user_id'])[0]['username']
    if request.method == 'POST':
        rem_movie = request.form.get('rem_movie')
        users_db.execute('DELETE FROM profiles WHERE id=?',rem_movie)
    movies = users_db.execute('SELECT * FROM profiles WHERE username=? AND type = "Movie"',username)
    return render_template('movies.html',movies=movies,username=username)

@app.route('/shows',methods=['GET','POST'])
@login_required
def shows():
    username = users_db.execute('SELECT username FROM users WHERE id = ?',session['user_id'])[0]['username']
    if request.method == 'POST':
        rem_show = request.form.get('rem_show')
        users_db.execute('DELETE FROM profiles WHERE id=?',rem_show)
    shows = users_db.execute('SELECT * FROM profiles WHERE username=? AND type = "Show"',username)
    return render_template('shows.html',shows=shows,username=username)

@app.route("/changepass", methods=["GET", "POST"])
@login_required
def change_pass():
    if request.method == 'GET':
        username = users_db.execute('SELECT username FROM users WHERE id = ?',session['user_id'])[0]['username']
        return render_template('changepass.html',username=username)
    else:
        hash_pass = users_db.execute("SELECT hash FROM users WHERE id=?", session['user_id'])[0]['hash']
        old_password = request.form.get('old-pass')
        new_password = request.form.get('new-pass')
        confirm_new_password = request.form.get('confirm-new-pass')
        if not old_password or not new_password or not confirm_new_password:
            return apology('Fill all the fields', 400)
        if len(new_password) < 8:
            return apology('password should be atleast 8 characters long')
        if not check_password_hash(hash_pass, old_password):
            return apology('Incorrect password', 400)
        if new_password != confirm_new_password:
            return apology('password and confirm password does not match', 400)
        new_password_hash = generate_password_hash(new_password)
        users_db.execute('UPDATE users SET hash=? WHERE id =?', new_password_hash, session['user_id'])
        flash('Password Changed!')
        return redirect('/')