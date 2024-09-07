#include <Ticker.h>
#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <PxMatrix.h>

#define P_LAT 16
#define P_A 5
#define P_B 4
#define P_C 15
#define P_OE 2
#define P_D 12

// WiFi credentials
const char* ssid = "TierKunV22";            // Replace with your WiFi SSID
const char* password = "01072007";    // Replace with your WiFi password

// WebSocket server details
const char* websocket_server = "scar.tierkun.my.id";  // WebSocket server address
const uint16_t websocket_port = 80;        // WebSocket server port

PxMATRIX display(64, 32, P_LAT, P_OE, P_A, P_B, P_C, P_D);
WebSocketsClient webSocket;
Ticker display_ticker;

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
  display.display(60); // Refresh rate
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      Serial.println("WebSocket Disconnected");
      break;
    case WStype_CONNECTED:
      Serial.println("WebSocket Connected");
      webSocket.sendTXT("ESP8266 connected");  // Send a message when connected
      break;
    case WStype_TEXT:
      Serial.printf("Received: %s\n", payload);  // Print received message

      // Parse JSON data
      StaticJsonDocument<200> jsonDoc;
      DeserializationError error = deserializeJson(jsonDoc, payload);

      if (error) {
        Serial.print("Failed to parse JSON: ");
        Serial.println(error.c_str());
        return;
      }

      // Extract values from JSON
      int available = jsonDoc["available"];
      int used = jsonDoc["used"];
      int total = jsonDoc["total"];

      // Declare the strings to hold the formatted values
      String Str_available;
      String Str_used;

            // Format the 'available' value with leading zeros if necessary
      if (String(available).length() == 3) {
          Str_available = "0" + String(available);
      } else if (String(available).length() == 2) {
          Str_available = "00" + String(available);
      } else if (String(available).length() == 1) {
          Str_available = "000" + String(available);
      } else {
          Str_available = String(available);
      }

      // Format the 'used' value with leading zeros if necessary
      if (String(used).length() == 3) {
          Str_used = "0" + String(used);
      } else if (String(used).length() == 2) {
          Str_used = "00" + String(used);
      } else if (String(used).length() == 1) {
          Str_used = "000" + String(used);
      } else {
          Str_used = String(used);
      }

      // Print the values on the LED matrix
      display.clearDisplay();
      display.setBrightness(5000);

      if (available <= 0) {
          display.setTextColor(myRED);
          display.setCursor(3, 1);
          display.print("A0000"); // Display 00000 if available is zero or negative
      } else {
          display.setTextColor(myGREEN);
          display.setCursor(3, 1);
          display.print("A"+Str_available); // Display the formatted available value
      }

      if (available <= 0) {
          display.setTextColor(myRED);
          display.setCursor(3, 17);  // Move to next line
          display.print("PENUH");
      } else {
          display.setTextColor(myRED);
          display.setCursor(3, 17);  // Move to next line
          display.print("U"+Str_used); // Display the formatted used value
      }
      break;
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

  // Set up WebSocket client
  webSocket.begin(websocket_server, websocket_port, "/count");
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000); // Try to reconnect every 5 seconds

  // Initialize the LED matrix display
  display.begin(8); // Brightness level
  display.clearDisplay(); // Clear the display
  display_ticker.attach(0.004, display_updater);

  // Set text color and size
  display.setTextSize(2); // Font size
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
    webSocket.begin(websocket_server, websocket_port, "/count");
  }

  webSocket.loop();  // WebSocket client loop
}
