from flask import Flask, render_template, request, jsonify
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
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000, debug=True)