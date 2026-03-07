/**
 * HARDEN-026: Tests for safeSetItem localStorage wrapper.
 */
import { safeSetItem } from "../../lib/storage";

beforeEach(() => {
  localStorage.clear();
});

describe("safeSetItem", () => {
  it("writes to localStorage on success", () => {
    safeSetItem("key1", "value1");
    expect(localStorage.getItem("key1")).toBe("value1");
  });

  it("overwrites existing values", () => {
    localStorage.setItem("key1", "old");
    safeSetItem("key1", "new");
    expect(localStorage.getItem("key1")).toBe("new");
  });

  it("evicts search_partial_* entries on QuotaExceededError and retries", () => {
    // Seed with evictable partial search entries
    localStorage.setItem("search_partial_abc", JSON.stringify({ data: "x" }));
    localStorage.setItem("search_partial_def", JSON.stringify({ data: "y" }));
    localStorage.setItem("keep_me", "important");

    let callCount = 0;
    const originalSetItem = Storage.prototype.setItem;
    jest.spyOn(Storage.prototype, "setItem").mockImplementation(function (
      this: Storage,
      key: string,
      value: string,
    ) {
      callCount++;
      if (callCount === 1) {
        // First call throws QuotaExceededError
        const err = new DOMException("quota exceeded", "QuotaExceededError");
        throw err;
      }
      // After eviction, allow the write
      return originalSetItem.call(this, key, value);
    });

    safeSetItem("new_key", "new_value");

    // Partial entries should be evicted
    expect(localStorage.getItem("search_partial_abc")).toBeNull();
    expect(localStorage.getItem("search_partial_def")).toBeNull();
    // Non-evictable entries preserved
    expect(localStorage.getItem("keep_me")).toBe("important");
    // The write succeeded on retry
    expect(localStorage.getItem("new_key")).toBe("new_value");

    jest.restoreAllMocks();
  });

  it("evicts smartlic_last_search as fallback", () => {
    localStorage.setItem("smartlic_last_search", JSON.stringify({ big: "data" }));

    let callCount = 0;
    const originalSetItem = Storage.prototype.setItem;
    jest.spyOn(Storage.prototype, "setItem").mockImplementation(function (
      this: Storage,
      key: string,
      value: string,
    ) {
      callCount++;
      if (callCount === 1) {
        throw new DOMException("quota exceeded", "QuotaExceededError");
      }
      return originalSetItem.call(this, key, value);
    });

    safeSetItem("my_key", "my_value");

    expect(localStorage.getItem("smartlic_last_search")).toBeNull();
    expect(localStorage.getItem("my_key")).toBe("my_value");

    jest.restoreAllMocks();
  });

  it("silently fails if eviction does not free enough space", () => {
    // No evictable entries exist
    localStorage.setItem("important_data", "keep");

    jest.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("quota exceeded", "QuotaExceededError");
    });

    // Should not throw
    expect(() => safeSetItem("key", "value")).not.toThrow();

    jest.restoreAllMocks();
    // Original data still intact
    expect(localStorage.getItem("important_data")).toBe("keep");
  });

  it("silently ignores non-quota errors", () => {
    jest.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("SecurityError");
    });

    expect(() => safeSetItem("key", "value")).not.toThrow();

    jest.restoreAllMocks();
  });

  it("handles legacy Firefox QuotaExceededError (code 1014)", () => {
    localStorage.setItem("search_partial_old", "data");

    let callCount = 0;
    const originalSetItem = Storage.prototype.setItem;
    jest.spyOn(Storage.prototype, "setItem").mockImplementation(function (
      this: Storage,
      key: string,
      value: string,
    ) {
      callCount++;
      if (callCount === 1) {
        const err = new DOMException("NS_ERROR_DOM_QUOTA_REACHED");
        Object.defineProperty(err, "code", { value: 1014 });
        throw err;
      }
      return originalSetItem.call(this, key, value);
    });

    safeSetItem("ff_key", "ff_value");
    expect(localStorage.getItem("ff_key")).toBe("ff_value");

    jest.restoreAllMocks();
  });
});
