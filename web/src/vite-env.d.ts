/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />

interface ImportMetaEnv {
  readonly VITE_APP_BASE?: string
  readonly VITE_CLOUDBASE_ENV_ID?: string
  readonly VITE_CLOUDBASE_ACCESS_KEY?: string
  readonly VITE_CLOUDBASE_FUNCTION_NAME?: string
  readonly VITE_SHERLOCK_API_URL?: string
  readonly VITE_DIRECT_UPLOAD_PROBE?: string
  readonly VITE_SPEAKING_DIRECT_UPLOAD_TEST?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
