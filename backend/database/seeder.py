"""
Database Seeder for Secure UPI.
Seeds demo admin and customer accounts, transaction baselines, alerts, and devices.
"""

import json
from datetime import datetime, timedelta
from backend.extensions import db
from backend.models import User, Account, Transaction, FraudPrediction, Alert, UserDevice, LoginHistory


def seed_database():
    # If demo user already exists, skip seeding
    if User.query.filter_by(email='demo@secureupi.com').first():
        return

    print("Seeding demo database with initial users, accounts, transactions, and alerts...")

    # 1. Admin User
    admin = User(
        name='Bank Fraud Admin',
        email='admin@secureupi.com',
        phone='9999999999',
        role='admin',
        language='en'
    )
    admin.password = 'admin123'
    db.session.add(admin)
    db.session.flush()

    admin_acc = Account(
        user_id=admin.id,
        account_number_masked='**** 0001',
        balance=5000000.0,
        currency='INR'
    )
    db.session.add(admin_acc)

    # 2. Main Demo Customer
    demo_user = User(
        name='Aarav Sharma',
        email='demo@secureupi.com',
        phone='9876543210',
        role='customer',
        language='en'
    )
    demo_user.password = 'demo123'
    db.session.add(demo_user)
    db.session.flush()

    demo_acc = Account(
        user_id=demo_user.id,
        account_number_masked='**** 4829',
        balance=100000.0,
        currency='INR'
    )
    db.session.add(demo_acc)

    # 3. Additional Customers for admin view
    priya = User(
        name='Priya Patel',
        email='priya@secureupi.com',
        phone='9812345678',
        role='customer',
        language='en'
    )
    priya.password = 'priya123'
    db.session.add(priya)
    db.session.flush()

    priya_acc = Account(
        user_id=priya.id,
        account_number_masked='**** 7312',
        balance=75000.0,
        currency='INR'
    )
    db.session.add(priya_acc)

    rahul = User(
        name='Rahul Verma',
        email='rahul@secureupi.com',
        phone='9898765432',
        role='customer',
        language='en'
    )
    rahul.password = 'rahul123'
    db.session.add(rahul)
    db.session.flush()

    rahul_acc = Account(
        user_id=rahul.id,
        account_number_masked='**** 9045',
        balance=120000.0,
        currency='INR'
    )
    db.session.add(rahul_acc)

    # 4. Devices & Login History
    dev1 = UserDevice(
        user_id=demo_user.id,
        device_id='DEV_ANDROID_14_HYD',
        device_name='OnePlus 12 (Android 14)',
        ip_address='103.24.12.8',
        location='Hyderabad',
        is_trusted=True
    )
    dev2 = UserDevice(
        user_id=demo_user.id,
        device_id='DEV_WEB_CHROME',
        device_name='Chrome on Windows 11',
        ip_address='103.24.12.8',
        location='Hyderabad',
        is_trusted=True
    )
    db.session.add_all([dev1, dev2])

    login1 = LoginHistory(
        user_id=demo_user.id,
        ip_address='103.24.12.8',
        device_id='DEV_ANDROID_14_HYD',
        location='Hyderabad',
        status='SUCCESS'
    )
    db.session.add(login1)

    # 5. Transactions for Demo User
    now = datetime.utcnow()
    sample_txns = [
        {
            'txn_id': 'TXN-9812401',
            'user': demo_user,
            'receiver_id': 'cafecoffee@upi',
            'receiver_name': 'Blue Tokai Coffee Roasters',
            'amount': 450.0,
            'type': 'P2M',
            'location': 'Hyderabad',
            'device_id': 'DEV_ANDROID_14_HYD',
            'status': 'SUCCESS',
            'risk_score': 8.5,
            'risk_level': 'LOW_RISK',
            'fraud_prob': 0.085,
            'prediction': 'Legitimate',
            'time_offset': timedelta(days=5, hours=3),
            'note': 'Morning specialty coffee'
        },
        {
            'txn_id': 'TXN-9812402',
            'user': demo_user,
            'receiver_id': 'naturebasket@upi',
            'receiver_name': 'Nature Basket Supermarket',
            'amount': 2450.0,
            'type': 'P2M',
            'location': 'Hyderabad',
            'device_id': 'DEV_ANDROID_14_HYD',
            'status': 'SUCCESS',
            'risk_score': 12.0,
            'risk_level': 'LOW_RISK',
            'fraud_prob': 0.120,
            'prediction': 'Legitimate',
            'time_offset': timedelta(days=4, hours=6),
            'note': 'Weekly groceries'
        },
        {
            'txn_id': 'TXN-9812403',
            'user': demo_user,
            'receiver_id': 'tsspdcl.bill@upi',
            'receiver_name': 'TSSPDCL Electricity Board',
            'amount': 1850.0,
            'type': 'BILL_PAYMENT',
            'location': 'Hyderabad',
            'device_id': 'DEV_WEB_CHROME',
            'status': 'SUCCESS',
            'risk_score': 6.0,
            'risk_level': 'LOW_RISK',
            'fraud_prob': 0.060,
            'prediction': 'Legitimate',
            'time_offset': timedelta(days=3, hours=10),
            'note': 'Monthly home electricity bill'
        },
        {
            'txn_id': 'TXN-9812404',
            'user': demo_user,
            'receiver_id': 'crocodevice@upi',
            'receiver_name': 'Croma Electronics Retail',
            'amount': 18900.0,
            'type': 'ONLINE_SHOPPING',
            'location': 'Bengaluru',
            'device_id': 'DEV_ANDROID_14_HYD',
            'status': 'FLAGGED_FOR_VERIFICATION',
            'risk_score': 54.0,
            'risk_level': 'MEDIUM_RISK',
            'fraud_prob': 0.540,
            'prediction': 'Suspicious',
            'time_offset': timedelta(days=2, hours=1),
            'note': 'Noise cancelling headphones',
            'reasons': [
                "Transaction amount exceeds typical daily baseline by 4.2x.",
                "Geographic location shift detected (Hyderabad -> Bengaluru)."
            ]
        },
        {
            'txn_id': 'TXN-9812405',
            'user': demo_user,
            'receiver_id': 'unverified.merchant88@ybl',
            'receiver_name': 'Unknown Crypto Exchange Gateway',
            'amount': 85000.0,
            'type': 'INVESTMENT',
            'location': 'Kolkata',
            'device_id': 'DEV_UNKNOWN_EMULATOR',
            'status': 'BLOCKED',
            'risk_score': 93.5,
            'risk_level': 'HIGH_RISK',
            'fraud_prob': 0.935,
            'prediction': 'Fraudulent',
            'time_offset': timedelta(days=1, hours=4),
            'note': 'Attempted midnight unauthorized transfer',
            'reasons': [
                "Critical transaction spike: ₹85,000 vs user average ₹1,800 (47x deviation).",
                "Unrecognized root emulator device ID.",
                "Unusual location: Kolkata (User base: Hyderabad).",
                "Abnormal timestamp (02:45 AM overnight window)."
            ]
        },
        {
            'txn_id': 'TXN-9812406',
            'user': priya,
            'receiver_id': 'quickmart@upi',
            'receiver_name': 'QuickMart Supermarket',
            'amount': 1200.0,
            'type': 'P2M',
            'location': 'Mumbai',
            'device_id': 'DEV_IOS_18',
            'status': 'SUCCESS',
            'risk_score': 10.0,
            'risk_level': 'LOW_RISK',
            'fraud_prob': 0.100,
            'prediction': 'Legitimate',
            'time_offset': timedelta(days=1, hours=8),
            'note': 'Daily essentials'
        },
        {
            'txn_id': 'TXN-9812407',
            'user': rahul,
            'receiver_id': 'unverified.wallet77@axl',
            'receiver_name': 'Unknown Beneficiary',
            'amount': 65000.0,
            'type': 'P2P',
            'location': 'Delhi',
            'device_id': 'DEV_UNKNOWN',
            'status': 'BLOCKED',
            'risk_score': 89.0,
            'risk_level': 'HIGH_RISK',
            'fraud_prob': 0.890,
            'prediction': 'Fraudulent',
            'time_offset': timedelta(hours=14),
            'note': 'Phishing transfer attempt blocked',
            'reasons': [
                "Unusually high amount to unverified recipient.",
                "Multiple failed PIN attempts detected before transfer."
            ]
        }
    ]

    for tdata in sample_txns:
        txn_time = now - tdata['time_offset']
        txn = Transaction(
            transaction_id=tdata['txn_id'],
            user_id=tdata['user'].id,
            receiver_id=tdata['receiver_id'],
            receiver_name=tdata['receiver_name'],
            amount=tdata['amount'],
            timestamp=txn_time,
            location=tdata['location'],
            device_id=tdata['device_id'],
            transaction_type=tdata['type'],
            status=tdata['status'],
            risk_score=tdata['risk_score'],
            risk_level=tdata['risk_level'],
            fraud_probability=tdata['fraud_prob'],
            prediction=tdata['prediction'],
            note=tdata.get('note', ''),
            created_at=txn_time
        )
        db.session.add(txn)
        db.session.flush()

        # Add Prediction record
        reasons_list = tdata.get('reasons', ["Transaction pattern is within expected normal behavior."])
        fp = FraudPrediction(
            transaction_id=txn.transaction_id,
            user_id=tdata['user'].id,
            model_name='Random Forest Classifier',
            fraud_probability=tdata['fraud_prob'],
            risk_score=tdata['risk_score'],
            risk_level=tdata['risk_level'],
            prediction=tdata['prediction'],
            explanation=json.dumps(reasons_list),
            feature_contributions=json.dumps([
                {'name': 'Amount Deviation', 'impact': 0.38 if tdata['risk_score'] > 50 else 0.05, 'contribution_level': 'High' if tdata['risk_score'] > 50 else 'Low'},
                {'name': 'Device Novelty', 'impact': 0.28 if 'UNKNOWN' in tdata['device_id'] else 0.02, 'contribution_level': 'High' if 'UNKNOWN' in tdata['device_id'] else 'Low'},
                {'name': 'Location Anomaly', 'impact': 0.22 if tdata['location'] != 'Hyderabad' else 0.01, 'contribution_level': 'Medium' if tdata['location'] != 'Hyderabad' else 'Low'}
            ]),
            created_at=txn_time
        )
        db.session.add(fp)

        # Add Alerts for Medium & High Risk
        if tdata['risk_level'] == 'HIGH_RISK':
            alert = Alert(
                transaction_id=txn.transaction_id,
                user_id=tdata['user'].id,
                risk_level='HIGH_RISK',
                severity='HIGH',
                title='High-Risk Fraudulent Transaction Blocked',
                message=f"A high-risk transaction of ₹{tdata['amount']:,.2f} to {tdata['receiver_name']} ({tdata['receiver_id']}) was automatically intercepted.",
                reason="; ".join(reasons_list),
                alert_status='ACTIVE',
                created_at=txn_time
            )
            db.session.add(alert)
        elif tdata['risk_level'] == 'MEDIUM_RISK':
            alert = Alert(
                transaction_id=txn.transaction_id,
                user_id=tdata['user'].id,
                risk_level='MEDIUM_RISK',
                severity='MEDIUM',
                title='Suspicious Transaction Flagged for Review',
                message=f"Suspicious activity detected on transaction ₹{tdata['amount']:,.2f} to {tdata['receiver_name']}.",
                reason="; ".join(reasons_list),
                alert_status='ACKNOWLEDGED',
                created_at=txn_time
            )
            db.session.add(alert)

    db.session.commit()
    print("Database seeding completed successfully.")
