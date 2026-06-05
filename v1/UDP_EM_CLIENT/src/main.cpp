#include <SPI.h>
#include <Ethernet.h>
#include <EthernetUdp.h>

// -------------------- NETWORK --------------------

byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };

IPAddress ip(192, 168, 1, 50);
IPAddress dns(192, 168, 1, 1);
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 255, 0);

EthernetUDP Udp;

IPAddress remoteIP(192, 168, 1, 222);
unsigned int ports[] = {9995, 9996, 9997, 9998, 9999};

unsigned long lastSend = 0;

// -------------------- FUNCTION PROTOTYPE --------------------
void sendUDP(const char* message, unsigned int port);

// -------------------- SETUP --------------------

void setup() {
  Serial.begin(9600);

  Serial.println("Starting Ethernet...");

  if (Ethernet.begin(mac) == 0) {
    Serial.println("DHCP failed → using static IP");
    Ethernet.begin(mac, ip, dns, gateway, subnet);
  }

  delay(1000);

  Udp.begin(8888);

  Serial.print("Arduino IP: ");
  Serial.println(Ethernet.localIP());

  randomSeed(analogRead(A0));
}

// -------------------- LOOP --------------------

void loop() {
  if (millis() - lastSend < 500) return;
  lastSend = millis();

  float ts = millis() / 1000.0;
  float temp = 22.0 + random(-150, 150) / 100.0;
  float voltage = 120.0 + random(-200, 200) / 100.0;
  float cpu = 10.0 + random(0, 450) / 10.0;
  int motion = random(0, 5) == 0;

  float julian = 150.0 + (millis() % 86400000L) / 86400000.0;

  char msg[160];

  // ---------------- ENV ----------------
  char tempStr[10];
  dtostrf(temp, 4, 1, tempStr);

  sprintf(msg,
    "ID=ENV_01|TS=%.2f|JUL=%.5f|TEMP=%sC|HUM=45%%|STATUS=OK",
    (double)ts,
    (double)julian,
    tempStr);
  sendUDP(msg, ports[0]);

  // ---------------- POWER ----------------
  char voltStr[10];
  dtostrf(voltage, 5, 1, voltStr);

  sprintf(msg,
    "ID=PWR_02|TS=%.2f|JUL=%.5f|VOLT=%sV|LOAD=4.2A|STATUS=NORMAL",
    (double)ts,
    (double)julian,
    voltStr);
  sendUDP(msg, ports[1]);

  // ---------------- SECURITY ----------------
  sprintf(msg,
    "ID=SEC_03|TS=%.2f|JUL=%.5f|MOTION=%d|DOOR=CLOSED|STATUS=ARMED",
    (double)ts,
    (double)julian,
    motion);
  sendUDP(msg, ports[2]);

  // ---------------- FLOW ----------------
  sprintf(msg,
    "ID=FLOW_04|TS=%.2f|JUL=%.5f|RATE=12.5LPM|PRESSURE=45PSI|STATUS=OK",
    (double)ts,
    (double)julian);
  sendUDP(msg, ports[3]);

  // ---------------- SYSTEM ----------------
  char cpuStr[10];
  dtostrf(cpu, 5, 1, cpuStr);

  sprintf(msg,
    "ID=SYS_05|TS=%.2f|JUL=%.5f|CPU=%s%%|RAM=2048MB|STATUS=OK",
    (double)ts,
    (double)julian,
    cpuStr);
  sendUDP(msg, ports[4]);
}

// -------------------- UDP SEND FUNCTION --------------------

void sendUDP(const char* message, unsigned int port) {
  Udp.beginPacket(remoteIP, port);
  Udp.write(message);
  Udp.endPacket();
}