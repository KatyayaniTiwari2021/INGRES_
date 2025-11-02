import sqlite3
import random
from datetime import datetime, timedelta
import json

def create_database():
    """Create and populate a mock INGRES database with sample groundwater data"""
    
    conn = sqlite3.connect('data/ingres_mock.db')
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    cursor.execute("DROP TABLE IF EXISTS groundwater_assessment")
    cursor.execute("DROP TABLE IF EXISTS blocks")
    cursor.execute("DROP TABLE IF EXISTS districts")
    cursor.execute("DROP TABLE IF EXISTS states")
    cursor.execute("DROP TABLE IF EXISTS historical_data")
    
    # Create states table
    cursor.execute("""
        CREATE TABLE states (
            state_id INTEGER PRIMARY KEY,
            state_name TEXT NOT NULL
        )
    """)
    
    # Create districts table
    cursor.execute("""
        CREATE TABLE districts (
            district_id INTEGER PRIMARY KEY,
            district_name TEXT NOT NULL,
            state_id INTEGER,
            FOREIGN KEY (state_id) REFERENCES states(state_id)
        )
    """)
    
    # Create blocks table
    cursor.execute("""
        CREATE TABLE blocks (
            block_id INTEGER PRIMARY KEY,
            block_name TEXT NOT NULL,
            district_id INTEGER,
            FOREIGN KEY (district_id) REFERENCES districts(district_id)
        )
    """)
    
    # Create groundwater assessment table
    cursor.execute("""
        CREATE TABLE groundwater_assessment (
            assessment_id INTEGER PRIMARY KEY,
            block_id INTEGER,
            assessment_year INTEGER,
            annual_recharge_mcm REAL,
            extractable_resources_mcm REAL,
            total_extraction_mcm REAL,
            stage_of_extraction REAL,
            category TEXT,
            water_level_pre_monsoon REAL,
            water_level_post_monsoon REAL,
            FOREIGN KEY (block_id) REFERENCES blocks(block_id)
        )
    """)
    
    # Create historical data table for trends
    cursor.execute("""
        CREATE TABLE historical_data (
            id INTEGER PRIMARY KEY,
            block_id INTEGER,
            year INTEGER,
            month INTEGER,
            water_level REAL,
            rainfall_mm REAL,
            FOREIGN KEY (block_id) REFERENCES blocks(block_id)
        )
    """)
    
    # Sample data for states
    states = [
        (1, 'Delhi'),
        (2, 'Haryana'),
        (3, 'Punjab'),
        (4, 'Rajasthan'),
        (5, 'Uttar Pradesh'),
        (6, 'Maharashtra'),
        (7, 'Karnataka'),
        (8, 'Tamil Nadu'),
        (9, 'Gujarat'),
        (10, 'West Bengal')
    ]
    
    cursor.executemany("INSERT INTO states VALUES (?, ?)", states)
    
    # Sample districts data
    districts = [
        (1, 'Central Delhi', 1),
        (2, 'North Delhi', 1),
        (3, 'South Delhi', 1),
        (4, 'Gurugram', 2),
        (5, 'Faridabad', 2),
        (6, 'Rohtak', 2),
        (7, 'Amritsar', 3),
        (8, 'Ludhiana', 3),
        (9, 'Jaipur', 4),
        (10, 'Udaipur', 4),
        (11, 'Agra', 5),
        (12, 'Lucknow', 5),
        (13, 'Pune', 6),
        (14, 'Mumbai', 6),
        (15, 'Bangalore Urban', 7),
        (16, 'Mysore', 7),
        (17, 'Chennai', 8),
        (18, 'Coimbatore', 8),
        (19, 'Ahmedabad', 9),
        (20, 'Kolkata', 10)
    ]
    
    cursor.executemany("INSERT INTO districts VALUES (?, ?, ?)", districts)
    
    # Generate blocks (3-5 blocks per district)
    block_id = 1
    blocks = []
    for district in districts:
        district_id = district[0]
        district_name = district[1]
        num_blocks = random.randint(3, 5)
        for i in range(num_blocks):
            block_name = f"{district_name} Block-{i+1}"
            blocks.append((block_id, block_name, district_id))
            block_id += 1
    
    cursor.executemany("INSERT INTO blocks VALUES (?, ?, ?)", blocks)
    
    # Generate groundwater assessment data
    categories = ['Safe', 'Semi-Critical', 'Critical', 'Over-Exploited']
    category_weights = [0.4, 0.3, 0.2, 0.1]  # More Safe areas, fewer Over-Exploited
    
    assessments = []
    assessment_id = 1
    current_year = 2024
    
    for block in blocks:
        block_id = block[0]
        for year in range(2020, current_year + 1):
            # Generate realistic data based on category
            category = random.choices(categories, weights=category_weights)[0]
            
            if category == 'Safe':
                stage_of_extraction = random.uniform(20, 70)
                annual_recharge = random.uniform(100, 200)
                water_level_pre = random.uniform(5, 15)
            elif category == 'Semi-Critical':
                stage_of_extraction = random.uniform(70, 90)
                annual_recharge = random.uniform(80, 120)
                water_level_pre = random.uniform(15, 25)
            elif category == 'Critical':
                stage_of_extraction = random.uniform(90, 100)
                annual_recharge = random.uniform(60, 90)
                water_level_pre = random.uniform(25, 35)
            else:  # Over-Exploited
                stage_of_extraction = random.uniform(100, 150)
                annual_recharge = random.uniform(40, 70)
                water_level_pre = random.uniform(35, 50)
            
            extractable_resources = annual_recharge * 0.85
            total_extraction = (stage_of_extraction / 100) * extractable_resources
            water_level_post = water_level_pre - random.uniform(2, 5)
            
            assessments.append((
                assessment_id, block_id, year, annual_recharge,
                extractable_resources, total_extraction, stage_of_extraction,
                category, water_level_pre, water_level_post
            ))
            assessment_id += 1
    
    cursor.executemany("""
        INSERT INTO groundwater_assessment VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, assessments)
    
    # Generate historical monthly data for trend analysis
    historical = []
    hist_id = 1
    
    for block in blocks[:20]:  # Sample data for first 20 blocks
        block_id = block[0]
        for year in range(2022, 2025):
            for month in range(1, 13):
                # Simulate seasonal variations
                if month in [6, 7, 8, 9]:  # Monsoon months
                    water_level = random.uniform(5, 15)
                    rainfall = random.uniform(100, 300)
                elif month in [3, 4, 5]:  # Summer months
                    water_level = random.uniform(20, 35)
                    rainfall = random.uniform(0, 50)
                else:  # Winter/Spring
                    water_level = random.uniform(10, 25)
                    rainfall = random.uniform(20, 80)
                
                historical.append((hist_id, block_id, year, month, water_level, rainfall))
                hist_id += 1
    
    cursor.executemany("""
        INSERT INTO historical_data VALUES (?, ?, ?, ?, ?, ?)
    """, historical)
    
    conn.commit()
    conn.close()
    print("Mock database created successfully with sample data!")
    print(f"Created {len(states)} states, {len(districts)} districts, {len(blocks)} blocks")
    print(f"Generated {len(assessments)} assessment records and {len(historical)} historical data points")

if __name__ == "__main__":
    create_database()
