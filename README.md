<div align="center">
	<img width="128px" src="https://framerusercontent.com/images/cAARifhJDsiixC5dDUpMal42BM.svg" />
	<br>
	<p>
		<b>moving your data from a to b, one shovel at a time.</b>
	</p>
	<br>
    <p align="center">
        <a href="#-key-features">Features</a> •
        <a href="#-installation">Installation</a> •
        <a href="#-how-to-use">How to use</a>
    </p>
</div>

## ✅ Key features

- Co-pilot for generating ETL code for HTTP APIs
- Support Airbyte low-code YAML connectors
- Scrapes API documentation
- Produces OpenAPI specifications

## 📦 Installation

1. Clone the repository

   ```bash
   git clone https://github.com/skyffel/airbyte-connector-generator-poc
   cd airbyte-connector-generator-poc
   ```

2. Setup virtual environment

   ```bash
   # Using virtualenv
   virtualenv env
   source env/bin/activate

   # Or using venv
   python3 -m venv env
   source env/bin/activate

   # Or using poetry
   poetry shell
   ```

3. Install required packages

   ```bash
   poetry install
   playwright install
   ```

## 🚀 How to use

Generates an Airbyte low-code YAML connector using the API documentation provided via URLs.

```bash
skyffel --goal "<MY ETL GOAL>" --urls "<URL DOC 1>" --urls "<URL DOC 2>"
```
Here we generate a connector for extracting all blog posts from the Department of Justice.

```bash
skyffel \
    --goal "extract all blog entries from department of justice" \
    --urls https://www.justice.gov/developer/api-documentation/api_v1
```

### 📥 Import to Airbyte

After generating the connector, you need to import it to Airbyte. Eventually they might expose an API to do this programatically 🤞 Until then, here's how:

1. Go to your Airbyte workspace
2. Click on Builder [BETA] in the menu

   <img width="200px" src="https://github.com/skyffel/airbyte-connector-generator-poc/assets/25622412/4b7ce182-03b4-48d7-a99a-bead287ff297" />

3. Click “New custom connector” in the upper right corner

   <img width="200px" src="https://github.com/skyffel/airbyte-connector-generator-poc/assets/25622412/f89d0660-1dc1-4f37-b46c-c22a94e7cee0" />
4. Click “Import a YAML” and select the generated `airbyte_connector.yaml`

   <img width="200px" src="https://github.com/skyffel/airbyte-connector-generator-poc/assets/25622412/dc210240-b23d-47b0-a024-26e70834b28a" />

5. Fill in the test values and run the test
6. Press “Publish to workspace”
