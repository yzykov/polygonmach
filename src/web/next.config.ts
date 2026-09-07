import type { NextConfig } from "next";
import path from "node:path";
import { config } from "dotenv";

config({
  path: path.resolve(process.cwd(), "../../.env"),
});

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
};

export default nextConfig;