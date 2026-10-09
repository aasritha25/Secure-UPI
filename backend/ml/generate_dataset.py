"""
Generate synthetic UPI transaction dataset for Secure UPI fraud detection.
Academic FinTech demonstration dataset containing realistic legitimate,
suspicious, and fraudulent UPI transaction patterns with realistic feature overlap and noise.
"""

import os
import numpy as np
import pandas as pd

def generate_upi_dataset(n_samples=10000, random_state=42):
    rng = np.random.default_rng(random_state)
    
    cities = ['Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow', 'Chandigarh', 'Kochi']
    txn_types = ['P2P', 'P2M', 'BILL_PAYMENT', 'ONLINE_SHOPPING', 'INVESTMENT', 'RECHARGE']
    devices = ['DEV_ANDROID_14', 'DEV_IOS_18', 'DEV_ANDROID_13', 'DEV_WEB_CHROME', 'DEV_ANDROID_12', 'DEV_UNKNOWN']
    
    users = []
    for uid in range(1, 151):
        user_id = f"USR{str(uid).zfill(4)}"
        home_city = rng.choice(cities[:6])
        primary_device = rng.choice(devices[:3])
        typical_avg_amount = float(rng.integers(400, 5000))
        typical_freq = float(rng.integers(5, 35))
        account_age = int(rng.integers(30, 1800))
        users.append({
            'user_id': user_id,
            'home_city': home_city,
            'primary_device': primary_device,
            'avg_amount': typical_avg_amount,
            'freq': typical_freq,
            'account_age': account_age
        })
    
    rows = []
    for i in range(n_samples):
        user = rng.choice(users)
        account_age_days = max(15, user['account_age'] + int(rng.integers(-20, 60)))
        user_avg_amount = user['avg_amount']
        
        # Base probability of fraud
        is_fraud = 0
        fraud_scenario = None
        
        if rng.random() < 0.095:  # ~9.5% fraud rate
            is_fraud = 1
            fraud_scenario = rng.choice(['high_value', 'velocity_burst', 'account_takeover', 'night_drain', 'phishing_transfer'])
            
        if is_fraud == 0:
            # LEGITIMATE TRANSACTION PATTERNS
            # Regular spending with some high-value spikes (e.g. rent, travel, festive shopping)
            if rng.random() < 0.06:
                # Legitimate large purchase (e.g. electronics or flight ticket)
                amount = float(user_avg_amount * rng.uniform(3.0, 7.5))
            else:
                amount = float(np.clip(rng.lognormal(mean=np.log(user_avg_amount), sigma=0.45), 20.0, user_avg_amount * 3.5))
                
            time_of_day = int(rng.choice(
                list(range(6, 24)), 
                p=[0.02, 0.04, 0.06, 0.07, 0.08, 0.08, 0.09, 0.09, 0.08, 0.08, 0.08, 0.07, 0.05, 0.04, 0.03, 0.02, 0.01, 0.01]
            ))
            # Legitimate travel occasionally (12% of time in another city)
            location = user['home_city'] if rng.random() < 0.88 else rng.choice(cities)
            # Legitimate device upgrade or web login (10% of time)
            device_id = user['primary_device'] if rng.random() < 0.90 else rng.choice(devices[:4])
            time_since_last_txn = float(np.clip(rng.exponential(scale=180.0), 5.0, 2880.0))
            failed_txn_count = int(rng.choice([0, 0, 0, 0, 0, 1, 1, 2], p=[0.70, 0.12, 0.08, 0.04, 0.02, 0.02, 0.01, 0.01]))
            txn_frequency = float(np.clip(rng.normal(user['freq'], 3.5), 1.0, 45.0))
            txn_velocity = float(np.clip(rng.normal(1.2, 0.6), 0.1, 4.5))
            is_known_receiver = 1 if rng.random() < 0.74 else 0
            txn_type = rng.choice(txn_types, p=[0.42, 0.32, 0.11, 0.09, 0.03, 0.03])
            
        else:
            # FRAUDULENT PATTERNS WITH REALISTIC OVERLAP
            if fraud_scenario == 'high_value':
                amount = float(rng.uniform(user_avg_amount * 4.5, max(35000.0, user_avg_amount * 12.0)))
                time_of_day = int(rng.integers(0, 24))
                location = rng.choice([c for c in cities if c != user['home_city']]) if rng.random() < 0.75 else user['home_city']
                device_id = rng.choice(['DEV_UNKNOWN', 'DEV_WEB_CHROME', 'DEV_ANDROID_12']) if rng.random() < 0.80 else user['primary_device']
                time_since_last_txn = float(rng.uniform(2.0, 45.0))
                failed_txn_count = int(rng.choice([1, 2, 3, 4, 5]))
                txn_frequency = float(rng.integers(12, 50))
                txn_velocity = float(rng.uniform(3.5, 9.5))
                is_known_receiver = 1 if rng.random() < 0.12 else 0
                txn_type = rng.choice(['P2P', 'INVESTMENT', 'P2M'])
                
            elif fraud_scenario == 'velocity_burst':
                amount = float(rng.uniform(user_avg_amount * 1.5, user_avg_amount * 5.0))
                time_of_day = int(rng.integers(0, 24))
                location = rng.choice(cities)
                device_id = rng.choice(devices)
                time_since_last_txn = float(rng.uniform(0.2, 4.0)) # Rapid consecutive
                failed_txn_count = int(rng.integers(1, 6))
                txn_frequency = float(rng.integers(22, 65))
                txn_velocity = float(rng.uniform(5.5, 14.0))
                is_known_receiver = 1 if rng.random() < 0.18 else 0
                txn_type = rng.choice(['P2P', 'ONLINE_SHOPPING'])
                
            elif fraud_scenario == 'night_drain':
                amount = float(rng.uniform(user_avg_amount * 2.8, user_avg_amount * 7.0))
                time_of_day = int(rng.choice([1, 2, 3, 4, 5])) # Odd early hours
                location = rng.choice([c for c in cities if c != user['home_city']]) if rng.random() < 0.70 else user['home_city']
                device_id = 'DEV_UNKNOWN' if rng.random() < 0.65 else rng.choice(devices)
                time_since_last_txn = float(rng.integers(20, 300))
                failed_txn_count = int(rng.integers(0, 4))
                txn_frequency = float(rng.integers(8, 35))
                txn_velocity = float(rng.uniform(2.0, 7.5))
                is_known_receiver = 0
                txn_type = 'P2P'
                
            elif fraud_scenario == 'account_takeover':
                amount = float(rng.uniform(user_avg_amount * 3.5, user_avg_amount * 9.0))
                time_of_day = int(rng.integers(0, 24))
                location = rng.choice([c for c in cities if c != user['home_city']])
                device_id = 'DEV_UNKNOWN'
                time_since_last_txn = float(rng.uniform(5.0, 60.0))
                failed_txn_count = int(rng.integers(3, 8))
                txn_frequency = float(rng.integers(15, 55))
                txn_velocity = float(rng.uniform(4.0, 11.0))
                is_known_receiver = 0
                txn_type = rng.choice(['P2P', 'INVESTMENT'])
                
            else: # phishing_transfer
                amount = float(rng.uniform(user_avg_amount * 1.8, user_avg_amount * 4.5))
                time_of_day = int(rng.integers(8, 22))
                location = user['home_city'] if rng.random() < 0.60 else rng.choice(cities)
                device_id = user['primary_device'] if rng.random() < 0.50 else 'DEV_UNKNOWN'
                time_since_last_txn = float(rng.uniform(1.0, 25.0))
                failed_txn_count = int(rng.integers(0, 3))
                txn_frequency = float(rng.integers(10, 40))
                txn_velocity = float(rng.uniform(2.5, 6.5))
                is_known_receiver = 0
                txn_type = 'P2P'
                
        device_new = 1 if device_id != user['primary_device'] else 0
        location_change = 1 if location != user['home_city'] else 0
        amount_deviation = round(amount / max(user_avg_amount, 1.0), 3)
        
        rows.append({
            'transaction_id': f"TXN{str(100000 + i)}",
            'user_id': user['user_id'],
            'amount': round(amount, 2),
            'average_amount': round(user_avg_amount, 2),
            'amount_deviation': amount_deviation,
            'transaction_frequency': round(txn_frequency, 1),
            'time_since_last_transaction': round(time_since_last_txn, 1),
            'time_of_day': time_of_day,
            'location': location,
            'location_change': location_change,
            'device_id': device_id,
            'device_new': device_new,
            'account_age_days': account_age_days,
            'failed_transactions': failed_txn_count,
            'transaction_velocity': round(txn_velocity, 2),
            'is_known_receiver': is_known_receiver,
            'transaction_type': txn_type,
            'is_fraud': is_fraud
        })
        
    df = pd.DataFrame(rows)
    return df

if __name__ == '__main__':
    out_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(out_dir, 'dataset.csv')
    df = generate_upi_dataset(n_samples=10000, random_state=42)
    df.to_csv(dataset_path, index=False)
    print(f"Generated {len(df)} transactions dataset -> {dataset_path}")
    print(f"Legitimate: {(df['is_fraud'] == 0).sum()}, Fraudulent: {(df['is_fraud'] == 1).sum()} (Fraud Rate: {df['is_fraud'].mean()*100:.2f}%)")
