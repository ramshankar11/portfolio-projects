importScripts("https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js");

let pyodide = null;

async function loadPyodideAndPackages() {
    try {
        self.postMessage({ type: 'LOG', data: 'Loading Python Engine...' });
        pyodide = await loadPyodide();

        self.postMessage({ type: 'LOG', data: 'Loading Pandas...' });
        await pyodide.loadPackage("pandas");

        self.postMessage({ type: 'READY' });
    } catch (e) {
        self.postMessage({ type: 'ERROR', error: e.toString() });
    }
}

loadPyodideAndPackages();

self.onmessage = async function (e) {
    const { type, file, rules } = e.data;

    if (type === 'CLEAN') {
        if (!pyodide) {
            self.postMessage({ type: 'ERROR', error: 'Engine not ready.' });
            return;
        }

        try {
            self.postMessage({ type: 'LOG', data: 'Mounting file...' });

            pyodide.FS.writeFile('/input_data', new Uint8Array(file));

            const script = `
import pandas as pd
import io

print("Reading file...")
try:
    df = pd.read_csv('/input_data')
except:
    df = pd.read_excel('/input_data')

original_shape = df.shape
print(f"Loaded DataFrame: {original_shape}")

rules = ${JSON.stringify(rules)}

for rule in rules:
    rtype = rule['type']
    params = rule.get('params', {})
    
    if rtype == 'drop_duplicates':
        df.drop_duplicates(inplace=True)
        print("Dropped duplicates")
        
    elif rtype == 'drop_na':
        df.dropna(inplace=True)
        print("Dropped N/A rows")
        
    elif rtype == 'fill_na':
        val = params.get('value', 0)
        df.fillna(val, inplace=True)
        print(f"Filled N/A with {val}")

    elif rtype == 'fill_na_mean':
        numeric_cols = df.select_dtypes(include=['number']).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
        print("Filled N/A with mean")
        
    elif rtype == 'standard_columns':
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        print("Standardized columns")
        
    elif rtype == 'capitalize_strings':
        str_cols = df.select_dtypes(include=['object', 'string']).columns
        for c in str_cols:
            df[c] = df[c].astype(str).str.title()
        print("Capitalized string columns")

    elif rtype == 'trim_strings':
        str_cols = df.select_dtypes(include=['object', 'string']).columns
        for c in str_cols:
            df[c] = df[c].astype(str).str.strip()
        print("Trimmed whitespace")
        
    elif rtype == 'sort_values':
        col = params.get('column')
        if col in df.columns:
            df.sort_values(by=col, inplace=True)
            print(f"Sorted by {col}")
        else:
            print(f"Warning: Column {col} not found for sorting.")

final_shape = df.shape
print(f"Final Info: {final_shape}")

output = df.to_csv(index=False)
output
`;

            self.postMessage({ type: 'LOG', data: 'Running cleaning logic...' });
            const csvOutput = await pyodide.runPythonAsync(script);
            self.postMessage({ type: 'RESULT', data: csvOutput });

        } catch (err) {
            self.postMessage({ type: 'ERROR', error: err.toString() });
        }
    }
};
