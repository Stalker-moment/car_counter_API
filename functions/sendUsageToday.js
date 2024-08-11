const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();

/**
 * Fetch logs for the current week and retrieve the last 'used' and 'available' values for each day.
 * @returns {Promise<Object>} - A promise that resolves to an object with daily 'used' and 'available' values.
 */
async function sendWeeklyLogs() {
  try {
    const now = new Date();
    const startOfWeek = new Date(now);
    const dayOfWeek = now.getDay(); // 0 (Sunday) to 6 (Saturday)

    // Set start of the week (Sunday) to 0:00:00
    startOfWeek.setDate(now.getDate() - dayOfWeek);
    startOfWeek.setHours(0, 0, 0, 0);

    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6); // End of the week (Saturday)
    endOfWeek.setHours(23, 59, 59, 999);

    const logs = await prisma.logs.findMany({
      where: {
        timestamp: {
          gte: startOfWeek,
          lte: endOfWeek
        }
      },
      orderBy: {
        timestamp: 'asc' // Order by ascending time to easily find the last entry for each day
      }
    });

    const daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const weeklyData = {};

    // Initialize each day of the week
    for (let i = 0; i < 7; i++) {
      const dayKey = daysOfWeek[i];
      weeklyData[dayKey] = {
        used: 0,
        available: 0
      };
    }

    // Track the last seen 'used' and 'available' values for each day
    logs.forEach(log => {
      const logDate = new Date(log.timestamp);
      const dayKey = daysOfWeek[logDate.getDay()];

      weeklyData[dayKey] = {
        used: log.used,
        available: log.available
      };
    });

    return weeklyData;
  } catch (error) {
    console.error("Error fetching logs:", error);
    throw error; 
  }
}

module.exports = sendWeeklyLogs;
