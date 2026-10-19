# Project Guidelines (Strict Directives for Future Agents)

When interacting with or modifying this codebase, you MUST adhere to the following rules established by the user.

## 1. Data Privacy and Security (CRITICAL)
*   **NO BACKEND / NO CLOUD DATABASES:** Do not attempt to integrate Firebase, Supabase, MongoDB, or any other backend.
*   **NO API KEYS IN CODE:** Do not add Google Drive API keys, OAuth tokens, or any secrets to the code. 
*   **Data Persistence Strategy:** Data syncing is strictly handled via the OS native file picker interacting with local synced folders (like Google Drive desktop/mobile apps). The app reads/writes JSON files via the user's explicit clicks (`FileReader` and `Blob`/`URL.createObjectURL`).

## 2. Readability and UI Structure
The user prefers a highly readable, structured, and non-overwhelming interface. Do not break this top-to-bottom flow:
1.  **Header:** Clean, basic design with editable title/subtitle.
2.  **Control Panel:** Form inputs, version dropdowns, and file operations. (Must be hidden on print).
3.  **TOC (Table of Contents):** An editable agenda/overview mapping out the discussion.
4.  **Small Dives (High-Level Summaries):** All infographics and aggregate sums (Net Worth, Free vs Locked ratios) grouped together immediately after the TOC.
5.  **Deep Dives (Drill-Down Data):** All granular HTML tables grouped at the absolute bottom.

## 3. UI/UX Rules
*   **Collapsible Elements:** Granular data tables must use native HTML `<details>` and `<summary>` tags to prevent UI clutter.
*   **Hebrew First:** The document is `dir="rtl"` and `lang="he"`. All new labels, prompts, and alerts must be written in fluent Hebrew.
*   **Offline Functionality:** Infographics (Pie charts) use CSS `conic-gradient` instead of external charting libraries (like Chart.js) to ensure they render instantly even without internet access. Do not introduce CDN-dependent JS libraries unless absolutely necessary.
*   **Print Optimization:** The `@media print` CSS block is mandatory. If you add a new interactive element, ensure it is hidden during print. Ensure any `<details>` tags are forced open during print so all data is captured in the PDF.

## 4. Coding Standards
*   **Single File Mandate:** Keep all HTML, CSS, and JavaScript in a single `index.html` file.
*   **Vanilla JS:** Use modern Vanilla JavaScript (ES6+). No frameworks (React, Vue, etc.) are permitted.
*   **Non-Destructive Migrations:** If you alter the `dataLedger` JSON schema in the future, you must update the `loadLedger()` function to detect old JSON files and gracefully map their data to the new schema without deleting user data.