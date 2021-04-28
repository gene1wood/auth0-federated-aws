# Deprecated

This repo is deprecated in favor of the current evolution of these tools which can be found in

* https://github.com/mozilla-iam/mozilla-aws-cli
* https://github.com/mozilla-iam/federated-aws-rp
* https://github.com/mozilla-iam/auth0-deploy/blob/master/rules/AWS-Federated-AMR.js
* https://github.com/mozilla-iam/mozilla-aws-cli/blob/master/cloudformation/README.md

# Contents

A collection of tools to enable Mozilla users federated access to AWS using Auth0

## `auth0-rules/auth0-rule-aws-federated-group-role-mapping.js`

This is the [Auth0 Rule](https://auth0.com/docs/rules/current) that is used
with the two (dev and prod) Auth0 Clients for Auth0 Dev and Production. The
rule maps a list of AWS identity providers and AWS IAM Roles into the SAML 
assertions based on membership in LDAP groups. This allows us to grant
members of specific LDAP groups access to specific AWS IAM Roles in varying
AWS accounts.

## `cloudformation-templates/auth0-federated-iam-roles.json`

A CloudFormation template which creates two IAM roles in a given AWS account.
These roles are configured to trust an AWS identify provider passed in as a
parameter on stack creation. This AWS identity provider is one of the two 
global AWS identity providers configured in the infosec-prod account.

Alternatively, AWS account holders can setup their own AWS identity
providers that map to Auth0 Clients if they wish and pass those AWS
identity provider ARNs in.

## `auth0_federated_aws/`

This directory contains two examples from AWS documentation on how to do
federated AWS command line access with users passing their credentials and
MFA through a command line interactive interface.

There is no working code in this directory yet as this would involve option
1 below which isn't ideal. We may pursue this path if we're unable to get
option 3 to work or find that in our exploration that option #1 is the best.

# How to setup federated access

Here are instructions for setting up federated access which both enables
users to log into AWS with federated credentials and is a pre-requisite for
any solution to command line federated AWS access.

## Setup Auth0

These are the steps to setup the Auth0 side of the picture for federated access

* Browse to Auth0 clients : https://manage-dev.mozilla.auth0.com/#/clients
* Create a new client : https://manage-dev.mozilla.auth0.com/#/clients/create 
  * Name : AWS Account Federated Access Dev
* In the Add-on tab check "SAML2 Web App"
  * Settings... Application Callback URL : https://signin.aws.amazon.com/saml
  * Settings... Settings : Paste in the following config
  
        {
          "audience": "https://signin.aws.amazon.com/saml",
          "mappings": {
            "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
            "name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
          },
          "createUpnClaim": false,
          "passthroughClaimsWithNoMapping": false,
          "mapUnknownClaimsAsIs": false,
          "mapIdentities": false,
          "nameIdentifierFormat": "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent",
          "nameIdentifierProbes": [
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
          ]
        }
  * Click "Save"
  * In the "Usage" tab download the Identity Provider Metadata file

## Setup AWS

These are the steps to setup the AWS side of the picture for federated access

### Create the Identity Provider

* Log into the AWS account for which you want to enable federated login
* Browse to the [IAM](https://console.aws.amazon.com/iam/home?region=us-west-2#) product... [Identity Providers](https://console.aws.amazon.com/iam/home?region=us-west-2#/providers)...Create Provider
  * Provider Type : SAML
  * Provider Name : Mozilla-Auth0-Dev
  * Metadata Document : Load the Identity Provider Metadata file downloaded 
    above
  * Next Step... Create

### Create the IAM Roles

* Deploy the `auth0-federated-iam-roles.json` CloudFormation template to 
  create the roles.
* Update either the Auth0 Rule `auth0-rule-aws-federated-group-role-mapping
  .js` or in the future the json mapping of roles to groups to include these
  new roles. You should associate each IAM role with a set of LDAP groups for
  which you want to grant access to the role.

### Test the AWS Web Console

From this point you should be able to log into AWS using federated login
* Find the Identity Provider Login URL in the Auth0 management UI by going to
  Clients... "AWS Account Federated Access Dev"... Addons... SAML Web
  App...Usage
* Click the link
* Login to Auth0
* Get sent to the AWS Account/IAM Role chooser and select that AWS account
  and IAM Role you'd like to assume
* You should now be logged into the AWS Web Console

## Diagram

![Auth0 AWS Federated Access Diagram](https://github.com/gene1wood/auth0-federated-aws/blob/master/Auth0-AWS-Federated-Access.png)

## Setup Command Line Access

This is a work in progress. There are three general approaches to this.

### Option 1 : Scrape HTML Form and Auth on the Command Line

The method [recommended by AWS](https://aws.amazon.com/blogs/security/how-to-implement-a-general-solution-for-federated-apicli-access-using-saml-2-0/)
  which involves the user passing their username, password and MFA token
  through an interactive command line interface which then does web page
  scraping and parsing to simulate a browser interaction with Auth0. To
  accomplish this we'd need to

* Establish a non-javascript based Auth0 lock login interface. This could
  be done by writing a serverless (API Gateway + Lambda) Flask app the
  does what auth0.js or the Auth0 hosted Lock do.
* Extend `samlapi_formauth.py` to interact with this new non-javascript
  based Auth0 login interface
* Accept the poor experience of users having to copy paste their LDAP
  password from their password manager onto the command line

### Option 2 : Web login and pass API keys to the filesystem
A method that I've not come up with based on 
  [Auth0's recommended method](https://auth0.com/docs/integrations/aws#obtain-aws-tokens-to-securely-call-aws-apis-and-resources)
  that involves the user logging into a web based relying party, obtaining
  AWS API keys from AWS STS over the web, and then conveying these credentials
  from the web context into the filesystem so it's available to awscli and
  boto (this step is what I haven't solved)

### Option 3 : Web login and push API keys to a queue
A method that we've envisioned where

* A user runs a script on the command line that
  * generates an ephemeral symmetric key
  * launches a browser tab to a web based relying party, POSTing the
    symmetric key to the RP over HTTPS
* In the browser the RP persists the symmetric key into the users session
  and sends them off to Auth0 to authenticate
* The user returns from Auth0 to the RP and the RP uses
  [Auth0's AWS addon for identity delegation](https://auth0.com/docs/integrations/aws#obtain-aws-tokens-to-securely-call-aws-apis-and-resources)
  to obtain AWS STS credentials
* The RP then encrypts those credentials with the symmetric key provided
  at the beginning from the command line tool and publishes them to a
  publicly readable queue
* Earlier when the command line tool launched the browser tab, immediately
  after it began polling the queue, looking for messages that decrypt
  successfully with it's ephemeral symmetric key
* Once the symmetrically encrypted message shows up on the queue the 
  command line tool fetches it, deletes it from the queue, decrypts it
  and inserts the decrypted AWS STS credentials into the 
  ~/.aws/credentials filestore

## Option 3 Setup

* In the Auth0 management Dashboard go to "Clients"
* Create a new client, distinct from the client setup for AWS Web Console access above, named "AWS API STS Key Fetcher Dev" for example
* In the "Addons" tab flip the switch on the "Amazon Web Services" addon.


# Sources
* https://auth0.com/docs/integrations/aws
* https://aws.amazon.com/blogs/security/how-to-implement-a-general-solution-for-federated-apicli-access-using-saml-2-0/
* http://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_saml_assertions.html
* https://auth0.com/docs/protocols/saml/saml-configuration/saml-assertions
* https://auth0.com/docs/integrations/aws#obtain-aws-tokens-to-securely-call-aws-apis-and-resources
* https://auth0.com/docs/integrations/aws#get-the-aws-token-for-an-authenticated-user
* https://auth0.com/docs/api-auth/tutorials/adoption/delegation#third-party-apis-firebase-aws-etc-
* https://auth0.com/blog/building-serverless-apps-with-aws-lambda/
* https://auth0.com/docs/client-auth/current/client-side-web
