from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import io

from .models import Transaction, Insight, Recommendation
from .serializers import (
    TransactionSerializer, InsightSerializer, 
    RecommendationSerializer, UserSerializer
)

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Username and password required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email or '',
                password=password
            )
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                },
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def upload_csv(self, request):
        csv_file = request.FILES.get('file')
        
        if not csv_file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        print("=" * 50)
        print(f"Upload by user: {request.user.username} (ID: {request.user.id})")
        
        try:
            content = csv_file.read().decode('utf-8')
            io_string = io.StringIO(content)
            reader = csv.DictReader(io_string)
            
            headers = reader.fieldnames
            print(f"Headers: {headers}")
            
            transactions = []
            for row in reader:
                try:
                    amount = float(row.get('amount', 0))
                    merchant = row.get('merchant', '').strip()
                    timestamp_str = row.get('timestamp', '')
                    
                    if amount and merchant and timestamp_str:
                        # Parse date
                        try:
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d')
                        except:
                            try:
                                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            except:
                                timestamp = timezone.now()
                        
                        transactions.append(Transaction(
                            user=request.user,
                            amount=amount,
                            merchant=merchant,
                            category=row.get('category', 'other'),
                            timestamp=timezone.make_aware(timestamp)
                        ))
                except Exception as e:
                    print(f"Error processing row: {e}")
            
            if transactions:
                Transaction.objects.bulk_create(transactions)
                print(f"Saved {len(transactions)} transactions")
                
                # Generate sample insights
                Insight.objects.filter(user=request.user).delete()
                Recommendation.objects.filter(user=request.user).delete()
                
                # Create some sample insights
                Insight.objects.create(
                    user=request.user,
                    insight_type='trend',
                    title='Welcome to AI Finance Coach!',
                    description=f'You have {len(transactions)} transactions. Keep uploading to get personalized insights!',
                    severity=1
                )
                
                # Create a sample recommendation
                Recommendation.objects.create(
                    user=request.user,
                    title='Upload More Transactions',
                    description='Upload more transactions to receive AI-powered spending insights and recommendations.',
                    potential_savings=0
                )
                
                return Response({
                    'message': f'Successfully uploaded {len(transactions)} transactions',
                    'insights_generated': 1,
                    'recommendations_generated': 1
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'No valid transactions found'}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"Upload error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        transactions = self.get_queryset()
        
        total_spending = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        
        category_breakdown = transactions.values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        # Add human-readable category names
        category_names = {
            'food': 'Food & Dining',
            'transport': 'Transportation',
            'shopping': 'Shopping',
            'entertainment': 'Entertainment',
            'bills': 'Bills & Utilities',
            'health': 'Healthcare',
            'education': 'Education',
            'other': 'Other'
        }
        
        for item in category_breakdown:
            item['category_name'] = category_names.get(item['category'], item['category'])
        
        return Response({
            'total_spending': total_spending,
            'transaction_count': transactions.count(),
            'category_breakdown': category_breakdown,
        })

class InsightViewSet(viewsets.ModelViewSet):
    serializer_class = InsightSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Insight.objects.filter(user=self.request.user)

class RecommendationViewSet(viewsets.ModelViewSet):
    serializer_class = RecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Recommendation.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def action(self, request, pk=None):
        recommendation = self.get_object()
        recommendation.is_actioned = True
        recommendation.save()
        return Response({'status': 'actioned'})
