import csv
import chardet
from datetime import datetime, timedelta, date
import os
import glob  # Import glob to handle file pattern matching

def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    return chardet.detect(raw_data)['encoding']

def parse_finnish_float(value):
    return float(value.replace(',', '.'))

def read_csv(file_path):
    encoding = detect_encoding(file_path)
    data = {}
    with open(file_path, 'r', encoding=encoding) as file:
        reader = csv.reader(file, delimiter=';')
        next(reader)  # Skip header
        for row in reader:
            try:
                timestamp = datetime.strptime(row[0], '%Y-%m-%dT%H:%M:%S')
                data[timestamp] = parse_finnish_float(row[3])
            except (ValueError, IndexError) as e:
                print(f"Skipping row in prices file due to error: {e}")
    return data

def read_consumption_csv(file_path):
    encoding = detect_encoding(file_path)
    data = {}
    with open(file_path, 'r', encoding=encoding) as file:
        reader = csv.reader(file, delimiter=';')
        next(reader)  # Skip header
        for row in reader:
            try:
                timestamp = datetime.strptime(row[0], '%d.%m. %H:%M:%S')
                timestamp = timestamp.replace(year=2024)
                day_consumption = row[1].strip()
                night_consumption = row[2].strip()
                
                if day_consumption:
                    consumption = parse_finnish_float(day_consumption)
                elif night_consumption:
                    consumption = parse_finnish_float(night_consumption)
                else:
                    print(f"Skipping row with empty consumption value: {row}")
                    continue
                
                data[timestamp] = consumption
            except (ValueError, IndexError) as e:
                if 'Yhteensä' not in str(e):  # Ignore the 'Yhteensä' row
                    print(f"Skipping row in consumption file due to error: {e}")
    return data

def process_data(prices, consumption):
    result = {}
    current_date = datetime(2024, 1, 1)
    end_date = min(datetime(2025, 1, 1), datetime.combine(date.today(), datetime.min.time()))

    while current_date < end_date:
        daily_data = []
        daily_total_cost = 0
        daily_total_consumption = 0
        for hour in range(24):
            timestamp = current_date + timedelta(hours=hour)
            price = prices.get(timestamp, 0)
            cons = consumption.get(timestamp, 0)
            cost = (price * cons) / 100  # Convert cents to euros
            daily_data.append({
                'hour': f'{hour:02d}:00',
                'consumption': cons,
                'price': price,
                'cost': cost
            })
            daily_total_cost += cost
            daily_total_consumption += cons

        result[current_date.date()] = {
            'hourly_data': daily_data,
            'total_cost': daily_total_cost,
            'total_consumption': daily_total_consumption
        }
        current_date += timedelta(days=1)

    return result

def save_processed_data(data, filename):
    # Create the 'processed' directory if it doesn't exist
    os.makedirs('processed', exist_ok=True)
    
    filepath = os.path.join('processed', filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['Date', 'Hour', 'Consumption (kW)', 'Price (snt/kWh)', 'Cost (EUR)'])
        writer.writeheader()
        
        for date, daily_data in data.items():
            for hour_data in daily_data['hourly_data']:
                writer.writerow({
                    'Date': date,
                    'Hour': hour_data['hour'],
                    'Consumption (kW)': hour_data['consumption'],
                    'Price (snt/kWh)': hour_data['price'],
                    'Cost (EUR)': hour_data['cost']
                })
    
    print(f"Processed data saved to {filepath}")

# Main execution
if __name__ == "__main__":
    prices = read_csv('downloads/spot_prices.csv')
    
    # Search for all consumption CSV files in the downloads directory
    consumption_files = glob.glob('downloads/consumption*.csv')
    
    if not consumption_files:
        raise FileNotFoundError("No consumption files found in the 'downloads' directory.")
    
    # Select the latest consumption file based on modification time
    latest_consumption_file = max(consumption_files, key=os.path.getmtime)
    
    consumption = read_consumption_csv(latest_consumption_file)
    processed_data = process_data(prices, consumption)
    save_processed_data(processed_data, 'processed_data_2024.csv')
