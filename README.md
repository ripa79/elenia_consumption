# Sähkö-kulutus (Electricity Consumption Analyzer)

This project analyzes electricity consumption and pricing data, comparing spot prices with a fixed-price contract to determine which option is more beneficial for Finnish electricity consumers.

## Features

- Fetches and processes electricity consumption data from Elenia (Finnish electricity provider)
- Retrieves spot price data from Vattenfall API
- Analyzes electricity consumption and pricing data
- Compares spot prices with a fixed-price contract (default: 8.5 snt/kWh)
- Provides monthly and annual summaries
- Displays current spot price
- Generates visualizations of monthly savings and cost comparisons

## Prerequisites

- Python 3.7+
- Chrome browser (for web scraping)
- Elenia account (for fetching consumption data)

## Installation

1. Clone the repository:
   ```
   git clone git@github.com:saltsami/elenia_consumption.git
   cd elenia_consumption
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root and add your Elenia credentials and fixed price:
   ```
   ELENIA_USERNAME=your_username
   ELENIA_PASSWORD=your_password
   FIXED_PRICE=8.5
   ```

## Usage

1. Fetch and process the latest data:
   ```
   python fetch_current_year_data.py
   python data_processing.py
   ```
   This will create a 'processed' folder and save the processed data there.

2. Run the analysis script:
   ```
   python data_analysis.py
   ```

3. The script will display the analysis results in the console and open a matplotlib window with visualizations.

## File Structure

After running the scripts, your project structure should look like this:

```
el