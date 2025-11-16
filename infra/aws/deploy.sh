#!/bin/bash

# Define colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
STACK_NAME="data-room"
STAGE="dev"
DEPLOY_TYPE="all"
REGION="us-east-1"

usage() {
  echo -e "${GREEN}Usage:${NC} $0 [options]"
  echo "Options:"
  echo "  -t, --type       Type of resource to deploy (all, storage, database, iam, api, frontend)"
  echo "  -s, --stage      Stage to deploy (dev, staging, prod) - default: dev"
  echo "  -n, --name       Stack name prefix - default: data-room"
  echo "  -r, --region     AWS region - default: us-east-1"
  echo "  -d, --domain     Custom domain name (optional)"
  echo "  -h, --help       Show this help message"
  exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -t|--type)
      DEPLOY_TYPE="$2"
      shift 2
      ;;
    -s|--stage)
      STAGE="$2"
      shift 2
      ;;
    -n|--name)
      STACK_NAME="$2"
      shift 2
      ;;
    -r|--region)
      REGION="$2"
      shift 2
      ;;
    -d|--domain)
      DOMAIN_NAME="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo -e "${RED}Unknown option:${NC} $1"
      usage
      ;;
  esac
done

# Validate deploy type
valid_types=("all" "storage" "database" "iam" "api" "frontend")
if [[ ! " ${valid_types[@]} " =~ " ${DEPLOY_TYPE} " ]]; then
    echo -e "${RED}Error:${NC} Invalid deployment type. Must be one of: ${valid_types[@]}"
    usage
fi

# Validate stage
valid_stages=("dev" "staging" "prod")
if [[ ! " ${valid_stages[@]} " =~ " ${STAGE} " ]]; then
    echo -e "${RED}Error:${NC} Invalid stage. Must be one of: ${valid_stages[@]}"
    usage
fi

# Get the script directory path
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_PATH"

# Deploy functions
deploy_storage() {
  echo -e "${GREEN}=== Deploying Storage Stack ===${NC}"
  aws cloudformation deploy \
    --template-file ./storage/s3.yaml \
    --stack-name "${STACK_NAME}-storage-${STAGE}" \
    --parameter-overrides Stage=${STAGE} \
    --capabilities CAPABILITY_NAMED_IAM \
    --region ${REGION}
}

deploy_database() {
  echo -e "${GREEN}=== Deploying Database Stack ===${NC}"
  aws cloudformation deploy \
    --template-file ./database/dynamodb.yaml \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --parameter-overrides Stage=${STAGE} \
    --capabilities CAPABILITY_NAMED_IAM \
    --region ${REGION}
}

deploy_iam() {
  echo -e "${GREEN}=== Deploying IAM Stack ===${NC}"

  # Get outputs from other stacks
  echo -e "${YELLOW}Getting outputs from other stacks...${NC}"
  
  # Get S3 ARN
  S3_BUCKET_ARN=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-storage-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='DataRoomBucketArn'].OutputValue" \
    --output text \
    --region ${REGION})
  
  # Get DynamoDB ARNs
  USERS_TABLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='UsersTableArn'].OutputValue" \
    --output text \
    --region ${REGION})
  
  DOCUMENTS_TABLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='DocumentsTableArn'].OutputValue" \
    --output text \
    --region ${REGION})
  
  FOLDERS_TABLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='FoldersTableArn'].OutputValue" \
    --output text \
    --region ${REGION})
  
  INTEGRATIONS_TABLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='IntegrationsTableArn'].OutputValue" \
    --output text \
    --region ${REGION})
  
  DOCUMENT_SHARES_TABLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='DocumentSharesTableArn'].OutputValue" \
    --output text \
    --region ${REGION})
  
  FOLDER_SHARES_TABLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='FolderSharesTableArn'].OutputValue" \
    --output text \
    --region ${REGION})
  
  DOCUMENT_VERSIONS_TABLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='DocumentVersionsTableArn'].OutputValue" \
    --output text \
    --region ${REGION})
  
  # Deploy IAM stack
  aws cloudformation deploy \
    --template-file ./iam/roles.yaml \
    --stack-name "${STACK_NAME}-iam-${STAGE}" \
    --parameter-overrides \
        Stage=${STAGE} \
        UsersTableArn=${USERS_TABLE_ARN} \
        DocumentsTableArn=${DOCUMENTS_TABLE_ARN} \
        FoldersTableArn=${FOLDERS_TABLE_ARN} \
        IntegrationsTableArn=${INTEGRATIONS_TABLE_ARN} \
        DocumentSharesTableArn=${DOCUMENT_SHARES_TABLE_ARN} \
        FolderSharesTableArn=${FOLDER_SHARES_TABLE_ARN} \
        DocumentVersionsTableArn=${DOCUMENT_VERSIONS_TABLE_ARN} \
        S3BucketArn=${S3_BUCKET_ARN} \
    --capabilities CAPABILITY_NAMED_IAM \
    --region ${REGION}
}

deploy_api() {
  echo -e "${GREEN}=== Deploying API Stack ===${NC}"
  
  # Get necessary outputs from other stacks
  echo -e "${YELLOW}Getting outputs from other stacks...${NC}"
  
  # Get Lambda Role ARN
  LAMBDA_ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-iam-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='DataRoomLambdaRoleArn'].OutputValue" \
    --output text \
    --region ${REGION})
  
  # Get S3 Bucket Name
  S3_BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-storage-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='DataRoomBucketName'].OutputValue" \
    --output text \
    --region ${REGION})
  
  # Get DynamoDB Table Names
  USERS_TABLE_NAME=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='UsersTableName'].OutputValue" \
    --output text \
    --region ${REGION})
  
  DOCUMENTS_TABLE_NAME=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='DocumentsTableName'].OutputValue" \
    --output text \
    --region ${REGION})
  
  FOLDERS_TABLE_NAME=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='FoldersTableName'].OutputValue" \
    --output text \
    --region ${REGION})
  
  INTEGRATIONS_TABLE_NAME=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='IntegrationsTableName'].OutputValue" \
    --output text \
    --region ${REGION})
  
  DOCUMENT_SHARES_TABLE_NAME=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='DocumentSharesTableName'].OutputValue" \
    --output text \
    --region ${REGION})
  
  FOLDER_SHARES_TABLE_NAME=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='FolderSharesTableName'].OutputValue" \
    --output text \
    --region ${REGION})
  
  DOCUMENT_VERSIONS_TABLE_NAME=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='DocumentVersionsTableName'].OutputValue" \
    --output text \
    --region ${REGION})
  
  # Get Google OAuth credentials from backend/.env file if it exists
  echo -e "${YELLOW}Loading credentials from backend/.env...${NC}"
  ENV_FILE="../../backend/.env"
  
  if [[ -f "$ENV_FILE" ]]; then
    # Extract values from .env file
    GOOGLE_CLIENT_ID=$(grep GOOGLE_CLIENT_ID "$ENV_FILE" | cut -d '=' -f2- | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
    GOOGLE_CLIENT_SECRET=$(grep GOOGLE_CLIENT_SECRET "$ENV_FILE" | cut -d '=' -f2- | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
    SECRET_KEY=$(grep SECRET_KEY "$ENV_FILE" | cut -d '=' -f2- | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
  
    # Remove quotes if present
    GOOGLE_CLIENT_ID=$(echo "$GOOGLE_CLIENT_ID" | sed "s/^['\"]//;s/['\"]$//")
    GOOGLE_CLIENT_SECRET=$(echo "$GOOGLE_CLIENT_SECRET" | sed "s/^['\"]//;s/['\"]$//")
    SECRET_KEY=$(echo "$SECRET_KEY" | sed "s/^['\"]//;s/['\"]$//")
  
    echo -e "${GREEN}Credentials loaded from .env file${NC}"
  else
    echo -e "${YELLOW}backend/.env file not found. Please provide credentials manually:${NC}"
    read -p "Google Client ID: " GOOGLE_CLIENT_ID
    read -p "Google Client Secret: " GOOGLE_CLIENT_SECRET
    read -p "Secret Key (press enter to use AWS Secrets Manager): " SECRET_KEY
  fi
  
  if [[ -z "$SECRET_KEY" ]]; then
    SECRET_KEY="{{resolve:secretsmanager:DataRoomSecrets:SecretString:SECRET_KEY}}"
  fi
  
  # Build backend Lambda package
  echo -e "${YELLOW}Creating Lambda deployment package...${NC}"
  echo -e "${YELLOW}Working directory: $(pwd)${NC}"
  
  # Create a temporary directory for the deployment package
  TEMP_DIR="/tmp/lambda-package-$(date +%s)"
  mkdir -p "$TEMP_DIR"
  
  # Copy the backend code to the temp directory
  echo -e "${YELLOW}Copying backend code to $TEMP_DIR...${NC}"
  mkdir -p "$TEMP_DIR/app"
  cp -r ../../backend/app/* "$TEMP_DIR/app/" || echo -e "${RED}Failed to copy app directory${NC}"
  cp ../../backend/requirements.txt "$TEMP_DIR/" || echo -e "${RED}Failed to copy requirements.txt${NC}"
  
# Use the existing Lambda handler file from app directory
echo -e "${YELLOW}Using existing Lambda handler from app directory...${NC}"
# Ensure the lambda_handler.py is copied from the app directory to the package root
cp ../../backend/app/lambda_handler.py "$TEMP_DIR/" || echo -e "${RED}Failed to copy lambda_handler.py${NC}"

# Verify the lambda_handler.py is correctly placed
if [ -f "$TEMP_DIR/lambda_handler.py" ]; then
  echo -e "${GREEN}Lambda handler copied successfully to package root${NC}"
  echo -e "${YELLOW}Lambda handler content:${NC}"
  cat "$TEMP_DIR/lambda_handler.py"
else
  echo -e "${RED}ERROR: Lambda handler not found in package root. Deployment will likely fail.${NC}"
fi
  
  # Verify the Lambda entry point
  echo -e "${YELLOW}Lambda deployment package structure:${NC}"
  ls -la "$TEMP_DIR/"
  
    # Install dependencies to the package directory
  cd "$TEMP_DIR"
  echo "Installing dependencies for Python 3.12 on Amazon Linux..."

  # Use pip to install dependencies, specifying the Lambda environment's architecture
  pip install \
    --platform manylinux2014_x86_64 \
    --python-version 3.12 \
    --implementation cp \
    --only-binary=:all: \
    -r requirements.txt -t . --no-cache-dir

  # === ADD THIS ERROR CHECKING BLOCK ===
  # Check if the pip install command was successful
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error: 'pip install' failed. Aborting deployment.${NC}"
    echo -e "${YELLOW}Check the output above for pip errors.${NC}"
    exit 1
  fi

  # Verify that the core 'fastapi' dependency was actually installed
  echo "Verifying package installation..."
  if [ ! -d "./fastapi" ]; then
    echo -e "${RED}Error: 'fastapi' directory not found after 'pip install'.${NC}"
    echo -e "${YELLOW}This means dependencies were not installed correctly. Listing current directory contents:${NC}"
    ls -la .
    exit 1
  fi
  echo -e "${GREEN}Verification successful. 'fastapi' directory found.${NC}"
  # === END OF NEW BLOCK ===
  
  # Remove unnecessary files to reduce package size
  find . -type d -name "__pycache__" -exec rm -rf {} +  2>/dev/null || true
#  find . -type d -name "*.dist-info" -exec rm -rf {} +  2>/dev/null || true
  find . -type d -name "*.egg-info" -exec rm -rf {} +  2>/dev/null || true
  find . -type f -name "*.pyc" -delete
  
  # Create a copy of the template with the updated CodeUri
  SCRIPT_DIR="$SCRIPT_PATH"
  API_DIR="${SCRIPT_DIR}/api"
  
  echo -e "${YELLOW}API directory: $API_DIR${NC}"
  ls -la "$API_DIR" || echo -e "${RED}Failed to list API directory content!${NC}"
  
  TEMPLATE_FILE="${API_DIR}/api-gateway.yaml"
  MODIFIED_TEMPLATE="${API_DIR}/api-gateway-modified.yaml"
  OUTPUT_TEMPLATE="${API_DIR}/packaged-template.yaml"
  
  if [ ! -f "$TEMPLATE_FILE" ]; then
    echo -e "${RED}Error: Template file not found at $TEMPLATE_FILE${NC}"
    exit 1
  fi
  
  echo -e "${YELLOW}Creating modified template...${NC}"
  rm -f "$MODIFIED_TEMPLATE"
  cp "$TEMPLATE_FILE" "$MODIFIED_TEMPLATE"
  
  # Replace the CodeUri in the copied template
  echo -e "${YELLOW}Updating CodeUri in template...${NC}"
  if [[ "$(uname)" == "Darwin" ]]; then
    # macOS requires an empty string after -i
    sed -i "" "s|CodeUri: ../../../backend/|CodeUri: $TEMP_DIR|g" "$MODIFIED_TEMPLATE"
  else
    # Linux doesn't require an empty string
    sed -i "s|CodeUri: ../../../backend/|CodeUri: $TEMP_DIR|g" "$MODIFIED_TEMPLATE"
  fi
  
  echo -e "${YELLOW}Verifying template modification...${NC}"
  grep -A 2 CodeUri "$MODIFIED_TEMPLATE"
  
  # Return to original directory
  cd "$SCRIPT_PATH" > /dev/null
  
  # Deploy API stack with SAM
  # First package the SAM template
  echo -e "${YELLOW}Packaging SAM template...${NC}"
  PACKAGE_BUCKET="dataroom-deployment-${STAGE}-artifacts"
  
  # Create artifact bucket if it doesn't exist
  aws s3api head-bucket --bucket "${PACKAGE_BUCKET}" 2>/dev/null || \
  aws s3 mb s3://${PACKAGE_BUCKET} --region ${REGION}
  
  # Package the SAM template
  echo -e "${YELLOW}Running cloudformation package command...${NC}"
  
  echo "Template file: $MODIFIED_TEMPLATE"
  echo "Output template: $OUTPUT_TEMPLATE"
  
  if [ ! -f "$MODIFIED_TEMPLATE" ]; then
    echo -e "${RED}Error: Template file not found at $MODIFIED_TEMPLATE${NC}"
    ls -la "$API_DIR"
    exit 1
  fi
  
  aws cloudformation package \
    --template-file "$MODIFIED_TEMPLATE" \
    --s3-bucket ${PACKAGE_BUCKET} \
    --s3-prefix lambda-code \
    --output-template-file "$OUTPUT_TEMPLATE" \
    --region ${REGION}
  
  if [ ! -f "$OUTPUT_TEMPLATE" ]; then
    echo -e "${RED}Error: Packaged template was not created at $OUTPUT_TEMPLATE${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}Successfully packaged template to $OUTPUT_TEMPLATE${NC}"
  
  # Deploy the packaged SAM template
  echo -e "${YELLOW}Deploying SAM template...${NC}"
  
  if [ ! -f "$OUTPUT_TEMPLATE" ]; then
    echo -e "${RED}Error: Cannot find packaged template at $OUTPUT_TEMPLATE${NC}"
    exit 1
  fi
  
  aws cloudformation deploy \
    --template-file "$OUTPUT_TEMPLATE" \
    --stack-name "${STACK_NAME}-api-${STAGE}" \
    --parameter-overrides \
        Stage=${STAGE} \
        GoogleClientId=${GOOGLE_CLIENT_ID} \
        GoogleClientSecret=${GOOGLE_CLIENT_SECRET} \
        SecretKey="${SECRET_KEY}" \
        DataRoomLambdaRoleArn=${LAMBDA_ROLE_ARN} \
        UsersTableName=${USERS_TABLE_NAME} \
        DocumentsTableName=${DOCUMENTS_TABLE_NAME} \
        FoldersTableName=${FOLDERS_TABLE_NAME} \
        IntegrationsTableName=${INTEGRATIONS_TABLE_NAME} \
        DocumentSharesTableName=${DOCUMENT_SHARES_TABLE_NAME} \
        FolderSharesTableName=${FOLDER_SHARES_TABLE_NAME} \
        DocumentVersionsTableName=${DOCUMENT_VERSIONS_TABLE_NAME} \
        S3BucketName=${S3_BUCKET_NAME} \
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
    --region ${REGION}
  
  # Check if deployment was successful
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to deploy CloudFormation stack${NC}"
    exit 1
  fi
  
  # Save a copy of the Lambda package for inspection if needed
  PACKAGE_ZIP="/tmp/lambda-package-$(date +%s).zip"
  echo -e "${YELLOW}Saving Lambda package to ${PACKAGE_ZIP} for inspection if needed${NC}"
  cd "$TEMP_DIR" && zip -r ${PACKAGE_ZIP} . > /dev/null
  echo -e "${GREEN}Lambda package saved to ${PACKAGE_ZIP}${NC}"
  
  # Clean up temporary files
  echo -e "${YELLOW}Cleaning up temporary files...${NC}"
  rm -f "$MODIFIED_TEMPLATE" "$OUTPUT_TEMPLATE"
  rm -rf "$TEMP_DIR"
}

deploy_frontend() {
  echo -e "${GREEN}=== Deploying Frontend Stack ===${NC}"

  # Get API endpoint from the API stack outputs
  API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-api-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='DataRoomApiEndpoint'].OutputValue" \
    --output text \
    --region ${REGION} 2>/dev/null || echo "")

  # Handle case where API endpoint is not found
  if [[ -z "$API_ENDPOINT" ]]; then
    if [[ "${DEPLOY_TYPE}" == "all" ]]; then
      echo -e "${RED}Error: API stack not found when deploying all resources. Cannot get API Endpoint.${NC}"
      exit 1
    else
      echo -e "${YELLOW}Warning: API stack not found. Deploying with a placeholder endpoint.${NC}"
      echo -e "${YELLOW}You may need to deploy the API first with: $0 --type api --stage ${STAGE}${NC}"
      API_ENDPOINT="https://api-placeholder.execute-api.${REGION}.amazonaws.com/${STAGE}/"
    fi
  fi

  # Deploy frontend infrastructure (S3, CloudFront, etc.)
  aws cloudformation deploy \
    --template-file ./frontend/static-site.yaml \
    --stack-name "${STACK_NAME}-frontend-${STAGE}" \
    --parameter-overrides \
        Stage=${STAGE} \
        ApiEndpoint=${API_ENDPOINT} \
        DomainName=${DOMAIN_NAME:-""} \
    --capabilities CAPABILITY_NAMED_IAM \
    --region ${REGION}

  # Build and deploy the frontend application
  echo -e "${YELLOW}Building frontend application...${NC}"
  cd ../../frontend

  # Get Google Client ID from backend/.env file
  BACKEND_ENV_FILE="../backend/.env"
  GOOGLE_CLIENT_ID=""

  if [[ -f "$BACKEND_ENV_FILE" ]]; then
    GOOGLE_CLIENT_ID=$(grep GOOGLE_CLIENT_ID "$BACKEND_ENV_FILE" | cut -d '=' -f2- | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//' | sed "s/^['\"]//;s/['\"]$//")
    echo "Found Google Client ID in backend/.env: ${GOOGLE_CLIENT_ID}"
  else
    echo -e "${YELLOW}backend/.env file not found. Using placeholder for Google Client ID.${NC}"
    GOOGLE_CLIENT_ID="placeholder-google-client-id"
  fi

  # --- CORRECTED URL CONSTRUCTION ---
  # The API_ENDPOINT from CloudFormation is the base URL of the stage (e.g., https://.../dev/)
  # We need to construct the full base path for the frontend, which includes '/api/v1'

  # Remove the trailing slash from the base endpoint to create a clean base
  BASE_API_ENDPOINT=${API_ENDPOINT%/}

  # Construct the final URL for the Vite build
  VITE_API_URL="${BASE_API_ENDPOINT}"

  # Create .env.production file with the correct, full API endpoint
  echo "VITE_API_URL=${VITE_API_URL}" > .env.production
  echo "VITE_GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}" >> .env.production

  echo "API_ENDPOINT: ${API_ENDPOINT}"
  echo "BASE_API_ENDPOINT: ${BASE_API_ENDPOINT}"
  echo "VITE_API_URL: ${VITE_API_URL}"
  echo "GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}"

  echo "Using API endpoint for frontend build: ${VITE_API_URL}"
  # --- END OF CORRECTION ---

  # Install dependencies and build
  npm ci
  npm run build

  # Get the frontend bucket name from the stack outputs
  FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-frontend-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
    --output text \
    --region ${REGION} 2>/dev/null)

  if [[ -z "$FRONTEND_BUCKET" ]]; then
    echo -e "${RED}Error: Frontend stack not found. S3 deploy failed.${NC}"
    cd "$SCRIPT_PATH"
    return 1
  fi

  # Deploy to S3
  echo -e "${YELLOW}Deploying frontend to S3...${NC}"
  aws s3 sync dist/ "s3://${FRONTEND_BUCKET}/" --delete

  # Invalidate CloudFront cache to ensure new assets are served
  CLOUDFRONT_DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-frontend-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" \
    --output text \
    --region ${REGION} 2>/dev/null)

  if [[ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]]; then
    echo -e "${YELLOW}Invalidating CloudFront cache...${NC}"
    aws cloudfront create-invalidation \
      --distribution-id ${CLOUDFRONT_DISTRIBUTION_ID} \
      --paths "/*" \
      --region ${REGION}
  else
    echo -e "${YELLOW}Warning: CloudFront distribution ID not found. Skipping cache invalidation.${NC}"
  fi

  # Return to original script directory
  cd "$SCRIPT_PATH"
}

deploy_all() {
  deploy_storage
  deploy_database
  deploy_iam
  deploy_api
  deploy_frontend
}

# Execute deployment based on type
case ${DEPLOY_TYPE} in
  all)
    deploy_all
    ;;
  storage)
    deploy_storage
    ;;
  database)
    deploy_database
    ;;
  iam)
    deploy_iam
    ;;
  api)
    deploy_api
    ;;
  frontend)
    deploy_frontend
    ;;
esac

# Display success message
echo -e "${GREEN}Deployment of ${DEPLOY_TYPE} completed successfully for stage: ${STAGE}${NC}"

# Show API endpoint if API was deployed
if [[ "${DEPLOY_TYPE}" == "all" || "${DEPLOY_TYPE}" == "api" ]]; then
  API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-api-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='DataRoomApiEndpoint'].OutputValue" \
    --output text \
    --region ${REGION})

  echo -e "${GREEN}API Endpoint:${NC} ${API_ENDPOINT}"
fi

# Show CloudFront URL if frontend was deployed
if [[ "${DEPLOY_TYPE}" == "all" || "${DEPLOY_TYPE}" == "frontend" ]]; then
  CLOUDFRONT_DOMAIN=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-frontend-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDomainName'].OutputValue" \
    --output text \
    --region ${REGION} 2>/dev/null)
  
  if [[ -n "$CLOUDFRONT_DOMAIN" && "$CLOUDFRONT_DOMAIN" != "None" ]]; then
    echo -e "${GREEN}Frontend URL:${NC} https://${CLOUDFRONT_DOMAIN}"
  else
    # Try getting CloudFront distribution ID directly
    CLOUDFRONT_ID=$(aws cloudformation describe-stacks \
      --stack-name "${STACK_NAME}-frontend-${STAGE}" \
      --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" \
      --output text \
      --region ${REGION} 2>/dev/null)
  
    if [[ -n "$CLOUDFRONT_ID" && "$CLOUDFRONT_ID" != "None" ]]; then
      # Get the CloudFront domain from the distribution ID
      CF_DOMAIN=$(aws cloudfront get-distribution \
        --id "$CLOUDFRONT_ID" \
        --query "Distribution.DomainName" \
        --output text \
        --region ${REGION} 2>/dev/null)
  
      if [[ -n "$CF_DOMAIN" ]]; then
        echo -e "${GREEN}Frontend URL:${NC} https://${CF_DOMAIN}"
      else
        echo -e "${YELLOW}Frontend URL: Deployment in progress or not found${NC}"
      fi
    else
      echo -e "${YELLOW}Frontend URL: Deployment in progress or not found${NC}"
    fi
  fi

  if [[ -n "${DOMAIN_NAME}" ]]; then
    echo -e "${GREEN}Custom Domain:${NC} https://${DOMAIN_NAME}"
  fi
fi