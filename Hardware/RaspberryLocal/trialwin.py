from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import psutil

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

@app.route('/status', methods=['GET'])
def get_status():
    # Mendapatkan CPU usage
    cpu_usage = psutil.cpu_percent(interval=1)

    # Mendapatkan memory usage
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent

    # Mengembalikan hasil dalam format JSON
    return jsonify({
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage,
        'total_memory': memory_info.total,
        'available_memory': memory_info.available,
        'used_memory': memory_info.used,
        'free_memory': memory_info.free
    })

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
                'state': log.state,
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
            'state': log.state,
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

@app.route('/get-latest-data')
def get_latest_data():
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
                'state': log.state,
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
            'state': log.state,
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
        description=f"Entry recorded as {log_type} at {location}"
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
    <title>Log Management</title>
    <link rel="icon" href="https://yt3.ggpht.com/a/AGF-l7_uB8jTXsIt1a2YbzprWQa0QlutQfKRfCcX7g=s900-c-k-c0xffffffff-no-rj-mo" type="image/x-icon">
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
    .card {
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }
    .card:hover {
        border-color: #60a5fa;
        transform: translateY(-5px);
        z-index: 1;
    }
    .hidden {
        display: none;
    }
    /* Sidebar akan selalu berada di kiri dengan left: 0 */
    .sidebar {
        position: fixed;
        top: 0;
        left: 0; /* Posisi tetap di kiri */
        height: 100%;
        width: 200px;
        background-color: #1f2937; /* bg-gray-800 */
        padding-top: 20px;
        padding: 20px;
        transform: translateX(0); /* Sidebar selalu muncul di desktop */
        transition: transform 0.3s ease;
        z-index: 998;
    }
    .sidebar.open {
        transform: translateX(0); /* Sidebar akan muncul di posisi kiri */
        z-index: 999;
    }
    .sidebar button {
        width: 100%;
        margin-bottom: 1rem;
        display: flex;
        justify-content: flex-start;
        align-items: center;
        padding: 12px;
    }
    .hamburger {
        display: none;
        position: fixed;
        top: 10px;
        left: 10px;
        z-index: 1000;
    }
    .state-1 {
        background-color: #FFCDD2; 
        border-radius: 0.5rem; 
        color: #B71C1C; 
    }
    .state-2 {
        background-color: #FFF9C4; 
        border-radius: 0.5rem;
        color: #F57F17; 
    }
    .state-3 {
        background-color: #C8E6C9; 
        border-radius: 0.5rem;
        color: #1B5E20; 
    }
    .state-4 {
        background-color: #BBDEFB;
        border-radius: 0.5rem;
        color: #0D47A1;
    }
    .state-5 {
        background-color: #D1C4E9;
        border-radius: 0.5rem;
        color: #4A148C;
    }
    table {
        border-spacing: 0 10px; /* Menambah space vertikal antar baris */
    }
    td {
        padding: 12px 8px; /* Memberikan padding dalam setiap cell */
    }
    @media (max-width: 768px) {
        .hamburger {
            display: block;
        }
        /* Sidebar tetap di posisi kiri di layar mobile */
        .sidebar {
            transform: translateX(-100%); /* Tetap hidden di mobile awalnya */
        }
        .sidebar.open {
            transform: translateX(0); /* Sidebar muncul di kiri ketika dibuka */
        }
    }

    </style>
</head>
<body class="bg-gray-900 p-2 text-white">

    <div class="max-w-4xl mx-auto p-6 mt-5 mb-5 bg-gray-800 rounded-lg shadow-lg">

        <!-- Title -->
        <h1 class="text-4xl font-bold text-blue-400 text-center mb-6">Parking Management</h1>

        <button id="hamburgerBtn" class="md:mt-0 mt-4 ml-1 hamburger text-white font-bold py-2 px-4 rounded-lg bg-gradient-to-r from-green-400 to-blue-500 hover:from-green-500 hover:to-blue-600 shadow-lg">
             <i class="fas fa-bars"></i>
        </button>

        <!-- Sidebar -->
        <div id="sidebar" class="sidebar p-2 z-999">
            <button class="mt-14
             text-white font-bold py-2 px-4 rounded-lg bg-gradient-to-r from-green-400 to-blue-500 hover:from-green-500 hover:to-blue-600 shadow-lg" onclick="setDirection('up')">
                <i class="fas fa-arrow-up mr-2"></i>Up
            </button>
            <button class="text-white font-bold py-2 px-4 rounded-lg bg-gradient-to-r from-red-400 to-pink-500 hover:from-red-500 hover:to-pink-600 shadow-lg" onclick="setDirection('down')">
                <i class="fas fa-arrow-down mr-2"></i>Down
            </button>
            <button class="text-white font-bold py-2 px-4 rounded-lg bg-gradient-to-r from-purple-400 to-indigo-500 hover:from-purple-500 hover:to-indigo-600 shadow-lg" onclick="setDirection('total')">
                <i class="fas fa-chart-pie mr-2"></i>Total
            </button>
        </div>

        <!-- Current Status Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div class="z-0 p-6 bg-gray-700 rounded-lg shadow-md flex items-center card">
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
            <p class="mb-2"><strong>Last Update:</strong> <span id="timestamp"></span></p>
            <p><strong>Total Capacity:</strong> <span id="totalCapacity"></span></p>
            <p class="mt-4"><strong>Current State:</strong> <span id="currentState" class="text-purple-400"></span></p>
        </div>

        <!-- Recent Logs -->
        <div class="mb-6 p-6 bg-gray-700 rounded-lg shadow-md">
            <h2 class="text-xl font-semibold mb-2">Recent Logs</h2>
            <div class="scrollable-table">
                <table id="logsTable" class="w-full border-collapse space-between space-y-3 text-sm">
                    <thead>
                        <tr class="p-2">
                            <th class="px-4 py-2 text-left">Time (Jakarta)</th>
                            <th class="px-4 py-2 text-left">Location</th>
                            <th class="px-4 py-2 text-left">Used</th>
                            <th class="px-4 py-2 text-left">Available</th>
                            <th class="px-4 py-2 text-left">Total</th>
                            <th class="px-4 py-2 text-left">State</th>
                            <th class="px-4 py-2 text-left">Description</th>
                        </tr>
                    </thead>
                    <tbody class=" space-y-3 ">
                        <!-- Logs will be inserted here -->
                    </tbody>
                </table>
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

    <!-- Modal -->
    <div id="messageModal" class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 hidden">
        <div class="bg-white text-black rounded-lg shadow-lg p-6 w-1/3">
            <h2 class="text-xl font-semibold mb-4" id="modalTitle">Alert</h2>
            <p id="modalMessage">This is an alert message.</p>
            <div class="mt-4 text-right">
                <button onclick="closeModal()" class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg">Close</button>
            </div>
        </div>
    </div>

    <script>
    let currentDirection = 'total';  // Default direction is 'total'
    let dataFetchInterval;

    // Initialize the data fetch interval
    function startDataFetch() {
        dataFetchInterval = setInterval(() => {
            handleButtonClick(currentDirection);
        }, 1000); // Fetch data every 1 second
    }

    function stopDataFetch() {
        clearInterval(dataFetchInterval);
    }

    function setDirection(direction) {
        currentDirection = direction;
        handleButtonClick(direction);
        updateCurrentState();
        toggleUpdateForms();
        // Restart data fetch with the new direction
        stopDataFetch();
        startDataFetch();
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

    function updateUsed() {
        const newUsed = document.getElementById('usedInput').value;
        fetch('/update-used', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ newUsed, direction: currentDirection })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                showModal(data.message);
                handleButtonClick(currentDirection);
            }
        });
    }

    function updateTotal() {
        const newTotal = document.getElementById('totalInput').value;
        fetch('/update-total', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ newTotal })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                showModal(data.message);
                handleButtonClick(currentDirection);
            }
        });
    }

    function handleButtonClick(direction) {
       
        fetch(`/get-latest-data?direction=${direction}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('currentUsed').innerText = data.currentUsed || 0;
            document.getElementById('currentAvailable').innerText = data.currentAvailable || 0;
            document.getElementById('timestamp').innerText = data.timestamp || '';
            document.getElementById('totalCapacity').innerText = data.totalCapacity || '';
        });
        updateLogsTable(data.logs || []);
    }
    function updateLogsTable(logs) {
        const tableBody = document.getElementById('logsTable').querySelector('tbody');
                                    
        tableBody.innerHTML = '';

        // Objek map untuk state description
        const stateDescription = {
            1: "Bawah masuk",
            2: "Bawah keluar",
            3: "Atas masuk",
            4: "Atas keluar",
            5: "Edit Data Used",
            6: "Edit Data Total"
        };

        logs.forEach(log => {
            const row = document.createElement('tr');
            row.style.marginBottom = '10px';

            const stateClass = `state-${log.state}`;
            
            const formattedTimestamp = new Date(log.timestamp).toLocaleString('en-US', {
                timeZone: 'Asia/Jakarta',
                hour12: false
            });

            const stateText = stateDescription[log.state] || 'Unknown State'; 

            row.innerHTML = `
                <td class="px-4 py-2">${formattedTimestamp}</td>
                <td class="px-4 py-2">${log.location}</td>
                <td class="px-4 py-2">${log.used}</td>
                <td class="px-4 py-2">${log.available}</td>
                <td class="px-4 py-2">${log.total}</td>
                <td class="px-4 text-center ">
                    <span class="px-4 py-1 w-full rounded-lg ${stateClass}">${stateText}</span>
                </td>
                <td class="px-4 py-2">${log.description}</td>
            `;
            tableBody.appendChild(row);
        });
    }




    function showModal(message) {
        document.getElementById('modalMessage').innerText = message;
        document.getElementById('messageModal').classList.remove('hidden');
    }

    function closeModal() {
        document.getElementById('messageModal').classList.add('hidden');
    }
    document.getElementById('hamburgerBtn').addEventListener('click', function() {
        document.getElementById('sidebar').classList.toggle('open');
    });
    // Start fetching data when the page loads
    window.onload = startDataFetch;
</script>

</body>
</html>''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)