from rest_framework import serializers
from .models import (
    APICollection, APIEnvironment, APIRequest, APITest, APITestResult,
    APITestSuite, APITestSuiteResult, APIAutomation
)

class APICollectionSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.email')
    request_count = serializers.SerializerMethodField()
    
    class Meta:
        model = APICollection
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')
    
    def get_request_count(self, obj):
        return obj.requests.count()

class APIEnvironmentSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.email')
    
    class Meta:
        model = APIEnvironment
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

class APIRequestSerializer(serializers.ModelSerializer):
    collection_name = serializers.ReadOnlyField(source='collection.name')
    test_count = serializers.SerializerMethodField()
    
    class Meta:
        model = APIRequest
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_test_count(self, obj):
        return obj.tests.count()

class APITestSerializer(serializers.ModelSerializer):
    request_name = serializers.ReadOnlyField(source='request.name')
    request_method = serializers.ReadOnlyField(source='request.method')
    
    class Meta:
        model = APITest
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class APITestResultSerializer(serializers.ModelSerializer):
    test_name = serializers.ReadOnlyField(source='test.name')
    request_name = serializers.ReadOnlyField(source='request.name')
    environment_name = serializers.ReadOnlyField(source='environment.name')
    
    class Meta:
        model = APITestResult
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'executed_at')

class APITestSuiteSerializer(serializers.ModelSerializer):
    collection_name = serializers.ReadOnlyField(source='collection.name')
    environment_name = serializers.ReadOnlyField(source='environment.name')
    test_count = serializers.SerializerMethodField()
    
    class Meta:
        model = APITestSuite
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_test_count(self, obj):
        return obj.tests.count()

class APITestSuiteResultSerializer(serializers.ModelSerializer):
    suite_name = serializers.ReadOnlyField(source='suite.name')
    environment_name = serializers.ReadOnlyField(source='environment.name')
    
    class Meta:
        model = APITestSuiteResult
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'started_at')

class APIAutomationSerializer(serializers.ModelSerializer):
    test_suite_name = serializers.ReadOnlyField(source='test_suite.name')
    
    class Meta:
        model = APIAutomation
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'last_run', 'next_run')

# Nested serializers for detailed views
class APITestDetailSerializer(APITestSerializer):
    request = APIRequestSerializer(read_only=True)
    results = APITestResultSerializer(many=True, read_only=True)

class APIRequestDetailSerializer(APIRequestSerializer):
    tests = APITestSerializer(many=True, read_only=True)
    test_results = APITestResultSerializer(many=True, read_only=True)

class APICollectionDetailSerializer(APICollectionSerializer):
    requests = APIRequestSerializer(many=True, read_only=True)
    test_suites = APITestSuiteSerializer(many=True, read_only=True)
    environments = APIEnvironmentSerializer(many=True, read_only=True)

class APITestSuiteDetailSerializer(APITestSuiteSerializer):
    tests = APITestDetailSerializer(many=True, read_only=True)
    suite_results = APITestSuiteResultSerializer(many=True, read_only=True)
