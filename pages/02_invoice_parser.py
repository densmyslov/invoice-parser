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
# from joblib import Parallel, delayed

if 'sign_in_state' not in st.session_state:
    st.session_state['sign_in_state'] = 0
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = None

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

    if st.sidebar.button("Refresh"):
        st.session_state['counter'] = 0
        st.rerun()
    st.sidebar.write(st.session_state.user_name)



    st.title(":orange[PDF Invoice Parser]")
    tab1, tab2 = st.tabs(["Upload invoices","Parse Invoices"])

    #=================================UPLOAD INVOICES====================================================
    with tab1:

        col1, col2 = st.columns(2)
        uploaded_files = col1.file_uploader("Upload pdf invoices", 
                                        type=["pdf", "png", "jpg", "jpeg"],
                                        accept_multiple_files=True)
        # @st.cache_data()
        def load_invoice_df(counter=None):
            bucket = 'bergena-invoice-parser'
            key = f"accounts/{st.session_state.user_name}/invoices_df.parquet"
            try:
                invoice_df = utils.pd_read_parquet(s3_client, bucket, key)
            except:
                invoice_df = pd.DataFrame()
            return invoice_df


        invoices_df = load_invoice_df(counter = st.session_state['counter'])

        combined_images = []
        if uploaded_files is not None:
            ts = datetime.now().strftime("%Y-%m-%d")
            for uploaded_file in uploaded_files:
                file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type}
                file_uid= uuid.uuid4().hex
                # st.write(file_uid)
                if uploaded_file.type == "application/pdf":
                    # Convert PDF to a list of images
                    images = parser.pdf_to_images(uploaded_file)
                    combined_image = parser.combine_images(images, direction='horizontal')
                    extracted_words,pages_used_for_parsing = parser.extract_words_from_pdf(uploaded_file,
                                                                    max_words_per_page=1700)
                    combined_images.append((

                                            file_uid, 
                                            extracted_words,
                                            uploaded_file.name, 
                                            uploaded_file.type,
                                            pages_used_for_parsing,
                                            combined_image))
                    
            st.write(f":blue[number of invoices:{len(combined_images)}]")
            image_data = []
            if len(combined_images)>0:
                with st.expander("Show invoices"):
                    for _,_,file_name,_,pages_used_for_parsing, combined_image in combined_images:
                        st.write(f"file name: :blue[{file_name}]")
                        st.write(f"pages to be used for parsing: {','.join([str(i+1) for i in pages_used_for_parsing])}")                      
                        st.image(combined_image, use_column_width=True)
                if st.button("Upload invoices to your cloud account",on_click=counter_up):
                    for ind, uploaded_file in enumerate(uploaded_files):
                        (file_uid,extracted_words, file_name,file_type, 
                         pages_used_for_parsing, combined_image) = combined_images[ind]

                        bucket = 'bergena-invoice-parser'
                        pdf_key = f"accounts/{st.session_state.user_name}/pdfs/{ts}/{file_uid}.pdf"
                        uploaded_file.seek(0)
                        r = s3_client.upload_fileobj(
                                                    uploaded_file,
                                                    Bucket=bucket, 
                                                     Key=pdf_key)
                    
                        
                        bucket = 'bergena-invoice-parser'
                        image_key = f"accounts/{st.session_state.user_name}/images/{ts}/{file_uid}.jpg"
                        buffer = BytesIO()
                        combined_image.save(buffer, format='jpeg')
                        r = s3_client.put_object(Bucket=bucket, Key=image_key, Body=buffer.getvalue(), ContentType='image/jpeg')
                        

                        is_parsed = False
                        source='manual'
                        image_data.append((file_uid,extracted_words,file_name,file_type, 
                                           ts, image_key, pdf_key, is_parsed,source,
                                           pages_used_for_parsing))
                        # image_url = f"https://{bucket}.s3.amazonaws.com/{image_key}"

                        # image_html = f"""
                        #         <!DOCTYPE html>
                        #         <html lang="en">
                        #         <head>
                        #             <meta charset="UTF-8">
                        #             <title>{uploaded_file.name}</title>
                        #         </head>
                        #         <body>
                        #             <img src="{image_url}" alt="{uploaded_file.name}">
                        #         </body>
                        #         </html>
                        #         """
                        # buffer= StringIO(image_html)
                        # html_key = f"accounts/{st.session_state.user_name}/htmls/{ts}/{file_uid}.html"
                        # s3_client.put_object(
                        #     Bucket=bucket,
                        #     Key=html_key,
                        #     Body = buffer.getvalue(),
                        #     ContentType = 'text/html'
                        # )
            
                    if len(image_data) > 0:
                        df = pd.DataFrame(image_data, 
                                        columns=['file_uid',
                                                'extracted_words',
                                                'file_name','file_type','date',
                                                'image_key','pdf_key','is_parsed',
                                                'source','pages_used_for_parsing'])
                        for col_name in ['prompt',
                                         'completion',
                                         'time_to_complete',
                                         'model',
                                         'total_sum_check',
                                         'line_items_sum_check']:
                            df[col_name] = None
                        
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
                        uploaded_files=None
                        counter_up()

    #=================================PARSE INVOICES====================================================
    with tab2:


        
        bucket = 'bergena-invoice-parser'
        key = f"accounts/{st.session_state.user_name}/invoices_df.parquet"
        invoices_df = utils.pd_read_parquet(s3_client, bucket, key)
        if invoices_df.empty:
            st.error("You have no invoices in your account")
        else:
            default_cols = ['file_name','invoice_type','date','is_parsed','model',
                            'total_sum_check','line_items_sum_check','time_to_complete',
                            'source','image_key']
            selection = utils.dataframe_with_selections(invoices_df[default_cols])
        
        #===========================INVOICE PROCESSING====================================
            col1, col2, col3 = st.columns(3)
            #----------------------delete invoices
            if col3.button(":red[Delete selected invoices]"):
                invoices_df = invoices_df[~invoices_df.index.isin(selection.index)]
                key = f"accounts/{st.session_state.user_name}/invoices_df.parquet"
                utils.pd_save_parquet(s3_client, invoices_df, bucket, key)
                st.success("Invoices deleted")
                st.session_state['counter'] += 1
                st.rerun()
            #----------------------show invoices

            if col2.button("Show selected invoices"):
                if selection.empty:
                    st.error("You have not selected any invoices")
                    st.stop()
                else:
                    # images = []

                    df_to_show = invoices_df.loc[selection.index,['date',
                                                                  'file_name',
                                                                  'is_parsed',
                                                                  'completion',
                                                                'source',
                                                                'pages_used_for_parsing',
                                                                'image_key']]
                    df_to_show['gpt_response'] = None
                    for row in df_to_show.itertuples():
                        if row.is_parsed:
                            gpt_response=  json.loads(row.completion)['choices'][0]['message']['content']
                            # json_data = json.loads(gpt_response)
                            # summary = json_data['Summary']
                            invoice_summary_df = parser.get_summary_df(gpt_response)
                            # line_items_df = get_line_items_df(gpt_response)
                            st.dataframe(invoice_summary_df)
                            # st.dataframe(line_items_df)

                            # json_data = json.loads(gpt_response)
                            # line_items = json_data['Line items']
                            line_items = parser.get_line_items_df(gpt_response)
                            st.write(line_items)



                        img = utils.download_image(s3_client,bucket, row.image_key)
                        st.image(img)




                    # st.dataframe(df_to_show)
                    # for key in selection['image_key']:
                    #     img = download_image(bucket, key)
                    #     st.image(img)
            #----------------------parse invoices
# triggers lambda 'invPar-step-function-trigger' which inturn triggers step machine 'invPar-step-function'
            if col1.button(":orange[Parse selected invoices]"):
                if selection.empty:
                    st.error("You have not selected any invoices")
                    st.stop()
                else:
                    image_invoices = []
                    json_for_parsing={}
                    for row in invoices_df.loc[selection.index].itertuples():
                        if row.invoice_type == 'text':
                            st.write(row.file_name)
                            constructed_text = parser.construct_text_from(row.extracted_words,
                                stop_at_string=None)
                            
                            json_for_parsing[row.file_uid] = {'constructed_text': constructed_text,
                                                            'model':'gpt-3.5-turbo-1106'}
                        else:
                            image_invoices.append(row.file_name)
                    # st.write(json_for_parsing)
                    if len(json_for_parsing)>0:
                        bucket='bergena-invoice-parser'
                        s3_client.put_object(
                            Bucket=bucket,
                            Key=f"accounts/{st.session_state.user_name}/parsing/json_for_parsing.json",
                            Body = json.dumps(json_for_parsing)
                        )
                        st.success("Invoices sent for parsing")
                    st.error(f"Image invoices: {image_invoices} are not supported at the moment")




            

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


