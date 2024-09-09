sudo apt update
sudo apt upgrade

----Install MariaDB-----
sudo apt install mariadb-server
sudo mysql_secure_installation

---Login MariaDB---
sudo mysql -u root -p

---CREATE DB & Table---
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

-- Setup first data
INSERT INTO ConfigurationDown (totalCapacity, timestamp)
VALUES (750, NOW());

INSERT INTO ConfigurationUp (totalCapacity, timestamp)
VALUES (750, NOW());

INSERT INTO LogDown (location, state, used, available, total, description, timestamp)
VALUES ('Down', 2, 50, 700, 750, 'Initial Data', NOW());

INSERT INTO LogUp (location, state, used, available, total, description, timestamp)
VALUES ('Up', 2, 50, 700, 750, 'Initial Data', NOW());

---Install Module For Server Code---
sudo apt install python3-venv
python3 -m venv myenv
source venv/bin/activate
pip install Flask Flask-SQLAlchemy

---Install Module For Client Code---
sudo apt-get install python3-rpi.gpio
pip install requests

---Setting Auto Start---
sudo nano /etc/systemd/system/name.service

---Add This Code (Server Side)---
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

---Add This Code (Client Side)---
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

---Enable Service---
sudo systemctl enable name.service

---Start Service---
sudo systemctl start name.service

---Check Service---
sudo systemctl status name.service

---Stop Service---
sudo systemctl stop name.service