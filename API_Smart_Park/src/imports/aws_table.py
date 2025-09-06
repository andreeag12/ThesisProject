import boto3

# Initialize a DynamoDB service resource
dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')

# Create the DynamoDB table
table = dynamodb.create_table(
    TableName='Users',
    # Define the key schema with email as the partition key
    KeySchema=[
        {
            'AttributeName': 'email',
            'KeyType': 'HASH' 
        },
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'email',
            'AttributeType': 'S'  
        },
    ],
    
    ProvisionedThroughput={
        'ReadCapacityUnits': 1,
        'WriteCapacityUnits': 1
    }
)

# Wait for the table to be created
table.meta.client.get_waiter('table_exists').wait(TableName='Users')

print(f"Table {table.table_name} created successfully!")