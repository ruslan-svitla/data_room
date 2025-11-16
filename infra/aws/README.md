# AWS Infrastructure Deployment

This directory contains AWS CloudFormation templates and a deployment script for deploying the Data Room application to AWS.

## Infrastructure Components

- **Storage**: S3 bucket for document storage
- **Database**: DynamoDB tables for storing application data
- **IAM**: Identity and Access Management roles and policies
- **API**: API Gateway and Lambda functions for backend services
- **Frontend**: S3 website hosting with CloudFront distribution

## Deployment Instructions

### Prerequisites

1. AWS CLI installed and configured with appropriate permissions
2. Bash shell environment
3. Python 3.12 for backend Lambda function
4. Node.js and npm for frontend build

### Deployment Options

You can deploy individual components or the entire stack:

```bash
# Deploy everything
./deploy.sh --type all --stage dev

# Deploy just the storage component
./deploy.sh --type storage --stage dev

# Deploy just the database component
./deploy.sh --type database --stage dev

# Deploy just the IAM roles
./deploy.sh --type iam --stage dev

# Deploy just the API
./deploy.sh --type api --stage dev

# Deploy just the frontend
./deploy.sh --type frontend --stage dev

# Use a different stack name prefix
./deploy.sh --type all --stage dev --name my-custom-name

# Deploy to a different AWS region
./deploy.sh --type all --stage dev --region us-west-2

# Deploy with a custom domain
./deploy.sh --type all --stage prod --domain myapp.example.com
```

## Environment Variables

The deployment script can automatically load credentials from the `backend/.env` file. This simplifies the deployment process by eliminating the need to manually enter credentials like Google OAuth credentials and secret keys.

### Required Environment Variables

Place these in your `backend/.env` file:

```
# Authentication
SECRET_KEY=your_secret_key_here

# Google Drive Integration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

If the `backend/.env` file exists, the deployment script will automatically read these values when deploying. If the file doesn't exist or specific variables are missing, the script will prompt you to enter them manually.

### Customizing Environment Variables

You can customize the environment variables by modifying the `backend/.env` file. For production deployments, consider using AWS Secrets Manager instead of storing sensitive values in the environment file.

## Deployment Outputs

After successful deployment, the script will output:

- API Endpoint URL
- Frontend URL
- Custom domain URL (if specified)

## Verifying Deployment

You can verify the deployment using the `test_deploy.sh` script. This script runs a series of checks against the deployed resources to ensure they are correctly configured and operational.

```bash
# Test all components
./test_deploy.sh --type all --stage dev

# Test specific component
./test_deploy.sh --type api --stage dev
```

## Teardown

To remove the deployed infrastructure, use the `teardown.sh` script. This script will delete the CloudFormation stacks and attempt to empty S3 buckets before deletion.

> [!WARNING]
> This action is irreversible. The script will ask for confirmation before proceeding.

```bash
# Remove everything
./teardown.sh --type all --stage dev

# Remove specific component
./teardown.sh --type frontend --stage dev
```

## Troubleshooting

If you encounter any issues during deployment, check the CloudFormation events in the AWS Console for detailed error messages:

```bash
aws cloudformation describe-stack-events --stack-name data-room-api-dev
```

You can also update a failed deployment by running the deployment command again after fixing the issues.