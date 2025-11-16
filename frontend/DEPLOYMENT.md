# Frontend Deployment Guide

The frontend of the Data Room application can be deployed to AWS using CloudFormation templates and the deployment script included in the `/infra/aws` directory.

## Automatic Deployment

The simplest way to deploy the frontend is using the provided deployment script:

```bash
cd infra/aws
./deploy.sh --type frontend --stage dev
```

This will:
1. Create/update the CloudFormation stack for the frontend (S3 bucket + CloudFront)
2. Build the React application with the correct API endpoint
3. Upload the built files to the S3 bucket
4. Invalidate the CloudFront cache

### Deployment with Custom Domain

To deploy with a custom domain:

```bash
./deploy.sh --type frontend --stage prod --domain yourdomain.com
```

**Note:** Before using a custom domain, make sure you have:
- Registered the domain
- Created an SSL certificate in AWS Certificate Manager (ACM) in the us-east-1 region
- Updated the Certificate ARN in the CloudFormation template

## Manual Deployment

If you need more control over the deployment process, you can deploy manually:

### 1. Deploy Infrastructure

```bash
cd infra/aws
aws cloudformation deploy \
  --template-file ./frontend/static-site.yaml \
  --stack-name "data-room-frontend-dev" \
  --parameter-overrides \
      Stage=dev \
      ApiEndpoint=https://your-api-endpoint.execute-api.region.amazonaws.com/dev \
      DomainName=""
```

### 2. Build the Frontend

```bash
cd frontend
echo "VITE_API_URL=https://your-api-endpoint.execute-api.region.amazonaws.com/dev" > .env.production
npm install
npm run build
```

### 3. Deploy to S3

```bash
aws s3 sync dist/ s3://data-room-frontend-dev-your-account-id/ --delete
```

### 4. Invalidate CloudFront Cache

```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

## Environment Variables

The frontend requires these environment variables:

- `VITE_API_URL` - URL of the API Gateway endpoint
- `VITE_GOOGLE_CLIENT_ID` - Google OAuth client ID (for Google Drive integration)

During automated deployment, `VITE_API_URL` is automatically set to match your deployed API.

## Troubleshooting

### Common Issues

1. **Blank page after deployment**
   - Check browser console for error messages
   - Verify that the API endpoint is correct in `.env.production`
   - Check if the S3 bucket has the correct files

2. **CORS errors**
   - Ensure your API Gateway has the appropriate CORS headers configured
   - Check the origin settings in your API Gateway

3. **Authentication issues**
   - Verify that Google OAuth client ID is correct
   - Check that redirect URIs are configured correctly in Google Console

4. **CloudFront caching old content**
   - Always run a cache invalidation after deploying new content
   - Use versioning in your asset filenames to bypass caching