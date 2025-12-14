# COBOL Deep Visualizer
*This entire project was vibe coded.*

A modern, interactive web-based tool for visualizing COBOL procedure flow. This application parses legacy COBOL source code and transforms it into interactive flowcharts and graphical decision trees.

## 🚀 Features
-   **Universal Parser**: Supports both Fixed and Free format COBOL.
-   **Hybrid Visualization**:
    -   **Flow View**: Vertical, collapsible list representing logical program flow.
    -   **Graph View**: Horizontal Node-Link Diagram powered by **D3.js**.
-   **Interactive AST**: Click on any node to inspect detailed logical attributes.
-   **Modern UI**: Cyberpunk-inspired aesthetic with glassmorphism, neon glows, and smooth transitions.

## 🛠️ Tech Stack
-   **Backend**: Python 3 (`http.server`, `subprocess`)
-   **Parser**: Python (Regex-based State Machine)
-   **Frontend**: HTML5, Vanilla JavaScript, CSS3
-   **Visualization**: D3.js (v7)
-   **Icons**: Lucide Icons

## 📖 Usage

### 1. Start the Server
The application requires a lightweight Python server to handle file uploads and parsing.
```bash
python server.py
```
*Server will start at `http://localhost:8000`*

### 2. Open the Visualizer
Open your web browser and navigate to:
[http://localhost:8000](http://localhost:8000)

### 3. Upload Code
-   Click **"Upload Source Code"** or drag-and-drop a `.cbl` or `.txt` file.
-   The visualizer will automatically parse and render the structure.

---

## 🧠 Codebase Explanation

### 1. The Parser (`cobolparser.py`)
This script is the brain of the operation. It performs a deep structural analysis of COBOL code.
-   **Format Detection**: Automatically detects if the code is **Fixed Format** (with sequence numbers) or **Free Format** and cleans it accordingly.
-   **Tokenization**: Breaks down lines into tokens (verbs, identifiers, literals).
-   **AST Construction**:
    -   Builds a JSON-serializable **Abstract Syntax Tree (AST)**.
    -   Groups code into `Divisions`, `Sections`, and `Paragraphs`.
    -   **Deep Parsing**: Specifically parses complex logic like `IF/ELSE`, `PERFORM`, and `EVALUATE` into nested JSON structures (`children`, `then`, `else`).

### 2. The Server (`server.py`)
A minimal HTTP bridge between the frontend and the parser.
-   **`do_POST`**: Handles file uploads to the `/parse` endpoint.
-   **Execution**: Saves the upload as a temp file, subprocesses `cobolparser.py`, and streams the resulting `output.json` back to the client.
-   **CORS**: Configured to allow local development access.

### 3. The Frontend (`visualizer.html`)
A single-file interactive dashboard.
-   **Hybrid View Engine**:
    -   **`renderListView()`**: Generates DOM elements for the vertical flowchart view. Uses recursion to handle nested `IF` statements.
    -   **`initD3()`**: Converts the AST into a D3 Hierarchy and renders a graphical SVG tree. Implements Pan/Zoom and Glow filters.
-   **Styling**: Uses CSS variables for theming (`--accent-primary`, `--bg-color`) to create a consistent "Dark Mode" UI.
