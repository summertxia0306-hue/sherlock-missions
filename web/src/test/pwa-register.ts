let refreshReady = false

export function setRefreshReadyForTest(value: boolean) {
  refreshReady = value
}

export function useRegisterSW() {
  return {
    needRefresh: [refreshReady, () => { refreshReady = false }] as const,
    offlineReady: [false, () => undefined] as const,
    updateServiceWorker: async () => undefined
  }
}
