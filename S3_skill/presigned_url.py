import os
from skill_files_to_s3 import get_s3_client

BUCKET_NAME = os.getenv("BUCKET_NAME")

def get_presigned_url(s3_client, s3_key, expiry_time=300):
    url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': BUCKET_NAME, 'Key':s3_key },
        ExpiresIn=expiry_time
    )
    return url

s3_client = get_s3_client()
s3_key = 'DM_skill_files//ECPC Transmission__1740111039229.pdf'
res = get_presigned_url(s3_client=s3_client, s3_key=s3_key)

print("URL : ", res)
