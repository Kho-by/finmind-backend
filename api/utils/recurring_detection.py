from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

class RecurringDetector:
    def __init__(self, user):
        self.user = user
        self.transactions = user.transactions.all()
    
    def detect_recurring(self):
        """Detect recurring transactions (subscriptions)"""
        recurring = defaultdict(list)
        
        # Group by merchant and amount (allowing small variation)
        for transaction in self.transactions:
            # Check if amount is similar (within $2 variation)
            matched = False
            for key in list(recurring.keys()):
                merchant, amount = key
                if merchant.lower() == transaction.merchant.lower() and abs(amount - float(transaction.amount)) <= 2:
                    recurring[(merchant, amount)].append(transaction)
                    matched = True
                    break
            
            if not matched:
                recurring[(transaction.merchant, float(transaction.amount))].append(transaction)
        
        results = []
        for (merchant, amount), transactions in recurring.items():
            if len(transactions) >= 2:
                # Check if they're approximately monthly
                dates = sorted([t.timestamp for t in transactions])
                
                if len(dates) >= 2:
                    avg_gap = (dates[-1] - dates[0]).days / (len(dates) - 1)
                    
                    # If average gap is between 25-35 days, it's likely monthly
                    if 25 <= avg_gap <= 35:
                        results.append({
                            'merchant': merchant,
                            'amount': amount,
                            'frequency': 'monthly',
                            'transactions': transactions,
                            'count': len(transactions)
                        })
                    # Check for weekly (5-9 days)
                    elif 5 <= avg_gap <= 9:
                        results.append({
                            'merchant': merchant,
                            'amount': amount,
                            'frequency': 'weekly',
                            'transactions': transactions,
                            'count': len(transactions)
                        })
        
        return results
