#!/bin/bash

# Define colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
STACK_NAME="data-room"
STAGE="dev"
DELETE_TYPE="all"
REGION="us-east-1"

usage() {
  echo -e "${GREEN}Usage:${NC} $0 [options]"
  echo "Options:"
  echo "  -t, --type       Type of resource to delete (all, storage, database, iam, api, frontend)"
  echo "  -s, --stage      Stage to delete (dev, staging, prod) - default: dev"
  echo "  -n, --name       Stack name prefix - default: data-room"
  echo "  -r, --region     AWS region - default: us-east-1"
  echo "  -h, --help       Show this help message"
  exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -t|--type)
      DELETE_TYPE="$2"
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
    -h|--help)
      usage
      ;;
    *)
      echo -e "${RED}Unknown option:${NC} $1"
      usage
      ;;
  esac
done

# Validate delete type
valid_types=("all" "storage" "database" "iam" "api" "frontend")
if [[ ! " ${valid_types[@]} " =~ " ${DELETE_TYPE} " ]]; then
    echo -e "${RED}Error:${NC} Invalid delete type. Must be one of: ${valid_types[@]}"
    usage
fi

# Validate stage
valid_stages=("dev" "staging" "prod")
if [[ ! " ${valid_stages[@]} " =~ " ${STAGE} " ]]; then
    echo -e "${RED}Error:${NC} Invalid stage. Must be one of: ${valid_stages[@]}"
    usage
fi

# Confirmation function
confirm() {
    read -p "Are you sure you want to delete ${DELETE_TYPE} stack(s) for stage '${STAGE}'? This action cannot be undone. (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Operation cancelled.${NC}"
        exit 1
    fi
}

# Delete functions
delete_frontend() {
  echo -e "${GREEN}=== Deleting Frontend Stack ===${NC}"
  
  # Try to empty the bucket first (best effort)
  FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-frontend-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
    --output text \
    --region ${REGION} 2>/dev/null)
    
  if [[ -n "$FRONTEND_BUCKET" ]]; then
      echo -e "${YELLOW}Attempting to empty frontend bucket: ${FRONTEND_BUCKET}...${NC}"
      aws s3 rm "s3://${FRONTEND_BUCKET}" --recursive --region ${REGION} 2>/dev/null || echo -e "${YELLOW}Could not empty bucket automatically.${NC}"
  fi

  aws cloudformation delete-stack \
    --stack-name "${STACK_NAME}-frontend-${STAGE}" \
    --region ${REGION}
    
  echo -e "${YELLOW}Deletion initiated for Frontend stack. Check AWS Console for progress.${NC}"
}

delete_api() {
  echo -e "${GREEN}=== Deleting API Stack ===${NC}"
  aws cloudformation delete-stack \
    --stack-name "${STACK_NAME}-api-${STAGE}" \
    --region ${REGION}
  echo -e "${YELLOW}Deletion initiated for API stack.${NC}"
}

delete_iam() {
  echo -e "${GREEN}=== Deleting IAM Stack ===${NC}"
  aws cloudformation delete-stack \
    --stack-name "${STACK_NAME}-iam-${STAGE}" \
    --region ${REGION}
  echo -e "${YELLOW}Deletion initiated for IAM stack.${NC}"
}

delete_database() {
  echo -e "${GREEN}=== Deleting Database Stack ===${NC}"
  aws cloudformation delete-stack \
    --stack-name "${STACK_NAME}-database-${STAGE}" \
    --region ${REGION}
  echo -e "${YELLOW}Deletion initiated for Database stack.${NC}"
}

delete_storage() {
  echo -e "${GREEN}=== Deleting Storage Stack ===${NC}"
  
  # Try to empty the bucket first (best effort)
  STORAGE_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}-storage-${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='DataRoomBucketName'].OutputValue" \
    --output text \
    --region ${REGION} 2>/dev/null)
    
  if [[ -n "$STORAGE_BUCKET" ]]; then
      echo -e "${YELLOW}Attempting to empty storage bucket: ${STORAGE_BUCKET}...${NC}"
      # Note: This simple rm --recursive might not delete versions if versioning is enabled.
      # For versioned buckets, a more complex script is needed, but this helps for simple cases.
      aws s3 rm "s3://${STORAGE_BUCKET}" --recursive --region ${REGION} 2>/dev/null || echo -e "${YELLOW}Could not empty bucket automatically.${NC}"
      
      # Try to delete versions (if any) - this is a bit risky/complex in bash, so we'll warn user instead
      echo -e "${YELLOW}WARNING: If versioning is enabled, you may need to manually empty the bucket versions in AWS Console.${NC}"
  fi

  aws cloudformation delete-stack \
    --stack-name "${STACK_NAME}-storage-${STAGE}" \
    --region ${REGION}
  echo -e "${YELLOW}Deletion initiated for Storage stack.${NC}"
}

delete_all() {
  # Delete in reverse order of dependencies
  delete_frontend
  echo -e "${YELLOW}Waiting for Frontend deletion to complete...${NC}"
  aws cloudformation wait stack-delete-complete --stack-name "${STACK_NAME}-frontend-${STAGE}" --region ${REGION} 2>/dev/null
  
  delete_api
  echo -e "${YELLOW}Waiting for API deletion to complete...${NC}"
  aws cloudformation wait stack-delete-complete --stack-name "${STACK_NAME}-api-${STAGE}" --region ${REGION} 2>/dev/null
  
  delete_iam
  echo -e "${YELLOW}Waiting for IAM deletion to complete...${NC}"
  aws cloudformation wait stack-delete-complete --stack-name "${STACK_NAME}-iam-${STAGE}" --region ${REGION} 2>/dev/null
  
  delete_database
  # Database and Storage can be deleted in parallel or sequence, sequence is safer
  echo -e "${YELLOW}Waiting for Database deletion to complete...${NC}"
  aws cloudformation wait stack-delete-complete --stack-name "${STACK_NAME}-database-${STAGE}" --region ${REGION} 2>/dev/null
  
  delete_storage
  echo -e "${YELLOW}Waiting for Storage deletion to complete...${NC}"
  aws cloudformation wait stack-delete-complete --stack-name "${STACK_NAME}-storage-${STAGE}" --region ${REGION} 2>/dev/null
}

# Ask for confirmation
confirm

# Execute deletion based on type
case ${DELETE_TYPE} in
  all)
    delete_all
    ;;
  storage)
    delete_storage
    ;;
  database)
    delete_database
    ;;
  iam)
    delete_iam
    ;;
  api)
    delete_api
    ;;
  frontend)
    delete_frontend
    ;;
esac

echo -e "${GREEN}Teardown process completed.${NC}"
