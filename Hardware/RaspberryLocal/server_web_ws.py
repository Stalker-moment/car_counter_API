from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_sock import Sock
from datetime import datetime
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:TierKun123@localhost/counter'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

sock = Sock(app)

# Model untuk konfigurasi
class Configuration(db.Model):
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
class Log(db.Model):
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
current_data = None

@app.before_request
def setup_default_config():
    global setup_ran
    if not setup_ran:
        config = Configuration.query.first()
        if not config:
            default_capacity = 1500
            default_config = Configuration(totalCapacity=default_capacity)
            db.session.add(default_config)
            db.session.commit()
            print(f"Default configuration created with totalCapacity = {default_capacity}")
        setup_ran = True

# Helper function to get the latest log data
def get_latest_log():
    latest_log = Log.query.order_by(Log.id.desc()).first()
    if latest_log:
        return {
            "available": latest_log.available,
            "used": latest_log.used,
            "total": latest_log.total,
            "timestamp": latest_log.timestamp.isoformat()
        }
    return None

# WebSocket endpoint
@sock.route('/receive-data')
def receive_data(ws):
    global current_data
    initial_data = get_latest_log()
    
    if initial_data:
        ws.send(json.dumps(initial_data))  # Send initial data to client

    while True:
        new_data = get_latest_log()

        # Check if the data has changed
        if new_data != current_data:
            ws.send(json.dumps(new_data))  # Send updated data
            current_data = new_data

@app.route('/update-used', methods=['POST'])
def update_used():
    data = request.json
    new_used = data.get('newUsed')

    if new_used is None:
        return jsonify({"error": "Missing required fields"}), 400

    config = Configuration.query.first()
    if not config:
        return jsonify({"error": "Configuration not found. Please set the total capacity first."}), 404

    total_capacity = config.totalCapacity
    available = total_capacity - new_used

    updated_log = Log(
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

    if new_total is None:
        return jsonify({"error": "Missing required fields"}), 400

    config = Configuration.query.first()

    if config and config.totalCapacity == new_total:
        return jsonify({"error": "Total capacity still same"}), 200

    if config:
        config.totalCapacity = new_total
    else:
        config = Configuration(totalCapacity=new_total)
        db.session.add(config)

    latest_log = Log.query.order_by(Log.id.desc()).first()
    used = latest_log.used if latest_log else 0
    available = new_total - used

    updated_log = Log(
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

    if not location or not log_type:
        return jsonify({"error": "Missing required fields"}), 400

    if log_type not in ["entrance", "exit"]:
        return jsonify({"error": "Invalid type"}), 400

    config = Configuration.query.first()
    if not config:
        return jsonify({"error": "Configuration not found. Please set the total capacity first."}), 404

    total_capacity = config.totalCapacity
    latest_log = Log.query.order_by(Log.id.desc()).first()

    used = latest_log.used if latest_log else 0
    available = total_capacity - used

    if log_type == "entrance":
        used += 1
    elif log_type == "exit":
        used = max(0, used - 1)

    available = total_capacity - used

    new_log = Log(
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
    latest_log = Log.query.order_by(Log.id.desc()).first()
    if not latest_log:
        return jsonify({"error": "No logs found"}), 404

    response = {
        "available": latest_log.available,
        "used": latest_log.used,
        "total": latest_log.total,
        "timestamp": latest_log.timestamp.isoformat()
    }

    return jsonify(response), 200

@app.route('/')
def index():
    config = Configuration.query.first()
    log = Log.query.order_by(Log.id.desc()).first() or {}  # Default to empty dict if no logs
    return render_template_string('''
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Log Management</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            color: #333;
        }
        .container {
            width: 80%;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }
        h1 {
            text-align: center;
            color: #007bff;
        }
        .card {
            margin-bottom: 20px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
            box-shadow: 0 0 5px rgba(0,0,0,0.1);
        }
        .card h2 {
            margin-top: 0;
            color: #333;
        }
        .card p {
            margin: 5px 0;
        }
        .card input, .card button {
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
            border: 1px solid #ddd;
            width: 100%;
            box-sizing: border-box;
        }
        .card button {
            background-color: #007bff;
            color: #fff;
            border: none;
            cursor: pointer;
        }
        .card button:hover {
            background-color: #0056b3;
        }
        .error {
            color: red;
            font-weight: bold;
        }
        .success {
            color: green;
            font-weight: bold;
        }
        .warning {
            color: orange;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Log Management</h1>
        <div class="card">
            <h2>Current Configuration</h2>
            <p><strong>Total Capacity:</strong> {{ config.totalCapacity }}</p>
            <p><strong>Timestamp:</strong> {{ config.timestamp }}</p>
        </div>
                <div class="card">
            <h2>Latest Log</h2>
            <p><strong>Location:</strong> {{ log.location }}</p>
            <p><strong>State:</strong> {{ log.state }}</p>
            <p><strong>Used:</strong> {{ log.used }}</p>
            <p><strong>Available:</strong> {{ log.available }}</p>
            <p><strong>Total:</strong> {{ log.total }}</p>
            <p><strong>Description:</strong> {{ log.description }}</p>
            <p><strong>Timestamp:</strong> {{ log.timestamp }}</p>
        </div>
        <div class="card">
            <h2>Update Used Value</h2>
            <form id="update-used-form">
                <input type="number" id="newUsed" name="newUsed" placeholder="Enter new used value" required>
                <button type="submit">Update Used</button>
                <p id="update-used-response" class="error"></p>
            </form>
        </div>
        <div class="card">
            <h2>Update Total Capacity</h2>
            <form id="update-total-form">
                <input type="number" id="newTotal" name="newTotal" placeholder="Enter new total capacity" required>
                <button type="submit">Update Total</button>
                <p id="update-total-response" class="error"></p>
            </form>
        </div>
        <div class="card">
            <h2>Log Count</h2>
            <form id="log-count-form">
                <input type="text" id="location" name="location" placeholder="Enter location" required>
                <select id="type" name="type" required>
                    <option value="entrance">Entrance</option>
                    <option value="exit">Exit</option>
                </select>
                <button type="submit">Record Log</button>
                <p id="log-count-response" class="error"></p>
            </form>
        </div>
        <script>
            document.getElementById('update-used-form').addEventListener('submit', async function(e) {
                e.preventDefault();
                const newUsed = document.getElementById('newUsed').value;
                try {
                    const response = await fetch('/update-used', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ newUsed })
                    });
                    const result = await response.json();
                    document.getElementById('update-used-response').textContent = result.message || '';
                } catch (error) {
                    document.getElementById('update-used-response').textContent = 'An error occurred';
                }
            });

            document.getElementById('update-total-form').addEventListener('submit', async function(e) {
                e.preventDefault();
                const newTotal = document.getElementById('newTotal').value;
                try {
                    const response = await fetch('/update-total', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ newTotal })
                    });
                    const result = await response.json();
                    document.getElementById('update-total-response').textContent = result.message || '';
                } catch (error) {
                    document.getElementById('update-total-response').textContent = 'An error occurred';
                }
            });

            document.getElementById('log-count-form').addEventListener('submit', async function(e) {
                e.preventDefault();
                const location = document.getElementById('location').value;
                const type = document.getElementById('type').value;
                try {
                    const response = await fetch('/count', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ location, type })
                    });
                    const result = await response.json();
                    document.getElementById('log-count-response').textContent = result.message || '';
                } catch (error) {
                    document.getElementById('log-count-response').textContent = 'An error occurred';
                }
            });

            // WebSocket handling
            const ws = new WebSocket('ws://localhost:5000/receive-data');
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                console.log('Received data:', data);
                // Optionally update UI with new data here
            };
        </script>
    </div>
</body>
</html>
    ''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

