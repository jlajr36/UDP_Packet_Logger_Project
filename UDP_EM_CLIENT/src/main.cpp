#include <Arduino.h>
#include <SPI.h>
#include <Ethernet.h>

// MAC address (must be unique on your network)
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };

// Static fallback IP (used if DHCP fails)
IPAddress ip(192, 168, 1, 50);

EthernetServer server(80);

void setup() {
  Serial.begin(9600);
  while (!Serial) {}

  Serial.println("Starting Ethernet...");

  // Try DHCP first
  if (Ethernet.begin(mac) == 0) {
    Serial.println("DHCP failed, using static IP");
    Ethernet.begin(mac, ip);
  }

  delay(1000);

  server.begin();

  Serial.print("My IP address: ");
  Serial.println(Ethernet.localIP());
}

void loop() {
  EthernetClient client = server.available();

  if (client) {
    Serial.println("Client connected");

    boolean blankLine = true;

    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        Serial.write(c);

        // End of HTTP request
        if (c == '\n' && blankLine) {

          // HTTP response
          client.println("HTTP/1.1 200 OK");
          client.println("Content-Type: text/html");
          client.println("Connection: close");
          client.println();

          client.println("<!DOCTYPE html>");
          client.println("<html>");
          client.println("<head><title>Arduino W5100</title></head>");
          client.println("<body>");

          client.println("<h1>Ethernet OK</h1>");
          client.print("<p>IP Address: ");
          client.print(Ethernet.localIP());
          client.println("</p>");

          client.println("</body>");
          client.println("</html>");

          break;
        }

        if (c == '\n') {
          blankLine = true;
        } else if (c != '\r') {
          blankLine = false;
        }
      }
    }

    delay(1);
    client.stop();
    Serial.println("Client disconnected");
  }
}