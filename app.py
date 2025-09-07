from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from models.recommend import get_recommendations
import pandas as pd
import logging
from datetime import timedelta

# Configure logging
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config.from_pyfile('config.py')
app.permanent_session_lifetime = timedelta(minutes=30)  # Session timeout

# Database connection with error handling
def get_db_connection():
    try:
        conn = sqlite3.connect('database/auth.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {str(e)}")
        raise RuntimeError("Database connection failed")

# Error handler for 404
@app.errorhandler(404)
def page_not_found(e):
    logging.warning(f"404 Error: {request.url}")
    return render_template('404.html'), 404

# Error handler for 500
@app.errorhandler(500)
def internal_server_error(e):
    logging.error(f"500 Error: {str(e)}")
    return render_template('500.html'), 500

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        logging.info(f"User {session['username']} accessed home page")
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please fill all fields')
            return redirect(url_for('login'))
        
        try:
            conn = get_db_connection()
            user = conn.execute(
                'SELECT * FROM users WHERE username = ?', 
                (username,)
            ).fetchone()
            conn.close()
            
            if user and check_password_hash(user['password'], password):
                session.permanent = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                logging.info(f"User {username} logged in successfully")
                return redirect(url_for('dashboard'))
            else:
                logging.warning(f"Failed login attempt for username: {username}")
                flash('Invalid username or password')
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            flash('Login service temporarily unavailable')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if len(password) < 6:
            flash('Password must be at least 6 characters')
            return redirect(url_for('register'))
        
        try:
            hashed_password = generate_password_hash(password)
            conn = get_db_connection()
            
            # Check if username exists
            existing_user = conn.execute(
                'SELECT 1 FROM users WHERE username = ?', 
                (username,)
            ).fetchone()
            
            if existing_user:
                flash('Username already exists')
                conn.close()
                return redirect(url_for('register'))
            
            # Insert new user
            conn.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, hashed_password)
            )
            conn.commit()
            conn.close()
            
            logging.info(f"New user registered: {username}")
            flash('Registration successful! Please login')
            return redirect(url_for('login'))
            
        except Exception as e:
            logging.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again')
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        logging.warning("Unauthorized dashboard access attempt")
        return redirect(url_for('login'))
    
    logging.info(f"User {session['username']} accessed dashboard")
    return render_template('dashboard.html')

@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    if 'user_id' not in session:
        logging.warning("Unauthorized recommendations access attempt")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Get form data with defaults
            user_id = request.form.get('user_id', '').strip()
            product_id = request.form.get('product_id', '').strip()
            customer_name = request.form.get('customer_name', '').strip()
            category = request.form.get('category', '').strip()
            
            logging.info(
                f"Recommendation request by {session['username']} - "
                f"Params: user_id={user_id}, product_id={product_id}, "
                f"customer_name={customer_name}, category={category}"
            )
            
            # Get recommendations
            rec_details, plot_html = get_recommendations(
                user_id=user_id if user_id else None,
                product_id=product_id if product_id else None,
                customer_name=customer_name if customer_name else None,
                category=category if category else None
            )
            
            logging.info(
                f"Generated {len(rec_details)} recommendations for {session['username']}"
            )
            
            return render_template(
                'recommendations.html',
                recommendations=rec_details,
                plot_html=plot_html
            )
            
        except Exception as e:
            logging.error(f"Recommendation error: {str(e)}", exc_info=True)
            flash('Error generating recommendations. Please try different parameters')
            return redirect(url_for('recommendations'))
    
    return render_template('recommendations.html')

@app.route('/logout')
def logout():
    username = session.get('username', 'Unknown')
    session.clear()
    logging.info(f"User {username} logged out")
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Check if database exists
    if not os.path.exists('database/auth.db'):
        logging.warning("Database not found. Creating new database...")
        from database.create_tables import init_db
        init_db()
    
    # Start the application
    logging.info("Starting application...")
    app.run(debug=True, host='0.0.0.0')