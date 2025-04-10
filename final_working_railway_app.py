import streamlit as st
import mysql.connector
import hashlib
from datetime import datetime
import pandas as pd
import random

# Database connection
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Your MySQL username
        password="avighyan@2003",  # Your MySQL password
    )

# Initialize DB
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Drop existing database to start fresh (for development purposes)
    cursor.execute("DROP DATABASE IF EXISTS railwaydb")
    cursor.execute("CREATE DATABASE railwaydb")
    cursor.execute("USE railwaydb")
   
    # Create tables with corrected syntax
    cursor.execute("""
        CREATE TABLE users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE,
            password VARCHAR(255),
            full_name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(20),
            address TEXT,
            user_type ENUM('customer', 'admin', 'staff') DEFAULT 'customer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trains (
            train_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            train_number VARCHAR(50) UNIQUE,
            source VARCHAR(100),
            destination VARCHAR(100),
            departure_time DATETIME,
            arrival_time DATETIME,
            total_seats INT,
            available_seats INT,
            base_price DECIMAL(10,2),
            status ENUM('active', 'maintenance', 'cancelled') DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            station_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            code VARCHAR(10) UNIQUE,
            city VARCHAR(100),
            state VARCHAR(100),
            platform_count INT,
            is_junction BOOLEAN DEFAULT FALSE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS train_stops (
            stop_id INT AUTO_INCREMENT PRIMARY KEY,
            train_id INT,
            station_id INT,
            arrival_time TIME,
            departure_time TIME,
            sequence_number INT,
            distance_from_source INT,
            FOREIGN KEY (train_id) REFERENCES trains(train_id),
            FOREIGN KEY (station_id) REFERENCES stations(station_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            train_id INT,
            seats_booked INT,
            total_fare DECIMAL(10,2),
            booking_status ENUM('confirmed', 'waiting', 'cancelled') DEFAULT 'confirmed',
            pnr_number VARCHAR(15) UNIQUE,
            booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (train_id) REFERENCES trains(train_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS passengers (
            passenger_id INT AUTO_INCREMENT PRIMARY KEY,
            booking_id INT,
            name VARCHAR(255),
            age INT,
            gender ENUM('male', 'female', 'other'),
            seat_number VARCHAR(10),
            coach_number VARCHAR(10),
            FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coaches (
            coach_id INT AUTO_INCREMENT PRIMARY KEY,
            train_id INT,
            coach_type ENUM('sleeper', 'ac', 'seater', 'executive'),
            coach_number VARCHAR(10),
            total_seats INT,
            available_seats INT,
            FOREIGN KEY (train_id) REFERENCES trains(train_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INT AUTO_INCREMENT PRIMARY KEY,
            booking_id INT,
            amount DECIMAL(10,2),
            payment_method ENUM('credit_card', 'debit_card', 'net_banking', 'upi', 'wallet'),
            payment_status ENUM('pending', 'completed', 'failed', 'refunded'),
            transaction_id VARCHAR(255),
            payment_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cancellations (
            cancellation_id INT AUTO_INCREMENT PRIMARY KEY,
            booking_id INT,
            user_id INT,
            cancellation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            refund_amount DECIMAL(10,2),
            cancellation_reason TEXT,
            FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            train_id INT,
            rating INT CHECK (rating BETWEEN 1 AND 5),
            comments TEXT,
            feedback_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (train_id) REFERENCES trains(train_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            staff_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            designation VARCHAR(100),
            department VARCHAR(100),
            salary DECIMAL(10,2),
            joining_date DATE,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS train_schedule (
            schedule_id INT AUTO_INCREMENT PRIMARY KEY,
            train_id INT,
            day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'),
            runs_on_day BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (train_id) REFERENCES trains(train_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            announcement_id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255),
            content TEXT,
            start_date DATE,
            end_date DATE,
            is_active BOOLEAN DEFAULT TRUE,
            created_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        )
    """)

    # Insert sample data
    insert_sample_data(cursor)
    
    conn.commit()
    cursor.close()
    conn.close()

def insert_sample_data(cursor):
    # Insert sample users
    users = [
        ("john_doe", "password123", "John Doe", "john@example.com", "1234567890", "123 Main St", "customer"),
        ("alice_smith", "alicepassword", "Alice Smith", "alice@example.com", "2345678901", "456 Oak Ave", "customer"),
        ("bob_jones", "bobpassword", "Bob Jones", "bob@example.com", "3456789012", "789 Pine Rd", "customer"),
        ("charlie_brown", "charliepassword", "Charlie Brown", "charlie@example.com", "4567890123", "321 Elm St", "customer"),
        ("emily_davis", "emilypassword", "Emily Davis", "emily@example.com", "5678901234", "654 Maple Dr", "customer"),
        ("admin", "admin123", "System Admin", "admin@railway.com", "9876543210", "1 Admin Plaza", "admin"),
        ("staff1", "staff123", "Train Manager", "staff1@railway.com", "8765432109", "2 Staff Lane", "staff"),
        ("staff2", "staff123", "Ticket Inspector", "staff2@railway.com", "7654321098", "3 Staff Lane", "staff")
    ]
    for username, password, full_name, email, phone, address, user_type in users:
        cursor.execute("""
            INSERT IGNORE INTO users (username, password, full_name, email, phone, address, user_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (username, hash_password(password), full_name, email, phone, address, user_type))
    
    # Insert sample stations
    stations = [
        ("New York Central", "NYC", "New York", "New York", 15, True),
        ("Chicago Union", "CHI", "Chicago", "Illinois", 12, True),
        ("Los Angeles Terminal", "LAX", "Los Angeles", "California", 10, True),
        ("San Francisco Central", "SFC", "San Francisco", "California", 8, False),
        ("Miami Central", "MIA", "Miami", "Florida", 6, False),
        ("Denver Union", "DEN", "Denver", "Colorado", 9, True),
        ("Seattle King", "SEA", "Seattle", "Washington", 7, False)
    ]
    for name, code, city, state, platform_count, is_junction in stations:
        cursor.execute("""
            INSERT IGNORE INTO stations (name, code, city, state, platform_count, is_junction)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, code, city, state, platform_count, is_junction))
    
    # Insert sample trains
    trains = [
        ("Express 101", "EXP101", "New York", "Chicago", "2025-04-10 09:00:00", "2025-04-10 15:00:00", 200, 180, 75.50),
        ("SuperFast 202", "SF202", "Los Angeles", "San Francisco", "2025-04-10 08:00:00", "2025-04-10 10:00:00", 150, 120, 45.00),
        ("Coastal 303", "CST303", "Miami", "Orlando", "2025-04-10 07:30:00", "2025-04-10 09:30:00", 100, 80, 35.75),
        ("Mountain Express", "MTN404", "Denver", "Salt Lake City", "2025-04-11 07:00:00", "2025-04-11 13:00:00", 180, 150, 65.25),
        ("Pacific Cruiser", "PAC505", "Seattle", "San Diego", "2025-04-11 06:30:00", "2025-04-11 12:00:00", 220, 200, 85.00),
        ("Desert Flyer", "DES606", "Phoenix", "Las Vegas", "2025-04-12 08:30:00", "2025-04-12 12:00:00", 120, 100, 55.50),
        ("Midnight Express", "MID707", "Dallas", "Houston", "2025-04-13 00:15:00", "2025-04-13 06:15:00", 150, 130, 60.00)
    ]
    for name, train_number, source, destination, dep_time, arr_time, total_seats, available_seats, base_price in trains:
        cursor.execute("""
            INSERT IGNORE INTO trains (name, train_number, source, destination, departure_time, arrival_time, total_seats, available_seats, base_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, train_number, source, destination, dep_time, arr_time, total_seats, available_seats, base_price))
    
    # Insert train stops
    cursor.execute("SELECT train_id FROM trains WHERE name = 'Express 101'")
    exp101_id = cursor.fetchone()[0]
    cursor.execute("SELECT station_id FROM stations WHERE code IN ('NYC', 'CHI')")
    nyc_id, chi_id = [row[0] for row in cursor.fetchall()]
    cursor.execute("""
        INSERT IGNORE INTO train_stops (train_id, station_id, arrival_time, departure_time, sequence_number, distance_from_source)
        VALUES (%s, %s, NULL, '09:00:00', 1, 0),
               (%s, %s, '15:00:00', NULL, 2, 500)
    """, (exp101_id, nyc_id, exp101_id, chi_id))
    
    # Insert coaches
    cursor.execute("SELECT train_id FROM trains")
    train_ids = [row[0] for row in cursor.fetchall()]
    for train_id in train_ids:
        for i, coach_type in enumerate(['sleeper', 'ac', 'seater']):
            total_seats = random.randint(30, 50)
            cursor.execute("""
                INSERT IGNORE INTO coaches (train_id, coach_type, coach_number, total_seats, available_seats)
                VALUES (%s, %s, %s, %s, %s)
            """, (train_id, coach_type, f"{coach_type[0].upper()}{i+1}", total_seats, total_seats))
    
    # Insert train schedules
    for train_id in train_ids:
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            runs = random.choice([True, False])
            cursor.execute("""
                INSERT IGNORE INTO train_schedule (train_id, day_of_week, runs_on_day)
                VALUES (%s, %s, %s)
            """, (train_id, day, runs))
    
    # Insert sample bookings
    cursor.execute("SELECT user_id FROM users WHERE user_type = 'customer'")
    user_ids = [row[0] for row in cursor.fetchall()]
    for user_id in user_ids[:5]:
        train_id = random.choice(train_ids)
        seats = random.randint(1, 4)
        pnr = generate_pnr()
        cursor.execute("SELECT base_price FROM trains WHERE train_id = %s", (train_id,))
        base_price = cursor.fetchone()[0]
        total_fare = base_price * seats
        
        cursor.execute("""
            INSERT IGNORE INTO bookings (user_id, train_id, seats_booked, total_fare, pnr_number)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, train_id, seats, total_fare, pnr))
        
        # Insert passengers
        cursor.execute("""
    INSERT IGNORE INTO passengers (booking_id, name, age, gender, seat_number, coach_number)
    VALUES (%s, %s, %s, %s, %s, %s)
""", (booking_id, f"Passenger {i+1}", random.randint(18, 60), random.choice(['male', 'female']),
      f"{random.randint(1, 50)}", random.choice(['A1', 'B2', 'C3'])))

        
        # Insert payment
        cursor.execute("""
            INSERT IGNORE INTO payments (booking_id, amount, payment_method, payment_status, transaction_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (booking_id, total_fare, random.choice(['credit_card', 'debit_card', 'net_banking']), 
              'completed', f"TXN{random.randint(100000, 999999)}"))
    
    # Insert announcements
    announcements = [
        ("System Maintenance", "System will be down for maintenance on April 15 from 2AM to 4AM.", "2025-04-10", "2025-04-15", 6),
        ("New Trains Added", "Three new trains have been added to our fleet.", "2025-04-01", "2025-04-30", 6),
        ("Summer Discount", "Get 15% discount on all bookings made in April for summer travel.", "2025-04-01", "2025-04-30", 6)
    ]
    for title, content, start_date, end_date, created_by in announcements:
        cursor.execute("""
            INSERT IGNORE INTO announcements (title, content, start_date, end_date, created_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, content, start_date, end_date, created_by))
    
    # Insert staff
    cursor.execute("SELECT user_id FROM users WHERE user_type = 'staff'")
    staff_user_ids = [row[0] for row in cursor.fetchall()]
    for user_id in staff_user_ids:
        cursor.execute("""
            INSERT IGNORE INTO staff (user_id, designation, department, salary, joining_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, random.choice(['Manager', 'Inspector', 'Coordinator']), 
              random.choice(['Operations', 'Customer Service', 'Maintenance']),
              random.randint(3000, 8000), f"202{random.randint(0, 4)}-{random.randint(1, 12)}-{random.randint(1, 28)}"))
    
    # Insert feedback
    cursor.execute("SELECT user_id FROM users WHERE user_type = 'customer' LIMIT 3")
    feedback_user_ids = [row[0] for row in cursor.fetchall()]
    for user_id in feedback_user_ids:
        train_id = random.choice(train_ids)
        cursor.execute("""
            INSERT IGNORE INTO feedback (user_id, train_id, rating, comments)
            VALUES (%s, %s, %s, %s)
        """, (user_id, train_id, random.randint(3, 5), "Great service and comfortable journey!"))

# Utilities
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_pnr():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))

def user_exists(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE railwaydb")
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None

def register_user(username, password, full_name, email, phone, address):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE railwaydb")
    hashed_pw = hash_password(password)
    cursor.execute("""
        INSERT INTO users (username, password, full_name, email, phone, address, user_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (username, hashed_pw, full_name, email, phone, address, "customer"))
    conn.commit()
    cursor.close()
    conn.close()

def validate_login(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE railwaydb")
    cursor.execute("SELECT user_id, password, user_type FROM users WHERE username=%s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result and hash_password(password) == result[1]

def get_user_type(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE railwaydb")
    cursor.execute("SELECT user_type FROM users WHERE username=%s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def search_trains(source, destination, date=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE railwaydb")
    
    query = """
        SELECT t.*, 
               (SELECT GROUP_CONCAT(s.name SEPARATOR ', ') 
                FROM train_stops ts 
                JOIN stations s ON ts.station_id = s.station_id 
                WHERE ts.train_id = t.train_id AND ts.sequence_number > 1) AS stops
        FROM trains t
        WHERE t.source LIKE %s AND t.destination LIKE %s
    """
    params = [f"%{source}%", f"%{destination}%"]
    
    if date:
        query += " AND DATE(t.departure_time) = %s"
        params.append(date)
    
    query += " ORDER BY t.departure_time"
    
    cursor.execute(query, tuple(params))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def show_all_trains():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE railwaydb")
    cursor.execute("""
        SELECT t.*, 
               (SELECT GROUP_CONCAT(s.name SEPARATOR ', ') 
                FROM train_stops ts 
                JOIN stations s ON ts.station_id = s.station_id 
                WHERE ts.train_id = t.train_id AND ts.sequence_number > 1) AS stops
        FROM trains t
        ORDER BY t.name
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def get_train_details(train_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE railwaydb")
    cursor.execute("""
        SELECT t.*, 
               (SELECT GROUP_CONCAT(s.name SEPARATOR ' → ') 
                FROM train_stops ts 
                JOIN stations s ON ts.station_id = s.station_id 
                WHERE ts.train_id = t.train_id 
                ORDER BY ts.sequence_number) AS route
        FROM trains t
        WHERE t.train_id = %s
    """, (train_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def get_train_coaches(train_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE railwaydb")
    cursor.execute("""
        SELECT * FROM coaches 
        WHERE train_id = %s
        ORDER BY coach_type, coach_number
    """, (train_id,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def get_user_id(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE railwaydb")
    cursor.execute("SELECT user_id FROM users WHERE username=%s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def book_train(user_id, train_id, passengers):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE railwaydb")
    
    try:
        # Check seat availability
        cursor.execute("SELECT available_seats, base_price FROM trains WHERE train_id=%s", (train_id,))
        train = cursor.fetchone()
        if not train or train[0] < len(passengers):
            return None, "Not enough seats available"
        
        # Calculate total fare
        total_fare = train[1] * len(passengers)
        pnr = generate_pnr()
        
        # Create booking
        cursor.execute("""
            INSERT INTO bookings (user_id, train_id, seats_booked, total_fare, pnr_number)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, train_id, len(passengers), total_fare, pnr))
        
        booking_id = cursor.lastrowid
        
        # Add passengers
        for i, passenger in enumerate(passengers):
            cursor.execute("""
                INSERT INTO passengers (booking_id, name, age, gender, seat_number, coach_number)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (booking_id, passenger['name'], passenger['age'], passenger['gender'], 
                  f"{i+1}", passenger.get('coach', 'A1')))
        
        # Update available seats
        cursor.execute("""
            UPDATE trains SET available_seats = available_seats - %s 
            WHERE train_id = %s
        """, (len(passengers), train_id))
        
        # Create payment record
        cursor.execute("""
            INSERT INTO payments (booking_id, amount, payment_method, payment_status, transaction_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (booking_id, total_fare, 'credit_card', 'completed', f"TXN{random.randint(100000, 999999)}"))
        
        conn.commit()
        return booking_id, None
    
    except Exception as e:
        conn.rollback()
        return None, str(e)
    
    finally:
        cursor.close()
        conn.close()

def view_bookings(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE railwaydb")
    cursor.execute("""
        SELECT b.booking_id, b.pnr_number, t.name AS train_name, t.train_number, 
               t.source, t.destination, t.departure_time, t.arrival_time, 
               b.seats_booked, b.total_fare, b.booking_status, b.booking_time,
               p.payment_status, p.transaction_id
        FROM bookings b
        JOIN trains t ON b.train_id = t.train_id
        LEFT JOIN payments p ON b.booking_id = p.booking_id
        WHERE b.user_id = %s
        ORDER BY b.booking_time DESC
    """, (user_id,))
    bookings = cursor.fetchall()
    
    # Get passengers for each booking
    for booking in bookings:
        cursor.execute("""
            SELECT name, age, gender, seat_number, coach_number
            FROM passengers
            WHERE booking_id = %s
        """, (booking['booking_id'],))
        booking['passengers'] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return bookings

def cancel_booking(booking_id, user_id, reason=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE railwaydb")
    
    try:
        # Get booking details
        cursor.execute("""
            SELECT b.train_id, b.seats_booked, b.total_fare, t.base_price
            FROM bookings b
            JOIN trains t ON b.train_id = t.train_id
            WHERE b.booking_id = %s AND b.user_id = %s
        """, (booking_id, user_id))
        booking = cursor.fetchone()
        
        if not booking:
            return False, "Booking not found"
        
        train_id, seats_booked, total_fare, base_price = booking
        
        # Calculate refund (80% of fare)
        refund_amount = total_fare * 0.8
        
        # Update booking status
        cursor.execute("""
            UPDATE bookings 
            SET booking_status = 'cancelled' 
            WHERE booking_id = %s
        """, (booking_id,))
        
        # Update available seats
        cursor.execute("""
            UPDATE trains 
            SET available_seats = available_seats + %s 
            WHERE train_id = %s
        """, (seats_booked, train_id))
        
        # Update payment status
        cursor.execute("""
            UPDATE payments 
            SET payment_status = 'refunded' 
            WHERE booking_id = %s
        """, (booking_id,))
        
        # Record cancellation
        cursor.execute("""
            INSERT INTO cancellations (booking_id, user_id, refund_amount, cancellation_reason)
            VALUES (%s, %s, %s, %s)
        """, (booking_id, user_id, refund_amount, reason))
        
        conn.commit()
        return True, None
    
    except Exception as e:
        conn.rollback()
        return False, str(e)
    
    finally:
        cursor.close()
        conn.close()

def admin_add_train(name, train_number, source, destination, dep_time, arr_time, total_seats, base_price):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE railwaydb")
    
    try:
        cursor.execute("""
            INSERT INTO trains (name, train_number, source, destination, departure_time, arrival_time, total_seats, available_seats, base_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, train_number, source, destination, dep_time, arr_time, total_seats, total_seats, base_price))
        
        train_id = cursor.lastrowid
        
        # Add default coaches
        coach_types = ['sleeper', 'ac', 'seater']
        for i, coach_type in enumerate(coach_types):
            coach_seats = total_seats // len(coach_types)
            cursor.execute("""
                INSERT INTO coaches (train_id, coach_type, coach_number, total_seats, available_seats)
                VALUES (%s, %s, %s, %s, %s)
            """, (train_id, coach_type, f"{coach_type[0].upper()}{i+1}", coach_seats, coach_seats))
        
        conn.commit()
        return True, None
    
    except Exception as e:
        conn.rollback()
        return False, str(e)
    
    finally:
        cursor.close()
        conn.close()

def admin_view_all_bookings():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE railwaydb")
    cursor.execute("""
        SELECT b.booking_id, b.pnr_number, u.full_name, t.name AS train_name, 
               t.source, t.destination, b.seats_booked, b.total_fare, 
               b.booking_status, b.booking_time, p.payment_status
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        JOIN trains t ON b.train_id = t.train_id
        LEFT JOIN payments p ON b.booking_id = p.booking_id
        ORDER BY b.booking_time DESC
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def admin_view_all_users():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE railwaydb")
    cursor.execute("""
        SELECT user_id, username, full_name, email, phone, user_type, created_at
        FROM users
        ORDER BY created_at DESC
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def admin_view_train_performance():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE railwaydb")
    cursor.execute("""
        SELECT t.train_id, t.name, t.train_number, 
               COUNT(b.booking_id) AS total_bookings,
               SUM(b.seats_booked) AS total_passengers,
               SUM(b.total_fare) AS total_revenue,
               AVG(f.rating) AS avg_rating
        FROM trains t
        LEFT JOIN bookings b ON t.train_id = b.train_id
        LEFT JOIN feedback f ON t.train_id = f.train_id
        GROUP BY t.train_id
        ORDER BY total_revenue DESC
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def get_announcements():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE railwaydb")
    cursor.execute("""
        SELECT title, content 
        FROM announcements 
        WHERE is_active = TRUE 
        AND start_date <= CURDATE() 
        AND end_date >= CURDATE()
        ORDER BY created_at DESC
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def submit_feedback(user_id, train_id, rating, comments):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE railwaydb")
    
    try:
        cursor.execute("""
            INSERT INTO feedback (user_id, train_id, rating, comments)
            VALUES (%s, %s, %s, %s)
        """, (user_id, train_id, rating, comments))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

def get_user_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("USE railwaydb")
    cursor.execute("""
        SELECT username, full_name, email, phone, address, user_type, created_at
        FROM users
        WHERE user_id = %s
    """, (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def update_user_profile(user_id, full_name, email, phone, address):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("USE railwaydb")
    
    try:
        cursor.execute("""
            UPDATE users
            SET full_name = %s, email = %s, phone = %s, address = %s
            WHERE user_id = %s
        """, (full_name, email, phone, address, user_id))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cursor.close()
        conn.close()

# Init DB
# init_db()  # Disabled to avoid dropping DB every time

# Streamlit App
st.set_page_config(page_title="Railway Management System", page_icon="🚆", layout="wide")
st.title("🚆 Railway Management System")

# Display announcements
announcements = get_announcements()
if announcements:
    with st.expander("📢 Announcements", expanded=True):
        for ann in announcements:
            st.info(f"**{ann['title']}**: {ann['content']}")

# Session state
if "username" not in st.session_state:
    st.session_state.username = None
    st.session_state.user_id = None
    st.session_state.user_type = None

# Login/Register
if not st.session_state.username:
    auth_option = st.radio("Select Option", ["Login", "Register"], horizontal=True)
    
    if auth_option == "Register":
        st.subheader("Create New Account")
        with st.form("register_form"):
            new_user = st.text_input("Username")
            new_pass = st.text_input("Password", type="password")
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone Number")
            address = st.text_area("Address")
            
            if st.form_submit_button("Register"):
                if user_exists(new_user):
                    st.error("Username already exists!")
                else:
                    register_user(new_user, new_pass, full_name, email, phone, address)
                    st.success("Registered successfully! Please login.")

    elif auth_option == "Login":
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login"):
                if validate_login(user, pwd):
                    st.session_state.username = user
                    st.session_state.user_id = get_user_id(user)
                    st.session_state.user_type = get_user_type(user)
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

# Logged-in User
else:
    # User profile section
    user_profile = get_user_profile(st.session_state.user_id)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### Welcome, {user_profile['full_name']} ({st.session_state.user_type.capitalize()})")
    with col2:
        if st.button("Logout"):
            st.session_state.username = None
            st.session_state.user_id = None
            st.session_state.user_type = None
            st.success("Logged out successfully!")
            st.rerun()
    
    # Main menu based on user type
    if st.session_state.user_type == 'customer':
        menu = st.sidebar.selectbox("Menu", ["Search Trains", "Book Ticket", "My Bookings", "My Profile", "Feedback"])
        if menu == "Search Trains":
            st.subheader("🔍 Search Trains")
            with st.form("search_form"):
                col1, col2 = st.columns(2)
                with col1:
                    src = st.text_input("From Station")
                with col2:
                    dest = st.text_input("To Station")
                travel_date = st.date_input("Travel Date", datetime.now())

                if st.form_submit_button("Search Trains"):
                    results = search_trains(src, dest, travel_date)
                    if results:
                        st.success(f"Found {len(results)} trains")
                        for train in results:
                            with st.expander(f"{train['name']} ({train['train_number']})"):
                                st.write(f"From: {train['source']} → To: {train['destination']}")
                                st.write(f"Departure: {train['departure_time']} | Arrival: {train['arrival_time']}")
                                st.write(f"Available Seats: {train['available_seats']} | Price: ${train['base_price']}")
                                st.write(f"Stops: {train['stops']}")
                    else:
                        st.warning("No trains found for the given criteria.")
        elif menu == "Book Ticket":
            st.subheader("🎟️ Book Train Ticket")

            trains = show_all_trains()
            train_map = {f"{t['name']} ({t['train_number']})": t['train_id'] for t in trains}

            with st.form("book_form"):
                selected_train = st.selectbox("Select Train", list(train_map.keys()))
                num_passengers = st.number_input("Number of Passengers", min_value=1, max_value=6, step=1)

                passenger_data = []
                for i in range(num_passengers):
                    st.markdown(f"**Passenger {i + 1}**")
                    name = st.text_input(f"Name (P{i+1})", key=f"name_{i}")
                    age = st.number_input(f"Age (P{i+1})", min_value=0, max_value=100, key=f"age_{i}")
                    gender = st.selectbox(f"Gender (P{i+1})", ["male", "female", "other"], key=f"gender_{i}")
                    coach = st.text_input(f"Coach (P{i+1})", value="A1", key=f"coach_{i}")
                    passenger_data.append({"name": name, "age": age, "gender": gender, "coach": coach})

                if st.form_submit_button("Book Ticket"):
                    if any(p['name'].strip() == "" for p in passenger_data):
                        st.warning("All passenger names are required.")
                    else:
                        train_id = train_map[selected_train]
                        booking_id, err = book_train(st.session_state.user_id, train_id, passenger_data)
                        if booking_id:
                            st.success(f"Booking successful! Your PNR: {view_bookings(st.session_state.user_id)[0]['pnr_number']}")
                        else:
                            st.error(f"Booking failed: {err}")
                

        elif menu == "My Profile":
            st.subheader("👤 My Profile")
            user_profile = get_user_profile(st.session_state.user_id)
            if user_profile:
                with st.form("profile_form"):
                    full_name = st.text_input("Full Name", user_profile['full_name'])
                    email = st.text_input("Email", user_profile['email'])
                    phone = st.text_input("Phone", user_profile['phone'])
                    address = st.text_area("Address", user_profile['address'])

                    if st.form_submit_button("Update Profile"):
                        success, err = update_user_profile(st.session_state.user_id, full_name, email, phone, address)
                        if success:
                            st.success("Profile updated successfully!")
                            st.rerun()
                        else:
                            st.error(f"Update failed: {err}")

        elif menu == "My Bookings":
            st.subheader("📜 My Bookings")
            bookings = view_bookings(st.session_state.user_id)
            if bookings:
                for booking in bookings:
                    with st.expander(f"PNR: {booking['pnr_number']} | {booking['train_name']}"):
                        st.write(f"Route: {booking['source']} → {booking['destination']}")
                        st.write(f"Departure: {booking['departure_time']} | Arrival: {booking['arrival_time']}")
                        st.write(f"Seats Booked: {booking['seats_booked']} | Fare: ${booking['total_fare']}")
                        st.write(f"Status: {booking['booking_status']} | Payment: {booking['payment_status']}")
                        st.write("Passengers:")
                        for p in booking['passengers']:
                            st.write(f"- {p['name']}, {p['age']} yrs, {p['gender']}, Seat: {p['seat_number']} Coach: {p['coach_number']}")

        elif menu == "Feedback":
            st.subheader("💬 Submit Feedback")
            trains = show_all_trains()
            train_options = {f"{t['name']} ({t['train_number']})": t['train_id'] for t in trains}
            with st.form("feedback_form"):
                train_selection = st.selectbox("Select Train", list(train_options.keys()))
                rating = st.slider("Rating (1 = Bad, 5 = Excellent)", 1, 5, 4)
                comments = st.text_area("Comments")
                if st.form_submit_button("Submit Feedback"):
                    train_id = train_options[train_selection]
                    success, error = submit_feedback(st.session_state.user_id, train_id, rating, comments)
                    if success:
                        st.success("Feedback submitted successfully!")
                    else:
                        st.error(f"Failed to submit feedback: {error}")
            
            
            if menu == "Search Trains":
                st.subheader("🔍 Search Trains")
                with st.form("search_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        src = st.text_input("From Station")
                    with col2:
                        dest = st.text_input("To Station")
                    
                    travel_date = st.date_input("Travel Date", datetime.now())
                    
                    if st.form_submit_button("Search Trains"):
                        results = search_trains(src, dest, travel_date)
                        if results:
                            st.success(f"Found {len(results)} trains")
                        