# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "seaborn",
#   "matplotlib",
#   "openai",
# ]
# ///

import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import openai

# Environment setup for AI Proxy token
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    print("Error: AIPROXY_TOKEN environment variable not set.")
    sys.exit(1)

openai.api_key = AIPROXY_TOKEN

def load_data(file_path):
    """Load CSV data and provide a quick summary."""
    try:
        data = pd.read_csv(file_path)
        print(f"Data loaded successfully: {file_path}")
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

def analyze_data(data):
    """Perform basic analysis and return summaries."""
    summary = {
        "shape": data.shape,
        "columns": data.columns.tolist(),
        "dtypes": data.dtypes.to_dict(),
        "missing_values": data.isnull().sum().to_dict(),
        "sample_rows": data.sample(5).to_dict(orient="records"),
        "summary_stats": data.describe(include="all").to_dict(),
    }
    return summary

def send_to_llm(summary):
    """Query GPT-4o-Mini for insights."""
    prompt = (
        "Analyze the following dataset summary:\n"
        f"Shape: {summary['shape']}\n"
        f"Columns: {summary['columns']}\n"
        f"Missing Values: {summary['missing_values']}\n"
        f"Sample Rows: {summary['sample_rows']}\n"
        "Provide insights, trends, and any unusual patterns found in the data."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error querying LLM: {e}")
        sys.exit(1)

def visualize_data(data, filename_prefix):
    """Create and save visualizations."""
    try:
        # Correlation heatmap
        numeric_data = data.select_dtypes(include="number")
        if not numeric_data.empty:
            plt.figure(figsize=(8, 6))
            sns.heatmap(numeric_data.corr(), annot=True, cmap="coolwarm")
            plt.title("Correlation Heatmap")
            heatmap_file = f"{filename_prefix}_heatmap.png"
            plt.savefig(heatmap_file)
            plt.close()
            print(f"Saved: {heatmap_file}")

        # Missing value bar chart
        missing_counts = data.isnull().sum()
        if missing_counts.any():
            plt.figure(figsize=(8, 6))
            missing_counts.plot(kind="bar", color="skyblue")
            plt.title("Missing Values")
            plt.ylabel("Count")
            plt.xticks(rotation=45)
            missing_file = f"{filename_prefix}_missing.png"
            plt.savefig(missing_file)
            plt.close()
            print(f"Saved: {missing_file}")
    except Exception as e:
        print(f"Error creating visualizations: {e}")

def create_readme(summary, insights, visualizations):
    """Generate a Markdown README.md."""
    with open("README.md", "w") as f:
        f.write("# Automated Analysis Results\n\n")
        f.write("## Dataset Overview\n")
        f.write(f"Shape: {summary['shape']}\n\n")
        f.write(f"Columns: {', '.join(summary['columns'])}\n\n")
        f.write("## Key Insights\n")
        f.write(insights + "\n\n")
        f.write("## Visualizations\n")
        for viz in visualizations:
            f.write(f"![{viz}]({viz})\n")

def main():
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <dataset.csv>")
        sys.exit(1)

    file_path = sys.argv[1]
    data = load_data(file_path)
    summary = analyze_data(data)
    insights = send_to_llm(summary)

    visualize_data(data, "dataset")
    visualizations = [file for file in os.listdir() if file.endswith(".png")]

    create_readme(summary, insights, visualizations)
    print("Analysis complete. Outputs generated.")

if __name__ == "__main__":
    main()
