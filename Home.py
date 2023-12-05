import os
from dotenv import load_dotenv
# from dotenv import dotenv_values
import boto3
# from cognito import CognitoIdentityProviderWrapper as cogwrap
import cognito
import streamlit as st
import text_labels as tl
# import locale_options
import re
import utils
from botocore.exceptions import ClientError

st.title("Home page")



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

languages = {
    "🇺🇸": "us",
    "🇨🇳":"cn",
    "🇪🇸":'es',
    "🇫🇷": "fr",
}
if 'selected_language' not in st.session_state:
    st.session_state.selected_language = "us"
# selected_language = st.session_state.selected_language

@st.cache_data
def get_language_idx_from_(selected_language):
    return list(languages.values()).index(selected_language)

idx = get_language_idx_from_(st.session_state.selected_language)

# selected_language = st.sidebar.radio("Select your language", 
#                                             ("🇺🇸","🇨🇳","🇪🇸","🇫🇷"),
#                                             index=idx)
# st.session_state.selected_language = languages[selected_language]

st.header("You can sign in to your account here")

if 'sign_in_state' not in st.session_state:
    st.session_state.sign_in_state = None
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'refresh_token' not in st.session_state:
    st.session_state.refresh_token = None
if 'id_token' not in st.session_state:
    st.session_state.id_token = None
if 'email' not in st.session_state:
    st.session_state.user_email = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'delete_account' not in st.session_state:
    st.session_state.delete_account = False

if st.session_state.user_email:
    st.write(f"You are signed in as {st.session_state.user_email}")
    st.write(f"Your user name is {st.session_state.user_name}")

else:


    with st.form(key='sign_in_form'):

        st.session_state.user_email = st.text_input("email address")
        st.session_state.password = st.text_input("password", 
                                type='password')

        submit_button = st.form_submit_button(label="sign-in")
        
        if submit_button:
            st.session_state.user_name = None
            st.session_state.sign_up_state = None
            # st.session_state.user_email = None
            # st.session_state.password = None
            st.session_state.user_given_name = None
            st.session_state.user_family_name = None
            st.session_state.delete_account = False

            # retrieves user's record from dynamodb CUSTOMERS_TABLE_NAME
            # from user's record, retrieves email_status, user_name
            # if email_status is CONFIRMED, then sign in user
            # if email_status is not CONFIRMED, then ask user to confirm email

            r = utils.get_dynamodb_table_record_from_(dynamodb_client,
                                                        CUSTOMERS_TABLE_NAME,
                                                        st.session_state.user_email
                                                    )
            # st.write(r)

            if r:
                email_status=r[0]['email_status']['S']
                st.session_state.user_name = r[0]['user_id']['S']
                if email_status =='CONFIRMED':
                
                    try:
                        r = cognito_service.sign_in_user(st.session_state.user_email,
                                                        st.session_state.password)

                        result = r['AuthenticationResult']
                        st.session_state.sign_in_state = 1
                        # st.session_state.access_token = result['AccessToken']
                        # st.session_state.refresh_token = result['RefreshToken']
                        # st.session_state.id_token = result['IdToken']
                        
                        # st.session_state.email = email
                        st.success(f"You are signed in as {st.session_state.user_email}")
                        st.write(f"Your user name is {st.session_state.user_name}")

                    



                    except :
                        # st.write('cognito failure to sign in')
                        st.error("wrong password")
                        st.rerun()
                else:
                    st.session_state.user_name = r[0]['user_id']['S']
                    st.write("Please confirm your email address")
                    st.session_state.sign_in_state = 'email_confirmation_required'

            else:
                st.error("Your password or email is incorrect")
                # st.error(tl.account_setup_dict['email_not_exists_error_0'][st.session_state.selected_language])
                # st.error(tl.account_setup_dict['email_not_exists_error_1'][st.session_state.selected_language])
                # st.error(tl.account_setup_dict['email_not_exists_error_2'][st.session_state.selected_language])

                # st.markdown('<a href="/my_account" target="_self">my_account</a>', unsafe_allow_html=True)
                # st.markdown('<a href="/sign-up" target="_self">sign-up</a>', unsafe_allow_html=True)
                st.session_state.sign_in_state = 0
                st.session_state.user_email=None
                st.session_state.password=None
                st.stop()
            st.rerun()

if st.session_state.sign_in_state == 'email_confirmation_required':
    st.write("Please confirm your email")
    if st.button("Send confirmation code"):
        try:
            r = cognito_service.resend_confirmation(st.session_state.user_name)
            # st.write(r)
        except ClientError as e:
            st.error(f"Error: {e.response['Error']['Message']}")

    with st.form('confirm_email_form0'):
        st.write(tl.account_setup_dict['confirm_email_form_0'][st.session_state.selected_language])
        verification_code = st.text_input(tl.account_setup_dict['confirm_email_form_1'][st.session_state.selected_language])
        

        
        if st.form_submit_button(label=tl.submit_button_label[st.session_state.selected_language]):
            try:
                r = cognito_service.confirm_user_sign_up(st.session_state.user_name, 
                                                        st.session_state.user_email, 
                                                        verification_code)
                if r:
                    
                    st.write("Success ! Your account has been activated")
                    st.session_state.sign_in_state = 'email_confirmed'
                else:
                    st.write(tl.account_setup_dict['error_message'][st.session_state.selected_language])
                    r = cognito_service.resend_confirmation(st.session_state.user_name)
                    # st.write(r)
            except ClientError as e:
                st.error(f"Error: {e.response['Error']['Message']}")


# else:
#     st.sidebar.write(f"You are signed in as {st.session_state.email}")

# st.write(st.session_state.user_name)
if st.session_state.user_email:
    
    if st.button(":red[Delete account]"):
        st.session_state.delete_account=True
        st.rerun()

if st.session_state.delete_account:
        st.write(":red[Are you sure you want to delete your account?]")
        if st.button("Yes, delete my account"):

            #Delete the user from the user pool
            r = cognito_idp_client.admin_delete_user(
                UserPoolId=AWS_COGNITO_USER_POOL_ID,
                Username=st.session_state.user_name
            )

            st.write("Your account has been deleted")
            # Delete user from DynamoDB invoiceParserCustomers
            item_key = {
                'user_id': {'S': st.session_state.user_name},  # Replace with your user_id
                'email': {'S': st.session_state.user_email}       # Replace with your email
            }

            # Delete item
            r = dynamodb_client.delete_item(
                TableName=CUSTOMERS_TABLE_NAME,
                Key=item_key
            )

            # Delete user folder and its objects in s3
            bucket_name = 'bergena-invoice-parser'
            prefix = f"accounts/{st.session_state.user_name}"

            # # First, delete all objects in the bucket
            # bucket = s3_client_BRG.Bucket(bucket_name)
            # bucket.objects.all().delete()

            # Next, delete the bucket itself

            paginator = utils.s3_client_BRG.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

            # Delete the objects
            for page in pages:
                if 'Contents' in page:  # Check if the page has content
                    for obj in page['Contents']:
                        print(f"Deleting object {obj['Key']}...")
                        utils.s3_client_BRG.delete_object(Bucket=bucket_name, Key=obj['Key'])

            st.session_state.user_name = None
            st.session_state.sign_up_state = None
            st.session_state.user_email = None
            st.session_state.password = None
            st.session_state.user_given_name = None
            st.session_state.user_family_name = None
            st.session_state.delete_account = False
   
            st.rerun()


if st.session_state.user_email:
    st.sidebar.write(f"You are signed in as {st.session_state.user_email}")
else:
    st.sidebar.write("You are not signed in")