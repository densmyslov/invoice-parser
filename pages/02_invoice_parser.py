import streamlit as st
import fitz
import io
from PIL import Image
import pandas as pd
from time import time
from difflib import SequenceMatcher
import utils
from time import time
import pdfplumber
import json
import re
import numpy as np
import math
import utils_parser as parser
import openai
import requests
import uuid
from datetime import datetime
from io import BytesIO, StringIO

if 'sign_in_state' not in st.session_state:
    st.session_state['sign_in_state'] = 0
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

if st.session_state.user_email:
    st.sidebar.write(f"Signed in as {st.session_state.user_email}")

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
    def counter_up():
        st.session_state['counter'] += 1
        return st.session_state['counter']

    if st.sidebar.button("Reset"):
        st.session_state['counter'] = 0



    st.title(":orange[PDF Invoice Parser]")
    tab1, tab2 = st.tabs(["Upload invoices","View your invoices"])
    with tab1:

        col1, col2 = st.columns(2)
        uploaded_files = col1.file_uploader("Upload pdf invoices", 
                                        type=["pdf", "png", "jpg", "jpeg"],
                                        accept_multiple_files=True)
        parser_type = 'gpt'
        def load_invoice_df(counter=None):
            bucket = 'bergena-invoice-parser'
            key = f"accounts/{st.session_state.user_name}/invoice_df.parquet"
            try:
                invoice_df = utils.pd_read_parquet(s3_client, bucket, key)
            except:
                invoice_df = pd.DataFrame()
            return invoice_df


        invoice_df = load_invoice_df(counter = st.session_state['counter'])

        combined_images = []
        if uploaded_files is not None:
            ts = datetime.now().strftime("%Y-%m-%d")
            for uploaded_file in uploaded_files:
                file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type}
                file_uid= uuid.uuid4().hex
                if uploaded_file.type == "application/pdf":
                    # Convert PDF to a list of images
                    images = parser.pdf_to_images(uploaded_file)
                    combined_image = parser.combine_images(images, direction='horizontal')
                    extracted_words = parser.extract_words_from_pdf(uploaded_file)
                    combined_images.append((file_uid, 
                                            extracted_words,
                                            uploaded_file.name, 
                                            uploaded_file.type, 
                                            combined_image))
                    
            st.write(len(combined_images))
            image_data = []
            if len(combined_images)>0:
                with st.expander("Show invoices"):
                    for _,_,_,_, combined_image in combined_images:
                        st.image(combined_image, use_column_width=True)
                if st.button("Upload invoices to your cloud account",on_click=counter_up):
                    
                    for file_uuid,extracted_words, file_name,file_type, combined_image in combined_images:
                        bucket = 'bergena-invoice-parser'
                        image_key = f"accounts/{st.session_state.user_name}/images/{ts}/{file_uid}.jpg"
                        buffer = BytesIO()
                        combined_image.save(buffer, format='jpeg')
                        r = s3_client.put_object(Bucket=bucket, Key=image_key, Body=buffer.getvalue(), ContentType='image/jpeg')
                        
                        pdf_key = f"accounts/{st.session_state.user_name}/pdfs/{ts}/{file_uid}.pdf"
                        r = s3_client.put_object(Bucket=bucket, Key=pdf_key, Body=uploaded_file, ContentType='application/pdf')
                        image_data.append((file_uuid,extracted_words,file_name,file_type, ts, image_key, pdf_key))
                        image_url = f"https://{bucket}.s3.amazonaws.com/{image_key}"

                        image_html = f"""
                                <!DOCTYPE html>
                                <html lang="en">
                                <head>
                                    <meta charset="UTF-8">
                                    <title>{uploaded_file.name}</title>
                                </head>
                                <body>
                                    <img src="{image_url}" alt="{uploaded_file.name}">
                                </body>
                                </html>
                                """
                        buffer= StringIO(image_html)
                        html_key = f"accounts/{st.session_state.user_name}/htmls/{ts}/{file_uid}.html"
                        s3_client.put_object(
                            Bucket=bucket,
                            Key=html_key,
                            Body = buffer.getvalue(),
                            ContentType = 'text/html'
                        )
            
                if len(image_data) > 0:
                    df = pd.DataFrame(image_data, columns=['file_uuid','extracted_words','file_name','file_type','date','image_key','pdf_key'])
                    st.dataframe(df)
                    key = f"accounts/{st.session_state.user_name}/invoice_df.parquet"
                    invoice_df = pd.concat([invoice_df, df],
                                            ignore_index=True)
                    utils.pd_save_parquet(s3_client, invoice_df, bucket, key)
                    counter_up()


    with tab2:
        bucket = 'bergena-invoice-parser'
        key = f"accounts/{st.session_state.user_name}/invoice_df.parquet"
        try:
            invoice_df = utils.pd_read_parquet(s3_client, bucket, key)
        except:
            invoice_df = pd.DataFrame()
        st.dataframe(invoice_df)




    st.stop()

    if uploaded_file.type == "application/pdf":
        # model=st.sidebar.radio("Select model", ('gpt-3.5-turbo-1106',
        #                                         # 'gpt-3.5-turbo-instruct',
        #                                         'gpt-4-1106-preview'))
        # st.session_state.gpt_response = None
        # st.session_state.res_invoice_summary_df = pd.DataFrame()
        # st.session_state.res_items_df = pd.DataFrame()
        extracted_words = None
        try:
            extracted_words = parser.extract_words_from_pdf(uploaded_file)
        except:
            pass

        if  len(extracted_words)==0:
            invoice_type = 'image'
            img = images[0]
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            image_bytes = buf.getvalue()
            r = rekognition_client.detect_text(
                        Image={'Bytes': image_bytes}
                    )
            
            extracted_words = []
            image_width_in_points = 100
            image_height_in_points = 100
            for i in r['TextDetections']:
                if i['Type']=='LINE':
                    text = i['DetectedText']
                    rekognition_box = i['Geometry']['BoundingBox']
                    x0 = rekognition_box['Left'] * image_width_in_points
                    x1 = (rekognition_box['Left'] + rekognition_box['Width']) * image_width_in_points
                    top = rekognition_box['Top'] * image_height_in_points
                    bottom = (rekognition_box['Top'] + rekognition_box['Height']) * image_height_in_points
                    
                    converted_coordinates = {
                                        'text': text,  # You would get this from the Rekognition output
                                        'x0': x0,
                                        'x1': x1,
                                        'top': top,
                                        'bottom': bottom
                                    }
                    extracted_words.append(converted_coordinates)
                # print(len(extracted_words))

        
        else:
            invoice_type = 'text'
        

            
        constructed_text = parser.construct_text_from(extracted_words,
                        stop_at_string=None)
         
            # extracted_words = parser.group_words_by_line_rekognition(detect_text_response, tolerance=5)
        if st.session_state.password_entered:
            with st.expander("Show extracted words"):
                st.write(extracted_words)
            
            with st.expander("Show constructed text"):
                    
                    # st.write(extracted_words)
                    st.write(constructed_text.splitlines())
        st.write(f"invoice_type: {invoice_type}")
        #++++++++++++++++++++++++++++++++++++++++++++++SLOW BUT THOROUGH++++++++++++++++++++++++++++++++++++++++++++++
        if st.sidebar.button(":red[Parse invoice]",
                                on_click=counter_up,
                                key = 'slow_but_thorough'):
            gpt_response = None
            st.write(st.session_state['counter'])

            st.session_state.start_parsing_time = time()
            st.session_state.gpt_response = None
            st.session_state.invoice_summary_df = pd.DataFrame()
            st.session_state.line_items_df = pd.DataFrame()
            st.session_state.df_to_download = pd.DataFrame()
            st.session_state.parsing_time = None

            prompt = parser.get_prompt(constructed_text)
            model = 'gpt-3.5-turbo-1106'
            completion = parser.slow_but_thorough_parsing(constructed_text,
                    openai,
                    counter=st.session_state['counter'],
                    model=model)
            invoice_summary_df, line_items_df, token_sum = parser.parse_slow_but_thorough_response(completion,
                                     model,
                                     parser.gpt_pricing,
                                     counter=st.session_state['counter'])
            



            st.session_state.gpt_response =completion.choices[0].message.content
            st.session_state.invoice_summary_df = invoice_summary_df
            st.session_state.line_items_df = line_items_df

            with st.expander("Show raw API response"):
                st.write(st.session_state.gpt_response.splitlines())

            

            
    


            # if st.session_state.gpt_response:
            try:

                item_sums = st.session_state.line_items_df['Item total price'].round(2).sum()
                invoice_total = st.session_state.invoice_summary_df['Total amount'].round(2).sum()
                tax_amount = st.session_state.invoice_summary_df['Tax amount'].round(2).tolist()[0]
                
                col1, col2,col3 = st.columns(3)
                col1.write(f"item_sums: {item_sums}")
                col2.write(f"invoice_total: {invoice_total}")
                col3.write(f"tax_amount: {tax_amount}")

                assert 0.99 <abs(item_sums/(invoice_total - tax_amount)) < 1.01 or 0.99< abs(item_sums/invoice_total) < 1.01 

                st.write("sums test passed")
                st.session_state.parsing_time = time()- st.session_state.start_parsing_time
                st.write(f"finished parsing in {round(st.session_state.parsing_time,2)} seconds")

                st.subheader(":orange[Parsed invoice results:]")
                st.caption("Click on the table to edit the results")
            except:
                # col1, col2,col3 = st.columns(3)
                # col1.write(f"item_sums: {item_sums}")
                # col2.write(f"invoice_total: {invoice_total}")
                # col3.write(f"tax_amount: {tax_amount}")
                tab1, tab2 = st.tabs(['Summary fields', 'Items table'])

                tab1.dataframe(st.session_state.invoice_summary_df)

                tab2.dataframe(st.session_state.line_items_df)
                st.write("1st model failed to parse correctly, sending to the 2nd model")
                model = 'gpt-4-1106-preview'
                completion = parser.slow_but_thorough_parsing(constructed_text,
                        openai,
                        counter=st.session_state['counter'],
                        model=model)
                invoice_summary_df, line_items_df, token_sum = parser.parse_slow_but_thorough_response(completion,
                            model,
                            parser.gpt_pricing,
                            counter=st.session_state['counter'])
                st.session_state.gpt_response =completion.choices[0].message.content
                st.session_state.invoice_summary_df = invoice_summary_df
                st.session_state.line_items_df = line_items_df
            


                st.session_state.gpt_response =completion.choices[0].message.content

                try:
                    item_sums = st.session_state.line_items_df['Item total price'].round(2).sum()
                    invoice_total = st.session_state.invoice_summary_df['Total amount'].round(2).sum()
                    tax_amount = st.session_state.invoice_summary_df['Tax amount'].round(2).tolist()[0]
                    assert 0.99 <abs(item_sums/(invoice_total - tax_amount)) < 1.01 or 0.99< abs(item_sums/invoice_total) < 1.01 
                    st.success("sums test passed")
                    col1, col2,col3 = st.columns(3)
                    col1.write(f"item_sums: {item_sums}")
                    col2.write(f"invoice_total: {invoice_total}")
                    col3.write(f"tax_amount: {tax_amount}")

                    st.session_state.parsing_time = time()- st.session_state.start_parsing_time
                    st.write(f"finished parsing in {round(st.session_state.parsing_time,2)} seconds")

                except:
                    st.write("2nd model failed")
                    try:
                        col1, col2,col3 = st.columns(3)
                        col1.write(f"item_sums: {item_sums}")
                        col2.write(f"invoice_total: {invoice_total}")
                        col3.write(f"tax_amount: {tax_amount}")
                    except:
                        pass



            
            tab1, tab2 = st.tabs(['Summary fields', 'Items table'])

            tab1.dataframe(st.session_state.invoice_summary_df)

            tab2.dataframe(st.session_state.line_items_df)

        with st.expander("Show invoice"):
            for img in images:
                st.image(img, use_column_width=True)
            # st.image(image, use_column_width=True)
        
        def get_summary_df(gpt_response):
            json_data = json.loads(gpt_response)
            summary = json_data['Summary']
            invoice_summary_df = pd.DataFrame.from_dict(summary, orient='index').T
            columns = ['Date of invoice','Due date']
            for col_name in columns:
                value = invoice_summary_df[col_name].tolist()[0]
            try:
                value = pd.to_datetime(value,
                                    infer_datetime_format=True).strftime('%Y-%m-%d')
                invoice_summary_df.loc[0,col_name] = value
            except:
                pass
            return invoice_summary_df
        
        def get_line_items_df(gpt_response):
            json_data = json.loads(gpt_response)
            line_items = json_data['Line items']
            if isinstance(line_items, list):
                line_items_df = pd.DataFrame(line_items)
            else:
                line_items = list(line_items.items())[1]
                line_items_df = pd.DataFrame(line_items)
            return line_items_df

        gpt_response = st.session_state.gpt_response
        st.write(gpt_response.splitlines())

        summary_df = get_summary_df(gpt_response)
        st.dataframe(summary_df)

        line_items_df = get_line_items_df(gpt_response)
        st.dataframe(line_items_df)
        st.write(line_items_df.dtypes)


