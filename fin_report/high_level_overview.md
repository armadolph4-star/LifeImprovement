# High Level Overview: Family Financial Status Report

## 1. Purpose and Goal
This tool is a dedicated presentation and tracking application designed for a family to map out their total economic stature. Its primary immediate use case is to prepare for and present data during meetings with a Financial Adviser. 

It aims to provide absolute clarity on:
*   Total net worth and asset allocation.
*   Liquidity vs. Locked capital (specifically tracking capital locked for a new two-story house construction project).
*   Debt balance vs. Real estate value.

## 2. The Philosophy
*   **Presentation Ready:** The UI is designed to look like a polished, professional report. It is not just a spreadsheet; it is a presentation tool.
*   **Privacy First:** Financial data is highly sensitive. The user explicitly requested that data **never** touch a third-party server or database. It lives on the local device and in the user's private Google Drive.
*   **Ease of Use:** The user and their spouse need to easily input data from their phones or PCs, flip through historical snapshots, and visually digest the information.

## 3. Key Functional Pillars
1.  **Version Control (Snapshots):** The tool allows saving historical states (e.g., "Baseline", "Post-Construction Budget", "Adviser Recommendations").
2.  **Top-Down Reading Flow:** The document reads like an executive summary. High-level charts are grouped at the top for quick viewing, while granular data tables are tucked away at the bottom.
3.  **Print to PDF Mastery:** The tool features specific CSS media queries targeting print (`@media print`). The control panels disappear, and hidden/collapsible tables automatically force themselves open so a perfect physical report can be generated with `Ctrl+P`.
4.  **"Free" vs "Locked" Classification:** A critical feature is categorizing assets not just by type (Stock vs Cash), but by intent (Free for investment vs. Locked for upcoming construction expenses).