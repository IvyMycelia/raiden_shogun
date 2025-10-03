import json
import os

def insert(data: dict, file: str):
    """
    Inserts data into a JSON file.
    If the file does not exist, it creates a new one.
    If the file exists, it appends the data to the existing file.
    """
    # Ensure data is in a valid format (dict)
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary.")

    file = f"./bot/dataBase/{file}.json"

    # Check if the file exists
    if os.path.exists(file):
        try:
            with open(file, 'r') as f:
                try:
                    existing_data = json.load(f)
                    # Ensure the existing data is a list, if it's not, make it one
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
                except json.JSONDecodeError:
                    existing_data = []  # If the file is empty or malformed, use an empty list
        except Exception as e:
            print(f"Error reading {file}: {e}")
            existing_data = []
    else:
        existing_data = []

    # Append the new data
    existing_data.append(data)

    # Write data back to the file
    try:
        with open(file, 'w') as f:
            json.dump(existing_data, f, indent=4)
    except Exception as e:
        print(f"Error writing to {file}: {e}")
