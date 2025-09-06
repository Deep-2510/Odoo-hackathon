import os
from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # change this in production
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Registration
@app.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        contact = request.form['contact']
        dob = request.form['dob']
        gender = request.form['gender']
        address = request.form['address']
        description = request.form['description']

        if password != confirm_password:
            return "❌ Passwords do not match."

        # Save user data with empty profile image (will be updated later)
        with open('data.txt', 'a') as f:
            f.write(f"{email},{password},{contact},{dob},{gender},{address},{description},\n")

        return redirect(url_for('login'))

    return render_template('index.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            with open('data.txt', 'r') as f:
                users = f.readlines()

            for user in users:
                saved_email, saved_password, *_ = user.strip().split(',')
                if email == saved_email and password == saved_password:
                    session['user'] = email
                    return redirect(url_for('dashboard'))

            error = "❌ Invalid email or password."

        except FileNotFoundError:
            error = "❌ No users registered yet."

    return render_template('login.html', error=error)

# Dashboard
@app.route('/dashboard')
def dashboard():
    user = session.get('user')
    if not user:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=user)

# Profile
@app.route('/profile/<user>', methods=['GET', 'POST'])
def profile(user):
    uploaded_image = None
    image_filename = f"{secure_filename(user)}.jpg"
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    full_image_url = f"/{app.config['UPLOAD_FOLDER']}/{image_filename}"

    # Read all users and find the matching one
    users = []
    current_user = None
    with open('data.txt', 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if parts[0] == user:
                current_user = parts
            users.append(parts)

    if current_user is None:
        return "❌ No user data found."

    # Handle image upload once
    if request.method == 'POST':
        file = request.files['profile_image']
        if file:
            file.save(image_path)

            # Add image name to the user's record (only if not saved before)
            if len(current_user) < 8 or not current_user[7]:
                current_user = current_user[:7] + [image_filename]
                # Update users list
                for i in range(len(users)):
                    if users[i][0] == user:
                        users[i] = current_user
                        break
                # Write back to file
                with open('data.txt', 'w') as f:
                    for u in users:
                        f.write(','.join(u) + '\n')

    # Check if image exists
    if os.path.exists(image_path):
        uploaded_image = full_image_url

    user_info = {
        'email': current_user[0],
        'contact': current_user[2],
        'dob': current_user[3],
        'gender': current_user[4],
        'address': current_user[5],
        'description': current_user[6],
    }

    return render_template('profile.html', user=user, user_info=user_info, uploaded_image=uploaded_image)


# About Page
@app.route('/about')
def about():
    user = session.get('user')  # keep track of logged-in user
    return render_template('about.html', user=user)



# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
