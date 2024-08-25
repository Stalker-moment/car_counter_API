const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();

async function sendCount() {
  try {
    // Fetch the most recent log entry
    let latestLog = await prisma.logs.findFirst({
      orderBy: {
        timestamp: 'desc', // Sort by timestamp in descending order
      },
    });

    // Check if a log entry exists
    if (!latestLog) {
      throw new Error('No logs found');
    }

    // Get jumlah account
    const totalAccount = await prisma.account.count();

    latestLog = {
        available: latestLog.available,
        used: latestLog.used,
        total: latestLog.total,
        totalAccount: totalAccount,
        timestamp: latestLog.timestamp
    };

    return latestLog; // Return the latest log entry
  } catch (error) {
    console.error("Error fetching latest log:", error);
    throw error;
  }
}

module.exports = sendCount;