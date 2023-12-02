import random
import sqlite3

# Connect to SQLite database (creates a new file if it doesn't exist)
conn = sqlite3.connect('vehicles.db')
cursor = conn.cursor()

# Create the Vehicles table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Vehicles (
        id INTEGER PRIMARY KEY,
        make TEXT,
        model TEXT,
        year INTEGER,
        color TEXT
    )
''')

# List of sample data
makes = ['Toyota', 'Honda', 'Ford', 'Chevrolet', 'Nissan', 'Jeep', 'Hyundai', 'Subaru', 'BMW', 'Mercedes']
models = ['Camry', 'Civic', 'F-150', 'Malibu', 'Altima', 'Wrangler', 'Elantra', 'Outback', 'X5', 'C-Class']
colors = ['Red', 'Blue', 'Green', 'Silver', 'Black', 'White', 'Gray']

# Insert 100 records
for _ in range(100):
    make = random.choice(makes)
    model = random.choice(models)
    year = random.randint(2000, 2023)
    color = random.choice(colors)

    cursor.execute('''
        INSERT INTO Vehicles (make, model, year, color) VALUES (?, ?, ?, ?)
    ''', (make, model, year, color))

# Commit changes and close connection
conn.commit()
conn.close()
