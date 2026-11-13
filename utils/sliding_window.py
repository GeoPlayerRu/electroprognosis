# Единый способ сделать скользящее окно

#import pandas as pd
#from datetime import timedelta

start_date = pd.Timestamp('2026-01-01')
end_date = pd.Timestamp('2026-01-31') 


initial_train_end = pd.Timestamp('2025-12-31')

folds = []
current_test_date = start_date

while current_test_date <= end_date:
    
    train_df = df[df['date'] < current_test_date].copy()
    
    
    test_df = df[df['date'] == current_test_date].copy()
    
    if len(test_df) > 0: 
        folds.append({
            'train': train_df,
            'test': test_df,
            'forecast_date': current_test_date
        })
    
    
    current_test_date += timedelta(days=1)


