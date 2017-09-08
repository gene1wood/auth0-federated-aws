
* run a command line tool on their laptop that
* generates an ephemeral shared secret
* posts that shared secret to this AWS Lambda+API Gateway app
* the lambda function then sends the user to the Auth0 hosted lock where they log in
* the user returns to the lambda function
* the lambda function exchanges the code that the user returns with for an id_token from Auth0
* the lambda function calls the /delegation endpoint with the id_token and the ARN of the AWS identity provide and and AWS role and gets back a set of ephemeral AWS STS credentials
* the lambda function encrypts those credentials with the shared secret obtained back at the beginning of the flow and publishes those now-encrypted credentials to a publicly readable queue (AWS SQS maybe, S3 maybe, SNS, not sure)
* this whole time the command line tool that initiated the flow has been watching that public queue and waiting for events to show up, each event that shows up on the queue, the command line tool tries to decrypt it with the shared secret
* as soon as the encrypted credentials show up on the queue the command line tool succeeds at fetching and decrypting them and stores those ephemeral credentials in the ~/.aws/config or ~/.aws/credentials or ~/.aws/cli/cache/ files for use by awscli or any aws SDK
