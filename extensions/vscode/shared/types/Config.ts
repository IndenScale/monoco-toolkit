/**
 * Configuration types
 */

export interface MonocoConfig {
  executablePath: string;
  webUrl: string;
  apiBaseUrl?: string;
}

export const DEFAULT_CONFIG: MonocoConfig = {
  executablePath: "monoco",
  webUrl: "http://127.0.0.1:8642",
  apiBaseUrl: "http://127.0.0.1:8642/api/v1",
};
