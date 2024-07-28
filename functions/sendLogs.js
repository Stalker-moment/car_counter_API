const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();

/**
 * Fetch logs filtered by a specific date or return all logs.
 * @param {Date|null} filterDate - The date to filter logs by. If null, fetch logs for today.
 * @returns {Promise<Array>} - A promise that resolves to an array of logs.
 */

async function sendLogs(filterDate = null) {
  try {
    let logs;
    
    if (filterDate) {
      const startOfDay = new Date(filterDate);
      startOfDay.setHours(0, 0, 0, 0);

      const endOfDay = new Date(filterDate);
      endOfDay.setHours(23, 59, 59, 999);

      logs = await prisma.logs.findMany({
        where: {
          timestamp: {
            gte: startOfDay,
            lte: endOfDay
          }
        },
        orderBy: {
          timestamp: 'desc'
        }
      });
    } else {
      const today = new Date();
      const startOfToday = new Date(today);
      startOfToday.setHours(0, 0, 0, 0);

      const endOfToday = new Date(today);
      endOfToday.setHours(23, 59, 59, 999);

      logs = await prisma.logs.findMany({
        where: {
          timestamp: {
            gte: startOfToday,
            lte: endOfToday
          }
        },
        orderBy: {
          timestamp: 'desc'
        }
      });
    }

    return logs;
  } catch (error) {
    console.error("Error fetching logs:", error);
    throw error; 
  }
}

module.exports = sendLogs;