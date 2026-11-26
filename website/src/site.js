// One place for URLs and names, so changing the repo, domain or contact touches a single file.
// REPO_URL assumes the repo is public. If it stays private, the install steps in the docs have nothing to clone.
export const REPO_URL = "https://github.com/monitry/Monitry";
export const ISSUES_URL = `${REPO_URL}/issues`;
// The Mac app (.dmg) is attached to a GitHub Release by .github/workflows/build-mac.yml when a version tag (v1.0.0) is pushed.
// Until the first release exists this link shows a 404, so publish a release before deploying the site.
export const DOWNLOAD_URL = `${REPO_URL}/releases/latest`;
export const APP_DATA_FOLDER = "~/Library/Application Support/Onitry";
export const CLONE_URL = `${REPO_URL}.git`;
export const ANTHROPIC_PRIVACY_URL = "https://www.anthropic.com/legal/privacy";
export const ANTHROPIC_CONSOLE_URL = "https://console.anthropic.com/";
export const PRODUCT = "Onitry";
export const LAST_UPDATED = "2026-11-26"; // shown on the privacy and terms pages; update when they change
