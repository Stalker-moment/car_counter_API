const express = require("express");
const router = express.Router();
const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();
const dotenv = require("dotenv");
const jwt = require("jsonwebtoken");

dotenv.config();

// Middleware to verify JWT token and check admin role
const authenticateAdmin = (req, res, next) => {
  const { authorization } = req.headers;

  if (!authorization) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  try {
    const token = authorization.replace("Bearer ", "");
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // Check for admin role
    if (decoded.role !== "admin") {
      return res.status(401).json({ error: "Unauthorized" });
    }

    // Check token expiration
    if (decoded.expired < Date.now()) {
      return res.status(401).json({ error: "Unauthorized" });
    }

    // Attach decoded user info to request, including email
    req.user = {
      email: decoded.email,
      role: decoded.role,
      id: decoded.id,
      noReg: decoded.noReg,
    };

    next(); // Proceed to the next middleware/handler
  } catch (error) {
    return res.status(401).json({ error: "Unauthorized" });
  }
};

// Route to update the used value globally
router.post("/update-used", authenticateAdmin, async (req, res) => {
  const { newUsed } = req.body;

  if (newUsed == null) {
    return res.status(400).json({ error: "Missing required fields" });
  }

  try {
    // Get the configuration to access the total capacity
    const config = await prisma.configuration.findFirst();

    // If configuration doesn't exist, handle this case
    if (!config) {
      return res.status(404).json({
        error: "Configuration not found. Please set the total capacity first.",
      });
    }

    const { totalCapacity } = config;

    // Ensure newUsed does not exceed total capacity
    if (newUsed > totalCapacity) {
      return res
        .status(400)
        .json({ error: "Used value cannot exceed total capacity" });
    }

    const available = totalCapacity - newUsed;

    // Create a new log entry with new used value
    const updatedLog = await prisma.logs.create({
      data: {
        location: "-",
        state: 2, // 2 for edit-used
        used: newUsed,
        available,
        total: totalCapacity,
        description: `Updated used value to ${newUsed} by ${req.user.email}`,
      },
    });

    return res
      .status(200)
      .json({ message: "Used value updated successfully", log: updatedLog });
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: "Internal server error" });
  }
});

// Route to update total capacity globally
router.post("/update-total", authenticateAdmin, async (req, res) => {
  const { newTotal } = req.body;

  if (newTotal == null) {
    return res.status(400).json({ error: "Missing required fields" });
  }

  try {
    //check value before update
    const configBefore = await prisma.configuration.findFirst();

    //check value same
    if (configBefore.totalCapacity == newTotal) {
      return res.status(200).json({ error: "Total capacity still same" });
    }

    // Update or create the total capacity in Configuration
    const config = await prisma.configuration.upsert({
      where: { id: 1 }, // Using ID 1 for a single configuration scenario
      update: { totalCapacity: newTotal },
      create: { totalCapacity: newTotal },
    });

    // Get the latest log entry
    const latestLog = await prisma.logs.findFirst({
      orderBy: { timestamp: "desc" },
    });

    let used = 0;
    if (latestLog) {
      used = latestLog.used;
    }

    const available = newTotal - used;

    // Create a new log entry for the update
    const updatedLog = await prisma.logs.create({
      data: {
        location: "-",
        state: 3, // 3 for edit-total
        used,
        available,
        total: newTotal,
        description: `Updated total capacity to ${newTotal} by ${req.user.email}`,
      },
    });

    return res.status(200).json({
      message: "Total capacity updated successfully",
      config,
      log: updatedLog,
    });
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: "Internal server error" });
  }
});

// Route to handle entrance and exit logs
router.post("/count", async (req, res) => {
  const { location, type } = req.body;

  if (!location || !type) {
    return res.status(400).json({ error: "Missing required fields" });
  }

  if (type !== "entrance" && type !== "exit") {
    return res.status(400).json({ error: "Invalid type" });
  }

  try {
    // Get the configuration to access the total capacity
    const config = await prisma.configuration.findFirst();

    // If configuration doesn't exist, handle this case
    if (!config) {
      return res.status(404).json({
        error: "Configuration not found. Please set the total capacity first.",
      });
    }

    const { totalCapacity } = config;

    // Get the latest log entry
    const latestLog = await prisma.logs.findFirst({
      orderBy: { timestamp: "desc" },
    });

    let used = 0;
    let available = totalCapacity;

    // If there is an existing log entry, use its values
    if (latestLog) {
      used = latestLog.used;
      available = latestLog.available;
    }

    if (type === "entrance") {
      // Increment used
      used += 1;
    } else if (type === "exit") {
      // Decrement used if greater than zero to avoid negative numbers
      used = Math.max(0, used - 1);
    } else {
      return res.status(400).json({ error: "Invalid type" });
    }

    // Calculate available slots
    available = totalCapacity - used;

    // Create a new log entry
    const newLog = await prisma.logs.create({
      data: {
        location,
        state: type === "entrance" ? 1 : 0, // 1 for entrance, 0 for exit
        available,
        used,
        total: totalCapacity,
        description: `Entry recorded as ${type} at ${location}`,
      },
    });

    return res
      .status(200)
      .json({ message: "Log created successfully", log: newLog });
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: "Internal server error" });
  }
});

router.post("/mancount", async (req, res) => {
  let { location, type } = req.body;

  if (!location || !type) {
    return res.status(400).json({ error: "Missing required fields" });
  }

  if (type !== "entrance" && type !== "exit") {
    return res.status(400).json({ error: "Invalid type" });
  }

  try {
    const config = await prisma.configuration.findFirst();

    if (!config) {
      return res.status(404).json({
        error: "Configuration not found. Please set the total capacity first.",
      });
    }

    const { totalCapacity } = config;

    const latestLog = await prisma.logs.findFirst({
      orderBy: { timestamp: "desc" },
    });

    let used = 0;
    let available = totalCapacity - used;

    if ((type = "entrance")) {
      used += 1;
    } else if ((type = "exit")) {
      used = Math.max(0, used - 1);
    } else {
      return res.status(400).json({ error: "Invalid type" });
    }

    const addNewLog = await prisma.logs.create({
      data: {
        location,
        state: type === "entrance" ? 1 : 0,
        available,
        used,
        total: totalCapacity,
        description: `Manual Entry recorded as ${type} at ${location}`,
      },
    });

    return res
      .status(200)
      .json({ message: "Log created successfully", log: addNewLog });
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: "Internal server error" });
  }
});

module.exports = router;
