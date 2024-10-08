from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:TierKun123@localhost:3304/countering'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model untuk konfigurasi
class ConfigurationDown(db.Model):
    __tablename__ = 'ConfigurationDown'
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
    __tablename__ = 'ConfigurationUp'
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
    __tablename__ = 'LogDown'
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
    __tablename__ = 'LogUp'
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
    direction = request.args.get('direction')  # Up, Down, atau Total

    if not direction:
        return jsonify({'error': 'Missing required fields'}), 400

    if direction == 'up':
        config = ConfigurationUp.query.first()
        logs = LogUp.query.order_by(LogUp.id.desc()).limit(20).all()  # Mengurutkan berdasarkan ID terbaru
    elif direction == 'down':
        config = ConfigurationDown.query.first()
        logs = LogDown.query.order_by(LogDown.id.desc()).limit(20).all()  # Mengurutkan berdasarkan ID terbaru
    elif direction == 'total':
        # Mengambil data terbaru dari kedua arah
        config_up = ConfigurationUp.query.first()
        config_down = ConfigurationDown.query.first()

        if not config_up or not config_down:
            return jsonify({'error': 'No Configuration data found'}), 404

        # Menggabungkan total kapasitas dari kedua arah
        total_capacity = config_up.totalCapacity + config_down.totalCapacity

        # Mengambil log terbaru dari masing-masing arah, diurutkan berdasarkan ID terbaru
        logs_up = LogUp.query.order_by(LogUp.id.desc()).limit(10).all()
        logs_down = LogDown.query.order_by(LogDown.id.desc()).limit(10).all()

        # Gabungkan logs dari up dan down, kemudian urutkan berdasarkan ID terbaru
        logs = logs_up + logs_down

        # Sorting logs berdasarkan timestamp terbaru
        logs = sorted(logs, key=lambda x: x.timestamp, reverse=True)

        # Menjumlahkan total `used` dan `available` untuk kedua arah log terbaru saja
        uplogs_new = logs_up[0] if logs_up else None
        downlogs_new = logs_down[0] if logs_down else None


        total_used = (uplogs_new.used if uplogs_new else 0) + (downlogs_new.used if downlogs_new else 0)
        total_available = (uplogs_new.available if uplogs_new else config_up.totalCapacity) + (downlogs_new.available if downlogs_new else config_down.totalCapacity)

        log_list = [
            {
                'timestamp': timestamp_to_jakarta(log.timestamp),
                'state': log.state,
                'location': log.location,
                'used': log.used,
                'available': log.available,
                'total': log.total,
                'description': log.description
            } for log in logs
        ]

        response_data = {
            'timestamp': max(config_up.timestamp, config_down.timestamp).isoformat(),
            'totalCapacity': total_capacity,
            'currentUsed': total_used,  # Menampilkan total current used
            'currentAvailable': total_available,  # Menampilkan total current available
            'logs': log_list
        }

        return jsonify(response_data)

    else:
        return jsonify({'error': 'Invalid direction'}), 400

    if not config:
        return jsonify({'error': f'No Configuration{direction.capitalize()} data found'}), 404

    log_list = [
        {
            'timestamp': timestamp_to_jakarta(log.timestamp),
            'state': log.state,
            'location': log.location,
            'used': log.used,
            'available': log.available,
            'total': log.total,
            'description': log.description
        } for log in logs
    ]

    response_data = {
        'timestamp': config.timestamp.isoformat(),
        'totalCapacity': config.totalCapacity,
        'currentUsed': logs[0].used if logs else 0,  # Mengambil used dari log terbaru
        'currentAvailable': logs[0].available if logs else config.totalCapacity,  # Mengambil available dari log terbaru
        'logs': log_list
    }

    return jsonify(response_data)

@app.route('/receive')
def receive():
    direction = request.args.get('direction')  # Up, Down, atau Total

    if not direction:
        return jsonify({'error': 'Missing required fields'}), 400

    if direction == 'up':
        config = ConfigurationUp.query.first()
        logs = LogUp.query.order_by(LogUp.id.desc()).limit(10).all()  # Mengurutkan berdasarkan ID terbaru
    elif direction == 'down':
        config = ConfigurationDown.query.first()
        logs = LogDown.query.order_by(LogDown.id.desc()).limit(10).all()  # Mengurutkan berdasarkan ID terbaru
    elif direction == 'total':
        # Mengambil data terbaru dari kedua arah
        config_up = ConfigurationUp.query.first()
        config_down = ConfigurationDown.query.first()

        if not config_up or not config_down:
            return jsonify({'error': 'No Configuration data found'}), 404

        # Menggabungkan total kapasitas dari kedua arah
        total_capacity = config_up.totalCapacity + config_down.totalCapacity

        # Mengambil log terbaru dari masing-masing arah, diurutkan berdasarkan ID terbaru
        logs_up = LogUp.query.order_by(LogUp.id.desc()).limit(5).all()
        logs_down = LogDown.query.order_by(LogDown.id.desc()).limit(5).all()

        # Gabungkan logs dari up dan down, kemudian urutkan berdasarkan ID terbaru
        logs = logs_up + logs_down
        logs = sorted(logs, key=lambda x: x.id, reverse=True)[:10]

        # Menjumlahkan total `used` dan `available` untuk kedua arah log terbaru saja
        uplogs_new = logs_up[0] if logs_up else None
        downlogs_new = logs_down[0] if logs_down else None


        total_used = (uplogs_new.used if uplogs_new else 0) + (downlogs_new.used if downlogs_new else 0)
        total_available = (uplogs_new.available if uplogs_new else config_up.totalCapacity) + (downlogs_new.available if downlogs_new else config_down.totalCapacity)

        log_list = [
            {
                'timestamp': timestamp_to_jakarta(log.timestamp),
                'location': log.location,
                'used': log.used,
                'available': log.available,
                'total': log.total,
                'description': log.description
            } for log in logs
        ]

        response_data = {
            'timestamp': max(config_up.timestamp, config_down.timestamp).isoformat(),
            'totalCapacity': total_capacity,
            'currentUsed': total_used,  # Menampilkan total current used
            'currentAvailable': total_available,  # Menampilkan total current available
            'logs': log_list
        }

        return jsonify(response_data)

    else:
        return jsonify({'error': 'Invalid direction'}), 400

    if not config:
        return jsonify({'error': f'No Configuration{direction.capitalize()} data found'}), 404

    log_list = [
        {
            'timestamp': timestamp_to_jakarta(log.timestamp),
            'location': log.location,
            'used': log.used,
            'available': log.available,
            'total': log.total,
            'description': log.description
        } for log in logs
    ]

    response_data = {
        'timestamp': config.timestamp.isoformat(),
        'totalCapacity': config.totalCapacity,
        'currentUsed': logs[0].used if logs else 0,  # Mengambil used dari log terbaru
        'currentAvailable': logs[0].available if logs else config.totalCapacity,  # Mengambil available dari log terbaru
        'logs': log_list
    }

    return jsonify(response_data)

# Route untuk update used
@app.route('/update-used', methods=['POST'])
def update_used():
    data = request.json
    try:
        new_used = int(data.get('newUsed'))  # Parse newUsed menjadi integer
    except (TypeError, ValueError):
        return jsonify({"error": "newUsed must be an integer"}), 400

    direction = data.get('direction')

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


# Route untuk update total
@app.route('/update-total', methods=['POST'])
def update_total():
    data = request.json
    try:
        new_total = int(data.get('newTotal'))  # Parse newTotal menjadi integer
    except (TypeError, ValueError):
        return jsonify({"error": "newTotal must be an integer"}), 400

    direction = data.get('direction')

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
        description=f"Recorded {log_type} at {location}"
    )

    db.session.add(new_log)
    db.session.commit()

    return jsonify({"message": "Log created successfully", "log": new_log.to_dict()}), 200

@app.route('/')
def index():
    return render_template_string('''<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Parking Management</title>
    <link rel="icon" href="https://yt3.ggpht.com/a/AGF-l7_uB8jTXsIt1a2YbzprWQa0QlutQfKRfCcX7g=s900-c-k-c0xffffffff-no-rj-mo" type="image/x-icon">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
    .scrollable-table {
        max-height: 400px;
        overflow-y: auto;
        position: relative;
    }
    .scrollable-table thead th {
        position: sticky;
        top: 0;
        background-color: #2d3748; /* Adjust based on your background */
        z-index: 1;
        box-shadow: 0 2px 2px -1px rgba(0, 0, 0, 0.4);
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
    .card {
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }
    .card:hover {
        border-color: #60a5fa;
        transform: translateY(-5px);
    }
    .hidden {
        display: none;
    }
    .modal {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 300px;
        background-color: white;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
        z-index: 1000;
        padding: 20px;
        border-radius: 8px;
    }

    .modal-content {
        margin-bottom: 20px;
        text-align: center;
        color: #333;
    }

    .modal-footer {
        text-align: right;
    }

    .modal-close {
        background-color: #007bff;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 4px;
        cursor: pointer;
    }

    .modal-close:hover {
        background-color: #0056b3;
    }

    .modal-error {
        color: #f87171; /* Red color for errors */
    }
</style>
</head>
<body class="bg-gray-900 text-white">

    <div class="max-w-7xl mx-auto p-6 bg-gray-800 rounded-lg shadow-lg">

        <!-- Title -->
        <h1 class="text-4xl font-bold text-blue-400 text-center mb-6">Parking Management</h1>

        <!-- State Selection Buttons -->
        <div class="text-center mb-6">
            <button class="text-white font-bold py-2 px-6 rounded-lg bg-gradient-to-r from-green-400 to-blue-500 hover:from-green-500 hover:to-blue-600 shadow-lg mr-2" onclick="setDirection('up')">
                <i class="fas fa-arrow-up mr-2"></i>Up
            </button>
            <button class="text-white font-bold py-2 px-6 rounded-lg bg-gradient-to-r from-red-400 to-pink-500 hover:from-red-500 hover:to-pink-600 shadow-lg mr-2" onclick="setDirection('down')">
                <i class="fas fa-arrow-down mr-2"></i>Down
            </button>
            <button class="text-white font-bold py-2 px-6 rounded-lg bg-gradient-to-r from-purple-400 to-indigo-500 hover:from-purple-500 hover:to-indigo-600 shadow-lg" onclick="setDirection('total')">
                <i class="fas fa-chart-pie mr-2"></i>Total
            </button>
        </div>

        <!-- Current Status Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4 mb-6">
            <div class="p-6 bg-gray-700 rounded-lg shadow-md flex items-center card">
                <i class="fas fa-chart-line card-icon text-green-400"></i>
                <div>
                    <h2 class="text-xl font-semibold">Current Used</h2>
                    <p id="currentUsed" class="card-value">0</p>
                </div>
            </div>
            <div class="p-6 bg-gray-700 rounded-lg shadow-md flex items-center card">
                <i class="fas fa-archive card-icon text-blue-400"></i>
                <div>
                    <h2 class="text-xl font-semibold">Current Available</h2>
                    <p id="currentAvailable" class="card-value">0</p>
                </div>
            </div>
        </div>

        <!-- Current Configuration -->
        <div class="mb-6 p-6 bg-gray-700 rounded-lg shadow-md">
            <h2 class="text-xl font-semibold mb-2">Current Configuration</h2>
            <!-- <p class="mb-2"><strong>Last Update:</strong> <span id="timestamp"></span></p> -->
            <p><strong>Total Capacity:</strong> <span id="totalCapacity"></span></p>
            <p class="mt-4"><strong>Current State:</strong> <span id="currentState" class="text-purple-400"></span></p>
        </div>

        <!-- Recent Logs -->
        <div class="mb-6 p-6 bg-gray-700 rounded-lg shadow-md">
            <h2 class="text-xl font-semibold mb-2">Recent Logs</h2>
            <div class="scrollable-table">
                <table id="logsTable" class="w-full border-collapse text-sm">
                    <thead>
                        <tr>
                            <th class="px-4 py-2 text-left">Time (Jakarta)</th>
                            <th class="px-4 py-2 text-left">Location</th>
                            <th class="px-4 py-2 text-left">Status</th>
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
                                  
        <!-- Modal Structure -->
        <div id="messageModal" class="modal" style="display:none;">
            <div id="modalContent" class="modal-content">
                <p id="modalMessage"></p>
            </div>
            <div class="modal-footer">
                <button id="modalCloseBtn" class="modal-close btn">Close</button>
            </div>
        </div>

        <!-- Update Used -->
        <div class="mb-6" id="updateUsedSection">
            <h2 class="text-xl font-semibold mb-2">Update Used</h2>
            <div class="flex">
                <input type="number" id="usedInput" placeholder="Enter new used value" class="flex-grow p-3 rounded-lg text-black">
                <button onclick="updateUsed()" class="bg-gradient-to-r from-green-400 to-blue-500 hover:from-green-500 hover:to-blue-600 text-white font-bold py-2 px-6 rounded-lg ml-4 shadow-lg">Update Used</button>
            </div>
        </div>

        <!-- Update Total -->
        <div class="mb-6" id="updateTotalSection">
            <h2 class="text-xl font-semibold mb-2">Update Total</h2>
            <div class="flex">
                <input type="number" id="totalInput" placeholder="Enter new total capacity" class="flex-grow p-3 rounded-lg text-black">
                <button onclick="updateTotal()" class="bg-gradient-to-r from-blue-400 to-indigo-500 hover:from-blue-500 hover:to-indigo-600 text-white font-bold py-2 px-6 rounded-lg ml-4 shadow-lg">Update Total</button>
            </div>
        </div>

    </div>

    <script>
        let currentDirection = 'total';  // Default direction is 'total'

        function setDirection(direction) {
            currentDirection = direction;
            handleButtonClick(direction);
            updateCurrentState();
            toggleUpdateForms();
        }

        function updateCurrentState() {
            const stateText = currentDirection.charAt(0).toUpperCase() + currentDirection.slice(1);
            const stateColor = {
                'up': 'text-green-400',
                'down': 'text-red-400',
                'total': 'text-purple-400'
            };
            document.getElementById('currentState').innerText = stateText;
            document.getElementById('currentState').className = stateColor[currentDirection];
        }

        function toggleUpdateForms() {
            const updateUsedSection = document.getElementById('updateUsedSection');
            const updateTotalSection = document.getElementById('updateTotalSection');

            if (currentDirection === 'total') {
                updateUsedSection.classList.add('hidden');
                updateTotalSection.classList.add('hidden');
            } else {
                updateUsedSection.classList.remove('hidden');
                updateTotalSection.classList.remove('hidden');
            }
        }

        function showModal(message, isError = false) {
            const modalMessage = document.getElementById('modalMessage');
            const modal = document.getElementById('messageModal');
            modalMessage.textContent = message;
            modalMessage.className = isError ? 'modal-content modal-error' : 'modal-content';
            modal.style.display = 'block';

            document.getElementById('modalCloseBtn').onclick = function() {
                modal.style.display = 'none';
            };
        }

        function updateUsed() {
            const newUsed = document.getElementById('usedInput').value;
            if(newUsed === '') {
                showModal('Please enter a value', true);
                return;
            }
            if(newUsed > 9999) {
                showModal('Used value cannot exceed 9999', true);
                document.getElementById('usedInput').value = '';
                return;
            }
            fetch('/update-used', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ newUsed, direction: currentDirection })
            })
            .then(response => response.json())
            .then(data => {
            document.getElementById('usedInput').value = '';
                if (data.message) {
                    showModal(data.message, data.success === false);
                    handleButtonClick(currentDirection);
                }
            })
            .catch(error => {
                showModal('Error updating used: ' + error.message, true);
            });
        }

        function updateTotal() {
            const newTotal = document.getElementById('totalInput').value;
            if(newTotal === '') {
                showModal('Please enter a value', true);
                return;
            }
            if(newTotal > 9999) {
                showModal('Used value cannot exceed 9999', true);
                document.getElementById('totalInput').value = '';
                return;
            }
            fetch('/update-total', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ newTotal, direction: currentDirection })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('totalInput').value = '';
                if (data.message) {
                    showModal(data.message, data.success === false);
                    handleButtonClick(currentDirection);
                }
            })
            .catch(error => {
                showModal('Error updating total: ' + error.message, true);
            });
        }
                                  
        window.onclick = function(event) {
            const modal = document.getElementById('messageModal');
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        };

        function handleButtonClick(direction) {
            fetch(`/get-latest-data?direction=${direction}`)
                .then(response => response.json())
                .then(data => {
                    if (data.timestamp !== undefined) {
                        //document.getElementById('timestamp').innerText = data.timestamp;
                        document.getElementById('totalCapacity').innerText = data.totalCapacity;

                        const logsTable = document.getElementById('logsTable').querySelector('tbody');
                        logsTable.innerHTML = '';
                                  
                        const statusColor = {
                            2: 'text-yellow-400',
                            1: 'text-green-400',
                            0: 'text-red-400'
                        };
                                  
                        const statusText = {
                            2: 'Edit',
                            1: 'Entrance',
                            0: 'Exit'
                        };

                        data.logs.forEach((log) => {
                            const row = `<tr>
                                <td class="px-4 py-2">${log.timestamp}</td>
                                <td class="px-4 py-2">${log.location}</td>
                                <td class="px-4 py-2"><span class="${statusColor[log.state]} bg-gray-800 rounded px-2 py-1">${statusText[log.state]}</span></td>
                                <td class="px-4 py-2">${log.used}</td>
                                <td class="px-4 py-2 ${log.available <= 0 ? 'available-negative' : 'available-positive'}">${log.available}</td>
                                <td class="px-4 py-2">${log.total}</td>
                                <td class="px-4 py-2">${log.description}</td>
                            </tr>`;
                            logsTable.insertAdjacentHTML('beforeend', row);
                        });

                        const latestLog = data || {};
                        const availableElement = document.getElementById('currentAvailable');
                        const currentAvailable = latestLog.currentAvailable || '0';

                        document.getElementById('currentUsed').innerText = latestLog.currentUsed || '0';
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

        // Initialize with the "total" state
        handleButtonClick('total');
        updateCurrentState();
        toggleUpdateForms();
        setInterval(() => {
            handleButtonClick(currentDirection);
        }, 1000);
    </script>
</body>
</html>''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000, debug=True)