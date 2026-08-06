import assert from "node:assert/strict";
import test from "node:test";

import { normalizeTitle } from "../src/normalize-title.js";

test("normalizes a title into a slug", () => {
  assert.equal(normalizeTitle("Safe Repository Agent"), "safe-repository-agent");
});

test("ignores whitespace around a title", () => {
  assert.equal(normalizeTitle("  Safe Repository Agent  "), "safe-repository-agent");
});

