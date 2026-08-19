#!/bin/bash

ECR_URL=432232239026.dkr.ecr.eu-north-1.amazonaws.com
BUILD_COMPONENT_PREFIX="metsis-ee"
BUILD_COMPONENT="ui"
BUILD_VERSION="latest"

npm install
ng build --prod

docker build -t "${BUILD_COMPONENT_PREFIX}-${BUILD_COMPONENT}:${BUILD_VERSION}" .

docker tag "${BUILD_COMPONENT_PREFIX}-${BUILD_COMPONENT}" "${ECR_URL}/${BUILD_COMPONENT_PREFIX}-${BUILD_COMPONENT}:${BUILD_VERSION}"

$(aws ecr get-login --no-include-email --region eu-north-1)

docker push "${ECR_URL}/${BUILD_COMPONENT_PREFIX}-${BUILD_COMPONENT}:${BUILD_VERSION}"
