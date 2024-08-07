const express = require("express");
const router = express.Router();
const bodyParser = require("body-parser");
const cors = require("cors");
const dotenv = require("dotenv");
const WebSocket = require("ws");
const http = require("http");

dotenv.config();

