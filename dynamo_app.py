"""
DynamoDB Best Practices Demo
Demonstrates proper patterns for interacting with DynamoDB
"""

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from decimal import Decimal
import time
import json
from config import AWS_REGION, TABLE_NAME, GSI_NAME


class DynamoDBApp:
    """Handles DynamoDB operations with best practices"""
    
    def __init__(self):
        """Initialize DynamoDB resource and table"""
        self.dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        self.table = self.dynamodb.Table(TABLE_NAME)
    
    def load_seed_data(self, filename='seed_data.json'):
        """
        Load initial data from JSON file
        - Useful for resetting table to known state
        - Batch writes for efficiency
        """
        try:
            with open(filename, 'r') as f:
                items = json.load(f)
            
            # Batch write items
            with self.table.batch_writer() as batch:
                for item in items:
                    batch.put_item(Item=item)
            
            print(f"✓ Loaded {len(items)} items from {filename}")
            return len(items)
        except FileNotFoundError:
            print(f"✗ File {filename} not found")
            raise
        except Exception as e:
            print(f"✗ Error loading seed data: {str(e)}")
            raise
    
    def put_user_profile(self, user_id, email, first_name, last_name, **kwargs):
        """
        BEST PRACTICE: Use put_item for full item creation/replacement
        - Includes ConditionExpression to prevent accidental overwrites
        - Accepts additional attributes via kwargs for schema flexibility
        """
        timestamp = str(int(time.time()))
        
        item = {
            'userId': user_id,
            'timestamp': timestamp,
            'email': email,
            'firstName': first_name,
            'lastName': last_name,
            **kwargs  # Schema flexibility
        }
        
        try:
            # BEST PRACTICE: Use condition to prevent overwriting existing items
            response = self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(userId) AND attribute_not_exists(#ts)',
                ExpressionAttributeNames={
                    '#ts': 'timestamp'
                }
            )
            print(f"✓ Created profile for {user_id}")
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print(f"✗ Item already exists for {user_id} at timestamp {timestamp}")
            else:
                print(f"✗ Error: {e.response['Error']['Message']}")
            raise
    
    def get_user_profile(self, user_id, timestamp):
        """
        BEST PRACTICE: Use get_item for single-item retrieval by primary key
        - Most efficient operation (direct key lookup)
        - Use ProjectionExpression to fetch only needed attributes
        """
        try:
            response = self.table.get_item(
                Key={
                    'userId': user_id,
                    'timestamp': timestamp
                },
                # BEST PRACTICE: Fetch only required attributes
                ProjectionExpression='userId, email, firstName, lastName, loginCount'
            )
            
            if 'Item' in response:
                print(f"✓ Retrieved profile for {user_id}")
                return response['Item']
            else:
                print(f"✗ No item found for {user_id} at {timestamp}")
                return None
        except ClientError as e:
            print(f"✗ Error: {e.response['Error']['Message']}")
            raise
    
    def query_user_activity(self, user_id, start_time=None, end_time=None):
        """
        BEST PRACTICE: Use query (not scan) for efficient data retrieval
        - Queries within a partition using sort key conditions
        - Returns items in sort key order
        """
        try:
            # Build key condition
            key_condition = Key('userId').eq(user_id)
            
            # BEST PRACTICE: Add range conditions on sort key
            if start_time and end_time:
                key_condition &= Key('timestamp').between(start_time, end_time)
            elif start_time:
                key_condition &= Key('timestamp').gte(start_time)
            elif end_time:
                key_condition &= Key('timestamp').lte(end_time)
            
            response = self.table.query(
                KeyConditionExpression=key_condition,
                ScanIndexForward=True  # Sort ascending (False for descending)
            )
            
            items = response['Items']
            print(f"✓ Found {len(items)} activity records for {user_id}")
            return items
        except ClientError as e:
            print(f"✗ Error: {e.response['Error']['Message']}")
            raise
    
    def update_login_count(self, user_id, timestamp, increment=1):
        """
        BEST PRACTICE: Use update_item for partial updates
        - Atomic operations (ADD for counters)
        - Only sends changed data, not entire item
        - Use UpdateExpression, not replacing whole item
        """
        try:
            response = self.table.update_item(
                Key={
                    'userId': user_id,
                    'timestamp': timestamp
                },
                # BEST PRACTICE: Atomic counter increment
                UpdateExpression='ADD loginCount :inc',
                ExpressionAttributeValues={
                    ':inc': increment
                },
                ReturnValues='UPDATED_NEW'  # Return only updated attributes
            )
            
            new_count = response['Attributes'].get('loginCount', 0)
            print(f"✓ Updated login count to {new_count} for {user_id}")
            return response
        except ClientError as e:
            print(f"✗ Error: {e.response['Error']['Message']}")
            raise
    
    def update_preferences(self, user_id, timestamp, theme=None, notifications=None):
        """
        BEST PRACTICE: Update nested attributes using dot notation
        - Updates only specified nested fields
        - Preserves other nested attributes
        """
        update_parts = []
        attr_values = {}
        attr_names = {}
        
        if theme is not None:
            update_parts.append('#prefs.#theme = :theme')
            attr_values[':theme'] = theme
            attr_names['#prefs'] = 'preferences'
            attr_names['#theme'] = 'theme'
        
        if notifications is not None:
            update_parts.append('#prefs.#notif = :notif')
            attr_values[':notif'] = notifications
            attr_names['#prefs'] = 'preferences'
            attr_names['#notif'] = 'notifications'
        
        if not update_parts:
            print("✗ No updates specified")
            return None
        
        try:
            response = self.table.update_item(
                Key={
                    'userId': user_id,
                    'timestamp': timestamp
                },
                UpdateExpression='SET ' + ', '.join(update_parts),
                ExpressionAttributeNames=attr_names,
                ExpressionAttributeValues=attr_values,
                ReturnValues='ALL_NEW'
            )
            print(f"✓ Updated preferences for {user_id}")
            return response['Attributes']
        except ClientError as e:
            print(f"✗ Error: {e.response['Error']['Message']}")
            raise
    
    def query_by_email(self, email):
        """
        BEST PRACTICE: Use GSI for alternate access patterns
        - Query non-key attributes efficiently
        - Avoids expensive table scans
        """
        try:
            response = self.table.query(
                IndexName=GSI_NAME,
                KeyConditionExpression=Key('email').eq(email)
            )
            
            items = response['Items']
            print(f"✓ Found {len(items)} profiles with email {email}")
            return items
        except ClientError as e:
            print(f"✗ Error: {e.response['Error']['Message']}")
            raise
    
    def delete_user_profile(self, user_id, timestamp):
        """
        BEST PRACTICE: Use delete_item with conditions
        - Add ConditionExpression for safety
        - Returns deleted item if needed
        """
        try:
            response = self.table.delete_item(
                Key={
                    'userId': user_id,
                    'timestamp': timestamp
                },
                # BEST PRACTICE: Condition to ensure item exists before deleting
                ConditionExpression='attribute_exists(userId)',
                ReturnValues='ALL_OLD'  # Return deleted item
            )
            
            if 'Attributes' in response:
                print(f"✓ Deleted profile for {user_id} at {timestamp}")
                return response['Attributes']
            else:
                print(f"✗ No item found to delete")
                return None
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print(f"✗ Item does not exist")
            else:
                print(f"✗ Error: {e.response['Error']['Message']}")
            raise
    
    def batch_get_profiles(self, user_items):
        """
        BEST PRACTICE: Use batch_get_item for multiple items
        - Retrieves up to 100 items in single request
        - More efficient than multiple get_item calls
        - Input: list of {'userId': ..., 'timestamp': ...} dicts
        """
        try:
            response = self.dynamodb.batch_get_item(
                RequestItems={
                    TABLE_NAME: {
                        'Keys': user_items
                    }
                }
            )
            
            items = response['Responses'].get(TABLE_NAME, [])
            print(f"✓ Retrieved {len(items)} profiles in batch")
            return items
        except ClientError as e:
            print(f"✗ Error: {e.response['Error']['Message']}")
            raise


def demo():
    """Demonstrate DynamoDB best practices"""
    app = DynamoDBApp()
    
    print("\n=== 0. LOAD SEED DATA ===")
    app.load_seed_data()    

    print("\n=== 1. PUT ITEM (with condition) ===")
    try:
        app.put_user_profile(
            user_id='user789',
            email='user789@example.com',
            first_name='Alice',
            last_name='Johnson',
            preferences={'theme': 'dark', 'notifications': True},
            loginCount=0
        )
    except ClientError:
        pass
    
    print("\n=== 2. GET ITEM (with projection) ===")
    profile = app.get_user_profile('user123', '1698768000')
    if profile:
        print(f"Profile: {profile}")
    
    print("\n=== 3. QUERY (partition + sort key range) ===")
    activities = app.query_user_activity('user123', start_time='1698700000')
    for activity in activities:
        print(f"  - Timestamp: {activity['timestamp']}, Logins: {activity.get('loginCount', 0)}")
    
    print("\n=== 4. UPDATE ITEM (atomic counter) ===")
    app.update_login_count('user123', '1698768000', increment=1)
    
    print("\n=== 5. UPDATE NESTED ATTRIBUTES ===")
    updated = app.update_preferences('user123', '1698768000', theme='blue')
    if updated:
        print(f"New preferences: {updated.get('preferences')}")
    
    print("\n=== 6. QUERY GSI (by email) ===")
    profiles = app.query_by_email('user456@example.com')
    for profile in profiles:
        print(f"  - User: {profile['userId']}, Name: {profile.get('firstName')}")
    
    print("\n=== 7. BATCH GET ===")
    batch_items = app.batch_get_profiles([
        {'userId': 'user123', 'timestamp': '1698768000'},
        {'userId': 'user456', 'timestamp': '1698940800'}
    ])
    print(f"Retrieved {len(batch_items)} items")
    
    print("\n=== 8. DELETE ITEM (with condition) ===")
    try:
        app.delete_user_profile('user789', str(int(time.time())))
    except ClientError:
        pass


if __name__ == '__main__':
    demo()
