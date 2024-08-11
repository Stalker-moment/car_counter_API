const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();

/**
 * Fetch logs for the current week and categorize them by day.
 * @returns {Promise<Object>} - A promise that resolves to an object with daily log summaries.
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
          lte: endOfWeek,
        },
      },
      orderBy: {
        timestamp: "asc", // Order by ascending time to easily group by day
      },
    });

    const daysOfWeek = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    const weeklyData = {};

    for (let i = 0; i < 7; i++) {
      const day = new Date(startOfWeek);
      day.setDate(startOfWeek.getDate() + i);

      const dayKey = daysOfWeek[day.getDay()];
      const dateFormatted = day.toISOString().split("T")[0]; // Format as YYYY-MM-DD

      weeklyData[dayKey] = {
        date: dateFormatted,
        "Incoming Vehicle": 0,
        "Outgoing Vehicle": 0,
        "Edited Value": 0,
        "Edited Capacity": 0,
      };
    }

    logs.forEach((log) => {
      const logDate = new Date(log.timestamp);
      const dayKey = daysOfWeek[logDate.getDay()];

      switch (log.state) {
        case 0:
          weeklyData[dayKey]["Outgoing Vehicle"] += 1;
          break;
        case 1:
          weeklyData[dayKey]["Incoming Vehicle"] += 1;
          break;
        case 2:
          weeklyData[dayKey]["Edited Value"] += 1;
          break;
        case 3:
          weeklyData[dayKey]["Edited Capacity"] += 1;
          break;
        default:
          break;
      }
    });

    return weeklyData;
  } catch (error) {
    console.error("Error fetching logs:", error);
    throw error;
  }
}

module.exports = sendWeeklyLogs;
