import logging

from skill_files import get_s3_client

S3_BUCKET = 'glms-mediafiles-dev'

# Create S3 client
s3_client = get_s3_client()

def get_presigned_url(s3_client, s3_key, expiry_time=300):
    url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key':s3_key },
        ExpiresIn=expiry_time
    )
    return url
# Create S3 client
s3_client = get_s3_client()
res = get_presigned_url(s3_client=s3_client, s3_key="database_files/assessment.png")

print(res)