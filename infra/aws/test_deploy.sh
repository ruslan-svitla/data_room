#!/bin/bash

# Define colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
STACK_NAME="data-room"
STAGE="dev"
TEST_TYPE="all"
REGION="us-east-1"
TEST_TIMEOUT=10 # Seconds to wait for HTTP tests

# Status tracking
SUCCESS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

usage() {
  echo -e "${GREEN}Usage:${NC} $0 [options]"
  echo "Options:"
  echo "  -t, --type       Type of resource to test (all, storage, database, iam, api, frontend)"
  echo "  -s, --stage      Stage to test (dev, staging, prod) - default: dev"
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
      TEST_TYPE="$2"
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

# Validate test type
valid_types=("all" "storage" "database" "iam" "api" "frontend")
if [[ ! " ${valid_types[@]} " =~ " ${TEST_TYPE} " ]]; then
    echo -e "${RED}Error:${NC} Invalid test type. Must be one of: ${valid_types[@]}"
    usage
fi

# Validate stage
valid_stages=("dev" "staging" "prod")
if [[ ! " ${valid_stages[@]} " =~ " ${STAGE} " ]]; then
    echo -e "${RED}Error:${NC} Invalid stage. Must be one of: ${valid_stages[@]}"
    usage
fi

# Change to the script directory
cd "$(dirname "$0")"

# Helper function to report test result
report_test() {
    local test_name=$1
    local result=$2
    local message=$3

    if [[ $result -eq 0 ]]; then
        echo -e "${GREEN}✓ PASS:${NC} ${test_name} ${message}"
        ((SUCCESS_COUNT++))
    else
        echo -e "${RED}✗ FAIL:${NC} ${test_name} ${message}"
        ((FAIL_COUNT++))
    fi
}

# Helper function to report skipped test
skip_test() {
    local test_name=$1
    local reason=$2
    echo -e "${YELLOW}○ SKIP:${NC} ${test_name} (${reason})"
    ((SKIP_COUNT++))
}

test_cloudformation_stack() {
    local stack_name="${STACK_NAME}-$1-${STAGE}"
    local component_name=$2

    echo -e "${BLUE}=== Testing ${component_name} Stack ===${NC}"
    
    # Check if stack exists
    aws cloudformation describe-stacks --stack-name ${stack_name} --region ${REGION} &>/dev/null
    if [[ $? -ne 0 ]]; then
        report_test "Stack Exists" 1 "(Stack ${stack_name} not found)"
        return 1
    fi
    
    report_test "Stack Exists" 0 "(Stack ${stack_name} found)"

    # Check stack status
    local stack_status=$(aws cloudformation describe-stacks \
        --stack-name ${stack_name} \
        --query "Stacks[0].StackStatus" \
        --output text \
        --region ${REGION})
    
    case ${stack_status} in
        "CREATE_COMPLETE"|"UPDATE_COMPLETE")
            report_test "Stack Status" 0 "(Status: ${stack_status})"
            ;;
        *)
            report_test "Stack Status" 1 "(Status: ${stack_status} - Expected: CREATE_COMPLETE or UPDATE_COMPLETE)"
            ;;
    esac

    return 0
}

test_storage() {
    test_cloudformation_stack "storage" "Storage"
    if [[ $? -ne 0 ]]; then return 1; fi

    # Get S3 bucket name
    local bucket_name=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_NAME}-storage-${STAGE}" \
        --query "Stacks[0].Outputs[?OutputKey=='DataRoomBucketName'].OutputValue" \
        --output text \
        --region ${REGION})
    
    # Test bucket existence
    aws s3api head-bucket --bucket ${bucket_name} &>/dev/null
    report_test "Bucket Exists" $? "(${bucket_name})"
    
    # Test bucket permissions by writing a test file
    echo "test" > /tmp/test_file.txt
    aws s3 cp /tmp/test_file.txt "s3://${bucket_name}/test_file.txt" &>/dev/null
    report_test "S3 Write Permissions" $? "(Uploaded test file to ${bucket_name})"
    
    # Test bucket read permissions
    aws s3 cp "s3://${bucket_name}/test_file.txt" /tmp/test_file_downloaded.txt &>/dev/null
    report_test "S3 Read Permissions" $? "(Downloaded test file from ${bucket_name})"
    
    # Cleanup
    aws s3 rm "s3://${bucket_name}/test_file.txt" &>/dev/null
    rm -f /tmp/test_file.txt /tmp/test_file_downloaded.txt

    return 0
}

test_database() {
    test_cloudformation_stack "database" "Database"
    if [[ $? -ne 0 ]]; then return 1; fi

    # Get table names
    echo -e "${BLUE}Checking DynamoDB tables...${NC}"
    local users_table=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_NAME}-database-${STAGE}" \
        --query "Stacks[0].Outputs[?OutputKey=='UsersTableName'].OutputValue" \
        --output text \
        --region ${REGION})
    
    local documents_table=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_NAME}-database-${STAGE}" \
        --query "Stacks[0].Outputs[?OutputKey=='DocumentsTableName'].OutputValue" \
        --output text \
        --region ${REGION})
    
    local folders_table=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_NAME}-database-${STAGE}" \
        --query "Stacks[0].Outputs[?OutputKey=='FoldersTableName'].OutputValue" \
        --output text \
        --region ${REGION})

    # Test table existence and statuses
    for table in "${users_table}" "${documents_table}" "${folders_table}"; do
        local table_status=$(aws dynamodb describe-table \
            --table-name ${table} \
            --query "Table.TableStatus" \
            --output text \
            --region ${REGION} 2>/dev/null || echo "NOT_FOUND")
        
        if [[ "${table_status}" == "ACTIVE" ]]; then
            report_test "Table ${table}" 0 "(Status: ${table_status})"
        elif [[ "${table_status}" == "NOT_FOUND" ]]; then
            report_test "Table ${table}" 1 "(Table not found)"
        else
            report_test "Table ${table}" 1 "(Status: ${table_status} - Expected: ACTIVE)"
        fi
    done
    
    # Test basic write and read operations
    local test_id="test-$(date +%s)"
    echo -e "${BLUE}Testing DynamoDB operations with test ID: ${test_id}${NC}"
    
    # Write test item
    aws dynamodb put-item \
        --table-name ${users_table} \
        --item "{\"id\": {\"S\": \"${test_id}\"}, \"name\": {\"S\": \"Test User\"}, \"email\": {\"S\": \"test@example.com\"}}" \
        --return-consumed-capacity TOTAL \
        --region ${REGION} &>/dev/null
    report_test "DynamoDB Write" $? "(Created test user item in ${users_table})"
    
    # Read test item
    local read_result=$(aws dynamodb get-item \
        --table-name ${users_table} \
        --key "{\"id\": {\"S\": \"${test_id}\"}}" \
        --region ${REGION} \
        --output json)
    
    if echo "${read_result}" | grep -q "${test_id}"; then
        report_test "DynamoDB Read" 0 "(Retrieved test user item from ${users_table})"
    else
        report_test "DynamoDB Read" 1 "(Failed to retrieve test user item)"
    fi
    
    # Cleanup test item
    aws dynamodb delete-item \
        --table-name ${users_table} \
        --key "{\"id\": {\"S\": \"${test_id}\"}}" \
        --region ${REGION} &>/dev/null
    
    return 0
}

test_iam() {
    test_cloudformation_stack "iam" "IAM"
    if [[ $? -ne 0 ]]; then return 1; fi
    
    # Get Lambda role ARN
    local lambda_role=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_NAME}-iam-${STAGE}" \
        --query "Stacks[0].Outputs[?OutputKey=='DataRoomLambdaRoleArn'].OutputValue" \
        --output text \
        --region ${REGION})
    
    # Extract role name from ARN
    local role_name=$(echo ${lambda_role} | sed 's/.*role\///')
    
    # Test if role exists
    aws iam get-role --role-name ${role_name} &>/dev/null
    report_test "Lambda Role Exists" $? "(${role_name})"
    
    # Get role policies
    local policies=$(aws iam list-attached-role-policies \
        --role-name ${role_name} \
        --query "AttachedPolicies[].PolicyName" \
        --output text \
        --region ${REGION} 2>/dev/null || echo "FAILED")
    
    if [[ "${policies}" == "FAILED" ]]; then
        report_test "IAM Policies" 1 "(Failed to retrieve policies for ${role_name})"
    else
        report_test "IAM Policies" 0 "(Found policies: ${policies})"
    fi
    
    # Check trust relationship
    local trust_policy=$(aws iam get-role \
        --role-name ${role_name} \
        --query "Role.AssumeRolePolicyDocument.Statement[].Principal.Service" \
        --output text \
        --region ${REGION})
    
    if echo "${trust_policy}" | grep -q "lambda.amazonaws.com"; then
        report_test "Trust Relationship" 0 "(Lambda service trust relationship confirmed)"
    else
        report_test "Trust Relationship" 1 "(Lambda service trust relationship not found)"
    fi
    
    return 0
}

test_api() {
    test_cloudformation_stack "api" "API"
    if [[ $? -ne 0 ]]; then return 1; fi
    
    # Get API endpoint
    local api_endpoint=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_NAME}-api-${STAGE}" \
        --query "Stacks[0].Outputs[?OutputKey=='DataRoomApiEndpoint'].OutputValue" \
        --output text \
        --region ${REGION})
    
    # Get Lambda function name
    local lambda_function=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_NAME}-api-${STAGE}" \
        --query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionName'].OutputValue" \
        --output text \
        --region ${REGION} 2>/dev/null || echo "")
    
    if [[ -z "${lambda_function}" ]]; then
        # Try finding lambda function with a pattern
        lambda_function=$(aws lambda list-functions \
            --query "Functions[?contains(FunctionName, '${STACK_NAME}-${STAGE}')].FunctionName" \
            --output text \
            --region ${REGION})
    fi
    
    # Test Lambda function existence
    if [[ -n "${lambda_function}" ]]; then
        aws lambda get-function --function-name ${lambda_function} --region ${REGION} &>/dev/null
        report_test "Lambda Function" $? "(${lambda_function})"
        
        # Test Lambda function configuration
        local runtime=$(aws lambda get-function \
            --function-name ${lambda_function} \
            --query "Configuration.Runtime" \
            --output text \
            --region ${REGION})
        
        report_test "Lambda Runtime" 0 "(${runtime})"

        # Check Lambda environment variables
        local env_vars=$(aws lambda get-function-configuration \
            --function-name ${lambda_function} \
            --query "Environment.Variables" \
            --output text \
            --region ${REGION} 2>/dev/null || echo "FAILED")
        
        if [[ "${env_vars}" == "FAILED" || "${env_vars}" == "None" ]]; then
            report_test "Lambda Environment" 1 "(Failed to retrieve environment variables)"
        else
            report_test "Lambda Environment" 0 "(Environment variables configured)"
        fi
    else
        report_test "Lambda Function" 1 "(Could not find Lambda function)"
        skip_test "Lambda Runtime" "Lambda function not found"
        skip_test "Lambda Environment" "Lambda function not found"
    fi
    
    # Test API endpoint
    echo -e "${BLUE}Testing API endpoint: ${api_endpoint}${NC}"
    
    # Try health check endpoint first
    if curl -s -o /dev/null -w "%{http_code}" "${api_endpoint}/health" -m ${TEST_TIMEOUT} | grep -q "200"; then
        report_test "API Health Endpoint" 0 "(${api_endpoint}/health is responding)"
    else
        report_test "API Health Endpoint" 1 "(${api_endpoint}/health is not responding)"
    fi
    
    # Try docs endpoint (if FastAPI)
    if curl -s -o /dev/null -w "%{http_code}" "${api_endpoint}/docs" -m ${TEST_TIMEOUT} | grep -q "200"; then
        report_test "API Docs Endpoint" 0 "(${api_endpoint}/docs is responding)"
    else
        skip_test "API Docs Endpoint" "Not available or requires authentication"
    fi
    
    return 0
}

test_frontend() {
    test_cloudformation_stack "frontend" "Frontend"
    if [[ $? -ne 0 ]]; then return 1; fi
    
    # Get frontend bucket name
    local frontend_bucket=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_NAME}-frontend-${STAGE}" \
        --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
        --output text \
        --region ${REGION})
    
    # Test bucket existence
    aws s3api head-bucket --bucket ${frontend_bucket} &>/dev/null
    report_test "Frontend Bucket Exists" $? "(${frontend_bucket})"
    
    # Check for index.html in the bucket
    local index_exists=$(aws s3 ls "s3://${frontend_bucket}/index.html" 2>&1)
    if echo "${index_exists}" | grep -q "index.html"; then
        report_test "Frontend Index File" 0 "(index.html found in bucket)"
    else
        report_test "Frontend Index File" 1 "(index.html not found in bucket)"
    fi
    
    # Get CloudFront distribution
    local cloudfront_id=$(aws cloudformation describe-stacks \
        --stack-name "${STACK_NAME}-frontend-${STAGE}" \
        --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" \
        --output text \
        --region ${REGION} 2>/dev/null || echo "")
    
    if [[ -n "${cloudfront_id}" && "${cloudfront_id}" != "None" ]]; then
        # Check CloudFront distribution status
        local dist_status=$(aws cloudfront get-distribution \
            --id ${cloudfront_id} \
            --query "Distribution.Status" \
            --output text \
            --region ${REGION} 2>/dev/null || echo "FAILED")
        
        if [[ "${dist_status}" == "Deployed" ]]; then
            report_test "CloudFront Distribution" 0 "(${cloudfront_id} is ${dist_status})"
            
            # Get CloudFront domain and test it
            local cf_domain=$(aws cloudfront get-distribution \
                --id ${cloudfront_id} \
                --query "Distribution.DomainName" \
                --output text \
                --region ${REGION})
            
            echo -e "${BLUE}Testing CloudFront endpoint: https://${cf_domain}${NC}"
            
            if curl -s -o /dev/null -w "%{http_code}" "https://${cf_domain}" -m ${TEST_TIMEOUT} | grep -q -e "200" -e "301" -e "302"; then
                report_test "CloudFront Access" 0 "(https://${cf_domain} is responding)"
            else
                report_test "CloudFront Access" 1 "(https://${cf_domain} is not responding)"
            fi
        else
            report_test "CloudFront Distribution" 1 "(${cloudfront_id} status: ${dist_status}, expected: Deployed)"
            skip_test "CloudFront Access" "CloudFront not deployed"
        fi
    else
        skip_test "CloudFront Distribution" "No CloudFront distribution found"
        skip_test "CloudFront Access" "No CloudFront distribution found"
    fi
    
    return 0
}

test_all() {
    echo -e "${GREEN}=== Testing All Components ===${NC}"
    test_storage
    test_database
    test_iam
    test_api
    test_frontend
}

# Print header
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}= Data Room Infrastructure Test Tool          =${NC}"
echo -e "${BLUE}= Stack: ${STACK_NAME}  Stage: ${STAGE}  Region: ${REGION} =${NC}"
echo -e "${BLUE}================================================${NC}"

# Execute tests based on type
case ${TEST_TYPE} in
  all)
    test_all
    ;;
  storage)
    test_storage
    ;;
  database)
    test_database
    ;;
  iam)
    test_iam
    ;;
  api)
    test_api
    ;;
  frontend)
    test_frontend
    ;;
esac

# Print summary
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}= Test Summary                               =${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}PASS: ${SUCCESS_COUNT}${NC}"
echo -e "${RED}FAIL: ${FAIL_COUNT}${NC}"
echo -e "${YELLOW}SKIP: ${SKIP_COUNT}${NC}"
echo -e "${BLUE}================================================${NC}"

# Set exit code based on failures
if [[ ${FAIL_COUNT} -gt 0 ]]; then
    echo -e "${RED}Tests completed with failures.${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed successfully!${NC}"
    exit 0
fi