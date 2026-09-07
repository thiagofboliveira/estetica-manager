import { describe, it, expect } from "vitest";
import { compressImage } from "./imageUtils";

describe("compressImage utility", () => {
  it("rejects gracefully if file is invalid or not an image", async () => {
    const invalidFile = new File(["not an image"], "test.txt", { type: "text/plain" });
    await expect(compressImage(invalidFile)).rejects.toThrow();
  });
});
