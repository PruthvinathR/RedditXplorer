
# Steps to deploy the containerized Reddit Sentiment Analysis to Google Cloud Run:

## Set environment variables

export GCLOUD_PROJECT="your-project-name" 

export REPO="your-repo-name"

export REGION="us-east4"

export IMAGE="image-name"

## Build the image

docker build -t $IMAGE_TAG -f path/to/Dockerfile --platform linux/x86_64 .

## Push it to Artifact Registry:

docker push $IMAGE_TAG
