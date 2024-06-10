import os
import hashlib
import json
import boto3
import psycopg2
from datetime import datetime

def mask_value(value):
    return hashlib.sha256(value.encode()).hexdigest()

def process_message(message):
    data = json.loads(message['Body'])
    flattened_data = {
        'user_id': data['user_id'],
        'device_type': data['device']['type'],
        'masked_ip': mask_value(data['ip']),
        'masked_device_id': mask_value(data['device']['id']),
        'locale': data['locale'],
        'app_version': int(data['app_version'].split('.')[0]),  # assuming version is like "1.2.3"
        'create_date': datetime.strptime(data['create_date'], '%Y-%m-%d').date()
    }
    return flattened_data

def main():
    # SQS setup
    sqs = boto3.client('sqs', endpoint_url=os.environ['AWS_ENDPOINT_URL'])
    queue_url = sqs.get_queue_url(QueueName='user-logins-queue')['QueueUrl']

    # Postgres setup
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cursor = conn.cursor()

    while True:
        messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=20)
        if 'Messages' not in messages:
            break

        for message in messages['Messages']:
            data = process_message(message)
            cursor.execute(
                """
                INSERT INTO user_logins (user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (data['user_id'], data['device_type'], data['masked_ip'], data['masked_device_id'], data['locale'], data['app_version'], data['create_date'])
            )
            conn.commit()
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message['ReceiptHandle'])

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
