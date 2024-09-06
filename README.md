# invoice-parser

This is a project to parse invoices submitted to the app in the form of pdf files or images, and extract the relevant information. The output is a structured file (JSON or spreadsheet) that can be used for further analysis or integration with other systems.

[click here for the demo version of the app](https://pdf-invoice-pars.streamlit.app/)  

The app  is built with:  
* frontend: Streamlit 
* backend: AWS lambdas orchestrated by AWS State machine; s3 buckets for storage; AWS Cognito and AWS DynamoDB for user management
* Parsing agent: LLMs
