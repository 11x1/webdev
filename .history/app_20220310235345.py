from flask import Flask, url_for, redirect, session, render_template, request
import mysql.connector

from sql_helpers import login_and_return_db

app = Flask(__name__)
app.secret_key = 'cattofatto'

@app.route('/', methods=['GET'])
def index():
    if 'username' in session: return redirect(f'users/{session["username"]}.{session["uid"]}')
    return redirect('login')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = login_and_return_db()
        db_cursor = db.cursor()
        db_cursor.execute('use webdev')
        db_cursor.execute(f'select username, password, userid from users where username="{username}"')
        query = db_cursor.fetchall()
        if len(query) == 0: error = f'User {username} does not exist'
        else:
            db_returned_password = query[0][1]
            if not db_returned_password == password: error = f'Wrong password'
            session['username'] = query[0][0]
            session['uid'] = query[0][2]
            return redirect(f'users/{session["username"]}.{session["uid"]}')

    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_repeat = request.form['password_repeat']

        if not password_repeat == password: error = 'passwods do not match'
        elif len(username) < 3: error = 'username is too short'
        elif len(password) < 8: error = 'password is too short'
        else:
            db = login_and_return_db()
            db_cursor = db.cursor()
            db_cursor.execute('use webdev')
            db_cursor.execute('select count(*) from users')
            rows = db_cursor.fetchone()[0]
            db_cursor.execute(f'INSERT INTO users VALUES({rows + 1}, "{username}", "{password}", {0}, {0})')
            db.commit()
            return redirect('login')

    return render_template('register.html', error=error)


@app.route('/userlist')
def userlist_page():
    if not 'username' in session: return redirect('login')

    db = login_and_return_db()
    cursor = db.cursor()
    cursor.execute('use webdev')
    cursor.execute('select userid, username from users')
    data = cursor.fetchall()
    user_list = []
    for row in data:
        user_list.append(row[1])
    
    print(user_list)
    
    return render_template('userlist.html', len=len(user_list), list=user_list)


@app.route('/users/<string:username>.<int:userid>')
def profile(username, userid):
    # If we aren't logged in, return to login page
    if not 'username' in session: return redirect('login')
    # Connect to database
    db = login_and_return_db()
    cursor = db.cursor()
    cursor.execute('use webdev')

    # Redirect if uid doesnt match username
    cursor.execute(f'select username from users where userid = "{userid}"')
    real_username = cursor.fetchone()[0]
    if not real_username: return redirect('../profile_not_found')
    elif real_username != username: return redirect(f'../users/{real_username}.{userid}')

    is_owner = None
    url = None
    if session['username'] == username: 
        is_owner = True
        url = f'users/{username}.{userid}/edit'
    
    cursor.execute(f'select description from users where username = "{username}"')
    profile_description = cursor.fetchone()[0]
    cursor.execute(f'select profile_picture from users where username="{username}"')
    profile_picture_url = cursor.fetchone()[0]
    return render_template('profile.html', username=session['username'], uid=session['uid'], profile_username=username, profile_userid=userid, profile_description=profile_description, profile_picture_url=profile_picture_url, is_owner=is_owner, url=url)

@app.route('/profile_not_found')
def profilenofound_page(): return render_template('profilenofound.html')


@app.route('/users/<string:username>.<int:userid>/edit', methods=['POST', 'GET'])
def edit_profile(username, userid):
    if not 'username' in session: return redirect('login')
    if not session['username'] == username: return redirect(f'../users/{username}.{userid}')
    error = None

    db = login_and_return_db()
    cursor = db.cursor()
    cursor.execute(f'use webdev')
    cursor.execute(f'select description from users where username="{username}"')
    description = cursor.fetchone()[0]
    cursor.execute(f'select profile_picture from users where username="{username}"')
    profile_picture_url = cursor.fetchone()[0]

    if request.method == 'POST':
        new_pfp_url = request.form['profile_picture_url']
        new_desc = request.form['description']
        if len(new_desc) > 100: error = 'Description too long (>100 chars)'
        else:
            if new_pfp_url != profile_picture_url:
                cursor.execute(f"UPDATE users SET profile_picture = '{new_pfp_url}' WHERE username = '{username}'")
            if new_desc != description:
                cursor.execute(f"UPDATE users SET description = '{new_desc}' WHERE username = '{username}'")
            db.commit()
            return redirect(f'/users/{username}.{userid}')

    return render_template('profileedit.html', username=session['username'], uid=session['uid'], profile_username=username, profile_userid=userid, description=description, profile_picture_url=profile_picture_url, error=error)



@app.route('/logout')
def logout():
   # remove the username from the session if it is there
   session.pop('username', None)
   return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)