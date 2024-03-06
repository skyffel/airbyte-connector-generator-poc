<div align="center">
	<img width="100px" src="https://framerusercontent.com/images/cAARifhJDsiixC5dDUpMal42BM.svg" />
	<h1>skyffel</h1>
	<p>
		<b>Move your business data from A to B with AI.</b>
	</p>
	<br>
    <p align="center">
        <a href="#-key-features">Features</a> •
        <a href="#-installation">Installation</a> •
        <a href="#-how-to-use">How to use</a> •
    </p>
</div>

## ✅ Key features

- Supports Airbyte Low-Code generation
- Provides a production ready REST API.
- Customizable splitting/chunking.
- Includes options for encoding data using different encoding models both propriatory and open source.
- Built in code interpreter mode for computational question & answer scenarios.
- Allows session management through unique IDs for caching purposes.

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

Generates s

```bash
skyffel \
    --goal "extract all blog entries from department of justice" \
    --urls https://www.justice.gov/developer/api-documentation/api_v1
```
