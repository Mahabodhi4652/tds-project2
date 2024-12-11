import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import chardet  # For detecting file encoding

# Ensure AIPROXY_TOKEN is set
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    raise EnvironmentError("AIPROXY_TOKEN environment variable not set.")

# Constants for AI Proxy
AI_PROXY_ENDPOINT = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
MODEL = "gpt-4o-mini"

def query_llm(prompt):
    """Query AI Proxy LLM and return the response."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(AI_PROXY_ENDPOINT, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Error querying LLM: {response.status_code} - {response.json()}")
        return None
    return response.json()["choices"][0]["message"]["content"]

def detect_file_encoding(filepath):
    """Detect the encoding of a file using chardet."""
    with open(filepath, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def load_data(filepath):
    """Load the dataset with appropriate encoding handling."""
    print(f"Loading dataset: {filepath}")
    
    # Detect file encoding
    encoding = detect_file_encoding(filepath)
    print(f"Detected file encoding: {encoding}")
    
    try:
        # Try reading the CSV file with the detected encoding
        data = pd.read_csv(filepath, encoding=encoding)
        print("Data loaded successfully.")
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def create_visualizations(data, output_folder):
    """Create and save visualizations from the dataset."""
    heatmap_path = os.path.join(output_folder, "correlation_heatmap.png")
    print("Generating heatmap...")

    # Select only numeric columns
    numeric_data = data.select_dtypes(include=["number"])
    if numeric_data.empty:
        print("No numeric data available for correlation heatmap.")
        return None

    corr_matrix = numeric_data.corr()

    # Generate heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f")
    plt.title("Correlation Heatmap")
    plt.savefig(heatmap_path)
    plt.close()
    print(f"Heatmap saved as {heatmap_path}")

    # Additional visualization: Bar chart of missing values
    missing_values_path = os.path.join(output_folder, "missing_values_bar_chart.png")
    missing_data = data.isnull().sum()
    if missing_data.any():
        plt.figure(figsize=(10, 6))
        missing_data.plot(kind="bar", color="skyblue")
        plt.title("Missing Values by Column")
        plt.ylabel("Count of Missing Values")
        plt.savefig(missing_values_path)
        plt.close()
        print(f"Bar chart of missing values saved as {missing_values_path}")
    else:
        print("No missing data found.")

    return heatmap_path

def run_analysis(filepath):
    """Run the full analysis pipeline."""
    # Load the dataset
    data = load_data(filepath)
    if data is None:
        return

    # Derive folder name from file name
    base_name = os.path.basename(filepath)
    folder_name = base_name[:-4]  # Remove '.csv'
    output_folder = os.path.join(os.getcwd(), folder_name)

    # Create the folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    print(f"Output folder created: {output_folder}")

    print("Generating visualizations...")
    heatmap_path = create_visualizations(data, output_folder)

    print("Generating findings...")
    summary_stats = data.describe(include='all').to_string()
    prompt = (f"Analyze the dataset and provide insights. Columns: {', '.join(data.columns)}\n"
              f"Summary statistics: {summary_stats}")
    findings = query_llm(prompt)
    if findings:
        print("Findings from LLM:")
        print(findings)

        # Write findings to README.md
        readme_path = os.path.join(output_folder, "README.md")
        with open(readme_path, "w") as f:
            f.write("# Analysis Results\n\n")
            f.write(f"## Insights from Dataset\n\n{findings}\n\n")
            if heatmap_path:
                f.write(f"![Correlation Heatmap](./{os.path.basename(heatmap_path)})\n")
        print(f"README.md file created at {readme_path}.")
    else:
        print("Failed to retrieve findings from LLM.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <dataset.csv>")
    else:
        run_analysis(sys.argv[1])
