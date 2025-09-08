from flask import Flask, render_template, request, jsonify
import csv
import os

app = Flask(__name__)

def json_body():
    data = request.get_json(silent=True)
    if not data:
        return None, jsonify({'success': False, 'message': 'No data provided'})
    return data, None

def _norm(value):
    return str(value).strip() if value else ''

class HotelManagement:
    def __init__(self):
        self.rooms = {}
        self.customers = {}
        self.bookings = {}
        self.max_rooms = 20
        self.load_data()

    def load_data(self):
        if os.path.exists('data/rooms.csv'):
            with open('data/rooms.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.rooms[row['room_number']] = {
                        'room_type': row['room_type'],
                        'price': float(row['price']),
                        'is_occupied': row['is_occupied'].lower() == 'true'
                    }

        if os.path.exists('data/customers.csv'):
            with open('data/customers.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.customers[row['customer_id']] = {
                        'name': row['name'],
                        'phone': row['phone']
                    }

        if os.path.exists('data/bookings.csv'):
            with open('data/bookings.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.bookings[row['booking_id']] = {
                        'customer_id': row['customer_id'],
                        'room_number': row['room_number']
                    }

    def save_data(self):
        os.makedirs('data', exist_ok=True)

        with open('data/rooms.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['room_number', 'room_type', 'price', 'is_occupied'])
            writer.writeheader()
            for room_number, info in self.rooms.items():
                writer.writerow({
                    'room_number': room_number,
                    'room_type': info['room_type'],
                    'price': info['price'],
                    'is_occupied': str(info['is_occupied'])
                })

        with open('data/customers.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['customer_id', 'name', 'phone'])
            writer.writeheader()
            for customer_id, info in self.customers.items():
                writer.writerow({
                    'customer_id': customer_id,
                    'name': info['name'],
                    'phone': info['phone']
                })

        with open('data/bookings.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['booking_id', 'customer_id', 'room_number'])
            writer.writeheader()
            for booking_id, info in self.bookings.items():
                writer.writerow({
                    'booking_id': booking_id,
                    'customer_id': info['customer_id'],
                    'room_number': info['room_number']
                })

    def add_room(self, room_number, room_type, price):
        try:
            room_number = _norm(room_number)
            room_type = _norm(room_type)
            if not all([room_number, room_type]) or price is None or float(price) <= 0:
                return False, "Invalid room details"
            if not (1001 <= int(room_number) <= 1020):
                return False, "Room number must be between 1001-1020"
            if room_number in self.rooms:
                return False, f"Room {room_number} already exists"
            if len(self.rooms) >= self.max_rooms:
                return False, f"Cannot add more rooms. Capacity {self.max_rooms} reached"
            self.rooms[room_number] = {'room_type': room_type, 'price': float(price), 'is_occupied': False}
            self.save_data()
            return True, f"Room {room_number} added successfully"
        except Exception as e:
            return False, f"Error adding room: {str(e)}"

    def remove_room(self, room_number):
        try:
            if room_number not in self.rooms:
                return False, "Room not found"
            if self.rooms[room_number]['is_occupied']:
                return False, "Room is occupied"
            del self.rooms[room_number]
            self.save_data()
            return True, f"Room {room_number} removed"
        except Exception as e:
            return False, f"Error removing room: {str(e)}"

    def add_customer(self, customer_id, name, phone):
        try:
            customer_id = _norm(customer_id)
            name = _norm(name)
            phone = _norm(phone)
            if not all([customer_id, name, phone]):
                return False, "Invalid customer details"
            if customer_id in self.customers:
                return False, "Customer ID exists"
            for existing in self.customers.values():
                if _norm(existing.get('phone')) == phone:
                    return False, "Customer with this phone already exists"
                if _norm(existing.get('name')) == name and _norm(existing.get('phone')) == phone:
                    return False, "Customer already exists"
            self.customers[customer_id] = {'name': name, 'phone': phone}
            self.save_data()
            return True, f"Customer {name} added"
        except Exception as e:
            return False, f"Error adding customer: {str(e)}"

    def remove_customer(self, customer_id):
        try:
            if customer_id not in self.customers:
                return False, "Customer not found"
            if any(b['customer_id'] == customer_id for b in self.bookings.values()):
                return False, "Customer has active bookings"
            del self.customers[customer_id]
            self.save_data()
            return True, "Customer removed"
        except Exception as e:
            return False, f"Error removing customer: {str(e)}"

    def book_room(self, customer_id, room_number):
        try:
            customer_id = _norm(customer_id)
            room_number = _norm(room_number)
            if not all([customer_id in self.customers, room_number in self.rooms]):
                return False, "Invalid customer or room"
            if self.rooms[room_number]['is_occupied']:
                return False, "Room is occupied"
            if any(b['customer_id'] == customer_id for b in self.bookings.values()):
                return False, "Customer already has an active booking"
            booking_id = f"B{len(self.bookings) + 1}"
            self.bookings[booking_id] = {'customer_id': customer_id, 'room_number': room_number}
            self.rooms[room_number]['is_occupied'] = True
            self.save_data()
            return True, f"Room {room_number} booked"
        except Exception as e:
            return False, f"Error booking room: {str(e)}"

    def checkout(self, room_number):
        try:
            if room_number not in self.rooms:
                return False, "Room not found"
            if not self.rooms[room_number]['is_occupied']:
                return False, "Room not occupied"
            for bid, booking in list(self.bookings.items()):
                if booking['room_number'] == room_number:
                    del self.bookings[bid]
                    break
            self.rooms[room_number]['is_occupied'] = False
            self.save_data()
            return True, f"Room {room_number} checked out"
        except Exception as e:
            return False, f"Error during checkout: {str(e)}"

    def available_rooms(self):
        return {rn: info for rn, info in self.rooms.items() if not info['is_occupied']}

    def stats(self):
        total = len(self.rooms)
        occupied = sum(1 for r in self.rooms.values() if r['is_occupied'])
        available = total - occupied
        return {
            'max_rooms': self.max_rooms,
            'total_rooms': total,
            'occupied_rooms': occupied,
            'available_rooms': available,
            'customers': len(self.customers),
            'bookings': len(self.bookings)
        }

hotel = HotelManagement()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/rooms', methods=['GET', 'POST', 'DELETE'])
def handle_rooms():
    try:
        if request.method == 'GET':
            return jsonify(hotel.rooms)
        elif request.method == 'POST':
            data, err = json_body()
            if err:
                return err
            success, msg = hotel.add_room(data['room_number'], data['room_type'], float(data['price']))
            return jsonify({'success': success, 'message': msg})
        elif request.method == 'DELETE':
            data, err = json_body()
            if err:
                return err
            success, msg = hotel.remove_room(data['room_number'])
            return jsonify({'success': success, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/api/rooms/available', methods=['GET'])
def get_available_rooms():
    try:
        return jsonify(hotel.available_rooms())
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/api/customers', methods=['GET', 'POST', 'DELETE'])
def handle_customers():
    try:
        if request.method == 'GET':
            return jsonify(hotel.customers)
        elif request.method == 'POST':
            data, err = json_body()
            if err:
                return err
            success, msg = hotel.add_customer(data['customer_id'], data['name'], data['phone'])
            return jsonify({'success': success, 'message': msg})
        elif request.method == 'DELETE':
            data, err = json_body()
            if err:
                return err
            success, msg = hotel.remove_customer(data['customer_id'])
            return jsonify({'success': success, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/api/bookings', methods=['GET', 'POST', 'DELETE'])
def handle_bookings():
    try:
        if request.method == 'GET':
            return jsonify(hotel.bookings)
        elif request.method == 'POST':
            data, err = json_body()
            if err:
                return err
            success, msg = hotel.book_room(data['customer_id'], data['room_number'])
            return jsonify({'success': success, 'message': msg})
        elif request.method == 'DELETE':
            data, err = json_body()
            if err:
                return err
            success, msg = hotel.checkout(data['room_number'])
            return jsonify({'success': success, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        return jsonify(hotel.stats())
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True)
    