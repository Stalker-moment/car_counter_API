const express = require("express");
const router = express.Router();
const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");
const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();
const dotenv = require("dotenv");
dotenv.config();

router.post("/login", async (req, res) => {
  const { email, password } = req.body;

  try {
    if (!email || !password) {
      return res.status(400).json({ error: "Please fill all required fields" });
    }

    // Find the account using the unique email field
    const account = await prisma.account.findUnique({
      where: {
        email: email,
      },
    });

    if (!account) {
      return res.status(404).json({ error: "Account not found" });
    }

    const passwordMatch = await bcrypt.compare(password, account.password);

    if (!passwordMatch) {
      return res.status(401).json({ error: "Invalid password" });
    }

    // Find the contact using the same unique email field
    const contact = await prisma.contact.findUnique({
      where: {
        email: email,
      },
    });

    if (!contact) {
      return res.status(404).json({ error: "Contact not found" });
    }

    const expired = Date.now() + 60 * 60 * 60 * 1000; // 1 day

    const token = jwt.sign(
      {
        id: account.id,
        firstName: contact.firstName,
        lastName: contact.lastName,
        role: account.role,
        email: account.email,
        phone: contact.phone,
        noReg: contact.noReg,
        expired: expired,
      },
      process.env.JWT_SECRET
    );

    return res.status(200).json({ token });
  } catch (error) {
    console.log(error);
    return res.status(500).json({ error: error.message });
  }
});

module.exports = router;