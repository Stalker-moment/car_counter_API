const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();

/**
 * Fetch logs for the current year and categorize them by month.
 * @returns {Promise<Object>} - A promise that resolves to an object with monthly log summaries.
 */
async function sendYearlyLogs() {
  try {
    const now = new Date();
    const startOfYear = new Date(now.getFullYear(), 0, 1); // January 1st of the current year
    const endOfYear = new Date(now.getFullYear(), 11, 31, 23, 59, 59, 999); // December 31st of the current year

    const logs = await prisma.logs.findMany({
      where: {
        timestamp: {
          gte: startOfYear,
          lte: endOfYear,
        },
      },
      orderBy: {
        timestamp: "asc", // Order by ascending time to easily group by month
      },
    });

    const monthsOfYear = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ];
    const yearlyData = {};

    for (let i = 0; i < 12; i++) {
      const monthKey = monthsOfYear[i];

      yearlyData[monthKey] = {
        "Incoming Vehicle": 0,
        "Outgoing Vehicle": 0,
        "Edited Value": 0,
        "Edited Capacity": 0,
      };
    }

    logs.forEach((log) => {
      const logDate = new Date(log.timestamp);
      const monthKey = monthsOfYear[logDate.getMonth()];

      switch (log.state) {
        case 0:
          yearlyData[monthKey]["Outgoing Vehicle"] += 1;
          break;
        case 1:
          yearlyData[monthKey]["Incoming Vehicle"] += 1;
          break;
        case 2:
          yearlyData[monthKey]["Edited Value"] += 1;
          break;
        case 3:
          yearlyData[monthKey]["Edited Capacity"] += 1;
          break;
        default:
          break;
      }
    });

    return yearlyData;
  } catch (error) {
    console.error("Error fetching logs:", error);
    throw error;
  }
}

module.exports = sendYearlyLogs;
