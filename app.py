from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import math
import os
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")  



# MySQL Configuration
db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("PASSWORD"),
    database=os.getenv("DATABASE")
)


@app.route('/')
def index():
    return render_template('index.html', logged_in='username' in session)

@app.route('/description')
def description():
    return render_template('description.html', logged_in='username' in session)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username already exists
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            flash("Username already exists. Please choose a different one.", 'error')
            return render_template('register.html', logged_in='user_id' in session)

        # Hash password and insert new user into DB
        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        db.commit()

        if cursor.rowcount > 0:
            flash("Registration successful! You can now log in.", 'success')
            return redirect(url_for('login'))
        else:
            flash("An error occurred while registering. Please try again.", 'error')

    return render_template('register.html', logged_in='username' in session)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            
            session['username'] = user['username']
            flash("Login successful!", 'success')
            return redirect(url_for('profile'))
        else:
            flash("Invalid credentials. Please try again.", 'error')
            return render_template('login.html', logged_in='username' in session)

    return render_template('login.html', logged_in='username' in session)

@app.route('/logout',methods=['GET','POST'] )
def logout():
    session.clear()
    flash("You have been logged out.", 'info')
    return redirect(url_for('login'))




@app.route('/test', methods=['GET', 'POST'])
def test():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        
        chimney_height = float(request.form['chimney_height'])
        distance = float(request.form['distance'])
        wind_direction = float(request.form['wind_direction'])  
        wind_speed = float(request.form['wind_speed'])

        #horizontal distance based on wind direction
        wind_direction_radians = wind_direction * (math.pi / 180)
        horizontal_distance = distance * math.cos(wind_direction_radians)
        
        # Avoid invalid horizontal distance (less than or equal to zero)
        if horizontal_distance <= 0:
            flash("Invalid Distance!", 'error')
            return redirect(url_for('test'))

        
        adjusted_chimney_height = chimney_height * (1 + wind_speed / 10)
        downwind_concentration = adjusted_chimney_height / (wind_speed * math.sqrt(horizontal_distance))

        if downwind_concentration < 1.0:
            safety = "Safe"
        else:
            safety = "Unsafe"
        
       
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO tests (user_id, chimney_height, distance, wind_direction, wind_speed,horizontal_distance,downwind_concentration, result) "
            "VALUES (%s, %s, %s, %s, %s,%s,%s, %s)",
            (session['username'], chimney_height, distance, wind_direction, wind_speed,horizontal_distance, downwind_concentration,safety)
        )
        db.commit()

        # Flash success or error based on database insertion result
        if cursor.rowcount > 0:
            flash(f"Test result: {safety}", 'success')
        else:
            flash("An error occurred while saving the test result. Please try again.", 'error')
        
        return redirect(url_for('test'))

    return render_template('test.html', logged_in='username' in session)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO contact_messages (name, email, message) VALUES (%s, %s, %s)",
            (name, email, message)
        )
        db.commit()

        
        flash("Thank you for reaching out! We'll get back to you soon.", 'success')

        return redirect(url_for('contact'))

    return render_template('contact.html', logged_in='username' in session)


@app.route('/profile')
def profile():
    if 'username' not in session:  # Check if the user is logged in
        flash("No user logged in", 'error')
        return redirect(url_for('login'))
    
    # Pass user details to the template
    return render_template('profile.html', username=session['username'],logged_in='username' in session)

from werkzeug.security import generate_password_hash

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']

        # Check if the username exists in the database
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if not user:
            flash("Username not found. Please check your username.", 'error')
            return render_template('forgot_password.html', logged_in='username' in session)

        # Hash the new password
        hashed_password = generate_password_hash(new_password)

        # Update the password in the database
        cursor.execute("UPDATE users SET password = %s WHERE username = %s", (hashed_password, username))
        db.commit()

        if cursor.rowcount > 0:
            flash("Password updated successfully! You can now log in with your new password.", 'success')
            return redirect(url_for('login'))
        else:
            flash("An error occurred while updating the password. Please try again.", 'error')

    return render_template('forgot_password.html', logged_in='username' in session)


if __name__ == '__main__':
    app.run(debug=True)
