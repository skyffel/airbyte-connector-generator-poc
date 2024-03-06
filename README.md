<div align="center">
	<img width="100px" src="https://framerusercontent.com/images/cAARifhJDsiixC5dDUpMal42BM.svg" />
	<h1>skyffel</h1>
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

3. Install requried packages

   ```bash
   poetry install
   playwright install
   ```

4. Rename `.env.example` to `.env` and set your environment variables

## 🚀 How to use

Generates an Airbyte low-code YAML connector using the API documentation provided via URLs.

```bash
skyffel --goal "<MY ETL GOAL>" --urls "<URL DOC 1>" --urls "<URL DOC 2>"
```

### Example

Here we generate a connector for extracting all blog posts from the Department of Justice.

```bash
skyffel \
    --goal "extract all blog entries from department of justice" \
    --urls https://www.justice.gov/developer/api-documentation/api_v1
```
