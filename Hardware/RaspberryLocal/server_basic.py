from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:TierKun123@localhost/count'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model untuk konfigurasi
class Configuration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    totalCapacity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Add timestamp field

    def to_dict(self):
        return {
            "id": self.id,
            "totalCapacity": self.totalCapacity,
            "timestamp": self.timestamp.isoformat()  # Convert datetime to ISO format
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
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Add timestamp field

    def to_dict(self):
        return {
            "id": self.id,
            "location": self.location,
            "state": self.state,
            "used": self.used,
            "available": self.available,
            "total": self.total,
            "description": self.description,
            "timestamp": self.timestamp.isoformat()  # Convert datetime to ISO format
        }

setup_ran = False  # Flag untuk memastikan fungsi hanya berjalan sekali

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

    if new_used > total_capacity:
        return jsonify({"error": "Used value cannot exceed total capacity"}), 400

    available = total_capacity - new_used

    updated_log = Log(
        location="-",
        state=2,  # 2 for edit-used
        used=new_used,
        available=available,
        total=total_capacity,
        description=f"Updated used value to {new_used}"
    )

    db.session.add(updated_log)
    db.session.commit()

    return jsonify({"message": "Used value updated successfully", "log": updated_log.to_dict()}), 200

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
        state=3,  # 3 for edit-total
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
        state=1 if log_type == "entrance" else 0,  # 1 for entrance, 0 for exit
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
        "timestamp": latest_log.timestamp.isoformat()  # Convert datetime to ISO format
    }

    return jsonify(response), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Buat semua tabel jika belum ada
    app.run(host='0.0.0.0', port=5000, debug=True)