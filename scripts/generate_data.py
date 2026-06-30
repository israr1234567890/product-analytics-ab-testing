import os
import uuid
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_data(num_users=5000, output_dir="data"):
    os.makedirs(output_dir, exist_ok=True)
    print(f"Generating data for {num_users} users...")
    
    start_date = datetime(2026, 1, 1)
    end_date = datetime(2026, 3, 31)
    date_range_days = (end_date - start_date).days

    devices = ['iOS', 'Android', 'Web', None]  # Include None for missing values
    device_probs = [0.45, 0.35, 0.15, 0.05]
    
    countries = ['US', 'GB', 'CA', 'DE', 'FR', 'IN', 'unknown']
    country_probs = [0.4, 0.15, 0.1, 0.1, 0.1, 0.1, 0.05]
    
    # 1. Generate User Demographics
    users = []
    for i in range(num_users):
        user_id = str(uuid.uuid4())[:8]
        # Random signup date
        signup_days = random.randint(0, date_range_days)
        signup_date = start_date + timedelta(days=signup_days)
        
        device = np.random.choice(devices, p=device_probs)
        country = np.random.choice(countries, p=country_probs)
        
        # A/B test run from March 1st onwards
        is_in_ab_test = signup_date >= datetime(2026, 3, 1)
        ab_variant = 'treatment' if is_in_ab_test and random.random() > 0.5 else 'control'
        if not is_in_ab_test:
            ab_variant = 'not_applicable'
            
        users.append({
            'user_id': user_id,
            'signup_date': signup_date.strftime('%Y-%m-%d %H:%M:%S'),
            'device': device,
            'country': country if country != 'unknown' else None, # Let some be actual None
            'ab_variant': ab_variant
        })
        
    df_users = pd.DataFrame(users)
    
    # Inject dirty data: Some rows with extreme invalid signup dates
    bad_dates_indices = df_users.sample(frac=0.005).index # 0.5% bad dates
    df_users.loc[bad_dates_indices, 'signup_date'] = np.random.choice(
        ['1970-01-01 00:00:00', '2099-12-31 23:59:59'], 
        size=len(bad_dates_indices)
    )
    
    # 2. Generate Events
    events = []
    for idx, row in df_users.iterrows():
        user_id = row['user_id']
        signup_date_str = row['signup_date']
        
        # Skip generating event sequences for users with corrupt signup dates
        if signup_date_str in ['1970-01-01 00:00:00', '2099-12-31 23:59:59']:
            signup_date = start_date + timedelta(days=random.randint(0, date_range_days))
        else:
            signup_date = datetime.strptime(signup_date_str, '%Y-%m-%d %H:%M:%S')
            
        variant = row['ab_variant']
        
        # Decide how many days this user stays active
        # Real cohort retention drop-off: high probability of churning on day 1, 2, 3
        # Treatment group has a higher retention probability
        if variant == 'treatment':
            retention_probs = [1.0, 0.70, 0.55, 0.45, 0.40, 0.38, 0.36, 0.35] # Improved retention
        else:
            retention_probs = [1.0, 0.50, 0.35, 0.25, 0.20, 0.18, 0.16, 0.15] # Control & pre-test retention
            
        # Determine lifetime of user in days (up to 7 days for retention analysis)
        active_days = [0]
        for day in range(1, 8):
            if random.random() < retention_probs[day]:
                active_days.append(day)
                
        # Generate events for active days
        for day in active_days:
            event_date = signup_date + timedelta(days=day, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            
            # Always have a sign_up or page_view on day 0
            if day == 0:
                events.append({
                    'event_id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'timestamp': event_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'event_name': 'sign_up',
                    'event_value': 0.0
                })
                # Add email_verified event for 90% of users
                if random.random() < 0.90:
                    events.append({
                        'event_id': str(uuid.uuid4()),
                        'user_id': user_id,
                        'timestamp': (event_date + timedelta(minutes=random.randint(1, 5))).strftime('%Y-%m-%d %H:%M:%S'),
                        'event_name': 'email_verified',
                        'event_value': 0.0
                    })
            
            # Daily active actions
            num_actions = random.randint(2, 8)
            for _ in range(num_actions):
                action_time = event_date + timedelta(minutes=random.randint(5, 120))
                
                # Event selection based on variant to inject a treatment effect on purchases
                possible_events = ['page_view', 'click', 'tutorial_start']
                event_weights = [0.6, 0.3, 0.1]
                
                selected_event = np.random.choice(possible_events, p=event_weights)
                events.append({
                    'event_id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'timestamp': action_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'event_name': selected_event,
                    'event_value': 0.0
                })
                
                # Tutorial Completion & Purchase conversion
                # Let's say treatment variant onboarding flow makes them complete tutorial more and buy more!
                if selected_event == 'tutorial_start':
                    comp_prob = 0.85 if variant == 'treatment' else 0.50
                    if random.random() < comp_prob:
                        events.append({
                            'event_id': str(uuid.uuid4()),
                            'user_id': user_id,
                            'timestamp': action_time + timedelta(minutes=random.randint(2, 10)),
                            'event_name': 'tutorial_complete',
                            'event_value': 0.0
                        })
                        
                        # Purchase conversion after tutorial completion
                        purchase_prob = 0.35 if variant == 'treatment' else 0.15
                        if random.random() < purchase_prob:
                            purchase_val = np.random.normal(25.0, 5.0) # Average purchase of $25
                            # Inject some negative values as outliers/dirty data
                            if random.random() < 0.01:
                                purchase_val = -purchase_val
                                
                            events.append({
                                'event_id': str(uuid.uuid4()),
                                'user_id': user_id,
                                'timestamp': action_time + timedelta(minutes=random.randint(11, 30)),
                                'event_name': 'purchase',
                                'event_value': round(purchase_val, 2)
                            })

    df_events = pd.DataFrame(events)
    
    # Inject duplicates (double logging issue) - 2% of events
    duplicates = df_events.sample(frac=0.02)
    df_events = pd.concat([df_events, duplicates], ignore_index=True)
    
    # Shuffle events
    df_events = df_events.sample(frac=1).reset_index(drop=True)
    
    # Save datasets
    df_users.to_csv(os.path.join(output_dir, "raw_user_demographics.csv"), index=False)
    df_events.to_csv(os.path.join(output_dir, "raw_user_events.csv"), index=False)
    
    print("Data generation complete!")
    print(f"Demographics shape: {df_users.shape}")
    print(f"Events shape: {df_events.shape}")

if __name__ == '__main__':
    generate_data(num_users=6000)
