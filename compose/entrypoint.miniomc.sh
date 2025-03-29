#!/bin/sh

set -e

mc alias set local "$MINIO_ENDPOINT" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

mc mb --ignore-existing local/ingest
mc mb --ignore-existing local/stage
mc mb --ignore-existing local/serve

echo "Setting public read-only bucket policies..."
for bucket in ingest stage serve; do
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
