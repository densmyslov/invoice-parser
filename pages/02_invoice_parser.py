import streamlit as st
import pandas as pd
import utils
from time import time
import json
import uuid
from datetime import datetime
from io import BytesIO
from random import randint
from zipfile import ZipFile, ZIP_DEFLATED
from time import sleep


st.set_page_config(page_title='Invoice Parser', 
                   page_icon=None, layout="wide", 
                   initial_sidebar_state="auto", 
                   menu_items=None)

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
        

        default_cols = ['file_name','file_uid','num_pages','invoice_type','is_parsed',
                    'total_sum_check','line_items_sum_check',
                    'time_to_complete']
        selection = utils.dataframe_with_selections(invoices_df0[default_cols])

    
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

                # counter_up()
        #----------------------SHOW INVOICES
        def to_excel(df1, df2):
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df1.to_excel(writer, index=False, sheet_name='Summary')
            df2.to_excel(writer, index=False, sheet_name='Line Items')
            workbook = writer.book
            worksheet1 = writer.sheets['Summary']
            worksheet2 = writer.sheets['Line Items']
            # format1 = workbook.add_format({'num_format': '0.00'})
            # worksheet1.set_column('A:A', None, format1)
            # worksheet2.set_column('A:A', None, format1)
            writer.close()
            processed_data = output.getvalue()
            return processed_data


        
        # def get_df_to_show(invoices_df,
        #                    selection):
        #     df_to_show = invoices_df.loc[selection.index,:].copy()
            



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

                        excel_data = to_excel(summary_df.reset_index(), 
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






            

 
 