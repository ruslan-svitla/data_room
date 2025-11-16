# Frontend Deployment for Data Room

This directory contains the CloudFormation template and deployment instructions for the frontend application.

## Architecture

The frontend deployment uses the following AWS services:

- **S3**: To store the static frontend files (HTML, CSS, JS)
- **CloudFront**: To serve the frontend with low latency globally and handle SPA routing
- **IAM**: For necessary permissions and security

## Deployment

The frontend can be deployed using the main `deploy.sh` script from the parent directory:

```bash
# Deploy only the frontend
./deploy.sh --type frontend --stage dev

# Deploy everything including the frontend
./deploy.sh --type all --stage dev

# Deploy with a custom domain
./deploy.sh --type frontend --stage prod --domain your-domain.com
```

## Custom Domain Setup (Optional)

To use a custom domain with your deployment:

1. Register your domain using Amazon Route 53 or another DNS provider
2. Request an SSL certificate in AWS Certificate Manager (in the us-east-1 region)
3. Add the certificate ARN to the CloudFormation template (or your parameter store)
4. Create the appropriate DNS records pointing to your CloudFront distribution

## Development vs. Production

- For development, the frontend deployment uses the API Gateway endpoint from the dev stage
- For production, use the `--stage prod` parameter to deploy to the production environment

## Troubleshooting

- **Deployment Failures**: Check CloudFormation stack events for errors
- **404 Errors**: Ensure that the S3 bucket policy allows CloudFront access
- **API Connection Issues**: Verify that the VITE_API_URL environment variable is correctly set
- **CloudFront Cache**: Remember that CloudFront caches content - use invalidation when updating