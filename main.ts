// Entry point of the bounty's grader: copies VIDEO.json, which names the
// TikTok video, from this repository to the output folder. Standard library
// only, no network, and the same bytes on every run.
import { chmodSync, copyFileSync, mkdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = join(process.env.MAKEFUN_BOT_DIR ?? here, "VIDEO.json");
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";

// Fail loudly here rather than hand the grader a file it will refuse: the
// file must be a small JSON object whose url is a TikTok video's full address.
const raw = readFileSync(source);
if (raw.length > 16384) {
  throw new Error("VIDEO.json is larger than 16384 bytes");
}
const video = JSON.parse(raw.toString("utf8"));
const address = /^https:\/\/(www\.|m\.)?tiktok\.com\/@[^/]+\/video\/\d+/;
if (typeof video?.url !== "string" || !address.test(video.url)) {
  throw new Error("VIDEO.json needs the video's full TikTok address as url");
}

const target = join(outDir, "VIDEO.json");
mkdirSync(outDir, { recursive: true });
copyFileSync(source, target);
chmodSync(target, 0o644);
