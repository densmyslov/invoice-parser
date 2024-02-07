import os
from dotenv import load_dotenv
from dotenv import dotenv_values
import boto3
# from cognito import CognitoIdentityProviderWrapper as cogwrap
import cognito
import streamlit as st
import text_labels as tl
# import locale_options
import re
import utils
from botocore.exceptions import ClientError
import hmac
import hashlib
import base64
import logging
import uuid


load_dotenv()

AWS_COGNITO_CLIENT_ID = os.environ.get('AWS_COGNITO_CLIENT_ID')
AWS_COGNITO_CLIENT_SECRET = os.environ.get('AWS_COGNITO_CLIENT_SECRET')
AWS_COGNITO_USER_POOL_ID = os.environ.get('AWS_COGNITO_USER_POOL_ID')

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')

CUSTOMERS_TABLE_NAME = os.environ.get('CUSTOMERS_TABLE_NAME')





# CREATE COGNITO CLIENT
cognito_idp_client = boto3.client('cognito-idp',
                              region_name = 'us-east-1',
                              aws_access_key_id = AWS_ACCESS_KEY_ID,
            aws_secret_access_key = AWS_SECRET_KEY)


# CREATE COGNITO SERVICE
cognito_service = cognito.CognitoIdentityProviderWrapper(cognito_idp_client,
                               AWS_COGNITO_USER_POOL_ID,
                               AWS_COGNITO_CLIENT_ID,
                               client_secret = AWS_COGNITO_CLIENT_SECRET)
# CREATE DYNAMODB CLIENT
dynamodb_client = boto3.client('dynamodb', 
                        region_name='us-east-1',
                        aws_access_key_id = AWS_ACCESS_KEY_ID,
                        aws_secret_access_key = AWS_SECRET_KEY)



if 'sign_up_state' not in st.session_state:
    st.session_state.sign_up_state = None
if 'email' not in st.session_state:
    st.session_state.user_email = None
if 'password' not in st.session_state:
    st.session_state.password = None
if 'user_given_name' not in st.session_state:
    st.session_state.user_given_name = None
if 'user_family_name' not in st.session_state:
    st.session_state.user_family_name = None




# SIGN UP FORM


st.write("Please fill out the form below to sign up for a new account:")
with st.form('sign_up_form'):
    # email
    st.session_state.user_email = st.text_input("email address")

    # password
    st.caption("Your password must meet the following requirements:")
    st.caption("1. At least 8 characters in length.")
    st.caption("2. At least one uppercase letter.")
    st.caption("3. At least one lowercase letter.")
    st.caption("4. At least one number.")
    st.caption("5. At least one special character.")
    st.session_state.password = st.text_input("password", type='password')

    # given_name

    st.session_state.user_given_name = st.text_input("First name (optional)")

    # family_name
    st.session_state.user_family_name = st.text_input("Last name (optional)")


    

    if st.form_submit_button("Submit"): # "Submit"
        # CHECK IF USER EXISTS IN DYNAMO DB TABLE
        # if user exists, then sign_up_state = 2
        # next options: sign in, forgot password, resend confirmation code
        email_exists = utils.email_exists(dynamodb_client, 
                                CUSTOMERS_TABLE_NAME,  
                                st.session_state.user_email)
        # st.write(st.session_state.user_email)
        
        
        if email_exists:
            st.error("Account with this email address already exists. Please sign in or reset your password.")
            st.session_state.sign_up_state = 2

        
        # check password validity and if valid, then sign up user
        else:
            if utils.password_is_valid(st.session_state.password):
                st.write("password is valid")
                try:
                    r = cognito_service.sign_up_user( 
                                                given_name=st.session_state.user_given_name,
                                                family_name = st.session_state.user_family_name,
                                                email=st.session_state.user_email,
                                                password=st.session_state.password)
                    # check if r contains user_name; if so, then sign_up_state = 1 and 
                    # put user_name in session_state
                    if re.search(r'[0-9a-zA-Z]{8}-',r):
                        st.session_state.sign_up_state = "email_confirmation_required"
                        st.session_state.customer_id = r
                        st.write("please confirm your email address")



                except ClientError as e:
                    st.error(f"Error: {e.response['Error']['Message']}")

            else:
                st.error("Your password is not valid. Please try again.")




if st.session_state.sign_up_state == "email_confirmation_required":
    st.write("Please enter the confirmation code sent to your email address.")
    with st.form('confirm_email_form'):
        verification_code = st.text_input("Confirmation code")
        if st.form_submit_button("Submit"):
            try:
                r = cognito_service.confirm_user_sign_up(st.session_state.customer_id,  
                                                            verification_code)
                if r:
                    st.session_state.sign_up_state = "email_confirmed"
                    st.session_state.customer_id = None
                    st.session_state.sign_up_state = None
                    st.session_state.user_email = None
                    st.session_state.password = None
                    st.session_state.user_given_name = None
                    st.session_state.user_family_name = None
                    st.session_state.delete_account=False
                    st.session_state.sign_in_state = None
                    # st.rerun()
                    st.success("Success ! Your account has been activated")
            except:
                st.error("Error confirming email address")

    st.write("Code incorrect")
    # st.session_state.sign_up_state=None
    if st.button('Resend confirmation code'):
        try:
            r = cognito_service.resend_confirmation(st.session_state.customer_id)
            # st.session_state.user_name = None
            # st.session_state.sign_up_state = None
            # st.session_state.user_email = None
            # st.session_state.password = None
            # st.session_state.user_given_name = None
            # st.session_state.user_family_name = None

        except ClientError as e:
            st.error(f"Error: {e.response['Error']['Message']}")
            st.session_state.sign_up_state = "email_confirmation_required"

# st.write(st.session_state.sign_up_state)


