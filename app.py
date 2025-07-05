# Backend server for the WildWaste application using Flask.

from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'admin',
    'database': 'wildwaste_db'
}

# Database Connection Helper
def create_db_connection():
    """
    Creates and returns a connection to the MySQL database.
    """
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

@app.route('/')
def index():
    return "Welcome to the WildWaste Backend API!"

@app.route('/register', methods=['POST'])
def register_user():
    """
    Registers a new user.
    Expects JSON body: {"username": "user", "password": "pass"}
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"status": "error", "message": "Missing username or password"}), 400

    username = data['username']
    # Hash the password for security before storing
    password_hash = generate_password_hash(data['password'])

    conn = create_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        # Check if username already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"status": "error", "message": "Username already exists"}), 409

        # Insert new user
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
        conn.commit()
        return jsonify({"status": "success", "message": "User registered successfully"}), 201

    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/login', methods=['POST'])
def login_user():
    """
    Logs in a user.
    Expects JSON body: {"username": "user", "password": "pass"}
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"status": "error", "message": "Missing username or password"}), 400

    username = data['username']
    password = data['password']

    conn = create_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True) # dictionary=True returns rows as dicts
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            return jsonify({
                "status": "success",
                "message": "Login successful",
                "user_id": user['id'],
                "username": user['username']
            }), 200
        else:
            return jsonify({"status": "error", "message": "Invalid username or password"}), 401

    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/reports', methods=['POST'])
def add_report():
    """
    Adds a new trash report.
    Expects JSON body with report details.
    """
    data = request.get_json()
    required_fields = ['user_id', 'latitude', 'longitude', 'trash_type', 'quantity']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"status": "error", "message": "Missing required report data"}), 400

    conn = create_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        sql = """INSERT INTO trash_reports 
                 (user_id, latitude, longitude, trash_type, quantity, image_base64, notes) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        
        image_base64 = data.get('image_base64', None) # Optional field
        notes = data.get('notes', None) # Optional field

        cursor.execute(sql, (
            data['user_id'],
            data['latitude'],
            data['longitude'],
            data['trash_type'],
            data['quantity'],
            image_base64,
            notes
        ))
        conn.commit()
        return jsonify({"status": "success", "message": "Report submitted successfully"}), 201

    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/reports', methods=['GET'])
def get_all_reports():
    """
    Fetches all trash reports to display on the map.
    """
    conn = create_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500
    
    # Use dictionary=True to get column names in the result
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT tr.id, tr.user_id, tr.latitude, tr.longitude, tr.trash_type, 
                   tr.quantity, tr.notes, tr.reported_at, tr.image_base64, u.username
            FROM trash_reports tr
            JOIN users u ON tr.user_id = u.id
        """
        cursor.execute(query)
        reports = cursor.fetchall()
        
        # Convert datetime objects to string for JSON serialization
        for report in reports:
            report['reported_at'] = report['reported_at'].isoformat()
            
        return jsonify({"status": "success", "data": reports}), 200

    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/reports/user/<int:user_id>', methods=['GET'])
def get_user_reports(user_id):
    """
    Fetches all reports submitted by a specific user.
    """
    conn = create_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Fetching all details including the image for the user's history
        cursor.execute("SELECT * FROM trash_reports WHERE user_id = %s ORDER BY reported_at DESC", (user_id,))
        reports = cursor.fetchall()
        
        # Convert datetime objects to string
        for report in reports:
            report['reported_at'] = report['reported_at'].isoformat()

        return jsonify({"status": "success", "data": reports}), 200
        
    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/reports/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    """
    Deletes a specific trash report by its ID.
    TODO: Add a security check here to ensure the user making the request is the one who created the report.
    """
    conn = create_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        # Check if the report exists before deleting
        cursor.execute("SELECT id FROM trash_reports WHERE id = %s", (report_id,))
        if cursor.fetchone() is None:
            return jsonify({"status": "error", "message": "Report not found"}), 404

        # Delete the report
        cursor.execute("DELETE FROM trash_reports WHERE id = %s", (report_id,))
        conn.commit()

        if cursor.rowcount > 0:
            return jsonify({"status": "success", "message": "Report deleted successfully"}), 200
        else:
            return jsonify({"status": "error", "message": "Report not found or already deleted"}), 404

    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    # Use host='0.0.0.0' to make it accessible from the local network
    app.run(host='0.0.0.0', port=5000, debug=True)
