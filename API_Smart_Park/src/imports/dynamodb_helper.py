import boto3
import hashlib

# Create a shared DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')

def get_table(table_name: str):
    """Get a DynamoDB table reference"""
    return dynamodb.Table(table_name)

def hash_password(password: str) -> str:
    """Return a SHA-256 hashed version of the password"""
    return hashlib.sha256(password.encode()).hexdigest()
