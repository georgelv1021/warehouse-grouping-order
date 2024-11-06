import pandas as pd

# Constants for warehouse dimensions
AISLE_LENGTH = 112  # feet
AISLE_WIDTH = 24    # feet
MAX_ORDERS_PER_WAVE = 5

# Step 1: Load Data
file_path = '/Users/georgelyu/Desktop/DHL Interview/Order_Grouping_Data.xlsx'
data_df = pd.read_excel(file_path, sheet_name='Data')

# Step 2: Calculate Aisle Demand
aisle_demand = data_df['Asiles Located'].value_counts().reset_index()
aisle_demand.columns = ['Aisle', 'SKU_Count']
aisle_demand = aisle_demand.sort_values(by='SKU_Count', ascending=False)

print(aisle_demand)

def create_order_waves_with_proximity(data, aisle_priority, max_orders_per_wave=MAX_ORDERS_PER_WAVE):
    waves = []
    remaining_orders = data.copy()
    
    while not remaining_orders.empty:
        wave_orders = []
        
        # Process aisles based on both demand and proximity
        for aisle in aisle_priority['Aisle']:
            if len(wave_orders) >= max_orders_per_wave:
                break
            
            # Get orders for the current aisle
            aisle_orders = remaining_orders[remaining_orders['Asiles Located'] == aisle]
            
            for order in aisle_orders['Order Number'].unique():
                if len(wave_orders) < max_orders_per_wave:
                    # Add orders located in the current high-demand aisle
                    order_rows = remaining_orders[remaining_orders['Order Number'] == order]
                    wave_orders.append(order_rows)
                    remaining_orders = remaining_orders[remaining_orders['Order Number'] != order]
                else:
                    break
            
            # Only proceed if wave_orders is not empty
            if wave_orders:
                current_wave_aisles = pd.concat(wave_orders)['Asiles Located'].unique()
                min_aisle, max_aisle = min(current_wave_aisles), max(current_wave_aisles)
                
                # Check for nearby aisles and add them if they have high demand
                nearby_aisles = aisle_priority[(aisle_priority['Aisle'] >= min_aisle - 1) & 
                                               (aisle_priority['Aisle'] <= max_aisle + 1)]
                for nearby_aisle in nearby_aisles['Aisle']:
                    if len(wave_orders) >= max_orders_per_wave:
                        break
                    nearby_orders = remaining_orders[remaining_orders['Asiles Located'] == nearby_aisle]
                    for order in nearby_orders['Order Number'].unique():
                        if len(wave_orders) < max_orders_per_wave:
                            order_rows = remaining_orders[remaining_orders['Order Number'] == order]
                            wave_orders.append(order_rows)
                            remaining_orders = remaining_orders[remaining_orders['Order Number'] != order]
                        else:
                            break
        
        # Add the current wave to the list of waves if it has orders
        if wave_orders:
            waves.append(pd.concat(wave_orders))
    
    return waves


# Generate waves using the heuristic
waves = create_order_waves_with_proximity(data_df, aisle_demand)

# Step 4: Calculate Zigzag Distance
def calculate_zigzag_distance(aisles_required):
    """
    Calculate the zigzag distance for a set of aisles in a wave.
    Starts at the smallest aisle, traverses each aisle in order, and ends at the largest aisle.
    """
    if len(aisles_required) == 1:
        # Only one aisle: travel down only
        return AISLE_LENGTH
    else:
        # For multiple aisles, start at the smallest and end at the largest
        min_aisle = min(aisles_required)
        max_aisle = max(aisles_required)
        num_aisles_to_traverse = max_aisle - min_aisle + 1
        
        # Correct calculation based on actual traversal from min_aisle to max_aisle
        total_distance = (AISLE_LENGTH * num_aisles_to_traverse) + (AISLE_WIDTH * (num_aisles_to_traverse - 1))
        return total_distance

# Step 5: Calculate Total Distance for Heuristic Model
heuristic_distances = [calculate_zigzag_distance(wave['Asiles Located'].unique()) for wave in waves]
total_heuristic_distance = sum(heuristic_distances)

# Step 6: Calculate Total Distance for FCFS Model
def calculate_fcfs_distance(data, orders_per_wave=MAX_ORDERS_PER_WAVE):
    total_distance = 0
    unique_orders = data['Order Number'].unique()
    
    for i in range(0, len(unique_orders), orders_per_wave):
        # Get the order numbers for the current wave in FCFS order
        wave_orders = unique_orders[i:i + orders_per_wave]
        # Find the aisles required for these orders
        aisles_required = data[data['Order Number'].isin(wave_orders)]['Asiles Located'].unique()
        
        # Calculate zigzag distance for this wave using the smallest and largest aisle
        wave_distance = calculate_zigzag_distance(aisles_required)
        total_distance += wave_distance
    
    return total_distance

# Calculate total FCFS distance
fcfs_distance = calculate_fcfs_distance(data_df)

# Step 7: Output Wave Details and Distances
print("Heuristic Model Waves:")
for i, wave in enumerate(waves, start=1):
    wave_aisles = wave['Asiles Located'].unique()
    wave_distance = calculate_zigzag_distance(wave_aisles)
    print(f"\nWave {i}:")
    print(wave[['Order Number', 'SKU Number', 'Qty', 'Asiles Located']])
    print(f"Wave Distance: {wave_distance} feet")

# Output the total travel distances for comparison
print("\nTotal Travel Distance (Heuristic):", total_heuristic_distance)
print("Total Travel Distance (FCFS):", fcfs_distance)
