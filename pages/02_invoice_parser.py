import streamlit as st
# import io
# from PIL import Image
import pandas as pd
# from time import time
# from difflib import SequenceMatcher
import utils
from time import time
import json
# import re
# import numpy as np
# import math
# import utils_parser as parser
# import requests
import uuid
from datetime import datetime
from io import BytesIO
# from collections import defaultdict
# import PyPDF2
from random import randint
from zipfile import ZipFile, ZIP_DEFLATED
from time import sleep


st.set_page_config(page_title='PDF Invoice Parser', 
                   page_icon=None, layout="wide", 
                   initial_sidebar_state="auto", 
                   menu_items=None)

try:
    x= st.session_state['tokens']['access_token']
except:
    st.warning("Please sign in at Home page to use the app")
    st.stop()

st.write(st.__version__)

s3_client = utils.s3_client_BRG

BUCKET = bucket = 'bergena-invoice-parser-prod'

if 'counter' not in st.session_state:
    st.session_state['counter'] = 0
if 'upload_zip_key' not in st.session_state:
    st.session_state['upload_zip_key'] = randint(0,100000)
if 'upload_pdf_key' not in st.session_state:
    st.session_state['upload_pdf_key'] = randint(100001, 100000000)

def get_random_value():
    st.session_state['upload_pdf_key'] = randint(100001, 100000000)
    st.session_state['upload_zip_key'] = randint(0,100000)

def counter_up():
    st.session_state['counter'] += 1
    st.rerun()

if st.sidebar.button("Refresh"):
    st.session_state['counter'] +=1
    st.rerun()

# try:
# if st.session_state['tokens']['access_token']:
st.sidebar.write(f"Signed in as {st.session_state.user_email}")

access_token = st.session_state['tokens']['access_token']
customer_id = st.session_state[access_token]['customer_id']
st.sidebar.write(f"Customer ID:")
st.sidebar.write(customer_id)

st.title(":orange[PDF Invoice Parser]")
tab1, tab2 = st.tabs(["Upload invoices","View and Parse Invoices"])

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
                'customer_id': customer_id}
    if uploaded_zip_file:
    
        if st.button(":orange[Upload zipped invoices to your cloud account]"):
            file_uid= uuid.uuid4().hex
            
            key = f"accounts/{customer_id}/zip/{file_uid}/zipped_pdfs_v1.zip"
            zip_buffer = BytesIO(uploaded_zip_file.read())
            s3_client.put_object(Bucket=BUCKET, 
                                    Key=key, 
                                    Body=zip_buffer.getvalue(),
                                    Metadata = metadata)
            st.write(f"put object to {key}")


            # zip_buffer.seek(0)
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
                'customer_id': customer_id}
    def create_zip(uploaded_files):
        # In-memory buffer to store the zip file
        zip_buffer = BytesIO()
        
        # Create a zip file in the buffer
        with ZipFile(zip_buffer, "a", ZIP_DEFLATED, False) as zip_file:
            for file in uploaded_files:
                # Read the content of the file
                file_content = file.getvalue()
                # Add file to the zip file
                zip_file.writestr(file.name, file_content)

        # Go to the beginning of the buffer
        zip_buffer.seek(0)
        return zip_buffer
    if uploaded_pdf_files:
        # Create zip file from uploaded files
        

        if st.button(":orange[Upload PDF invoices to your cloud account]"):
            zip_buffer = create_zip(uploaded_pdf_files)

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

    

    # parser_mode = st.sidebar.radio("Parser mode",("Image","Text"), key = 'parser_mode')

    invoices_df = utils.load_invoice_df(s3_client,
                                        st.session_state[access_token]['customer_id'],
                                        counter = st.session_state['counter'])
    if invoices_df.empty:
        st.error("You have no invoices in your account")
    else:
        default_cols = ['file_name','file_uid','is_parsed','model',
                        'total_sum_check','line_items_sum_check','time_to_complete',
                        'source','completion']
        selection = utils.dataframe_with_selections(invoices_df)
        # selection = utils.dataframe_with_selections(invoices_df)
    
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
            st.write(selection.index)
            file_uids = invoices_df.loc[selection.index,'file_uid'].tolist()
            st.write(file_uids)

            for file_uid in file_uids:
                prefix = f"accounts/{customer_id}/"
                latest_ts, keys_to_delete = utils.get_latest_keys_from_(s3_client,
                                                        BUCKET, 
                                                        prefix, 
                                                        time_interval=360, 
                                                        time_unit='day', 
                                                        additional_str=file_uid,
                                                        zipped=False)
                for key in keys_to_delete:
                    s3_client.delete_object(Bucket=bucket, Key=key)
            invoices_df = invoices_df[~invoices_df.index.isin(selection.index)]
            key = f"accounts/{customer_id}/invoices_df.parquet"
            utils.pd_save_parquet(s3_client, invoices_df, bucket, key)
            st.success("Invoices deleted")
            st.session_state['counter'] += 1
            st.rerun()
        #----------------------SHOW INVOICES

        if col2.button("Show selected invoices"):
            if selection.empty:
                st.error("You have not selected any invoices")
                st.stop()
            else:
                # images = []
                cols_to_show=['date',
                            'file_name',
                            'invoice_type',
                            'num_pages',
                            'is_parsed',
                            'completion',
                            'source',
                            'pages_used_for_parsing',
                        'file_uid']

                df_to_show = invoices_df.loc[selection.index,:].copy()
                st.dataframe(df_to_show)
                # df_to_show['gpt_response'] = None
                for row in df_to_show.itertuples():
                    prefix = f"accounts/{customer_id}/images/{row.file_uid}/page"
                    # st.write(prefix)
                    page_keys_zip = utils.get_latest_keys_from_(s3_client,
                                                        bucket, 
                                                        prefix, 
                                                        time_interval=360, 
                                                        time_unit='day', 
                                                        additional_str='',
                                                        zipped=True)
                    
                    page_keys_df = pd.DataFrame(page_keys_zip, columns=['ts','page_key'])
                    page_keys_df['page_num'] = page_keys_df['page_key'].str.split('_').str[-1].str.split('.').str[0]
                    page_keys_df['page_num'] = page_keys_df['page_num'].astype('int')
                    page_keys_df.sort_values('page_num', inplace=True)
                    invoice_images = []
                    
                    for page_image_key in page_keys_df['page_key']:
                        page_image = utils.download_image(s3_client,
                                                bucket, 
                                                page_image_key)
                        invoice_images.append(page_image)

                
                    st.markdown(f"### :green[{row.file_name}]")
                    if row.is_parsed:
                        # try:
                        # gpt_response=  json.loads(row.completion)['choices'][0]['message']['content']
                            # st.write(row.completion)
                        gpt_response = json.loads(row.completion)
                        # st.write(gpt_response)
                        invoice_summary_df = pd.DataFrame.from_dict(gpt_response['Summary'],
                                                                    orient='index')
                        line_items = gpt_response['Line items']


                        line_items_df = pd.DataFrame(line_items)

                        with st.expander(":green[Show invoice summary fields:]"):
                            show_col1, show_col2 = st.columns((1,2))
                            summary_edited = show_col1.data_editor(invoice_summary_df,
                                                            num_rows="dynamic")
                            tab_names = [f"page {i+1}" for i in range(len(page_keys_df))]
                            # if page_keys:
                            # with show_col2.container(height=375):
                            with show_col2.container():
                                for ind, page_tab in enumerate(st.tabs(tab_names)):

                                        
                                        page_tab.image(invoice_images[ind])
                        with st.expander(":green[Show invoice line items:]"):
                            # show_col1, show_col2 = st.columns((1,2))
                            # with st.container(height=300):
                            with st.container():
                                st.write(f"Sum total of line items = {line_items_df.iloc[0,-1]}")
                                st.dataframe(line_items_df.iloc[:,1:-1],
                                                                column_order=('Line item product IDs',
                                                                            'Line item titles',
                                                                            'Line item quantities',
                                                                            'Line item unit prices',
                                                                            'Line item total amounts'))
                            
                            # if page_keys:
                            # with st.container(height=375):
                            with st.container():
                                tab_names = [f"page {i+1}" for i in range(len(page_keys_df))]
                                for ind, page_tab in enumerate(st.tabs(tab_names)):

                                        page_tab.image(invoice_images[ind])

                    else:
                        # SHOW PAGE IMAGES INSIDE PAGE TABS
                        with st.expander(":green[Show invoice pages:]"):
                            tab_names = [f"page {i+1}" for i in range(len(page_keys_df))]
                            # try:
                            for ind, page_tab in enumerate(st.tabs(tab_names)):
                                page_tab.image(invoice_images[ind])

                    try:
                        with st.expander("Show raw completion"):

                            # st.write(page_keys)
                            st.write(gpt_response)
                    except:
                        pass
        #----------------------PARSE INVOICES
# triggers lambda 'invPar-step-function-trigger' which in turn triggers step machine 'invPar-step-function'
        if col1.button(":orange[Parse selected invoices]"):
            if selection.empty:
                st.error("You have not selected any invoices")
                st.stop()
            else:                   
                
                json_for_parsing_invoices = []
                for row in invoices_df.loc[selection.index].itertuples():

                    json_for_parsing_invoices.append({'file_uid': row.file_uid,
                                                        'customer_id': customer_id
                                                        })


                    st.write(row.file_name)

                for key_end in ['invoices_to_pdfplumber']:
                    key = f"accounts/{customer_id}/parsing/{key_end}.json"
                    s3_client.put_object(
                        Bucket=BUCKET,
                        Key=key,
                        Body = json.dumps(json_for_parsing_invoices)
                    )
                    st.write(key)
                st.write(f"Sent for parsing. Click on 'Refresh' to see the results. It may take up to 5 minutes for results to appear")





            

 
 