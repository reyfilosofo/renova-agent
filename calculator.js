((root, factory) => {
  "use strict";

  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.RenovaCalculator = api;
})(typeof globalThis === "object" ? globalThis : window, () => {
  "use strict";

  const MAX_EXPRESSION_LENGTH = 200;

  function tokenize(expression) {
    if (typeof expression !== "string") throw new TypeError("Expression must be a string");
    if (!expression.trim()) throw new Error("Expression is empty");
    if (expression.length > MAX_EXPRESSION_LENGTH) throw new Error("Expression is too long");

    const tokens = [];
    let index = 0;
    while (index < expression.length) {
      const char = expression[index];
      if (/\s/.test(char)) {
        index += 1;
        continue;
      }

      const number = expression.slice(index).match(/^(?:\d+(?:\.\d*)?|\.\d+)/);
      if (number) {
        tokens.push({ type: "number", value: Number(number[0]) });
        index += number[0].length;
        continue;
      }

      if (expression.startsWith("**", index)) {
        tokens.push({ type: "operator", value: "**" });
        index += 2;
        continue;
      }

      if ("+-*/%()".includes(char)) {
        tokens.push({ type: char === "(" || char === ")" ? "paren" : "operator", value: char });
        index += 1;
        continue;
      }

      throw new Error(`Unsupported character: ${char}`);
    }
    tokens.push({ type: "eof", value: "" });
    return tokens;
  }

  class Parser {
    constructor(tokens) {
      this.tokens = tokens;
      this.index = 0;
    }

    current() {
      return this.tokens[this.index];
    }

    consume(value) {
      if (this.current().value !== value) throw new Error(`Expected ${value}`);
      this.index += 1;
    }

    parse() {
      const value = this.parseExpression();
      if (this.current().type !== "eof") throw new Error("Unexpected token");
      return value;
    }

    parseExpression() {
      let value = this.parseTerm();
      while (["+", "-"].includes(this.current().value)) {
        const operator = this.current().value;
        this.index += 1;
        const right = this.parseTerm();
        value = operator === "+" ? value + right : value - right;
      }
      return value;
    }

    parseTerm() {
      let value = this.parseUnary();
      while (["*", "/", "%"].includes(this.current().value)) {
        const operator = this.current().value;
        this.index += 1;
        const right = this.parseUnary();
        if (operator === "*") value *= right;
        else if (operator === "/") value /= right;
        else value %= right;
      }
      return value;
    }

    parseUnary() {
      if (this.current().value === "+") {
        this.index += 1;
        return this.parseUnary();
      }
      if (this.current().value === "-") {
        this.index += 1;
        return -this.parseUnary();
      }
      return this.parsePower();
    }

    parsePower() {
      const value = this.parsePrimary();
      if (this.current().value !== "**") return value;
      this.index += 1;
      return value ** this.parseUnary();
    }

    parsePrimary() {
      const token = this.current();
      if (token.type === "number") {
        this.index += 1;
        return token.value;
      }
      if (token.value === "(") {
        this.index += 1;
        const value = this.parseExpression();
        this.consume(")");
        return value;
      }
      throw new Error("Expected a number or parenthesized expression");
    }
  }

  function evaluate(expression) {
    const result = new Parser(tokenize(expression)).parse();
    if (!Number.isFinite(result)) throw new Error("Result is not finite");
    return result;
  }

  return { evaluate };
});
