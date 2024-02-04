import streamlit as st
import io
from PIL import Image
import pandas as pd
from time import time
# from difflib import SequenceMatcher
import utils
from time import time
import json
import re
import numpy as np
# import math
import utils_parser as parser
import openai
# import requests
import uuid
from datetime import datetime
from io import BytesIO, StringIO
from collections import defaultdict
import PyPDF2
from random import randint

# from joblib import Parallel, delayed

BUCKET = bucket = 'bergena-invoice-parser-prod'

if 'sign_in_state' not in st.session_state:
    st.session_state['sign_in_state'] = 0
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = None

if not st.session_state.user_email:
    st.warning("Please sign in at Home page to use the app")

if st.session_state.user_email:
    st.sidebar.write(f"Signed in as {st.session_state.user_email}")
    # st.sidebar.write(st.session_state.user_name)

    s3_client = utils.s3_client_BRG
    # textract_client = utils.textract_client
    rekognition_client = utils.rekognition_client
    openai_key = utils.OPENAI_KEY



    if 'counter' not in st.session_state:
        st.session_state['counter'] = 0
    if 'gpt_response' not in st.session_state:
        st.session_state['gpt_response'] = None
    if 'invoice_summary_df' not in st.session_state:
        st.session_state['invoice_summary_df'] = pd.DataFrame()
    if 'line_items_df' not in st.session_state:
        st.session_state['line_items_df'] = pd.DataFrame()
    if 'df_to_download' not in st.session_state:
        st.session_state['df_to_download'] = pd.DataFrame()
    if 'parsing_time' not in st.session_state:
        st.session_state['parsing_time'] = None
    if 'bank_statement' not in st.session_state:
        st.session_state['bank_statement'] = None
    if 'start_parsing_time' not in st.session_state:
        st.session_state['start_parsing_time'] = None
    if 'password_entered' not in st.session_state:
        st.session_state['password_entered'] = None
    if 'upload_key' not in st.session_state:
        st.session_state['upload_key'] = 0

    def counter_up():
        st.session_state['counter'] += 1
        return st.session_state['counter']

    if st.sidebar.button("Refresh"):
        st.session_state['counter'] +=1
        st.rerun()
    st.sidebar.write(st.session_state.user_name)



    st.title(":orange[PDF Invoice Parser]")
    tab1, tab2 = st.tabs(["Upload invoices","Parse Invoices"])

    #=================================UPLOAD INVOICES====================================================
    with tab1:



        invoices_df = utils.load_invoice_df(s3_client, counter = st.session_state['counter'])

        col1, col2 = st.columns(2)
        uploaded_files = col1.file_uploader("Upload pdf invoices", 
                                        type=["pdf", "zip"],
                                        accept_multiple_files=True,
                                        key = st.session_state['upload_key'])
        tags = col2.text_input("Enter tags for uploaded invoices",
                               help="e.g. 'clients';'Farmina LLC'",
                               key = 'tags')

        combined_images = []
        if uploaded_files is not None:
            ts = datetime.now().strftime("%Y-%m-%d")
            metadata = {'tags':tags,
                        'customer_id': st.session_state.user_name}

            for uploaded_file in uploaded_files:
                file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type}
                file_uid= uuid.uuid4().hex

                if uploaded_file.type == "application/zip":
                    if st.button("Upload invoices to your cloud account",on_click=counter_up):


                        key = f"accounts/{st.session_state.user_name}/zip/{file_uid}/zipped_pdfs_v1.zip"
                        zip_buffer = BytesIO(uploaded_file.read())
                        s3_client.put_object(Bucket=BUCKET, 
                                             Key=key, 
                                             Body=zip_buffer.getvalue(),
                                             Metadata = metadata)


                        zip_buffer.seek(0)
                        st.session_state.upload_key = str(randint(1000, 100000000))
                        counter_up()    
                        st.rerun()

                if uploaded_file.type == "application/pdf":
                    pdf_buffer = BytesIO(uploaded_file.read())
                    pdf_buffer.seek(0)
                    # Convert PDF to a list of images
                    # images = parser.pdf_to_images(uploaded_file)
                    images = parser.pdf_to_images(pdf_buffer)
                    combined_image = parser.combine_images(images, direction='horizontal')
                    pdf_buffer.seek(0)
                    extracted_words,pages_used_for_parsing = parser.extract_words_from_pdf(pdf_buffer,
                                                                    max_words_per_page=1700)
                    
                    combined_images.append((

                                            file_uid, 
                                            extracted_words,
                                            uploaded_file.name, 
                                            uploaded_file.type,
                                            pages_used_for_parsing,
                                            combined_image,
                                            len(images),
                                            images,
                                            # pdf_pages
                                            ))

                    
                    
            # st.write(f":blue[number of invoices:{len(combined_images)}]")
            image_data = []
            if len(combined_images)>0:
                with st.expander("Show invoices"):
                    for _,_,file_name,_,pages_used_for_parsing, combined_image,_ , invoice_images in combined_images:
                        st.write(f"file name: :blue[{file_name}]")
                        st.write(f"pages to be used for parsing: {','.join([str(i+1) for i in pages_used_for_parsing])}")                      
                        st.image(combined_image, use_column_width=True)
                
                if st.button("Upload invoices to your cloud account",on_click=counter_up):
                    ts = datetime.now().strftime("%Y-%m-%d")



                    for ind, uploaded_file in enumerate(uploaded_files):
                        st.write(uploaded_file.name)
                        (file_uid,extracted_words, file_name,file_type, 
                         pages_used_for_parsing, combined_image, num_pages, 
                         invoice_images) = combined_images[ind]
                        st.write(file_uid, file_name)


                    

                        # UPLOAD COMBINED IMAGE TO S3


                        combined_image_key = f"accounts/{st.session_state.user_name}/images/{file_uid}.jpg"
                        buffer = BytesIO()
                        combined_image.save(buffer, format='jpeg')
                        r = s3_client.put_object(Bucket=BUCKET, Key=combined_image_key, Body=buffer.getvalue(), ContentType='image/jpeg')
                        
                        # SAVE IMAGES OF INDIVIDUAL PAGES TO S3
                        for page_num, image in enumerate(invoice_images):

                            image_page_key = f"accounts/{st.session_state.user_name}/images/{file_uid}/pages/page_{page_num}.jpg"
                            buffer = BytesIO()
                            image.save(buffer, format='jpeg')
                            r = s3_client.put_object(Bucket=bucket, Key=image_page_key, Body=buffer.getvalue(), ContentType='image/jpeg')
                        

                        
                        # SAVE ORIGINAL PDF INVOICE TO S3

                        pdf_key = f"accounts/{st.session_state.user_name}/pdfs/{file_uid}.pdf"
                        uploaded_file.seek(0)
                        pdf_buffer = BytesIO(uploaded_file.read())
                        r = s3_client.put_object(
                                                Bucket=BUCKET, 
                                                Key=pdf_key,
                                                Body=pdf_buffer.getvalue())
                        is_parsed = False
                        source='manual'
                        image_data.append((file_uid,extracted_words,file_name,file_type, 
                                            ts, combined_image_key, pdf_key, is_parsed,source,
                                            pages_used_for_parsing, num_pages))
                        
                        # SAVE INDIVIDUAL PDF PAGES TO S3   

                        pdf_key = f"accounts/{st.session_state.user_name}/pdfs/{file_uid}.pdf"
                        obj = s3_client.get_object(Bucket=BUCKET, Key=pdf_key)
                        buffer = BytesIO(obj['Body'].read())
                        reader = PyPDF2.PdfReader(buffer)
                        for page_num in range(len(reader.pages)):
                            print(page_num)
                            writer = PyPDF2.PdfWriter()
                            writer.add_page(reader.pages[page_num])

                            # Create a BytesIO object for the current page
                            page_buffer = BytesIO()
                            writer.write(page_buffer)
                            pdf_page_key = f"accounts/{st.session_state.user_name}/pdfs/{file_uid}/pages/page_{page_num}.pdf"
                            buffer.seek(0) 
                            page_buffer.seek(0)
                            r = s3_client.put_object(Bucket=bucket, Key=pdf_page_key, Body=page_buffer.getvalue())
                    

                    # UPDATE INVOICE_DF WITH NEW INVOICES AND SAVE TO S3
                    if len(image_data) > 0:
                        df = pd.DataFrame(image_data, 
                                        columns=['file_uid',
                                                'extracted_words',
                                                'file_name','file_type','date',
                                                'image_key','pdf_key','is_parsed',
                                                'source','pages_used_for_parsing','num_pages'])
                        for col_name in ['prompt',
                                         'completion',
                                         'time_to_complete',
                                         'model',
                                         'total_sum_check',
                                         'line_items_sum_check']:
                            df[col_name] = None
                        # 'image' if extracted_words ==[] else 'text'
                        df['invoice_type'] = df['extracted_words'].apply(lambda x: 
                                                                         'image' if len(x)==0 
                                                                         else 'text')

                        key = f"accounts/{st.session_state.user_name}/invoices_df.parquet"
                        invoices_df = pd.concat([invoices_df, df],
                                                ignore_index=True)
                        utils.pd_save_parquet(s3_client, invoices_df, bucket, key)
                        if len(image_data)==1:
                            st.success("Your invoice has been uploaded :smile:")
                        else:
                            st.success("Your invoices have been uploaded :smile:")
                    
                    st.session_state.upload_key = str(randint(1000, 100000000))
                    counter_up()    
                    st.rerun()

    #=================================PARSE INVOICES====================================================
    with tab2:

        

        # parser_mode = st.sidebar.radio("Parser mode",("Image","Text"), key = 'parser_mode')

        invoices_df = utils.load_invoice_df(s3_client, counter = st.session_state['counter'])
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
                    prefix = f"accounts/{st.session_state.user_name}/"
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
                key = f"accounts/{st.session_state.user_name}/invoices_df.parquet"
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
                        st.markdown(f"### :green[{row.file_name}]")
                        if row.is_parsed:
                            # try:
                            # gpt_response=  json.loads(row.completion)['choices'][0]['message']['content']
                                # st.write(row.completion)
                                gpt_response = json.loads(row.completion)
                                # st.write(gpt_response)
                                invoice_summary_df = pd.DataFrame.from_dict(gpt_response['Summary'],
                                                                            orient='index').T
                                line_items = gpt_response['Line items']


                                line_items_df = pd.DataFrame(line_items)
                                # st.write(line_items_df['Item total price'].sum())
                                
                            
                                # invoice_summary_df = parser.get_summary_df(gpt_response)

                                st.dataframe(invoice_summary_df)
                                # line_items_df = parser.get_line_items_df(gpt_response)
                                # st.write(line_items_df['Item total price'].sum())
                                st.dataframe(line_items_df)

                            # except:
                            #     st.write("Sorry, smth went wrong")

                        prefix = f"accounts/{st.session_state.user_name}/images/{row.file_uid}/page"
                        # st.write(prefix)
                        _, page_keys = utils.get_latest_keys_from_(s3_client,
                                                                bucket, 
                                                                prefix, 
                                                                time_interval=360, 
                                                                time_unit='day', 
                                                                additional_str='',
                                                                zipped=False)
                        
                        # SHOW PAGE IMAGES INSIDE PAGE TABS
                        with st.expander(":green[Show invoice pages:]"):
                            tab_names = [f"page {i+1}" for i in range(len(page_keys))]
                            if page_keys:
                                for ind, page_tab in enumerate(st.tabs(tab_names)):
                                    with page_tab:
                                        page_image_key = page_keys[ind]
                                        page_image = utils.download_image(s3_client,
                                                bucket, 
                                                page_image_key)
                                        st.image(page_image)
                            else:
                                st.error("No pages to show")
                        with st.expander("Show invoice text:"):
                            try:
                                text_key = f"accounts/{st.session_state.user_name}/jsons/{row.file_uid}/invoice_text.json"
                                text_json=json.loads(s3_client.get_object(Bucket=bucket, Key=text_key)['Body'].read().decode('utf-8'))
                                invoice_lines = text_json['constructed_text']
                                st.write(invoice_lines)
                            except:
                                st.write("Image-type invoice")
                        try:
                            with st.expander("Show raw completion"):

                                st.write(page_keys)
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
                                                            'customer_id': st.session_state.user_name
                                                            })


                        st.write(row.file_name)
                                            # key = f"accounts/{st.session_state.user_name}/parsing/json_for_parsing.json"
                    
                    # send_to_pdfplumber = json.dumps(json_for_parsing_invoices)
                    # st.write(send_to_pdfplumber)
                    for key_end in ['invoices_to_pdfplumber']:
                        key = f"accounts/{st.session_state.user_name}/parsing/{key_end}.json"
                        s3_client.put_object(
                            Bucket=BUCKET,
                            Key=key,
                            Body = json.dumps(json_for_parsing_invoices)
                        )
                        st.write(key)
                    st.write(f"Sent for parsing. Click on 'Refresh' to see the results. It may take up to 5 minutes for results to appear")




            

 
 