const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();

async function sendAccount() {
  try {
    //get all account include contact
    let accounts = await prisma.account.findMany({
      include: {
        contact: true,
      },
    });

    //delete password field
    accounts.forEach((account) => {
      delete account.password;
    });

    return accounts;
  } catch (error) {
    console.error("Error fetching latest log:", error);
    throw error;
  }
}

module.exports = sendAccount;
