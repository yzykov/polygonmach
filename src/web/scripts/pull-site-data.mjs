import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  GetObjectCommand,
  S3Client,
} from "@aws-sdk/client-s3";
import { config } from "dotenv";

const here = path.dirname(
  fileURLToPath(import.meta.url),
);

const webRoot = path.resolve(
  here,
  "..",
);

const envPath = path.resolve(
  webRoot,
  "../../.env",
);

const outputDir = path.resolve(
  webRoot,
  ".generated",
);

const outputFile = path.resolve(
  outputDir,
  "site.json",
);

const objectKey = "index/site.json";

config({
  path: envPath,
});

function required(name) {
  const value =
    process.env[name]?.trim();

  if (!value) {
    throw new Error(
      `Environment variable ${name} is not set`,
    );
  }

  return value;
}

async function bodyToString(body) {
  if (
    body &&
    typeof body.transformToString === "function"
  ) {
    return body.transformToString(
      "utf-8",
    );
  }

  throw new Error(
    "Unsupported R2 response body",
  );
}

function validate(raw) {
  const value = JSON.parse(raw);

  if (
    !value ||
    typeof value !== "object" ||
    value.version !== 2 ||
    !value.categories ||
    !value.products ||
    !Array.isArray(value.routes) ||
    !Array.isArray(
      value.root_category_ids,
    )
  ) {
    throw new Error(
      "index/site.json has invalid format " +
        "or unsupported version. " +
        "Expected bundle version 2. " +
        "Run: python -m src.crawler.sync",
    );
  }

  return value;
}

async function downloadViaS3() {
  const bucket =
    required("R2_BUCKET");

  console.log(
    `[site-data] GET s3://${bucket}/${objectKey}`,
  );

  const client = new S3Client({
    region: "auto",
    endpoint:
      required("R2_ENDPOINT"),
    credentials: {
      accessKeyId:
        required(
          "R2_ACCESS_KEY_ID",
        ),
      secretAccessKey:
        required(
          "R2_SECRET_ACCESS_KEY",
        ),
    },
    maxAttempts: 5,
  });

  const response =
    await client.send(
      new GetObjectCommand({
        Bucket: bucket,
        Key: objectKey,
      }),
    );

  return bodyToString(
    response.Body,
  );
}

async function main() {
  fs.mkdirSync(
    outputDir,
    {
      recursive: true,
    },
  );

  const raw =
    await downloadViaS3();

  const parsed =
    validate(raw);

  const tempFile =
    `${outputFile}.tmp`;

  fs.writeFileSync(
    tempFile,
    raw,
    "utf-8",
  );

  fs.renameSync(
    tempFile,
    outputFile,
  );

  console.log(
    `[site-data] saved ${outputFile}: ` +
      `${Object.keys(parsed.categories).length} categories, ` +
      `${Object.keys(parsed.products).length} products, ` +
      `${parsed.routes.length} routes`,
  );

  console.log(
    "[site-data] Next.js page rendering " +
      "will use only this local file.",
  );
}

main().catch((error) => {
  console.error(
    "[site-data] failed:",
    error,
  );

  process.exitCode = 1;
});
