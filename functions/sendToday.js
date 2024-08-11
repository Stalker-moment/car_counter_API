const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();

/**
 * Fetch logs for the current day and categorize them by hour.
 * @returns {Promise<Object>} - A promise that resolves to an object with hourly log summaries.
 */
async function sendLogs() {
  try {
    const now = new Date();
    const startOfToday = new Date(now);
    startOfToday.setHours(0, 0, 0, 0);

    const endOfToday = new Date(now);
    endOfToday.setHours(23, 59, 59, 999);

    const logs = await prisma.logs.findMany({
      where: {
        timestamp: {
          gte: startOfToday,
          lte: endOfToday
        }
      },
      orderBy: {
        timestamp: 'asc' // Order by ascending time to easily group by hour
      }
    });

    const hourlyData = {};

    for (let hour = 0; hour < 24; hour++) {
      hourlyData[`${hour}:00`] = {
        "Incoming Vehicle": 0,
        "Outgoing Vehicle": 0,
        "Edited Value": 0,
        "Edited Capacity": 0
      };
    }

    logs.forEach(log => {
      const logHour = new Date(log.timestamp).getHours();
      const hourKey = `${logHour}:00`;

      switch (log.state) {
        case 0:
          hourlyData[hourKey]["Outgoing Vehicle"] += 1;
          break;
        case 1:
          hourlyData[hourKey]["Incoming Vehicle"] += 1;
          break;
        case 2:
          hourlyData[hourKey]["Edited Value"] += 1;
          break;
        case 3:
          hourlyData[hourKey]["Edited Capacity"] += 1;
          break;
        default:
          break;
      }
    });

    return hourlyData;
  } catch (error) {
    console.error("Error fetching logs:", error);
    throw error; 
  }
}

module.exports = sendLogs;
