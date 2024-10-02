import streamlit as st
import pandas as pd
import utils
from time import time
import json
import uuid
from datetime import datetime
from io import BytesIO
from random import randint
from time import sleep
import Home_app as home
import boto3
from botocore.exceptions import ClientError
import requests
import urllib.parse
from requests_aws4auth import AWS4Auth

# st.set_page_config(page_title='Invoice Processor', 
#                    page_icon=None, layout="wide", 
#                    initial_sidebar_state="auto", 
#                    menu_items=None)

st.title(':orange[Invoice Processor]')

try:
    access_token= st.session_state['tokens']['access_token']
    customer_id = st.session_state[access_token]['customer_id']
except:
    st.warning("Please sign in at Home page to use the app")
    st.stop()

# st.write(st.__version__)

s3_client = utils.s3_client_BRG

BUCKET = bucket = 'bergena-invoice-parser-prod'

if 'counter' not in st.session_state:
    st.session_state['counter'] = 0
if 'upload_zip_key' not in st.session_state:
    st.session_state['upload_zip_key'] = randint(0,100000)
if 'upload_pdf_key' not in st.session_state:
    st.session_state['upload_pdf_key'] = randint(100001, 100000000)
if 'summary_df' not in st.session_state:
    st.session_state['summary_df'] = pd.DataFrame()
if 'api_key_last_4' not in st.session_state:
    st.session_state['api_key_last_4'] = None

def get_random_value():
    st.session_state['upload_pdf_key'] = randint(100001, 100000000)
    st.session_state['upload_zip_key'] = randint(0,100000)

def counter_up():
    st.session_state['counter'] = randint(0,10000000)
    st.rerun()

# if st.sidebar.button("Refresh"):
#     st.session_state['counter'] +=1
#     st.rerun()

# try:
# if st.session_state['tokens']['access_token']:
st.sidebar.write(f"Signed in as {st.session_state.user_email}")

access_token = st.session_state['tokens']['access_token']
customer_id = st.session_state[access_token]['customer_id']
st.sidebar.write(f"Customer ID:")
st.sidebar.write(customer_id)



tab1, tab2, tab_invoices_from_email, tab_api_key = st.tabs(["Upload invoices",
                                                            "View and Parse Invoices", 
                                                            "Invoices from Email",
                                                            "Get API Key"])

#=================================UPLOAD INVOICES====================================================
with tab1:



    # UPLOAD ZIPPED INVOICES

    col1, col2 = st.columns(2)
    uploaded_zip_file = col1.file_uploader(":green[Upload invoices as zip file]", 
                                    type=["zip"],
                                    accept_multiple_files=False,
                                    key = st.session_state['upload_zip_key'])
    tags = col2.text_input(":green[Enter tags for uploaded zip invoices]",
                        help="e.g. 'clients';'Farmina LLC'",
                        key = 'zip_tags')
    ts = datetime.now().strftime("%Y-%m-%d")
    metadata = {'tags':tags,
                'customer_id': customer_id,
                'source':'manual_upload',
                }
    if uploaded_zip_file:
    
        if st.button(":orange[Upload zipped invoices to your cloud account]"):
            file_uid= uuid.uuid4().hex
            
            key = f"accounts/{customer_id}/zip/{file_uid}/zipped_pdfs_v1.zip"
            zip_buffer = BytesIO(uploaded_zip_file.read())
            s3_client.put_object(Bucket=BUCKET, 
                                    Key=key, 
                                    Body=zip_buffer.getvalue(),
                                    Metadata = metadata)



            zip_buffer.seek(0)
            st.session_state.upload_zip_key = str(randint(0, 100000))
            st.write(":orange[Your invoices have been uploaded to your cloud account]")  
            sleep(5) 
            counter_up()
                
            

    # UPLOAD PDF INVOICES

    col1, col2 = st.columns(2)
    uploaded_pdf_files = col1.file_uploader(":green[Upload PDF invoices]", 
                                    type=["pdf"],
                                    accept_multiple_files=True,
                                    key = st.session_state['upload_pdf_key'])
    tags = col2.text_input(":green[Enter tags for uploaded pdf invoices]",
                    help="e.g. 'clients';'Farmina LLC'",
                    key = 'pdf_tags')
    ts = datetime.now().strftime("%Y-%m-%d")
    metadata = {'tags':tags,
                'customer_id': customer_id,
                'source':'manual_upload'}

    if uploaded_pdf_files:
        # Create zip file from uploaded files
        

        if st.button(":orange[Upload PDF invoices to your cloud account]"):
            zip_buffer = utils.create_zip(uploaded_pdf_files)

            file_uid= uuid.uuid4().hex

            key = f"accounts/{customer_id}/zip/{file_uid}/zipped_pdfs_v1.zip"
            s3_client.put_object(Bucket=BUCKET, 
                                    Key=key, 
                                    Body=zip_buffer.getvalue(),
                                    Metadata = metadata)


            zip_buffer.seek(0)
            st.session_state.upload_pdf_key = randint(100000, 100000000)
            st.write(":orange[Your invoices have been uploaded to your cloud account]")  
            sleep(5) 
            counter_up()

 
#=================================PARSE INVOICES====================================================
with tab2:

    if st.button(":green[Refresh table]"):
        st.session_state['counter'] +=1
        st.rerun()

    # parser_mode = st.sidebar.radio("Parser mode",("Image","Text"), key = 'parser_mode')

    invoices_df = utils.load_invoice_df(s3_client,
                                        st.session_state[access_token]['customer_id'],
                                        counter = st.session_state['counter'])
    
    if invoices_df.empty:
        st.error("You have no invoices in your account")
    else:
        invoices_df0 = invoices_df.copy()
        q = st.sidebar.text_input("Search for invoice")
        if q:
            invoices_df0 = invoices_df0.query("search_str.str.contains(@q, case=False)")
        

        # default_cols = ['file_name','num_pages','invoice_type','source',
        #             'total_sum_check','line_items_sum_check',
        #             'time_to_complete']
        if st.session_state['customer_id'] in ['b2bb522f-bef0-4291-96d7-c5d05c61374f',
                                               'a67285fe-77eb-4d8f-a2d0-a5b0d2a25f95']:
            default_cols = ['file_name','file_uid','num_pages','invoice_type','source','model',
                    'total_sum_check','line_items_sum_check','is_parsed',
                    'time_to_complete','tags']
        selection = utils.dataframe_with_selections(invoices_df0[default_cols])
        # selection = utils.dataframe_with_selections(invoices_df0)

        

    
    #===========================INVOICE PROCESSING====================================
        col1, col2, col3 = st.columns(3)
        if 'df_to_parse' not in st.session_state:
            st.session_state['df_to_parse'] = pd.DataFrame()

        # if col0.button("Clear selection"):
        #     selection['Select'] = False
        #     st.rerun()
        #----------------------DELETE INVOICES
        if col3.button(":red[Delete selected invoices]"):
            if selection.empty:
                st.error("You have not selected any invoices")
                st.stop()
            # st.write(selection.index)
            file_names = invoices_df.loc[selection.index,'file_name'].tolist()
            file_uids = invoices_df.loc[selection.index,'file_uid'].tolist()
            
            st.write(file_names)
            
            keys_to_delete = []

            
            key = f"accounts/{st.session_state.customer_id}/file_uids_to_delete.json"
            s3_client.put_object(
                Bucket=BUCKET,
                Key=key,
                Body = json.dumps(file_uids)
            )


            invoices_df = invoices_df[~invoices_df.index.isin(selection.index)]
            key = f"accounts/{customer_id}/invoices_df.parquet"
            utils.pd_save_parquet(s3_client, invoices_df, BUCKET, key)
            with st.spinner('Wait while we delete your invoices'):
                sleep(5)
                st.success("Invoices deleted")
                sleep(2)
                counter_up()
            



        if col2.button("Show selected invoices"):
            if selection.empty:
                st.error("You have not selected any invoices")
                st.stop()

            else:

                df_to_show = invoices_df.loc[selection.index,:].copy()
                st.dataframe(df_to_show[default_cols])

                images_to_show = utils.get_images_to_show(s3_client,df_to_show,customer_id)


                for row in df_to_show.itertuples():
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

                        with st.expander(":green[Show invoice summary fields:]"):
                            show_col1, show_col2 = st.columns((1,2))
                            show_col1.dataframe(summary_df)
                            tab_names = [f"page {i+1}" for i in range(len(invoice_images))]
                            # st.write(tab_names)
                            # if page_keys:
                            with show_col2.container(height=375):
                            # with show_col2.container():
                                for ind, page_tab in enumerate(st.tabs(tab_names)):

                                        
                                        page_tab.image(images_to_show[row.file_uid][ind])
                        with st.expander(":green[Show invoice line items:]"):
                            # show_col1, show_col2 = st.columns((1,2))
                            with st.container(height=200):
                                if not line_items_df.empty:
                                    st.write(f"Sum total of line items = {line_items_df.iloc[0,-1]}")
                                    st.dataframe(line_items_df.iloc[:,1:-1],
                                                                    column_order=('Line item product IDs',
                                                                                'Line item titles',
                                                                                'Line item quantities',
                                                                                'Line item unit prices',
                                                                                'Line item total amounts'))
                                else:
                                    st.write("No line items found")
                            
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

                    # try:
                    #     with st.expander("Show raw completion"):

                    #         # st.write(page_keys)
                    #         st.write(gpt_response)
                    # except:
                    #     pass
        #----------------------PARSE INVOICES
# triggers lambda 'invPar-step-function-trigger' which in turn triggers step machine 'invPar-step-function'
        if col1.button(":orange[Parse selected invoices]"):
            if selection.empty:
                st.error("You have not selected any invoices")
                st.stop()
            else:

                # st.success('Done!')               
                
                json_for_parsing_invoices = []
                for row in invoices_df.loc[selection.index].itertuples():

                    json_for_parsing_invoices.append({'file_uid': row.file_uid,
                                                        'customer_id': customer_id
                                                        })


                    # st.write(row.file_name)

                for key_end in ['invoices_to_pdfplumber']:
                    key = f"accounts/{customer_id}/parsing/{key_end}.json"
                    s3_client.put_object(
                        Bucket=BUCKET,
                        Key=key,
                        Body = json.dumps(json_for_parsing_invoices)
                    )
                # st.write(json_for_parsing_invoices)
                
                with st.spinner('Wait while our models parse your invoices'):
                    first_uid = json_for_parsing_invoices[0]['file_uid']
                    for ind in range(45):
                        count = randint(0,100000)
                        invoices_df = utils.load_invoice_df(s3_client, customer_id, counter=count)
                        is_parsed = invoices_df.query("file_uid == @first_uid").iloc[0].is_parsed
                        print(ind, count, is_parsed)
                        if is_parsed:
                            st.balloons()
                            sleep(2)
                            st.success("Invoices parsed")
                            
                            counter_up()
                            break
                            
                        sleep(2)



#=============================================INVOICES FROM EMAIL==============================================
with tab_invoices_from_email:
    # if 'email_key' not in st.session_state:
    #     st.session_state['email_key'] = None


    
    if st.session_state.user_email:
        with st.form("Enter your email key"):
            service_email_address = st.text_input("Enter email address to retrieve invoices from",
                                                  value=st.session_state.user_email,
                                                    key = 'update_email_address')
            email_key = st.text_input("Enter your email key here",
                                      type='password',
                                      key='update_email_key')

            if st.form_submit_button("Submit"):
                if email_key:
                    r = utils.update_client_record_with_email_key(
                                            utils.CUSTOMERS_TABLE_NAME,
                                            customer_id,
                                            st.session_state.user_email,
                                            service_email_address,
                                            email_key
                                            )
                    if r['ResponseMetadata']['HTTPStatusCode']==200:
                        st.success("Your email key successfully submitted")

                    else:
                        st.error("Smth went wrong. Please try again later")
                else:
                    st.error("You did not enter your email key")

        if st.button("Delete your email key"):
            r = utils.delete_email_key_from_client_record(
                                                utils.CUSTOMERS_TABLE_NAME,
                                                customer_id,
                                                st.session_state.user_email
                                            )
            if r['ResponseMetadata']['HTTPStatusCode']==200:
                st.success("Your email key has been deleted")

            
#=============================================API_KEY==============================================
with tab_api_key:
    if st.session_state.user_email:

        with st.expander("Show last 4 symbols of your API key"):
            if st.button("Show last 4 symbols of your API key"):
                r = utils.get_dynamodb_table_record_from_(home.dynamodb_client,
                                                    home.CUSTOMERS_TABLE_NAME,
                                                    st.session_state.user_email
                                                )
                if 'api_key_last_4' in r[0]:
                    st.session_state.api_key_last_4 = r[0]['api_key_last_4']['S']
                
                    col1, col2 = st.columns(2)
                    col1.write("Last 4 symbols of your API key:")  
                    col2.write(f"...{st.session_state['api_key_last_4']}")
                else:
                    st.error("You have not generated an API key yet")

        with st.expander("Generate a new API key"):
            if st.button("Generate a new API key"):
                access_token = st.session_state['tokens']['access_token']
                client_id = st.session_state[access_token]['customer_id']
                username = st.session_state[st.session_state['tokens']['access_token']]['user_email']
                password = st.session_state.password

                session = boto3.Session(aws_access_key_id=home.AWS_ACCESS_KEY_ID, 
                                        aws_secret_access_key=home.AWS_SECRET_KEY, 
                                        region_name=home.REGION_NAME)
                credentials = session.get_credentials().get_frozen_credentials()
                service = "execute-api"
                auth = AWS4Auth(credentials.access_key, 
                                credentials.secret_key, 
                                home.REGION_NAME, 
                                service, 
                                session_token=credentials.token)

                # def calculate_secret_hash(username, client_id, client_secret):
                #     import hmac
                #     import hashlib
                #     import base64
                #     message = username + client_id
                #     dig = hmac.new(client_secret.encode('utf-8'), msg=message.encode('utf-8'), digestmod=hashlib.sha256).digest()
                #     return base64.b64encode(dig).decode()

                # def authenticate_user_and_get_jwt(username, password):
                #     try:
                #         # Calculate secret hash if the App Client has a secret
                #         secret_hash = calculate_secret_hash(username, 
                #                                             home.AWS_COGNITO_CLIENT_ID, 
                #                                             home.AWS_COGNITO_CLIENT_SECRET)

                #         # Authenticate user with username and password
                #         auth_response = home.cognito_idp_client.initiate_auth(
                #             AuthFlow='USER_PASSWORD_AUTH',
                #             AuthParameters={
                #                 'USERNAME': username,
                #                 'PASSWORD': password,
                #                 'SECRET_HASH': secret_hash  # Include the secret hash if necessary
                #             },
                #             ClientId=home.AWS_COGNITO_CLIENT_ID
                #         )

                #         # Extract the ID token (JWT)
                #         jwt_token = auth_response['AuthenticationResult']['IdToken']
                #         return jwt_token

                #     except ClientError as e:
                #         print(f"Error during authentication: {e}")
                #         return None



                # jwt_token = authenticate_user_and_get_jwt(username, password)
                # jwt_token = jwt_token.strip("'").strip()
                # encoded_jwt = urllib.parse.quote(jwt_token)
                # st.write(f"JWT Token: {jwt_token}")

                api_url = 'https://s3k5o51zxk.execute-api.us-east-1.amazonaws.com/default'
                params = {'email': st.session_state.user_email}
                response = requests.get(api_url, auth=auth, params=params)
                # headers = {
                #     "Authorization": f"Bearer {encoded_jwt}"  # Ensure correct formatting
                # }
                # st.write("Headers:", headers)

                # payload = {
                #     'email': st.session_state.user_email
                # }

                # # Trigger the Lambda function via API Gateway using POST
                # response = requests.post(api_url, headers=headers, json=json.dumps(payload))


                # Handle the response
                if response.status_code == 200:
                    st.write("Please save your API key, you won't be able to see it again:")
                    st.write("Response:", response.json())
                else:
                    st.write(f"Failed to generate API key. Status Code: {response.status_code}")
                    st.write("Error:", response.text)

                


            

 
 