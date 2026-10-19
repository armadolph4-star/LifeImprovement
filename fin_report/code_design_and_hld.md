# Code Design and High-Level Design (HLD)

## 1. Architecture Overview
This application is a **Zero-Dependency Single-Page Application (SPA)** built entirely within a single `index.html` file using Vanilla HTML, CSS, and JavaScript. 
*   **No Build Step:** No Webpack, React, or Node.js.
*   **No Backend:** State is strictly managed client-side in browser memory.
*   **Storage:** Data persistence is handled via manual JSON file import/export via the OS native file picker (allowing implicit integration with local Google Drive folders).

## 2. Data Structure (The "Ledger")
The application state is maintained in a global `dataLedger` object. It uses a snapshot-based version control system to allow users to compare states (e.g., "Before Meeting" vs. "After Meeting").

```javascript
let dataLedger = {
    title: "Document Title",
    subtitle: "Document Subtitle",
    versions: [
        {
            id: "v_123456789",
            name: "Snapshot Name",
            data: [
                {
                    id: "timestamp_string",
                    desc: "Asset/Liability Name",
                    category: "עו״ש" | "שוק ההון" | "פנסיה" | "קרן השתלמות" | "נדל״ן / דירה" | "הלוואות / חובות" | "אחר",
                    owner: "שלי" | "נעמה" | "משותף",
                    liquidity: "חופשי" | "נעול",
                    amount: 150000 // Number (Always positive in state, negated in UI if debt)
                }
            ]
        }
    ]
};
```

## 3. Global State Variables
*   `dataLedger`: The main state object.
*   `currentVersionId`: Tracks the currently selected snapshot in the UI.
*   `TARGET_FILE_NAME`: Default name for exported JSON (`financial_data.json`).
*   `categoryColors`: A mapping object dictating the color scheme for UI tags and chart slices.

## 4. Core Lifecycle & Functions
*   `init()`: Called on load. Attempts to fetch `financial_data.json` if served over HTTP. If local (`file://`), defaults to an empty ledger.
*   `loadLedger(loadedData)`: Validates imported JSON. Contains a **Migration Strategy** to upgrade legacy V1 (flat data array) to V2 (Ledger with versions array) without data loss.
*   `renderData()`: The core DOM update loop. 
    1. Clears existing table bodies.
    2. Filters the active version's data into three buckets: Liquid, Pension, Real Estate.
    3. Generates `<tr>` elements and injects them into the respective tables.
    4. Calls `updateCharts()`.
*   `updateCharts()`: Calculates sums, net worth, and free/locked ratios, then invokes `applyPieChart()` to update the visual CSS conic-gradients.

## 5. Adding New Features (Agent Instructions)
*   **Adding a new Category:** Add it to the `<select id="categoryInput">` options, assign it a color in `categoryColors`, and update the `if/else` sorting logic inside `renderData()` to route it to the correct table.
*   **Modifying the UI:** Ensure changes respect the strict DOM hierarchy (Controls -> TOC -> Summaries -> Tables).
*   **State Changes:** Any mutation to data *must* be followed by a call to `renderData()` and *must only* mutate `dataLedger.versions[getCurrentVersionIndex()].data`.