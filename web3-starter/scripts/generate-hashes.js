import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

function walk(dir) {
  const files = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walk(fullPath));
    } else {
      files.push(fullPath);
    }
  }
  return files;
}

function sha256(filePath) {
  const buffer = fs.readFileSync(filePath);
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function main() {
  const inputDir = process.argv[2];
  const outputFile = process.argv[3] || "document-registry.generated.json";

  if (!inputDir || !fs.existsSync(inputDir)) {
    console.error("Usage: node scripts/generate-hashes.js <input-directory> <output-file>");
    process.exit(1);
  }

  const records = walk(inputDir).map((filePath) => ({
    file: path.relative(process.cwd(), filePath),
    sha256: sha256(filePath),
    generatedAt: new Date().toISOString()
  }));

  fs.writeFileSync(outputFile, JSON.stringify({ records }, null, 2));
  console.log(`Wrote ${records.length} records to ${outputFile}`);
}

main();
