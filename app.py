# --- PERFORMANCE ANALYTICS MATH ENGINE (REPAIRED INTERVAL COST LOGIC) ---
    avg_mileage, cost_per_km = 0.0, 0.0
    if len(user_df) >= 2:
        user_df = user_df.sort_values("odometer").reset_index(drop=True)
        user_df['distance_driven'] = user_df['odometer'].diff()
        
        valid_tank_distances = []
        valid_tank_liters = []
        valid_tank_costs = []  # Tracks interval-aligned financial costs
        
        for i in range(1, len(user_df)):
            if user_df.iloc[i]["Full Tank?"] == "Yes" and user_df.iloc[i-1]["Full Tank?"] == "Yes":
                valid_tank_distances.append(user_df.iloc[i]["distance_driven"])
                valid_tank_liters.append(user_df.iloc[i]["liters"])
                valid_tank_costs.append(user_df.iloc[i]["cost"])
        
        if sum(valid_tank_distances) > 0 and sum(valid_tank_liters) > 0:
            avg_mileage = sum(valid_tank_distances) / sum(valid_tank_liters)
            cost_per_km = sum(valid_tank_costs) / sum(valid_tank_distances)
        else:
            total_km = user_df['distance_driven'].sum()
            avg_mileage = total_km / user_df['liters'].iloc[1:].sum() if user_df['liters'].iloc[1:].sum() > 0 else 0.0
            cost_per_km = user_df['cost'].iloc[1:].sum() / total_km if total_km > 0 else 0.0
