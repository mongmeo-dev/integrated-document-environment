import { readdir, readFile, writeFile } from "node:fs/promises";

const generatedRoot = new URL("../src/api/generated/", import.meta.url);

async function normalizeDirectory(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = new URL(entry.name, directory);
    if (entry.isDirectory()) {
      await normalizeDirectory(new URL(`${entry.name}/`, directory));
      continue;
    }
    if (!entry.name.endsWith(".ts") && !entry.name.endsWith(".md")) continue;

    const source = await readFile(path, "utf8");
    const normalized = `${source
      .split("\n")
      .map((line) => line.trimEnd())
      .join("\n")
      .trimEnd()}\n`;
    await writeFile(path, normalized);
  }
}

await normalizeDirectory(generatedRoot);
