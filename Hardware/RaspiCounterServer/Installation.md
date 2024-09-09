# Setup MariaDB dan Proyek Python

## Update dan Upgrade Sistem
```bash
sudo apt update
sudo apt upgrade
```

## Install MariaDB
```bash
sudo apt install mariadb-server
sudo mysql_secure_installation
```

## Login ke MariaDB
```bash
sudo mysql -u root -p
```

## Buat Database dan Tabel
```sql
CREATE DATABASE countering;
USE countering;

-- Tabel ConfigurationDown
CREATE TABLE ConfigurationDown (
    id INT AUTO_INCREMENT PRIMARY KEY,
    totalCapacity INT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabel ConfigurationUp
CREATE TABLE ConfigurationUp (
    id INT AUTO_INCREMENT PRIMARY KEY,
    totalCapacity INT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabel LogDown
CREATE TABLE LogDown (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location VARCHAR(50),
    state INT,
    used INT,
    available INT,
    total INT,
    description VARCHAR(255),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabel LogUp
CREATE TABLE LogUp (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location VARCHAR(50),
    state INT,
    used INT,
    available INT,
    total INT,
    description VARCHAR(255),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Setup Data Awal
```sql
INSERT INTO ConfigurationDown (totalCapacity, timestamp)
VALUES (750, NOW());

INSERT INTO ConfigurationUp (totalCapacity, timestamp)
VALUES (750, NOW());

INSERT INTO LogDown (location, state, used, available, total, description, timestamp)
VALUES ('Down', 2, 50, 700, 750, 'Initial Data', NOW());

INSERT INTO LogUp (location, state, used, available, total, description, timestamp)
VALUES ('Up', 2, 50, 700, 750, 'Initial Data', NOW());
```

## Install Modul untuk Kode Server
```bash
sudo apt install python3-venv
python3 -m venv myenv
source venv/bin/activate
pip install Flask Flask-SQLAlchemy
```

## Install Modul untuk Kode Klien
```bash
sudo apt-get install python3-rpi.gpio
pip install requests
```

## Setting Auto Start
```bash
sudo nano /etc/systemd/system/name.service
```

### Tambahkan Kode Ini (Server Side)
```ini
[Unit]
Description=Countering Server
After=network.target

[Service]
ExecStart=/bin/bash -c 'cd /home/pi/countering && source venv/bin/activate && python server.py'
WorkingDirectory=/home/pi/countering
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

### Tambahkan Kode Ini (Client Side)
```ini
[Unit]
Description=Countering Client

[Service]
ExecStart=/usr/bin/python3 /home/pi/countering/client.py
WorkingDirectory=/home/pi/countering
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

## Aktifkan Layanan
```bash
sudo systemctl enable name.service
```

## Mulai Layanan
```bash
sudo systemctl start name.service
```

## Cek Status Layanan
```bash
sudo systemctl status name.service
```

## Hentikan Layanan
```bash
sudo systemctl stop name.service
```