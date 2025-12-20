# Local Data Cleansing AI

Access the already deployed application at https://kaleidoscopic-pudding-305567.netlify.app/

A **Zero-Setup Data Cleansing App** that runs entirely in your browser using **WebAssembly (Pyodide)**.
Your data never leaves your machine. The heavy lifting is done by Python/Pandas running inside Chrome/Edge.

## 🚀 How to Run

Since modern browsers block some functionality when opening HTML files directly (via `file://`), you need to host it locally.
Since you have Python installed, this is instant:

1.  Open Terminal/Command Prompt in this folder:
    `Data Engineering\Data_Cleansing_UI`

2.  Run the instant server:
    ```powershell
    python -m http.server 8000
    ```

3.  Open your browser to:
    **[http://localhost:8000](http://localhost:8000)**

## ✨ Features
- **Local Processing**: Uses your CPU to run Pandas commands.
- **Premium UI**: Dark mode, glassmorphism, smooth animations.
- **Drag & Drop**: Load CSV/Excel files easily.
- **Pipeline Builder**: Chain transformations (Drop Nulls, Remove Duplicates, etc.).
- **Privacy**: No server uploads.

## 🛠 Tech Stack
- **Frontend**: Vanilla HTML5, CSS3, JavaScript.
- **Engine**: Pyodide (Python compiled to WebAssembly) + Pandas.
