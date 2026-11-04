import '@testing-library/jest-dom/vitest';

// O jsdom não implementa ResizeObserver (usado pelo ResponsiveContainer do Recharts).
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver ??= ResizeObserverStub as unknown as typeof ResizeObserver;
