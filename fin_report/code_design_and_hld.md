# Code Design and High-Level Design (HLD)

## 1. Architecture Overview
This application is a **Zero-Dependency Single-Page Application (SPA)** built entirely within a single `index.html` file using Vanilla HTML, CSS, and JavaScript. 
*   **No Build Step:** No Webpack, React, or Node.js.
*   **No Backend:** State is strictly managed client-side in browser memory.
*   **Storage:** Data persistence is handled via manual JSON file import/export via the OS native file picker (allowing implicit integration with local Google Drive folders).

## 2. Data Structure (The "Ledger")
The application state is maintained in a global `dataLedger` object with V3 snapshot-based version control supporting polymorphic entry types (`entryType`), centralized exchange rates, and explicit owner management (`owners`).

```javascript
let dataLedger = {
    rates: { "₪": 1, "$": 3.65, "€": 3.95 },
    owners: ["משותף", "שלי", "נעמה"],
    title: "Document Title",
    subtitle: "Document Subtitle",
    versions: [
        {
            id: "v_123456789",
            name: "Snapshot Name",
            data: [
                {
                    id: "timestamp_string",
                    entryType: "stock" | "realestate" | "pension" | "rsu" | "cash" | "alternative" | "debt",
                    owner: "משותף",
                    currency: "$" | "₪" | "€",
                    amount: 150000,
                    reType: "מגורים" | "השקעה",
                    debt: 50000,
                }
            ]
        }
    ]
};

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
*   **Adding a New Tab:** 
    1. Add a corresponding navigation `<button class="tab-btn" onclick="switchTab('tabId')">Tab Name</button>` inside `.tab-nav` (e.g., the **מניות** tab positioned between מבט על and נתונים).
    2. Create a matching `.tab-panel` container with `id="tabId"` containing the desired section content (such as `#tab-stocks` for stock portfolio analytics and KPIs).
    3. Verify that `@media print` rules force all `.tab-panel` elements to display properly so that multi-tab content is fully exported during native printing.
*   **Modifying the UI:** Ensure changes respect the strict DOM hierarchy (Toolbar -> Tab Navigation -> Tab Panels -> Tables).
*   **State Changes:** Any mutation to data *must* be followed by a call to `renderData()` and *must only* mutate `dataLedger.versions[getCurrentVersionIndex()].data`.
*   **V3.1 Dynamic Market & FX Sync Schema Updates:**
    *   **Ledger-level rates:** Maintain `dataLedger.rates` as active rates used by `toILS()`, alongside `dataLedger.defaultRates` (user-defined fallback rates) and `dataLedger.ratesMeta` (`{ source: "manual" | "live" | "fallback", updatedAt: string | null }`).
    *   **Item-level fields for `stock` and `rsu`:** `ticker` (`string`, optional), `manualPrice` (`number`, default price per share), `price` (`number`, effective price), `priceSource` (`"manual" | "live" | "fallback"`), and `priceUpdatedAt` (`string | null`).
    *   **Active-Snapshot Market Fetch:** Triggered strictly on-demand via `refreshDynamicMarketData()`. It fetches FX rates and stock/RSU quotes for the currently active snapshot version only, utilizing a 5-second `AbortController` timeout and falling back gracefully to `defaultRates` and `manualPrice` when offline, unconfigured, or blocked.
