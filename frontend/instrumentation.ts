// Polyfill localStorage for Node.js 25+ where it exists globally
// but throws "localStorage.getItem is not a function" without --localstorage-file.
// Next.js 15's dev overlay accesses localStorage during SSR, triggering this error.

export async function register() {
  if (typeof globalThis.localStorage !== "undefined") {
    try {
      globalThis.localStorage.getItem("__test__");
    } catch {
      // localStorage exists but is non-functional — replace with a no-op shim
      const store = new Map<string, string>();
      (globalThis as any).localStorage = {
        getItem: (key: string) => store.get(key) ?? null,
        setItem: (key: string, value: string) => store.set(key, String(value)),
        removeItem: (key: string) => store.delete(key),
        clear: () => store.clear(),
        get length() {
          return store.size;
        },
        key: (index: number) => [...store.keys()][index] ?? null,
      };
    }
  }
}
