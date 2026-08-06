"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const { evaluate } = require("../calculator.js");

test("evaluates arithmetic with precedence and parentheses", () => {
  assert.equal(evaluate("2 + 3 * 4"), 14);
  assert.equal(evaluate("(2 + 3) * 4"), 20);
  assert.equal(evaluate("10 % 4"), 2);
});

test("supports unary signs, decimals, and right-associative powers", () => {
  assert.equal(evaluate("-.5 + 2"), 1.5);
  assert.equal(evaluate("2 ** 3 ** 2"), 512);
  assert.equal(evaluate("2 ** -2"), 0.25);
});

test("rejects code, malformed expressions, and non-finite results", () => {
  assert.throws(() => evaluate("globalThis.process.exit()"), /Unsupported character/);
  assert.throws(() => evaluate("2 +"), /Expected/);
  assert.throws(() => evaluate("1 / 0"), /not finite/);
  assert.throws(() => evaluate(""), /empty/);
  assert.throws(() => evaluate("1".repeat(201)), /too long/);
  assert.throws(() => evaluate(null), /must be a string/);
});
