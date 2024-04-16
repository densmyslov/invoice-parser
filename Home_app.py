import os
from dotenv import load_dotenv
import boto3
import cognito
import streamlit as st
import time
import utils
from botocore.exceptions import ClientError
from random import randint
import uuid
from time import sleep
from random import randint
import pandas as pd
import json


BUCKET = os.environ.get('BUCKET')
s3_client = utils.s3_client_BRG

# BUCKET = bucket = 'bergena-invoice-parser-prod'

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
if 'upload_pdf_key1' not in st.session_state:
    st.session_state.upload_pdf_key1 = randint(0,1000000000)
if 'demo_session_id' not in st.session_state:
    st.session_state.demo_session_id = None
if 'counter' not in st.session_state:
    st.session_state['counter'] = 0



def counter_up():
    st.session_state['counter'] = randint(0,10000000)
    st.rerun()

st.title(":orange[Invoice Processor]")

with st.expander(":green[Watch demo video]"):
    st.video('https://youtu.be/zVXccGBUs_s')

with st.expander(":green[Test app without signing in]"):
    st.caption(""":orange[You can test the app without signing in. 
             However, you will not be able to save your work or process multiple invoices at a time.
             Please sign in to enjoy all the features.]""")

#DEMO:  USER IS NOT SIGNED IN
#================================================================================================
    tab1, tab2 = st.tabs(["Upload pdf invoice","View processed invoice"])
    customer_id = 'dcc6f7bf-1cf8-478a-b054-091769e488b3' # nearest@nearestllc.com

    # UPLOAD/PARSE PDF INVOICE
    #-------------------------------------------------------------------------------------------
    # 'demo' is added to an uploaded file name to differentiate it from a file uploaded by a signed-in user
    # file_id is replaced by st.session_state.demo_session_id
    with tab1:
        col1, col2 = st.columns(2)
        
        uploaded_pdf_files = col1.file_uploader(":green[Upload PDF invoice]", 
                                type=["pdf"],
                                accept_multiple_files=False,
                                key = st.session_state['upload_pdf_key1'])
        if uploaded_pdf_files:
            if st.button(":orange[Upload and Process PDF invoice]"):
        
                zip_buffer = utils.create_zip([uploaded_pdf_files])

                st.session_state.demo_session_id = uuid.uuid4().hex
                # st.write(st.session_state.demo_session_id)
                
                key = f"accounts/{customer_id}/zip/{st.session_state.demo_session_id}/zipped_pdfs_v1.zip"
                # st.write(key)
                
                metadata = {'customer_id': customer_id}
                s3_client.put_object(Bucket=BUCKET, 
                                            Key=key, 
                                            Body=zip_buffer.getvalue(),
                                            Metadata = metadata)


                zip_buffer.seek(0)
                st.session_state.upload_pdf_key = randint(100000, 100000000)
            # if st.session_state.demo_session_id:
                with st.spinner('Wait while our model processes your invoice'):
                    # first_uid = json_for_parsing_invoices[0]['file_uid']
                    for ind in range(15):
                        st.write(ind)
                        count = randint(0,100000)
                        invoices_df = utils.load_invoice_df(s3_client, customer_id, counter=count)
                        st.write(invoices_df.shape)
                        file_uid = st.session_state.demo_session_id
                        if not invoices_df.query("zip_file_uid == @file_uid").empty:
                            is_parsed = invoices_df.query("zip_file_uid == @file_uid").iloc[0].is_parsed
                            print(ind, count, is_parsed)
                            if is_parsed:
                                st.balloons()
                                sleep(2)
                                st.success("Invoices parsed")
                                
                                # counter_up()
                                
                                # st.session_state.demo_session_id = None
                                counter_up()
                                st.rerun()
                                break
                        # else:
                        #     if invoices_df.query("zip_file_uid == @file_uid").empty:
                        #         st.write("empty")
                            
                        sleep(3)
                    # st.write(":orange[Your invoices have been uploaded to your cloud account]")  
                    # sleep(5) 
            # st.session_state.demo_session_id = None
            # counter_up()


    with tab2:
        invoices_df = pd.DataFrame()
        zip_file_id = st.session_state.demo_session_id
        # if st.button(":green[Refresh table]"):
        #     st.session_state['counter'] +=1 
        #     st.rerun()
        if zip_file_id:
            invoices_df = utils.load_invoice_df(s3_client,
                                    customer_id,
                                    counter = st.session_state['counter'])
            invoices_df = invoices_df.query("zip_file_uid==@zip_file_id")
    
        if invoices_df.empty:
            st.error("Please upload an invoice first")
        else:
            
            default_cols = ['file_name','zip_file_uid','file_uid','num_pages','invoice_type','model',
                        'total_sum_check','line_items_sum_check','is_parsed',
                        'time_to_complete']
            # selection = utils.dataframe_with_selections(invoices_df[default_cols])
            images_to_show = utils.get_images_to_show(s3_client,invoices_df,customer_id)
            for row in invoices_df.itertuples():
                    # st.session_state['summary_df'][row[0]] = pd.DataFrame()
                    invoice_images = images_to_show[row.file_uid]

                
                    st.markdown(f"### :green[{row.file_name}]")
                    if row.is_parsed:
                        # try:
                        # gpt_response=  json.loads(row.completion)['choices'][0]['message']['content']
                            # st.write(row.completion)
                        gpt_response = json.loads(row.completion)
                        # st.write(gpt_response)
                        summary_df = pd.DataFrame.from_dict(gpt_response['Summary'],
                                                                    orient='index')
                        summary_df.columns = ['Value']
                        line_items = gpt_response['Line items']


                        line_items_df = pd.DataFrame(line_items)

                        excel_data = utils.to_excel(summary_df.reset_index(), 
                                              line_items_df.reset_index())

                        st.download_button(
                                            label=":blue[Download as Excel]",
                                            data=excel_data,
                                            file_name=f"{row.file_name}.xlsx",
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key = f"download_{row.file_uid}")

                        with st.container():
                            st.write(":green[Show invoice summary fields:]")
                            show_col1, show_col2 = st.columns((1,2))
                            show_col1.dataframe(summary_df)
                            tab_names = [f"page {i+1}" for i in range(len(invoice_images))]
                            # st.write(tab_names)
                            # if page_keys:
                            with show_col2.container(height=375):
                            # with show_col2.container():
                                for ind, page_tab in enumerate(st.tabs(tab_names)):

                                            
                                            page_tab.image(images_to_show[row.file_uid][ind])
                        # with st.expander(":green[Show invoice line items:]"):
                            # show_col1, show_col2 = st.columns((1,2))
                        with st.container(height=500):
                        # with st.container():
                            st.write(f"Sum total of line items = {line_items_df.iloc[0,-1]}")
                            st.dataframe(line_items_df.iloc[:,1:-1],
                                                            column_order=('Line item product IDs',
                                                                        'Line item titles',
                                                                        'Line item quantities',
                                                                        'Line item unit prices',
                                                                        'Line item total amounts'))
                            
                            # if page_keys:
                            with st.container(height=375):
                            # with st.container():
                                tab_names = [f"page {i+1}" for i in range(len(invoice_images))]
                                for ind, page_tab in enumerate(st.tabs(tab_names)):

                                        page_tab.image(invoice_images[ind])

                    else:
                        # SHOW PAGE IMAGES INSIDE PAGE TABS
                        with st.expander(":green[Show invoice pages:]"):
                            tab_names = [f"page {i+1}" for i in range(len(invoice_images))]
                            # try:
                            for ind, page_tab in enumerate(st.tabs(tab_names)):
                                page_tab.image(invoice_images[ind])



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
    # with st.expander(":green[Expand to sign in]"):
        st.sidebar.write(":green[Please sign in to your account here]")

        with st.sidebar.form(key='sign_in_form'):

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
                                st.sidebar.error("Login failed.")
                        
                        except:
                                st.sidebar.error("wrong password")
                                st.rerun()
                    else:
                            
                            st.sidebar.write("Please confirm your email address")
                            st.session_state.sign_in_state = 'email_confirmation_required'
                else:
                    st.sidebar.error("Your password or email is incorrect")
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
    if st.sidebar.button(":red[Forgot password?]"): 
        st.session_state.forgot_password = True
        st.rerun()
    if st.session_state.forgot_password:
        with st.sidebar.form('forgot_password_form'):
            st.sidebar.write("Enter your email address")
            user_email = st.sidebar.text_input("Email address")
            
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
                st.sidebar.write("Enter the code you received in your email")
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
                                    st.rerun()
                            except ClientError as e:
                                st.error(f"Error: {e.response['Error']['Message']}")
                        else:
                            st.error("Your password is not valid. Please try again.")
                    else:
                        st.error("Your passwords do not match.")



