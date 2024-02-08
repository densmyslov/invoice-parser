import streamlit as st
import pandas as pd
import os
import numpy as np
import re
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import sys
import subprocess
import importlib.util
import boto3
from io import BytesIO, StringIO
import string
from random import choice, choices
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
# import login
from dotenv import load_dotenv
import cognito
from botocore.exceptions import ClientError
from PIL import Image

# s3_client_BRG = boto3.client('s3',
#             aws_access_key_id = 'AKIAQZSZZFTKDGNFQVGL',
#             aws_secret_access_key = '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')

load_dotenv()

AWS_COGNITO_CLIENT_ID = os.environ.get('AWS_COGNITO_CLIENT_ID')
AWS_COGNITO_CLIENT_SECRET = os.environ.get('AWS_COGNITO_CLIENT_SECRET')
AWS_COGNITO_USER_POOL_ID = os.environ.get('AWS_COGNITO_USER_POOL_ID')

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')

CUSTOMERS_TABLE_NAME = os.environ.get('CUSTOMERS_TABLE_NAME')
BUCKET = os.environ.get('BUCKET')






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

s3_client_BRG = boto3.client('s3',
            aws_access_key_id = AWS_ACCESS_KEY_ID,
            aws_secret_access_key = AWS_SECRET_KEY)
rekognition_client= boto3.client('rekognition',
                                 region_name='us-east-1',
                                aws_access_key_id = AWS_ACCESS_KEY_ID,
                                aws_secret_access_key = AWS_SECRET_KEY)


# FUNCTIONS

def dataframe_with_selections(df: pd.DataFrame, init_value: bool = False) -> pd.DataFrame:
    df_with_selections = df.copy()
    # selected_all = st.toggle("Select all", key='select_all')
    # if selected_all:
    #     init_value = True
    df_with_selections.insert(0, "Select", init_value)

    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={"Select": st.column_config.CheckboxColumn(required=True)},
        disabled=df.columns,
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Select]
    return selected_rows.drop('Select', axis=1)


def delete_record(
                    dynamodb_client,
                    table_name, 
                    user_name, 
                    email):

    
    try:
        response = dynamodb_client.delete_item(
            TableName=table_name,
            Key={
                'user_id': {'S': user_name},
                'email': {'S': email}
            }
        )
        return response
    except Exception as e:
        print(f'Error deleting record: {e}')
        raise



def download_image(s3_client,bucket, key):
    # Use the S3 client to download the file
    
    buffer= BytesIO()
    s3_client.download_fileobj(bucket, key, buffer)
    buffer.seek(0)
    return Image.open(buffer)

# @st.cache_data()
def email_exists(_dynamodb_client, table_name, email):
  
    response = _dynamodb_client.query(
        TableName=table_name,
        IndexName='email-index',
        KeyConditionExpression='email = :email',
        ExpressionAttributeValues={
            ':email': {'S': email}
        }
    )

    return response['Count'] > 0

def get_col_idx_from(df,col_name):
    columns = df.columns.tolist()
    return columns.index(col_name)


def get_col_dict_from_(df, cols):
    col_dict = {col_name:None for col_name in cols}
    for col_name in cols:
        col_dict[col_name]=get_col_idx_from(df,col_name)
    return col_dict

def get_file_to_download_(df_to_download,
                            sheet_name='Template'):
    output_buffer = BytesIO()
    # with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
        # df_to_download.to_excel(writer, sheet_name=sheet_name, index=False)
    # writer.save()
    df_to_download.to_csv(output_buffer, sep='\t', index=False)

    # Reset the buffer position to the beginning
    output_buffer.seek(0)
    return output_buffer


def get_dynamodb_table_record_from_(_dynamodb_client,
                                    table_name,
                                    email):
  r = _dynamodb_client.query(
          TableName=table_name,
          IndexName='email-index',
          KeyConditionExpression='email = :email',
          ExpressionAttributeValues={
              ':email': {'S': email}
          })
  if r['Count']>0:
    return r['Items']
  
def get_latest_keys_from_(s3_client,
                          bucket, 
                          prefix, 
                          time_interval=1, 
                          time_unit='hour', 
                          additional_str='',
                          zipped=False):
  pat = re.compile(additional_str, re.I)
  paginator = s3_client.get_paginator('list_objects')

  try:
    page_iterator = paginator.paginate(Bucket=bucket,
                                      Prefix = prefix)
    key_ts = []
    for page in page_iterator:
      page_keys = [(i['Key'],i['LastModified']) for i in page['Contents'] if pat.search(i['Key'])]
      key_ts.extend(page_keys)
    key_ts.sort(key=lambda x: x[1], reverse=True)

    ts_latest = key_ts[0][1]
    time_units = {'second': 'seconds', 'hour': 'hours', 'day': 'days'}
    ts_earliest = ts_latest - timedelta(**{time_units[time_unit]: time_interval})

    latest_keys = [key[0] for key in key_ts if ts_earliest <= key[1] <= ts_latest]
    latest_ts = [key[1] for key in key_ts if ts_earliest <= key[1] <= ts_latest]
    last_ts_hour = ts_latest.strftime("%Y-%m-%d-%H")
    if zipped:
      return zip(latest_ts, latest_keys)
    
  except:
    last_ts_hour = None
    latest_keys = []
    if zipped:
      return zip([],[])
  return last_ts_hour, latest_keys


@st.cache_data()
def get_matched_datasets(selected_market_abbr):
    bucket = 'hamazin-seller-accounts'
    key = 'datasets/universal_matched_products_public.parquet'
    matched_df = pd_read_parquet(s3_client_BRG, bucket, key)

    matched_df.rename(columns={"amz_item_id": "asin",
                                "wlm_item_id": "item_id",
                                "amz_categories_flat":"amz_categories",
                                "wlm_categories_flat":"wlm_categories",
                                "barcode_number_12last":"upc"}, inplace=True)
    for store in ['amz', 'wlm']:
        matched_df[f'{store}_categories'] = matched_df[f'{store}_categories'].apply(lambda x: 
                                              [i.strip() for i in x.split('>')])

    key = f'datasets/{selected_market_abbr}_category_filter.parquet'
    category_df = pd_read_parquet(s3_client_BRG, bucket, key)
    return matched_df, category_df

@st.cache_data()
def get_matched_df_to_show(matched_df, 
                            selected_market_abbr, 
                            min_price, 
                            ratings_filter, 
                            category_filters_selected,
                            cols_to_show,
                            col_dict):
    matched_df_to_show = matched_df.copy()

    # create 'price' column, fill it from 'amz_price' or 'wlm_price', fillna with min_price
    col_name = f"{selected_market_abbr}_price"
    other_col_name = [i for i in col_dict if col_name!=1][0]
    idx0=col_dict[col_name]
    idx1=col_dict[other_col_name]


    matched_df_to_show['price']=matched_df_to_show.apply(lambda x: x[idx0] if x[idx0]>0 else x[idx1], axis=1)
    default_price = min_price
    if default_price==0:
        default_price += 1
    matched_df_to_show.fillna(value={'price':default_price}, inplace=True)
    
    # apply filters
    if category_filters_selected == ['All']:
        matched_df_to_show=matched_df_to_show.query(f"price >= @min_price & \
                                            {selected_market_abbr}_ratings_total >= @ratings_filter")[cols_to_show].copy()
    else:
        matched_df_to_show=matched_df_to_show[matched_df_to_show["amz_categories"].apply(lambda x: 
            len(set(x).intersection(set(category_filters_selected)))>0)].query(f"price >= @min_price & \
                                            {selected_market_abbr}_ratings_total >= @ratings_filter")[cols_to_show].copy()

    # reshuffle the dataframe
    return matched_df_to_show.sample(frac=1).reset_index(drop=True)

def get_page_header_for_(header_text, color_dict):
    color=color_dict['page_header_color']

    header_html1 = f'''
        <style>
            .header {{
                font-size: 48px;
                font-weight: 800;
                color: {color};
            }}
        </style>
        <div class="header">{header_text}</div>
    '''
    st.markdown(header_html1, unsafe_allow_html=True)

def get_sku_value(sku_length=8,
                sku_prefix=""):
    if sku_prefix:
        return sku_prefix + ''.join(choice(string.ascii_uppercase + 
                    # string.ascii_lowercase + 
                    string.digits) for _ in range(sku_length-len(sku_prefix)))
    else:
        return ''.join(choice(string.ascii_uppercase + 
                    string.digits) for _ in range(sku_length))

@st.cache_data()
def get_amz_summary_df(uploaded_file):
    """
    Reads an Excel file, processes the data, and returns a summary DataFrame and two lists of ASINs.
    
    Parameters
    ----------
    uploaded_file : io.BytesIO
        The Excel file to be read and processed, typically received from Streamlit's file_uploader.
    show_products : bool
        A flag indicating whether to display the products in the Streamlit app (currently unused).

    Returns
    -------
    summary_df : pandas.DataFrame
        The summary DataFrame containing the processed data from the Excel file.
    success_asins : list
        A list of ASINs with 'SUCCESS' in the 'number_of_attributes_with_errors' column.
    delete_asins : list
        A list of ASINs without 'SUCCESS' in the 'number_of_attributes_with_errors' column.
    """
    sheet_name = 'Template'
    try:
        summary_df = pd.read_excel(uploaded_file, 
                                sheet_name=sheet_name,
                                skiprows=[0],
                                header = 1)

        summary_df.columns = ['_'.join([x for x in i.lower().split()]) for i in summary_df.columns]
        summary_df['number_of_attributes_with_errors'] = summary_df['number_of_attributes_with_errors'].astype('str')

        summary_df.rename(columns={'product-id':'amz_item_id'},
                                    inplace=True)
        # st.write(summary_df.columns)

        required_cols = ['amz_item_id', 'sku', 'number_of_attributes_with_errors']
        # st.write(set(summary_df.columns).intersection(set(required_cols)))
        assert len(set(summary_df.columns).intersection(set(required_cols))) == 3, "Please check that you are uploading the right file"
        
        success_asins = summary_df.query("number_of_attributes_with_errors == 'SUCCESS'")['amz_item_id'].tolist()
        delete_asins = summary_df.query("number_of_attributes_with_errors != 'SUCCESS'")['amz_item_id'].tolist()
        
        return summary_df, success_asins, delete_asins
    except:
        st.write(f"Please check that you are uploading the right file. The file should have a sheet named '{sheet_name}'")

@st.cache_data()
def get_user_id_from_(_dynamodb_client, table_name, email):
  
    r = _dynamodb_client.query(
        TableName=table_name,
        IndexName='email-index',
        KeyConditionExpression='email = :email',
        ExpressionAttributeValues={
            ':email': {'S': email}
        }
    )
    if r['Count']>0:
        items = r['Items']
        return items[0]['user_id']['S']

@st.cache_data()
def get_wlm_manage_items_df(uploaded_file):
    wlm_df = pd.read_csv(uploaded_file)
    required_cols = ['SKU','ITEM ID','STATUS']
    assert set(wlm_df.columns).intersection(set(required_cols)) == set(required_cols), "Please check that you are uploading the right file"
    wlm_df = wlm_df[['SKU','ITEM ID','STATUS']]
    wlm_df.columns=['sku','wlm_item_id','status']
    return wlm_df

def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_regex, email))

def is_valid_password(password):
    min_length = 8
    has_digit = re.search(r'\d', password)
    has_letter = re.search(r'[a-zA-Z]', password)
    has_non_alphanumeric = re.search(r'\W', password)

    return (
        len(password) >= min_length
        and has_digit is not None
        and has_letter is not None
        and has_non_alphanumeric is not None
    )
def is_valid_name(name):
    name_regex = r'^[a-zA-Z ]+$'
    return bool(re.match(name_regex, name))




@st.cache_data()
def get_download_file_from_(df0, selected_market, sku_length, sku_prefix):


    # generate skus:
    df= df0.copy()
    df["sku"] = df.apply(lambda x: get_sku_value(sku_length=sku_length, sku_prefix=sku_prefix), axis=1)

    if selected_market == "Amazon.com":
        col_name = 'amz_price'
    elif selected_market == "Walmart.com":
        col_name = 'wlm_price'


    

    if selected_market == "Amazon.com":

        df["quantity"] = 0
        df["product-id"] = df["asin"]
        df["product-id-type"] = "ASIN"
        df["condition-type"] = "New"

    
        amz_cols = ['sku','price','quantity','product-id', 'product-id-type', 'condition-type']
        df_to_download = df[amz_cols].copy()


        # Custom header
        header = ["TemplateType=Offer\tVersion=2020.000",

        "sku\tprice\tquantity\tproduct-id\tproduct-id-type\tcondition-type\t\
        condition-note\tASIN-hint\ttitle\tproduct-tax-code\toperation-type\tsale-price\tsale-start-date\t\
        sale-end-date\tleadtime-to-ship\tlaunch-date\tis-giftwrap-available\tis-gift-message-available\t\
        fulfillment-center-id\tmain-offer-image\toffer-image1\toffer-image2\toffer-image3\toffer-image4\t\
        offer-image5\tbatteries_required\tare_batteries_included\tbattery_cell_composition\tbattery_type\t\
        number_of_batteries\tbattery_weight\tbattery_weight_unit_of_measure\tnumber_of_lithium_metal_cells\t\
        number_of_lithium_ion_cells\tlithium_battery_packaging\tlithium_battery_energy_content\t\
        lithium_battery_energy_content_unit_of_measure\tlithium_battery_weight\t\
        lithium_battery_weight_unit_of_measure\tsupplier_declared_dg_hz_regulation1\t\
        supplier_declared_dg_hz_regulation2\tsupplier_declared_dg_hz_regulation3\t\
        supplier_declared_dg_hz_regulation4\tsupplier_declared_dg_hz_regulation5\t\
        hazmat_united_nations_regulatory_id\tsafety_data_sheet_url\titem_weight\t\
        item_weight_unit_of_measure\titem_volume\titem_volume_unit_of_measure\tflash_point\t\
        ghs_classification_class1\tghs_classification_class2\tghs_classification_class3\t\
        california_proposition_65_compliance_type\tcalifornia_proposition_65_chemical_names1\t\
        california_proposition_65_chemical_names2\tcalifornia_proposition_65_chemical_names3\t\
        california_proposition_65_chemical_names4\tcalifornia_proposition_65_chemical_names5",

        "sku\tprice\tquantity\tproduct-id\tproduct-id-type\tcondition-type\t\
        condition-note\tASIN-hint\ttitle\tproduct-tax-code\toperation-type\tsale-price\tsale-start-date\t\
        sale-end-date\tleadtime-to-ship\tlaunch-date\tis-giftwrap-available\tis-gift-message-available\t\
        fulfillment-center-id\tmain-offer-image\toffer-image1\toffer-image2\toffer-image3\toffer-image4\t\
        offer-image5\tbatteries_required\tare_batteries_included\tbattery_cell_composition\tbattery_type\t\
        number_of_batteries\tbattery_weight\tbattery_weight_unit_of_measure\tnumber_of_lithium_metal_cells\t\
        number_of_lithium_ion_cells\tlithium_battery_packaging\tlithium_battery_energy_content\t\
        lithium_battery_energy_content_unit_of_measure\tlithium_battery_weight\t\
        lithium_battery_weight_unit_of_measure\tsupplier_declared_dg_hz_regulation1\t\
        supplier_declared_dg_hz_regulation2\tsupplier_declared_dg_hz_regulation3\t\
        supplier_declared_dg_hz_regulation4\tsupplier_declared_dg_hz_regulation5\t\
        hazmat_united_nations_regulatory_id\tsafety_data_sheet_url\titem_weight\t\
        item_weight_unit_of_measure\titem_volume\titem_volume_unit_of_measure\tflash_point\t\
        ghs_classification_class1\tghs_classification_class2\tghs_classification_class3\t\
        california_proposition_65_compliance_type\tcalifornia_proposition_65_chemical_names1\t\
        california_proposition_65_chemical_names2\tcalifornia_proposition_65_chemical_names3\t\
        california_proposition_65_chemical_names4\tcalifornia_proposition_65_chemical_names5"]


        # Save the DataFrame as an Excel file in memory
        output_buffer = BytesIO()
        with pd.ExcelWriter(output_buffer, engine='xlsxwriter') as writer:
            df_to_download.to_excel(writer, index=False, header=None, startrow=3)
            # workbook = writer.book
            worksheet = writer.sheets['Sheet1']
            # Write the custom header
            for row, header_row in enumerate(header):
                for col, header_cell in enumerate(header_row.split('\t')):
                    worksheet.write_string(row, col, header_cell)

        # writer.save()

        # Reset the buffer position to the beginning
        output_buffer.seek(0)
        return output_buffer

    elif selected_market == 'Walmart.com':

        wlm_quick_match_cols = ['sku',
                'productIdType',
                'productId',
                'price',
                'ShippingWeight']
        df0=df.copy()
        st.dataframe(df0)

        df0['productIdType'] = 'UPC'
        df0['productId'] = df['upc']

        cols = ['amz_weight_lbs','wlm_weight_lbs']
        col_dict = get_col_dict_from_(df, cols)


        # get 'price' col, if amz_price is 0/NaN, use wlm_price
        # fill 'price' col with default price if all prices are 0/NaN
        col_name = 'wlm_weight_lbs'
        other_col_name = [i for i in col_dict if col_name!=1][0]
        idx0=col_dict[col_name]
        idx1=col_dict[other_col_name]


        df0['ShippingWeight']=df0.apply(lambda x: x[idx0] if x[idx0]>0 else x[idx1], axis=1)
        default_weight = 0.22
        df0.fillna(value={'ShippingWeight':default_weight}, inplace=True)
        for col_name in ['price','ShippingWeight']:
            df0[col_name] = df0[col_name].round(2)


        bucket = 'hamazin-seller-accounts'
        key = 'datasets/quick_match_upload-walmart.xlsx'
        obj = s3_client_BRG.get_object(Bucket=bucket, Key=key)
        # buffer = BytesIO(obj['Body'].read())
        excel_buffer = BytesIO(obj['Body'].read())
        sheet_name = 'MP Item Setup by Match'

        # Read the Excel file with openpyxl
        wb = load_workbook(excel_buffer)
        ws = wb[sheet_name]
        # Find the last row number in the worksheet
        last_row = ws.max_row
        st.write(last_row)
        # df2 = df[wlm_quick_match_cols]

        # Write the updated DataFrame back to the original sheet starting from row 7 and column 4
        for index, r in enumerate(dataframe_to_rows(df0[wlm_quick_match_cols], index=False, header=False)):
            if index < 6:  # Skip the first 6 rows
                continue
            row_number = index - 6 + 7
            for col_number, value in enumerate(r, 4):  # Start writing from column 4
                ws.cell(row=row_number, column=col_number, value=value)


        # Save the workbook to a buffer
        output_buffer = BytesIO()
        wb.save(output_buffer)
        output_buffer.seek(0)  # Reset the buffer position to the beginning

        return output_buffer
    
@st.cache_data()
def load_invoice_df(_s3_client, customer_id, counter=None):
    bucket = 'bergena-invoice-parser-prod'
    key = f"accounts/{customer_id}/invoices_df.parquet"
    try:
        invoice_df = pd_read_parquet(_s3_client, bucket, key)
        invoice_df['search_str'] = invoice_df.apply(lambda x:
                                                    f"{x['file_name']}{x['file_uid']}{x['completion']}",
                                                    axis=1)
    except:
        invoice_df = pd.DataFrame()
    return invoice_df

def password_is_valid(password):
    # At least 8 characters in length
    if len(password) < 8:
        return False

    # Contains only Latin characters (A-Z, a-z), numbers (0-9), and special characters
    if not re.match(r"^[A-Za-z0-9!@#$%^&*()]+$", password):
        return False

    # At least one uppercase letter (A-Z)
    if not re.search(r"[A-Z]", password):
        return False

    # At least one lowercase letter (a-z)
    if not re.search(r"[a-z]", password):
        return False

    # At least one number (0-9)
    if not re.search(r"[0-9]", password):
        return False

    # At least one special character (!@#$%^&*())
    if not re.search(r"[!@#$%^&*()]", password):
        return False

    return True

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


@st.cache_data()
def login_and_get_user_id_from_(_s3_client, username, password):
    if username and password:
        user_account_id = login.authenticate_user(_s3_client,username, password)
        if user_account_id:
            login.main()
            return user_account_id

        else:
            st.sidebar.error("Invalid username or password.")
    elif not username and not password:
        st.info("Please enter your username and password to login.")
    else:
        st.warning("Click 'Login' to proceed.")

# @st.cache_data()
# def login_and_get_user_id_from_(_s3_client, username, password,login_button):

#     if login_button:
#         user_account_id = login.authenticate_user(_s3_client,username, password)
#         if user_account_id:
#             login.main()
#             return user_account_id

#         else:
#             st.sidebar.error("Invalid username or password.")
#     elif not username and not password:
#         st.info("Please enter your username and password to login.")
#     else:
#         st.warning("Click 'Login' to proceed.")

def pd_read_parquet(_s3_client,bucket,key,columns=None):

    """
    Reads a Parquet file from an S3 bucket and returns a pandas DataFrame.
    """


    try:
        obj = _s3_client.get_object(Bucket=bucket,Key=key)
        buffer = BytesIO(obj['Body'].read())
        if columns:
            return pd.read_parquet(buffer,
                                columns=columns)
        else:
            return pd.read_parquet(buffer)
    except:
        return pd.DataFrame()

def pd_save_parquet(_s3_client, df, bucket, key, schema=None):
    """
    Save a Pandas DataFrame as a parquet file to an S3 bucket.

    Args:
        _s3_client (boto3.client): A boto3 S3 client instance.
        df (pandas.DataFrame): The DataFrame to be saved as a parquet file.
        bucket (str): The name of the S3 bucket where the parquet file will be saved.
        key (str): The key (path) where the parquet file will be saved in the S3 bucket.
        schema (pyarrow.Schema, optional): The schema to use when saving the DataFrame. Defaults to None.

    Returns:
        None
    """
    buffer = BytesIO()
    if schema:
        df.to_parquet(buffer, schema=schema)
    df.to_parquet(buffer)
    _s3_client.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())

def update_values_in_(df, starting_row, values):
    for i, row_values in enumerate(values):
        for j, value in enumerate(row_values):
            st.write(starting_row + i, j+1)
            df.iat[starting_row + i, j+1] = value
    return df

def upload_df_to_s3_(s3_client,df,user_account_id,selected_market):
    ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    bucket = 'hamazin-seller-accounts'
    if selected_market == 'Amazon.com':
        market_abbr = 'amz'
    elif selected_market == 'Walmart.com':
        market_abbr = 'wlm'
    key = f"accounts/{user_account_id}/{market_abbr}_processing_summary/{ts}/{market_abbr}_ps.parquet"
    st.write(key)
    buffer = BytesIO()
    df.to_parquet(buffer)
    return s3_client.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())



