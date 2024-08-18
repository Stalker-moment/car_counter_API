const express = require("express");
const router = express.Router();
const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");
const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();
const dotenv = require("dotenv");
dotenv.config();

router.post("/edit", async (req, res) => {
  const { password, firstName, lastName, phone } = req.body;
  const { authorization } = req.headers;

  try {
    if (!authorization) {
      return res.status(401).json({ error: "Unauthorized" });
    }

    const token = authorization.replace("Bearer ", "");
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    if (decoded.expired < Date.now()) {
      return res.status(401).json({ error: "Unauthorized" });
    }

    const account = await prisma.account.findUnique({
      where: {
        email: decoded.email,
      },
      include: {
        contact: true, // Include the contact relation
      },
    });

    //console.log(account);

    if (!account) {
      return res.status(404).json({ error: "Account not found" });
    }

    //detect value of edited field
    let role = account.role;

    //hash password if it is edited
    let hashedPassword = account.password;
    if (password) {
      hashedPassword = await bcrypt.hash(password, 10);
    }

    let firstNamed = account.contact.firstName;
    if (firstName) {
      firstNamed = firstName;
    }

    let lastNamed = account.contact.lastName;
    if (lastName) {
      lastNamed = lastName;
    }

    let phoned = account.contact.phone;
    if (phone) {
      phoned = phone;
    }

    const updatedAccount = await prisma.account.update({
      where: {
        email: decoded.email,
      },
      data: {
        password: hashedPassword,
        role: role,
        contact: {
          update: {
            firstName: firstNamed,
            lastName: lastNamed,
            phone: phoned,
          },
        },
      },
    });

    if (!updatedAccount) {
      return res.status(500).json({ error: "Failed to update account" });
    }

    if(password){
      return res.status(201).json({ message: `Succes update account and password` });
    } 

    //search for the updated account
    const updatedAccount2 = await prisma.account.findUnique({
      where: {
        email: decoded.email,
      },
      include: {
        contact: true, // Include the contact relation
      },
    });

    //make a new jwt token
    const expired = Date.now() + 60 * 60 * 60 * 1000; // 1 day

    const newToken = jwt.sign(
      {
        id: updatedAccount2.id,
        firstName: updatedAccount2.contact.firstName,
        lastName: updatedAccount2.contact.lastName,
        role: updatedAccount2.role,
        email: updatedAccount2.email,
        phone: updatedAccount2.contact.phone,
        noReg: updatedAccount2.contact.noReg,
        expired: expired,
      },
      process.env.JWT_SECRET
    );

    return res.status(200).json({ message: `Succes update account (${decoded.email})`, token: newToken });
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: "Internal server error" });
  }
});

module.exports = router;
