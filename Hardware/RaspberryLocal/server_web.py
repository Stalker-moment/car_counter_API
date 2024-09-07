from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:TierKun123@localhost/counter'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
            <h2>Current Log</h2>
            <p><strong>Available:</strong> {{ log.available if log else 'N/A' }}</p>
            <p><strong>Used:</strong> {{ log.used if log else 'N/A' }}</p>
            <p><strong>Total:</strong> {{ log.total if log else 'N/A' }}</p>
            <p><strong>Timestamp:</strong> {{ log.timestamp if log else 'N/A' }}</p>
        </div>
        <div class="card">
            <h2>Update Used Value</h2>
            <input type="number" id="newUsed" placeholder="New Used Value">
            <button onclick="updateUsed()">Update</button>
            <p id="usedResponse"></p>
        </div>
        <div class="card">
            <h2>Update Total Capacity</h2>
            <input type="number" id="newTotal" placeholder="New Total Capacity">
            <button onclick="updateTotal()">Update</button>
            <p id="totalResponse"></p>
        </div>
        <div class="card">
            <h2>Record Entrance/Exit</h2>
            <input type="text" id="location" placeholder="Location">
            <select id="logType">
                <option value="entrance">Entrance</option>
                <option value="exit">Exit</option>
            </select>
            <button onclick="recordLog()">Record</button>
            <p id="recordResponse"></p>
        </div>
    </div>
    <script>
        function updateUsed() {
            const newUsed = document.getElementById('newUsed').value;
            fetch('/update-used', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ newUsed: parseInt(newUsed, 10) })
            })
            .then(response => response.json())
            .then(data => {
                const responseElement = document.getElementById('usedResponse');
                if (data.error) {
                    responseElement.innerText = data.error;
                    responseElement.className = 'error';
                } else {
                    responseElement.innerText = data.message;
                    responseElement.className = data.overLimit ? 'warning' : 'success';
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }

        function updateTotal() {
            const newTotal = document.getElementById('newTotal').value;
            fetch('/update-total', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ newTotal: parseInt(newTotal, 10) })
            })
            .then(response => response.json())
            .then(data => {
                const responseElement = document.getElementById('totalResponse');
                if (data.error) {
                    responseElement.innerText = data.error;
                    responseElement.className = 'error';
                } else {
                    responseElement.innerText = data.message;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }

        function recordLog() {
            const location = document.getElementById('location').value;
            const logType = document.getElementById('logType').value;
            fetch('/count', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ location: location, type: logType })
            })
            .then(response => response.json())
            .then(data => {
                const responseElement = document.getElementById('recordResponse');
                if (data.error) {
                    responseElement.innerText = data.error;
                    responseElement.className = 'error';
                } else {
                    responseElement.innerText = data.message;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }

        function fetchLog() {
            fetch('/receive')
                .then(response => response.json())
                .then(data => {
                    document.querySelector('.card:nth-child(2) p:nth-of-type(1)').innerText = `Available: ${data.available}`;
                    document.querySelector('.card:nth-child(2) p:nth-of-type(2)').innerText = `Used: ${data.used}`;
                    document.querySelector('.card:nth-child(2) p:nth-of-type(3)').innerText = `Total: ${data.total}`;
                    document.querySelector('.card:nth-child(2) p:nth-of-type(4)').innerText = `Timestamp: ${data.timestamp}`;
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        }

        setInterval(fetchLog, 5000);  // Poll every 5 seconds
    </script>
</body>
</html>
''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
