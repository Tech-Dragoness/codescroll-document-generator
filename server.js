const express = require("express");
const multer = require("multer");
const cors = require("cors");
const fs = require("fs");
const path = require("path");

const app = express();
const upload = multer({ dest: "uploads/" });
app.use(cors());

app.post("/upload", upload.array("files"), (req, res) => {
  const extensions = req.body.extensions.split(",").map((ext) => ext.trim());
  let documentation = "";

  req.files.forEach((file) => {
    const ext = path.extname(file.originalname);
    if (extensions.includes(ext)) {
      const content = fs.readFileSync(file.path, "utf-8");
      documentation += `📄 ${file.originalname}\n`;
      documentation += extractDocs(content, ext);
      documentation += "\n\n";
    }
    fs.unlinkSync(file.path); // Clean up
  });

  res.json({ documentation });
});

function extractDocs(content, ext) {
  if ([".js", ".py", ".java", ".cpp"].includes(ext)) {
    // Simple comment extractor for demo purposes
    return content
      .split("\n")
      .filter((line) => line.trim().startsWith("//") || line.trim().startsWith("#") || line.trim().startsWith("/*"))
      .join("\n");
  }
  return "(No parser for this file type)";
}

app.listen(4000, () => console.log("🌐 Server running on http://localhost:4000"));