from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:TierKun123@localhost/countering'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model untuk konfigurasi
class ConfigurationDown(db.Model):
    __tablename__ = 'ConfigurationDown'  # Nama tabel yang sesuai di database
    id = db.Column(db.Integer, primary_key=True)
    totalCapacity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "totalCapacity": self.totalCapacity,
            "timestamp": self.timestamp.isoformat()
        }

class ConfigurationUp(db.Model):
    __tablename__ = 'ConfigurationUp'  # Nama tabel yang sesuai di database
    id = db.Column(db.Integer, primary_key=True)
    totalCapacity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "totalCapacity": self.totalCapacity,
            "timestamp": self.timestamp.isoformat()
        }

# Model untuk log
class LogDown(db.Model):
    __tablename__ = 'LogDown'  # Nama tabel yang sesuai di database
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(50))
    state = db.Column(db.Integer)
    used = db.Column(db.Integer)
    available = db.Column(db.Integer)
    total = db.Column(db.Integer)
    description = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "location": self.location,
            "state": self.state,
            "used": self.used,
            "available": self.available,
            "total": self.total,
            "description": self.description,
            "timestamp": self.timestamp.isoformat()
        }

class LogUp(db.Model):
    __tablename__ = 'LogUp'  # Nama tabel yang sesuai di database
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(50))
    state = db.Column(db.Integer)
    used = db.Column(db.Integer)
    available = db.Column(db.Integer)
    total = db.Column(db.Integer)
    description = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "location": self.location,
            "state": self.state,
            "used": self.used,
            "available": self.available,
            "total": self.total,
            "description": self.description,
            "timestamp": self.timestamp.isoformat()
        }

setup_ran = False

@app.before_request
def setup_default_config():
    global setup_ran
    if not setup_ran:
        config = ConfigurationDown.query.first()
        if not config:
            default_capacity = 1500
            default_config = ConfigurationDown(totalCapacity=default_capacity)
            db.session.add(default_config)
            db.session.commit()
            print(f"Default ConfigurationDown created with totalCapacity = {default_capacity}")
        setup_ran = True

@app.route('/update-used', methods=['POST'])
def update_used():
    data = request.json
    new_used = data.get('newUsed')
    direction = data.get('direction')  # Up atau Down

    if new_used is None or not direction:
        return jsonify({"error": "Missing required fields"}), 400

    if direction == "up":
        config = ConfigurationUp.query.first()
        log_model = LogUp
    elif direction == "down":
        config = ConfigurationDown.query.first()
        log_model = LogDown
    else:
        return jsonify({"error": "Invalid direction"}), 400

    if not config:
        return jsonify({"error": f"Configuration{direction.capitalize()} not found. Please set the total capacity first."}), 404

    total_capacity = config.totalCapacity
    available = total_capacity - new_used

    updated_log = log_model(
        location="-",
        state=2,
        used=new_used,
        available=available,
        total=total_capacity,
        description=f"Updated used value to {new_used}"
    )

    db.session.add(updated_log)
    db.session.commit()

    return jsonify({"message": "Used value updated successfully", "log": updated_log.to_dict(), "overLimit": new_used > total_capacity}), 200

@app.route('/update-total', methods=['POST'])
def update_total():
    data = request.json
    new_total = data.get('newTotal')
    direction = data.get('direction')  # Up atau Down

    if new_total is None or not direction:
        return jsonify({"error": "Missing required fields"}), 400

    if direction == "up":
        config = ConfigurationUp.query.first()
        log_model = LogUp
    elif direction == "down":
        config = ConfigurationDown.query.first()
        log_model = LogDown
    else:
        return jsonify({"error": "Invalid direction"}), 400

    if config and config.totalCapacity == new_total:
        return jsonify({"error": "Total capacity still same"}), 200

    if config:
        config.totalCapacity = new_total
    else:
        config = ConfigurationDown(totalCapacity=new_total) if direction == "down" else ConfigurationUp(totalCapacity=new_total)
        db.session.add(config)

    latest_log = log_model.query.order_by(log_model.id.desc()).first()
    used = latest_log.used if latest_log else 0
    available = new_total - used

    updated_log = log_model(
        location="-",
        state=3,
        used=used,
        available=available,
        total=new_total,
        description=f"Updated total capacity to {new_total}"
    )

    db.session.add(updated_log)
    db.session.commit()

    return jsonify({
        "message": "Total capacity updated successfully",
        "config": config.to_dict(),
        "log": updated_log.to_dict()
    }), 200

@app.route('/count', methods=['POST'])
def count():
    data = request.json
    location = data.get('location')
    log_type = data.get('type')
    log_direction = data.get('direction')  # Up atau Down

    if not location or not log_type or not log_direction:
        return jsonify({"error": "Missing required fields"}), 400

    if log_type not in ["entrance", "exit"]:
        return jsonify({"error": "Invalid type"}), 400

    if log_direction == "up":
        config = ConfigurationUp.query.first()
        log_model = LogUp
    elif log_direction == "down":
        config = ConfigurationDown.query.first()
        log_model = LogDown
    else:
        return jsonify({"error": "Invalid direction"}), 400

    if not config:
        return jsonify({"error": f"Configuration{log_direction.capitalize()} not found. Please set the total capacity first."}), 404

    total_capacity = config.totalCapacity
    latest_log = log_model.query.order_by(log_model.id.desc()).first()

    used = latest_log.used if latest_log else 0
    available = total_capacity - used

    if log_type == "entrance":
        used += 1
    elif log_type == "exit":
        used = max(0, used - 1)

    available = total_capacity - used

    new_log = log_model(
        location=location,
        state=1 if log_type == "entrance" else 0,
        available=available,
        used=used,
        total=total_capacity,
        description=f"Entry recorded as {log_type} at {location}"
    )

    db.session.add(new_log)
    db.session.commit()

    return jsonify({"message": "Log created successfully", "log": new_log.to_dict()}), 200

@app.route('/receive', methods=['GET'])
def receive():
    direction = request.args.get('direction')  # Up atau Down

    if not direction:
        return jsonify({"error": "Missing required fields"}), 400

    log_model = LogUp if direction == "up" else LogDown
    latest_log = log_model.query.order_by(log_model.id.desc()).first()
    if not latest_log:
        return jsonify({"error": "No logs found"}), 404

    response = {
        "available": latest_log.available,
        "used": latest_log.used,
        "total": latest_log.total,
        "timestamp": latest_log.timestamp.isoformat()
    }

    return jsonify(response), 200

@app.template_filter('timestamp_to_jakarta')
def timestamp_to_jakarta(timestamp):
    if isinstance(timestamp, str):
        dt = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S')
    elif isinstance(timestamp, datetime):
        dt = timestamp
    else:
        raise TypeError("timestamp must be a string or datetime object")

    jakarta_time = dt + timedelta(hours=7)
    
    return jakarta_time.strftime('%H:%M:%S %d-%m-%Y')

@app.route('/get-latest-data')
def get_latest_data():
    direction = request.args.get('direction')  # Up atau Down

    if not direction:
        return jsonify({'error': 'Missing required fields'}), 400
    if direction not in ['up', 'down']:
        return jsonify({'error': 'Invalid direction'}), 400
    if direction == 'up':
        config = ConfigurationUp.query.first()
        logs = LogDown.query.order_by(LogDown.timestamp.desc()).limit(10).all()
    else:
        config = ConfigurationDown.query.first()
        logs = LogDown.query.order_by(LogDown.timestamp.desc()).limit(10).all()
    
    if not config:
        return jsonify({'error': 'No ConfigurationDown data found'}), 404


    log_list = [
        {
            'timestamp': timestamp_to_jakarta(log.timestamp),  # Convert timestamp to Jakarta time
            'location': log.location,
            'used': log.used,
            'available': log.available,
            'total': log.total,
            'description': log.description
        } for log in logs
    ] if logs else []

    response_data = {
        'timestamp': timestamp_to_jakarta(config.timestamp),
        'totalCapacity': config.totalCapacity,
        'logs': log_list
    }

    return jsonify(response_data)

# Route dan fungsionalitas aplikasi
@app.route('/configurations/<direction>', methods=['GET'])
def get_configuration(direction):
    if direction == 'up':
        config = ConfigurationUp.query.first()
    elif direction == 'down':
        config = ConfigurationDown.query.first()
    else:
        return jsonify({"error": "Invalid direction"}), 400

    if config is None:
        return jsonify({"error": "No configuration found"}), 404

    return jsonify(config.to_dict())

@app.route('/logs/<direction>', methods=['GET'])
def get_logs(direction):
    if direction == 'up':
        logs = LogUp.query.all()
    elif direction == 'down':
        logs = LogDown.query.all()
    else:
        return jsonify({"error": "Invalid direction"}), 400

    log_list = [log.to_dict() for log in logs]

    return jsonify(log_list)

@app.route('/')
def index():
    return render_template_string('''<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Log Management</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        .scrollable-table {
            max-height: 400px;
            overflow-y: auto;
        }
        .card-icon {
            font-size: 24px;
            margin-right: 8px;
            vertical-align: middle;
        }
        .card-value {
            font-size: 1.5rem;
            font-weight: bold;
        }
        .available-negative {
            color: #f87171;
        }
        .available-positive {
            color: #34d399;
        }
    </style>
</head>
<body class="bg-gray-900 text-white">
    <div class="max-w-4xl mx-auto p-4 pt-6 md:p-6 lg:p-12 bg-gray-800 rounded-lg shadow-lg">
        <h1 class="text-4xl font-bold text-blue-400 text-center mb-6">Parking Management</h1>

        <!-- Toggle Button -->
        <div class="text-center mb-6">
            <button id="toggleButton" class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg" onclick="toggleUpDown()">Up</button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div class="p-6 bg-gray-700 rounded-lg shadow-md flex items-center">
                <i class="fas fa-chart-line card-icon text-green-400"></i>
                <div>
                    <h2 class="text-xl font-semibold">Current Used</h2>
                    <p id="currentUsed" class="card-value">0</p>
                </div>
            </div>
            <div class="p-6 bg-gray-700 rounded-lg shadow-md flex items-center">
                <i class="fas fa-archive card-icon text-blue-400"></i>
                <div>
                    <h2 class="text-xl font-semibold">Current Available</h2>
                    <p id="currentAvailable" class="card-value">0</p>
                </div>
            </div>
        </div>

        <div class="mb-6 p-6 bg-gray-700 rounded-lg shadow-md">
            <h2 class="text-xl font-semibold mb-2">Current Configuration</h2>
            <p class="mb-2"><strong>Last Update:</strong> <span id="timestamp"></span></p>
            <p><strong>Total Capacity:</strong> <span id="totalCapacity"></span></p>
        </div>

        <div class="mb-6 p-6 bg-gray-700 rounded-lg shadow-md">
            <h2 class="text-xl font-semibold mb-2">Recent Logs</h2>
            <div class="scrollable-table">
                <table id="logsTable" class="w-full border-collapse text-sm">
                    <thead>
                        <tr>
                            <th class="px-4 py-2 text-left">Time (Jakarta)</th>
                            <th class="px-4 py-2 text-left">Location</th>
                            <th class="px-4 py-2 text-left">Used</th>
                            <th class="px-4 py-2 text-left">Available</th>
                            <th class="px-4 py-2 text-left">Total</th>
                            <th class="px-4 py-2 text-left">Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Logs will be inserted here -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <script>
        function handleButtonClick(direction) {
            fetch(`/get-latest-data?direction=${direction}`)
                .then(response => response.json())
                .then(data => {
                    if (data.timestamp !== undefined) {
                        document.getElementById('timestamp').innerText = data.timestamp;
                        document.getElementById('totalCapacity').innerText = data.totalCapacity;

                        const logsTable = document.getElementById('logsTable').querySelector('tbody');
                        logsTable.innerHTML = '';

                        data.logs.forEach((log) => {
                            const row = `<tr>
                                <td class="px-4 py-2">${log.timestamp}</td>
                                <td class="px-4 py-2">${log.location}</td>
                                <td class="px-4 py-2">${log.used}</td>
                                <td class="px-4 py-2 ${log.available <= 0 ? 'available-negative' : 'available-positive'}">${log.available}</td>
                                <td class="px-4 py-2">${log.total}</td>
                                <td class="px-4 py-2">${log.description}</td>
                            </tr>`;
                            logsTable.insertAdjacentHTML('beforeend', row);
                        });

                        const latestLog = data.logs[0] || {};
                        const availableElement = document.getElementById('currentAvailable');
                        const currentAvailable = latestLog.available || '0';

                        document.getElementById('currentUsed').innerText = latestLog.used || '0';
                        availableElement.innerText = currentAvailable;
                        availableElement.className = `card-value ${currentAvailable <= 0 ? 'available-negative' : 'available-positive'}`;
                    } else {
                        console.error('Data format error:', data);
                    }
                })
                .catch(error => {
                    console.error('Fetch error:', error);
                });
        }

        function toggleUpDown() {
            const button = document.getElementById('toggleButton');
            const currentDirection = button.innerText.toLowerCase();
            const newDirection = currentDirection === 'up' ? 'down' : 'up';

            // Update button text and color based on the new state
            button.innerText = newDirection.charAt(0).toUpperCase() + newDirection.slice(1);
            button.classList.toggle('bg-green-500', newDirection === 'up');
            button.classList.toggle('bg-red-500', newDirection === 'down');
            button.classList.toggle('hover:bg-green-700', newDirection === 'up');
            button.classList.toggle('hover:bg-red-700', newDirection === 'down');

            // Call handleButtonClick with the new direction
            handleButtonClick(newDirection);
        }

        // Initialize with the "up" state
        handleButtonClick('up');
        setInterval(() => {
            const button = document.getElementById('toggleButton');
            const currentDirection = button.innerText.toLowerCase();
            handleButtonClick(currentDirection);
        }, 1000);
    </script>
</body>
</html>''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)