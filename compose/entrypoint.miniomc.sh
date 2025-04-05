#!/bin/sh

set -e

mc alias set local "$MINIO_ENDPOINT_INTERNAL" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

mc mb --ignore-existing local/raw
mc mb --ignore-existing local/lakehouse

echo "Setting public read-only bucket policies..."
for bucket in raw lakehouse; do
cat <<EOF > /tmp/${bucket}_policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "s3:GetObject"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:s3:::${bucket}/*",
      "Principal": "*"
    }
  ]
}
EOF

mc anonymous set-json /tmp/${bucket}_policy.json local/${bucket}
done

echo "Bucket setup complete."
