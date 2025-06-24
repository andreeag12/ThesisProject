import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')

table = dynamodb.create_table(
    TableName='Reservations',
    KeySchema=[
        {
            'AttributeName': 'reservation_id',  # Partition key
            'KeyType': 'HASH'
        },
    ],
    AttributeDefinitions=[
        {
            'AttributeName': 'reservation_id',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'email',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'date',
            'AttributeType': 'S'
        }
    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 1,
        'WriteCapacityUnits': 1
    },
    GlobalSecondaryIndexes=[
        {
            'IndexName': 'EmailIndex',
            'KeySchema': [
                {
                    'AttributeName': 'email',
                    'KeyType': 'HASH'
                }
            ],
            'Projection': {
                'ProjectionType': 'ALL'
            },
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            }
        },
        {
            'IndexName': 'DateIndex',
            'KeySchema': [
                {
                    'AttributeName': 'date',
                    'KeyType': 'HASH'
                }
            ],
            'Projection': {
                'ProjectionType': 'ALL'
            },
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            }
        }
    ]
)

table.meta.client.get_waiter('table_exists').wait(TableName='Reservations')

print(f"Table {table.table_name} created successfully!")
