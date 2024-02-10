import os
from dotenv import load_dotenv
# from dotenv import dotenv_values
import boto3
# from cognito import CognitoIdentityProviderWrapper as cogwrap
import cognito
import streamlit as st
import text_labels as tl
import time
# import re
import utils
from botocore.exceptions import ClientError
from random import randint

st.title(":orange[PDF Invoice Parser]")

with st.expander("Watch demo video"):
    st.video('https://youtu.be/kvIwnsxDgUI')


BUCKET = os.environ.get('BUCKET')

load_dotenv()

AWS_COGNITO_CLIENT_ID = os.environ.get('AWS_COGNITO_CLIENT_ID')
AWS_COGNITO_CLIENT_SECRET = os.environ.get('AWS_COGNITO_CLIENT_SECRET')
AWS_COGNITO_USER_POOL_ID = os.environ.get('AWS_COGNITO_USER_POOL_ID')

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')

CUSTOMERS_TABLE_NAME = os.environ.get('CUSTOMERS_TABLE_NAME')
REGION_NAME = os.environ.get('REGION_NAME')



# CREATE COGNITO CLIENT
cognito_idp_client = boto3.client('cognito-idp',
                              region_name = REGION_NAME,
                              aws_access_key_id = AWS_ACCESS_KEY_ID,
            aws_secret_access_key = AWS_SECRET_KEY)


# CREATE COGNITO SERVICE
cognito_service = cognito.CognitoIdentityProviderWrapper(cognito_idp_client,
                               AWS_COGNITO_USER_POOL_ID,
                               AWS_COGNITO_CLIENT_ID,
                               client_secret = AWS_COGNITO_CLIENT_SECRET)
# CREATE DYNAMODB CLIENT
dynamodb_client = boto3.client('dynamodb', 
                        region_name=REGION_NAME,
                        aws_access_key_id = AWS_ACCESS_KEY_ID,
                        aws_secret_access_key = AWS_SECRET_KEY)





if 'tokens' not in st.session_state:
    st.session_state['tokens'] = {'access_token': None, 'refresh_token': None, 'id_token': None, 'last_refresh': time.time()}

if 'sign_in_state' not in st.session_state:
    st.session_state.sign_in_state = None

if 'delete_account' not in st.session_state:
    st.session_state.delete_account = False

if 'forgot_password' not in st.session_state:   
    st.session_state.forgot_password = True
if 'reset_password' not in st.session_state:
    st.session_state.reset_password = False

# USER IN SIGNED-IN STATE
if 'tokens' in st.session_state and 'access_token' in st.session_state['tokens'] and st.session_state['tokens']['access_token'] is not None:
    # Refresh token if it's been more than 55 minutes since the last refresh
    # if time.time() - st.session_state['tokens']['last_refresh'] > 3300:
    #     # st.session_state['tokens']['access_token'] = refresh_access_token(st.session_state['tokens']['refresh_token'])
    #     # st.session_state['tokens']['last_refresh'] = time.time()
    #     st.write("Your session has expired. Please sign in again.")

    st.write("Welcome! You're logged in.")
    # st.write(list(st.session_state.keys()))


# USER NEEDS TO SIGN IN
else:
    st.write(":green[Please sign in to your account here]")

    with st.form(key='sign_in_form'):

        st.session_state.user_email = st.text_input("email address")
        st.session_state.password = st.text_input("password", 
                                type='password')

        if st.form_submit_button(label=":green[sign-in]"):

            r = utils.get_dynamodb_table_record_from_(dynamodb_client,
                                            CUSTOMERS_TABLE_NAME,
                                            st.session_state.user_email
                                        )
            
            if r:

                email_status=r[0]['email_status']['S']
                st.session_state.customer_id = r[0]['user_id']['S']
                if email_status =='CONFIRMED':

                    try:

                        access_token, refresh_token, id_token = cognito_service.sign_in_user(st.session_state.user_email, 
                                                                                                st.session_state.password)
                        
                        # store customer_id in session_state so that it won't be overwritten by other users
                        st.session_state[access_token] = {'customer_id': st.session_state.customer_id,
                                                          'user_email': st.session_state.user_email,}

                        if access_token and refresh_token and id_token:
                            st.session_state['tokens'] = {'access_token': access_token, 
                                                            'refresh_token': refresh_token, 
                                                            'id_token': id_token, 
                                                            'last_refresh': time.time()}
                            
                            st.rerun()
                        else:
                            st.error("Login failed.")
                    
                    except:
                            st.error("wrong password")
                            st.rerun()
                else:
                        
                        st.write("Please confirm your email address")
                        st.session_state.sign_in_state = 'email_confirmation_required'
            else:
                st.error("Your password or email is incorrect")
                st.rerun()
                st.stop()
                # st.rerun()   


# USER NEEDS TO CONFIRM EMAIL
if st.session_state.sign_in_state == 'email_confirmation_required':
    st.write("Please confirm your email")
    if st.button("Send confirmation code"):
        try:
            r = cognito_service.resend_confirmation(st.session_state.customer_id)
            # st.write(r)
        except ClientError as e:
            st.error(f"Error: {e.response['Error']['Message']}")

    with st.form('confirm_email_form0'):
        # st.write(tl.account_setup_dict['confirm_email_form_0'][st.session_state.selected_language])
        verification_code = st.text_input("Enter the code you received in your email")
        

        
        if st.form_submit_button("Submit"):
            try:
                r = cognito_service.confirm_user_sign_up(st.session_state.customer_id,
                                                        verification_code)
                if r:
                    
                    st.write("Success ! Your account has been activated")
                    st.session_state.sign_in_state = 'email_confirmed'
                else:
                    st.write("Resend confirmation code")
                    r = cognito_service.resend_confirmation(st.session_state.customer_id)
                    # st.write(r)
            except ClientError as e:
                st.error(f"Error: {e.response['Error']['Message']}")




# DELETE ACCOUNT (IF USER IS SIGNED IN)

# if st.session_state['tokens'] and 'access_token' in st.session_state['tokens'] and st.session_state['tokens']['access_token'] is not None:
    
#     if st.button(":red[Delete account]"):
#         st.session_state.delete_account=True
#         st.rerun()

# if st.session_state.delete_account:
#         st.write(":red[Are you sure you want to delete your account?]")
#         if st.button("Yes, delete my account"):

#             #Delete the user from the user pool
#             r = cognito_idp_client.admin_delete_user(
#                 UserPoolId=AWS_COGNITO_USER_POOL_ID,
#                 Username=st.session_state.customer_id
#             )

#             st.write("Your account has been deleted")
#             # Delete user from DynamoDB invoiceParserCustomers
#             item_key = {
#                 'user_id': {'S': st.session_state.customer_id},  # Replace with your user_id
#                 'email': {'S': st.session_state.user_email}       # Replace with your email
#             }

#             # Delete item
#             r = dynamodb_client.delete_item(
#                 TableName=CUSTOMERS_TABLE_NAME,
#                 Key=item_key
#             )

#             # Delete user folder and its objects in s3
            
#             prefix = f"accounts/{st.session_state.customer_id}"

#             paginator = utils.s3_client_BRG.get_paginator('list_objects_v2')
#             pages = paginator.paginate(Bucket=BUCKET, Prefix=prefix)

#             # Delete the objects
#             for page in pages:
#                 if 'Contents' in page:  # Check if the page has content
#                     for obj in page['Contents']:
#                         print(f"Deleting object {obj['Key']}...")
#                         utils.s3_client_BRG.delete_object(Bucket=BUCKET, Key=obj['Key'])

#             st.session_state['tokens']['access_token'] = None
#             st.session_state['tokens']['refresh_token'] = None
#             st.session_state['tokens']['id_token'] = None
#             # st.session_state.sign_up_state = None
#             # st.session_state.user_email = None
#             # st.session_state.password = None
#             # st.session_state.user_given_name = None
#             # st.session_state.user_family_name = None
#             st.session_state.delete_account = False
#             for key in st.session_state.keys():
#                 del st.session_state[key]
   
#             st.rerun()


if st.session_state['tokens'] and 'access_token' in st.session_state['tokens'] and st.session_state['tokens']['access_token'] is not None: 
    access_token = st.session_state['tokens']['access_token']
    customer_id = st.session_state[access_token]['customer_id']
    user_email = st.session_state[st.session_state['tokens']['access_token']]['user_email']
    st.sidebar.write(f"You are signed in as {user_email}")
    st.sidebar.write(f"Your Customer_ID:")
    st.sidebar.write(customer_id)
    if st.sidebar.button(':red[Logout]'):
    # st.session_state['tokens'] = {'access_token': None, 'refresh_token': None, 'id_token': None, 'last_refresh': time.time()}
    # st.session_state['tokens'] = None
        for key in st.session_state.keys():
            # st.write(key)
            del st.session_state[key]
        st.rerun()
else:
    st.sidebar.write("You are not signed in")


# USER FORGOT PASSWORD
# st.write(st.session_state['tokens'])
if st.session_state['tokens'] and 'access_token' in st.session_state['tokens'] and not st.session_state['tokens']['access_token']:
    if st.button(":red[Forgot password?]"): 
        st.session_state.forgot_password = True
        st.rerun()
    if st.session_state.forgot_password:
        with st.form('forgot_password_form'):
            st.write("Enter your email address")
            user_email = st.text_input("Email address")
            
            if st.form_submit_button(":red[Submit]"):
                try:
                    r = cognito_service.forgot_password(user_email)
                    email_exists = utils.email_exists(dynamodb_client, 
                    CUSTOMERS_TABLE_NAME,  
                    user_email)
                    st.success("If you have an account, you will receive an email with a code to reset your password.")
                    if email_exists:
                        st.session_state.reset_password = True
                except ClientError as e:
                    st.error(f"Error: {e.response['Error']['Message']}")

        if st.session_state.reset_password:
            with st.form('reset_password_form'):
                st.write("Enter the code you received in your email")
                verification_code = st.text_input("Verification code")
                new_password = st.text_input("New password", type='password')
                new_password_confirm = st.text_input("Confirm new password", type='password')
                st.caption("Your password must meet the following requirements:")
                st.caption("1. At least 8 characters in length.")
                st.caption("2. At least one uppercase letter.")
                st.caption("3. At least one lowercase letter.")
                st.caption("4. At least one number.")
                st.caption("5. At least one special character.")
                if st.form_submit_button(":red[Submit]"):
                    if new_password == new_password_confirm:
                        if utils.password_is_valid(new_password):
                            st.write("password is valid")
                            try:
                                st.write("please wait...")
                                r = cognito_service.confirm_forgot_password(user_email, verification_code, new_password)
                                if r:
                                    st.success("Your password has been reset")
                                    st.session_state.reset_password = False
                                    st.session_state.forgot_password = False
                            except ClientError as e:
                                st.error(f"Error: {e.response['Error']['Message']}")
                        else:
                            st.error("Your password is not valid. Please try again.")
                    else:
                        st.error("Your passwords do not match.")


