const express = require("express");
const bodyParser = require("body-parser");
const cors = require("cors");
const dotenv = require("dotenv");
const WebSocket = require("ws"); // Import the ws package
const http = require("http"); // Import the http package

dotenv.config();

const app = express();

// Load controllers
const usersLogin = require("./controllers/users/login");
const usersRegister = require("./controllers/users/register");
const userEdit = require("./controllers/users/edit");
const internalCount = require("./controllers/internal/count");

// Load Functions
const sendLogs = require("./functions/sendLogs");
const sendCount = require("./functions/sendCount");
const sendToday = require("./functions/sendToday");
const sendWeek = require("./functions/sendWeek");
const sendYear = require("./functions/sendYear");
const sendUsageToday = require("./functions/sendUsageToday");
const sendAccount = require("./functions/sendAccount");

//-----------------Configuration------------------//
app.use(bodyParser.json());
app.use(cors());
app.use(bodyParser.json({ limit: "50mb" }));
app.use(bodyParser.urlencoded({ extended: true }));

app.enable("trust proxy");
app.set("view engine", "ejs");

const PORT = process.env.PORT || 2025;

//-----------------Routes------------------//

app.get("/", (req, res) => {
  res.send("Welcome to the API");
});

app.use("/api/users", usersLogin);
app.use("/api/users", usersRegister);
app.use("/api/users", userEdit);
app.use("/api/internal", internalCount);

//handler if route not found
app.use((req, res) => {
  res.status(404).send({ error: "Not found" });
});

const server = http.createServer(app);

const wss = new WebSocket.Server({ server });

// Setup WebSocket connections
wss.on("connection", async (ws, req) => {
  console.log(`WebSocket client connected from ${req.url}`);
  const requestArray = ["/logs", "/count", "/today", "/week", "/year", "/usage-today", "/accounts"];

  if (!requestArray.some((endpoint) => req.url.startsWith(endpoint))) {
    ws.send(JSON.stringify({ error: "Invalid request URL" }));
    ws.close();
    return;
  }

  if (req.url.startsWith("/logs")) {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const dateParam = url.searchParams.get("date");
    let filterDate = null;

    if (dateParam) {
        const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
        if (dateRegex.test(dateParam)) {
            const [year, month, day] = dateParam.split("-").map(Number);
            filterDate = new Date(year, month - 1, day);
        } else {
            ws.send(
                JSON.stringify({ error: "Invalid date format. Use YYYY-MM-DD." })
            );
            ws.close();
            return;
        }
    } else {
        const today = new Date();
        filterDate = new Date(
            today.getFullYear(),
            today.getMonth(),
            today.getDate()
        );
    }

    // Send the initial data
    let data = await sendLogs(filterDate);

    data = JSON.stringify(data);
    ws.send(data);

    // Send the data if there is a new log entry
    const intervalId = setInterval(async () => {
        let newData = await sendLogs(filterDate);

        if (JSON.stringify(newData) !== data) {
            data = JSON.stringify(newData);
            ws.send(data);
        }
    }, 1000);

    ws.on("close", () => {
        console.log("WebSocket client disconnected from /logs");
        clearInterval(intervalId);
    });
} 

  if (req.url === "/count") {
    //send initial data
    let data = await sendCount();
    data = JSON.stringify(data);
    ws.send(data);

    //send data if there is a new log entry

    const intervalId = setInterval(async () => {
      let newData = await sendCount();

      if (JSON.stringify(newData) !== data) {
        data = JSON.stringify(newData);
        ws.send(data);
      }
    }, 1000);

    ws.on("close", () => {
      console.log("WebSocket client disconnected from /count");
      clearInterval(intervalId);
    });
  }

  if (req.url === "/today") {
    //send initial data
    let data = await sendToday();
    data = JSON.stringify(data);
    ws.send(data);

    //send data if there is a new log entry

    const intervalId = setInterval(async () => {
      let newData = await sendToday();

      if (JSON.stringify(newData) !== data) {
        data = JSON.stringify(newData);
        ws.send(data);
      }
    }, 1000);

    ws.on("close", () => {
      console.log("WebSocket client disconnected from /today");
      clearInterval(intervalId);
    });
  }

  if (req.url === "/week") {
    //send initial data
    let data = await sendWeek();
    data = JSON.stringify(data);
    ws.send(data);

    //send data if there is a new log entry

    const intervalId = setInterval(async () => {
      let newData = await sendWeek();

      if (JSON.stringify(newData) !== data) {
        data = JSON.stringify(newData);
        ws.send(data);
      }
    }, 1000);

    ws.on("close", () => {
      console.log("WebSocket client disconnected from /week");
      clearInterval(intervalId);
    });
  }

  if (req.url === "/year") {
    //send initial data
    let data = await sendYear();
    data = JSON.stringify(data);
    ws.send(data);

    //send data if there is a new log entry

    const intervalId = setInterval(async () => {
      let newData = await sendYear();

      if (JSON.stringify(newData) !== data) {
        data = JSON.stringify(newData);
        ws.send(data);
      }
    }, 1000);

    ws.on("close", () => {
      console.log("WebSocket client disconnected from /year");
      clearInterval(intervalId);
    });
  }

  if (req.url === "/usage-today") {
    //send initial data
    let data = await sendUsageToday();
    data = JSON.stringify(data);
    ws.send(data);

    //send data if there is a new log entry

    const intervalId = setInterval(async () => {
      let newData = await sendUsageToday();

      if (JSON.stringify(newData) !== data) {
        data = JSON.stringify(newData);
        ws.send(data);
      }
    }, 1000);

    ws.on("close", () => {
      console.log("WebSocket client disconnected from /usage-today");
      clearInterval(intervalId);
    });
  }

  if (req.url === "/accounts") {
    //send initial data
    let data = await sendAccount();
    data = JSON.stringify(data);
    ws.send(data);

    //send data if there is a new log entry

    const intervalId = setInterval(async () => {
      let newData = await sendAccount();

      if (JSON.stringify(newData) !== data) {
        data = JSON.stringify(newData);
        ws.send(data);
      }
    }, 1000);

    ws.on("close", () => {
      console.log("WebSocket client disconnected from /accounts");
      clearInterval(intervalId);
    });
  }
});

// Start the server
server.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
  console.log(`WebSocket server is running on ws://localhost:${PORT}`);
});
