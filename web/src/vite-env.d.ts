/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />

interface ImportMetaEnv {
  readonly VITE_CLOUDBASE_ENV_ID?: string
  readonly VITE_CLOUDBASE_ACCESS_KEY?: string
  readonly VITE_CLOUDBASE_FUNCTION_NAME?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

