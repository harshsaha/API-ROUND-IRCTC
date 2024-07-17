from flask import Flask, request, jsonify, render_template
import mysql.connector

app = Flask(__name__, template_folder='templates')

# Database connection
db_host = 'localhost'
db_user = 'root'
db_password = 'Harsh1213'
db_name = 'railway_management'

db = None
cursor = None

try:
    db = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    print("Database connection established successfully!")
    cursor = db.cursor()
except mysql.connector.Error as err:
    print("Error connecting to database:", err)

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Register page
@app.route('/register')
def register():
    return render_template('register.html')

# Login page
@app.route('/login')
def login():
    return render_template('login.html')

# Add train page (admin only)
@app.route('/add_train')
def add_train():
    return render_template('add_train.html')

# Get seat availability page
@app.route('/get_seat_availability')
def get_seat_availability():
    return render_template('get_seat_availability.html')

# Book seat page
@app.route('/book')
def book_seat():
    return render_template('book_seat.html')

# Dashboard page
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Register a user
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'message': 'Invalid request'}), 400
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        db.commit()
        return jsonify({'message': 'User registered successfully'})
    except mysql.connector.Error as err:
        return jsonify({'message': 'Error registering user'}), 500

# Login user
@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'message': 'Invalid request'}), 400
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        if user:
            return jsonify({'token': 'ome_token', 'message': 'Login successful'})
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
    except mysql.connector.Error as err:
        return jsonify({'message': 'Error logging in'}), 500

# Add a new train (admin only)
@app.route('/trains', methods=['POST'])
def add_train_api():
    if request.headers.get('API-KEY') != 'your_admin_api_key':
        return jsonify({'message': 'Unauthorized'}), 401
    data = request.get_json()
    train_number = data.get('train_number')
    source = data.get('source')
    destination = data.get('destination')
    total_seats = data.get('total_seats')
    if not train_number or not source or not destination or not total_seats:
        return jsonify({'message': 'Invalid request'}), 400
    try:
        cursor.execute("INSERT INTO trains (train_number, source, destination, total_seats) VALUES (%s, %s, %s, %s)", (train_number, source, destination, total_seats))
        db.commit()
        return jsonify({'message': 'Train added successfully'})
    except mysql.connector.Error as err:
        return jsonify({'message': 'Error adding train'}), 500

# Get seat availability
@app.route('/trains/<source>/<destination>', methods=['GET'])
def get_seat_availability_api(source, destination):
    try:
        cursor.execute("SELECT * FROM trains WHERE source = %s AND destination = %s", (source, destination))
        trains = cursor.fetchall()
        availability = []
        for train in trains:
            cursor.execute("SELECT COUNT(*) FROM bookings WHERE train_number = %s", (train[0],))
            booked_seats = cursor.fetchone()[0]
            availability.append({'train_number': train[0], 'availability': train[3] - booked_seats})
        return jsonify(availability)
    except mysql.connector.Error as err:
        return jsonify({'message': 'Error getting seat availability'}), 500

# Book a seat
@app.route('/book', methods=['POST'])
def book_seat_api():
    token = request.headers.get('Authorization')
    if token!= 'ome_token':
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.get_json()
    train_number = data.get('train_number')
    username = data.get('username')

    if not train_number or not username:
        return jsonify({'message': 'Invalid request'}), 400

    try:
        # Check if the train exists
        cursor.execute("SELECT * FROM trains WHERE train_number = %s", (train_number,))
        train = cursor.fetchone()
        if not train:
            return jsonify({'message': 'Train not found'}), 404

        # Check if the user exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        # Check if the seat is available
        cursor.execute("SELECT COUNT(*) FROM bookings WHERE train_number = %s", (train_number,))
        booked_seats = cursor.fetchone()[0]
        if booked_seats >= train[3]:  # total_seats
            return jsonify({'message': 'Seat not available'}), 400

        # Book the seat
        cursor.execute("INSERT INTO bookings (train_number, username) VALUES (%s, %s)", (train_number, username))
        db.commit()
        return jsonify({'message': 'Seat booked successfully'})
    except mysql.connector.Error as err:
        return jsonify({'message': 'Error booking seat'}), 500

# Cancel booking
@app.route('/cancel', methods=['POST'])
def cancel_booking_api():
    token = request.headers.get('Authorization')
    if token!= 'ome_token':
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.get_json()
    train_number = data.get('train_number')
    username = data.get('username')

    if not train_number or not username:
        return jsonify({'message': 'Invalid request'}), 400

    try:
        # Check if the booking exists
        cursor.execute("SELECT * FROM bookings WHERE train_number = %s AND username = %s", (train_number, username))
        booking = cursor.fetchone()
        if not booking:
            return jsonify({'message': 'Booking not found'}), 404

        # Cancel the booking
        cursor.execute("DELETE FROM bookings WHERE train_number = %s AND username = %s", (train_number, username))
        db.commit()
        return jsonify({'message': 'Booking cancelled successfully'})
    except mysql.connector.Error as err:
        return jsonify({'message': 'Error cancelling booking'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)