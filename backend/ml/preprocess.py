"""
Preprocessing & Feature Engineering Pipeline for Secure UPI Fraud Detection.
Handles missing values, categorical encoding, feature scaling, and engineered features.
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler

# Feature columns utilized for model training and inference
NUMERICAL_FEATURES = [
    'amount',
    'average_amount',
    'amount_deviation',
    'transaction_frequency',
    'time_since_last_transaction',
    'time_of_day',
    'account_age_days',
    'failed_transactions',
    'transaction_velocity',
]

BINARY_FEATURES = [
    'location_change',
    'device_new',
    'is_known_receiver',
    'is_unusual_hour',
    'is_high_value_spike',
    'is_rapid_velocity',
]

CATEGORICAL_FEATURES = [
    'transaction_type'
]

ALL_MODEL_INPUT_COLUMNS = [
    'amount',
    'average_amount',
    'transaction_frequency',
    'time_since_last_transaction',
    'time_of_day',
    'location_change',
    'device_new',
    'account_age_days',
    'failed_transactions',
    'transaction_velocity',
    'is_known_receiver',
    'transaction_type'
]

class UPIFeaturePipeline(BaseEstimator, TransformerMixin):
    """
    Feature engineering and transformation pipeline for UPI transactions.
    """
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_names_out_ = []
        self.txn_types_ = ['P2P', 'P2M', 'BILL_PAYMENT', 'ONLINE_SHOPPING', 'INVESTMENT', 'RECHARGE']
        
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df_out = df.copy()
        
        # Missing value handling
        if 'average_amount' not in df_out.columns or df_out['average_amount'].isnull().all():
            df_out['average_amount'] = df_out['amount']
        df_out['average_amount'] = df_out['average_amount'].fillna(df_out['amount']).replace(0, 1.0)
        
        # Amount deviation
        df_out['amount_deviation'] = df_out['amount'] / df_out['average_amount']
        
        # Unusual hour feature (1 AM - 5 AM)
        if 'time_of_day' in df_out.columns:
            df_out['is_unusual_hour'] = df_out['time_of_day'].apply(lambda h: 1 if 1 <= h <= 5 else 0)
        else:
            df_out['is_unusual_hour'] = 0
            
        # High value spike indicator (e.g. > 4x user average or > 25,000 INR)
        df_out['is_high_value_spike'] = ((df_out['amount_deviation'] >= 4.0) | (df_out['amount'] >= 30000)).astype(int)
        
        # Rapid velocity indicator
        if 'transaction_velocity' in df_out.columns and 'time_since_last_transaction' in df_out.columns:
            df_out['is_rapid_velocity'] = ((df_out['transaction_velocity'] >= 5.0) & (df_out['time_since_last_transaction'] <= 10.0)).astype(int)
        else:
            df_out['is_rapid_velocity'] = 0
            
        # Ensure default values for missing binaries/numericals
        for col in ['location_change', 'device_new', 'is_known_receiver']:
            if col not in df_out.columns:
                df_out[col] = 0
            else:
                df_out[col] = df_out[col].fillna(0).astype(int)
                
        for col in ['failed_transactions', 'transaction_frequency', 'time_since_last_transaction', 'account_age_days']:
            if col not in df_out.columns:
                df_out[col] = 0.0
            else:
                df_out[col] = df_out[col].fillna(0.0).astype(float)
                
        return df_out

    def fit(self, X, y=None):
        X_df = pd.DataFrame(X).copy()
        X_eng = self._engineer_features(X_df)
        
        # Fit scaler on numerical columns
        self.scaler.fit(X_eng[NUMERICAL_FEATURES])
        
        # Determine feature names out
        encoded_txn_cols = [f"txn_type_{t}" for t in self.txn_types_]
        self.feature_names_out_ = NUMERICAL_FEATURES + BINARY_FEATURES + encoded_txn_cols
        return self

    def transform(self, X):
        X_df = pd.DataFrame(X).copy()
        X_eng = self._engineer_features(X_df)
        
        # Scale numerical features
        num_scaled = self.scaler.transform(X_eng[NUMERICAL_FEATURES])
        num_df = pd.DataFrame(num_scaled, columns=NUMERICAL_FEATURES, index=X_df.index)
        
        # Binary features
        bin_df = X_eng[BINARY_FEATURES].astype(float)
        
        # One-hot encode transaction_type
        type_series = X_eng['transaction_type'] if 'transaction_type' in X_eng.columns else pd.Series(['P2P'] * len(X_df), index=X_df.index)
        encoded_types = []
        for t in self.txn_types_:
            encoded_types.append((type_series == t).astype(float))
        type_df = pd.concat(encoded_types, axis=1)
        type_df.columns = [f"txn_type_{t}" for t in self.txn_types_]
        
        transformed = pd.concat([num_df, bin_df, type_df], axis=1)
        return transformed[self.feature_names_out_].values

    def get_feature_names(self):
        return self.feature_names_out_
