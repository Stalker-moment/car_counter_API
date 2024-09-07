#include <Ticker.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <PxMatrix.h>

#define P_LAT 16
#define P_A 5
#define P_B 4
#define P_C 15
#define P_OE 2
#define P_D 12

// WiFi credentials
const char* ssid = "TierKunV22";    // Replace with your WiFi SSID
const char* password = "01072007";  // Replace with your WiFi password

//Serial on?
bool needSerial = false;

// WebSocket server details
String base_ip = "172.21.14.133:5000";
String APIHealt = "true";

PxMATRIX display(64, 32, P_LAT, P_OE, P_A, P_B, P_C, P_D);
Ticker display_ticker;

int available = 0;
int used = 0;
int total = 0;

int prev_available = -1;  // Previous value to track changes
int prev_used = -1;       // Previous value to track changes

String Str_available;
String Str_used;
String Str_total;

// Some standard colors
uint16_t myRED = display.color565(255, 0, 0);
uint16_t myGREEN = display.color565(0, 255, 0);
uint16_t myBLUE = display.color565(0, 0, 255);
uint16_t myWHITE = display.color565(255, 255, 255);
uint16_t myYELLOW = display.color565(255, 255, 0);
uint16_t myCYAN = display.color565(0, 255, 255);
uint16_t myMAGENTA = display.color565(255, 0, 255);
uint16_t myBLACK = display.color565(0, 0, 0);

// Function to refresh the display
void display_updater() {
  display.display(30);  // Refresh rate
}

// Function to format the numbers with leading zeros
String formatNumber(int value) {
  String formatted = String(value);
  while (formatted.length() < 4) {
    formatted = "0" + formatted;
  }
  return formatted;
}

void recalData() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    // Lokasi URL API yang akan diminta
    String url = "http://" + base_ip + "/receive";

    if (needSerial == true) {
      Serial.print("Sending HTTP GET request to: ");
      Serial.println(url);
    }

    // Menggunakan WiFiClient untuk memulai koneksi
    WiFiClient client;
    http.begin(client, url);

    int httpCode = http.GET();

    if (needSerial == true) {
      Serial.println(httpCode);
    }
    
    if (httpCode == 502) {
      if (needSerial == true) {
        Serial.print("HTTP request failed with error code: ");
        Serial.println(httpCode);
      }
      APIHealt = "No";
    }
    if (httpCode > 0) {
      // Penerimaan respon berhasil
      if (httpCode == HTTP_CODE_OK) {
        String payload = http.getString();
        if (needSerial == true) {
          Serial.println("Response payload:");
          Serial.println(payload);
        }

        // Parsing JSON
        DynamicJsonDocument doc(1024);
        deserializeJson(doc, payload);

        // Mendapatkan nilai OnGoing.stats
        available = doc["available"];
        used = doc["used"];
        total = doc["total"];
        APIHealt = "Yes";
      }
    } else {
      if (needSerial == true) {
        Serial.print("HTTP request failed with error code: ");
        Serial.println(httpCode);
      }
      APIHealt = "No";
    }

    // Menutup koneksi
    http.end();
  }

  // Only update the display if the values have changed
  if (available != prev_available || used != prev_used) {
    prev_available = available;
    prev_used = used;

    // Print the values on the LED matrix
    display.clearDisplay();
    display.setBrightness(500);

    // Format the 'available' and 'used' values with leading zeros
    Str_available = formatNumber(available);
    Str_used = formatNumber(used);

    if (APIHealt == "No") {
      display.setTextSize(1);
      display.setTextColor(myBLUE);
      display.setCursor(3, 1);
      display.print("Wait For");  // Display Wait Connection
      display.setTextColor(myBLUE);
      display.setCursor(3, 17);
      display.print("Connection");  // Display Wait Connection
      return;
    }

    if (available <= 0) {
      display.setTextSize(2);  // Font size
      display.setTextColor(myRED);
      display.setCursor(3, 1);
      display.print("A0000");  // Display 00000 if available is zero or negative
    } else {
      display.setTextSize(2);  // Font size
      display.setTextColor(myGREEN);
      display.setCursor(3, 1);
      display.print("A" + Str_available);  // Display the formatted available value
    }

    if (available <= 0) {
      display.setTextSize(2);  // Font size
      display.setTextColor(myRED);
      display.setCursor(3, 17);  // Move to next line
      display.print("PENUH");
    } else {
      display.setTextSize(2);  // Font size
      display.setTextColor(myRED);
      display.setCursor(3, 17);       // Move to next line
      display.print("U" + Str_used);  // Display the formatted used value
    }
  }
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  // Connect to WiFi
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  // Initialize the LED matrix display
  display.begin(8);        // Brightness level
  display.clearDisplay();  // Clear the display
  display_ticker.attach(0.004, display_updater);

  // Set text color and size
  display.setTextSize(2);  // Font size
  display.setCursor(0, 0);
}


void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi Disconnected. Reconnecting...");
    WiFi.disconnect();
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
      delay(1000);
      Serial.println("Reconnecting to WiFi...");
    }
    Serial.println("Reconnected to WiFi");
    recalData();
  }
  recalData();
  delay(500);
}