import io
import pandas as pd
import streamlit as st
import re
import fitz
from PIL import Image
import json
from difflib import SequenceMatcher
import re
import pdfplumber
import requests



def wrap_into_json(key, value):
    return json.dumps({key: value})

gpt_pricing = {'gpt-3.5-turbo-1106': {'tokens_in' : 0.001,
                                 'tokens_out': 0.002},
               'gpt-3.5-turbo-instruct' : {'tokens_in':0.0015,
                                        'tokens_out':0.002},
               'gpt-4-1106-preview': {'tokens_in':0.01,
                                        'tokens_out':0.03}
               }

def get_prompt(constructed_text):
  start = """
  Given the invoice details:

  <invoice text starts here>"""


  end = """
  <invoice text ends here>



  Extract the following summary fields from the invoice text above:
  - Invoice number
  - Date of invoice
  - Due date
  - Total amount
  - Tax amount
  - Packing
  - Freight
  - Invoice currency
  - Issued by
  - Issued to person
  - Issued to business
  - Issued by address
  - Issued to address
  'Issued by' and 'Issued to business' can't be the same. 'Issued by' field on the invoice can be
  indicated by a business name and address; 'Issued to' is usually preceded by 'Bill to', 'Issued to'
  or equivalent. 'Issued to' and 'Issued by' can't be the same. Issues by is a vendor, issued to is a client.
  If 'Issued to person' is present on the invoice, it usually has name and surname of the person.
  Wrap summary fields into json, such as in the example below:
  {'Summary' :
        {'Invoice number': '000148',
      'Date of invoice': '6/27/2023',
      'Due date': '6/27/2023',
      'Total amount': '10086.00',
      'Tax amount': '0.00'
      'Packing' : '1.00',
      'Freight' : '10.00',
      'Invoice currency': 'USD',
      'Issued by': 'Ascend Distribution LLC',
      'Issued to person': 'John Doe',
      'Issued to business': 'Hi Standards Marketplace / Ten Twenty Holdings',
      'Issued by address': '941 Avenue N, Suite A, Grand Prairie, TX 75050, United States',
      'Issued to address': '867 Boylston St 5th Floor #1336, BOSTON 02116 MA, United States'}
  }


  Extract line items from the invoice text above.
  Line items are billed products or services, wich can have the following attributes:
  product_id, title, quantity, unit price, total price, VAT.
  To understand which attributes are present in the invoice, treat line items as a table.
  First, deduce headers of the table. Headers are the attributes that are present in all line items.
  Total price equals to quantity multiplied by unit price.
  If the first line item startswith 1, the second line item starts with 2, and so on, disregard these numbers.
  Ensure that all line items are parsed and in the exact order as they appear in the invoice.
  Do not make any assumptions about missing values; use None instead.
  Remember that in Europe comma is used as a decimal separator, and dot is used as a thousand separator.
  Convert all prices and amounts to float using US decimal separator.
  Convert quantity to integer.
  Example of an line_items output:
  {'Line items':
    [
      {'Product id': 'B9414851','Item name': 'Dixie Perfectouch Insulated Paper Hot Cup, Coffee Haze Design, 75 Count 16oz', 'Item quantity': 200, 'Item unit price': 12, 'Item total price': 2400.00},
    {'Product id': 'AZ-345BF', 'Item name': 'Breathe Right Nasal Strips, Extra Clear for Sensitive Skin, 72 Clear Strips', 'Item quantity': 200, 'Item unit price': 13.65, 'Item total price': 2730.00},
    {'Product id': 'g345-JJ-k100','Item name': 'Pup-Peroni Dog Snacks Original Beef Flavor, 50 oz', 'Item quantity': 200, 'Item unit price': 18.96, 'Item total price': 3792.00}
    ]
  }
    Return output as json comprising Summary and Line items
    """
  return start + constructed_text + end


def combine_images(images, direction='horizontal'):
    """
    Combine a list of images into one, displayed in the specified direction.

    :param images: List of PIL Image objects.
    :param direction: 'horizontal' or 'vertical'
    :return: Combined Image object.
    """
    if direction not in ['horizontal', 'vertical']:
        raise ValueError("direction argument should be either 'horizontal' or 'vertical'")

    # Determine the size of the combined image
    if direction == 'horizontal':
        total_width = sum(image.width for image in images)
        max_height = max(image.height for image in images)
        combined_image = Image.new('RGB', (total_width, max_height))
    else:  # direction == 'vertical'
        total_height = sum(image.height for image in images)
        max_width = max(image.width for image in images)
        combined_image = Image.new('RGB', (max_width, total_height))

    # Paste images into the combined image
    current_position = 0
    for image in images:
        if direction == 'horizontal':
            combined_image.paste(image, (current_position, 0))
            current_position += image.width
        else:  # direction == 'vertical'
            combined_image.paste(image, (0, current_position))
            current_position += image.height

    return combined_image





def pdf_to_images(pdf_file):
    # Load the PDF file
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        images = []
        for page_number in range(len(doc)):
            # Get the page
            page = doc.load_page(page_number)
            # Render page to an image
            pix = page.get_pixmap()
            # Store the image as PIL.Image
            images.append(Image.open(io.BytesIO(pix.tobytes("png"))))
        return images
    except:
        st.error("Error: Invalid file format")

#++++++++++++++++++++++++++++++++++++SLOW BUT THOROUGH PARSING+++++++++++++++++++++++++++++++++++++++++++++++

@st.cache_data()
def construct_text_from(extracted_words, stop_at_string=None):

    lines_coords = group_words_by_line(extracted_words)

    lines = {}
    for line_coord in lines_coords:
        for word_data in line_coord['coords']:
            line_top = word_data['top']
            if line_top not in lines:
                lines[line_top] = []
            lines[line_top].append(word_data)

    # Sort words in each line based on the 'x0' value
    for line_top, words in lines.items():
        lines[line_top] = sorted(words, key=lambda x: x['x0'])

    # Construct lines of text with proportional spaces
    constructed_lines = []
    for line_top in sorted(lines):
        line_words = lines[line_top]
        line_text = ''
        for i, word_data in enumerate(line_words):
            if i > 0:
                # Calculate space width as difference between current word's 'x0' and previous word's 'x1'
                space_width = word_data['x0'] - line_words[i - 1]['x1']
                # Convert space width to an integer number of spaces, for example by dividing by a fixed value
                space_count = int(space_width / 5)  # Adjust the divisor to set the scale for spaces
                line_text += ' ' * max(space_count, 1)  # Ensure at least one space
            line_text += word_data['text']
        constructed_lines.append(line_text)

    # Join the constructed lines and return
    constructed_text = '\n'.join(constructed_lines)

    # Cut off page with "Terms & Conditions"
    if stop_at_string:
        pat = re.compile(stop_at_string, re.I)
        match = pat.search(constructed_text)
        stop_at = None
        if match:
            stop_at = match.span()[0]
            constructed_text = constructed_text[:stop_at]

    return constructed_text

def extract_words_with_rekognition(rekognition_client,
                                   images,
                                   counter = None):
    # Extract words only, excluding lines
    img = images[0]
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    image_bytes = buf.getvalue()
    r = rekognition_client.detect_text(
                Image={'Bytes': image_bytes}
            )
    
    extracted_words = []
    image_width_in_points = 1
    image_height_in_points = 1
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

    return extracted_words
    
    # Sort words by their Y position (top) and then X position (left)
    # words.sort(key=lambda w: (w['Geometry']['BoundingBox']['Top'], w['Geometry']['BoundingBox']['Left']))

    # lines = []
    # current_line = []

    # for word in words:
    #     # Calculate the top and left position of the word
    #     top = word['Geometry']['BoundingBox']['Top']
    #     left = word['Geometry']['BoundingBox']['Left']
        
    #     if not current_line:
    #         current_line.append(word)
    #     else:
    #         # Check if the current word is on the same line as the previous word
    #         if abs(current_line[-1]['Geometry']['BoundingBox']['Top'] - top) <= tolerance:
    #             current_line.append(word)
    #         else:
    #             lines.append(current_line)
    #             current_line = [word]
    
    # # Add the last line if not empty
    # if current_line:
    #     lines.append(current_line)

    # # Now transform the coordinates
    # line_coords = []
    # for line in lines:
    #     # Sort words in the line by their X position (left)
    #     sorted_line = sorted(line, key=lambda w: w['Geometry']['BoundingBox']['Left'])
        
    #     # Extract the coordinates and compute x0, x1, top, bottom
    #     coords = []
    #     for w in sorted_line:
    #         x0 = w['Geometry']['BoundingBox']['Left']
    #         y0 = w['Geometry']['BoundingBox']['Top']
    #         x1 = x0 + w['Geometry']['BoundingBox']['Width']
    #         y1 = y0 + w['Geometry']['BoundingBox']['Height']
            
    #         coords.append({
    #             'text': w['DetectedText'],
    #             'x0': x0,
    #             'x1': x1,
    #             'top': y0,
    #             'bottom': y1
    #         })
        
    # return sorted(coords, key=lambda word: word['top'])




@st.cache_data()
def extract_words_from_pdf(uploaded_file,
                           counter=None):


    all_extracted_words = []
    with pdfplumber.open(uploaded_file) as pdf:
        # Initialize the height offset as 0
        height_offset = 0
        for page_number, pdf_page in enumerate(pdf.pages):
            try:
                # Extract words from the current page
                extracted_words = pdf_page.extract_words()
                if len(extracted_words)>1700:
                   pass
                else:

                  # If this is not the first page, adjust the vertical coordinates
                  if page_number > 0:
                      for word in extracted_words:
                          word['top'] += height_offset
                          word['bottom'] += height_offset

                  # Append adjusted words to the main list
                  all_extracted_words.extend(extracted_words)

                  # Update the height offset by adding the height of the current page
                  height_offset += pdf_page.height

            except Exception as e:
                
                pass

    return normalize_extracted_words(all_extracted_words)

def group_words_by_line(words, tolerance=3):
    lines = []
    current_line = []

    for word in sorted(words, key=lambda w: (-w['top'], w['x0'])):
        if not current_line:
            current_line.append(word)
        else:
            # Check if the current word is on the same line as the previous word
            if abs(current_line[-1]['top'] - word['top']) <= tolerance:
                current_line.append(word)
            else:
                lines.append(sorted(current_line, key=lambda w: w['x0']))
                current_line = [word]

    # Add the last line if not empty
    if current_line:
        lines.append(sorted(current_line, key=lambda w: w['x0']))

    line_coords = [{'coords': line, 'y_position': line[0]['top']} for line in lines]

    return line_coords

def normalize_extracted_words(extracted_words):
    for d in extracted_words:
        if 'Text' in d:
            d['text'] = d.pop('Text')
    return extracted_words

@st.cache_data()
def parse_line_items_in_(gpt_response):
  json_data = json.loads(gpt_response)
  keys = list(json_data)
  if isinstance(json_data[keys[1]], list):
      line_items = json_data[keys[1]]
  else:
      keys1 = list(json_data[keys[1]])
      line_items = json_data[keys[1]][keys1[0]]
  # # matches = re.findall(r'\[ *\{.*?\}.*]', ''.join(gpt_response.splitlines()))
  # pat = re.compile(r'\{.*?Product.?id".*\}',re.I)
  # matches = pat.findall(gpt_response)
  # # try:
  # line_items = [eval(i) for i in matches if i]
  # except:
  # # line_items_df = pd.DataFrame(line_items)
  #   if len(matches) >0:
  #   # st.write(matches)
  #     for match in matches:

  #       try:
  #         extracted_dict = eval(match)  # Convert string representation of dictionary to an actual dictionary
  #       except:
  #         extracted_dict = match
  #         extracted_dict = json.loads(extracted_dict)
  #       line_items.extend(extracted_dict)
  return line_items

@st.cache_data()
def slow_but_thorough_parsing(constructed_text,
                       openai,
                       model,
                      counter=None):
  # constructed_text = construct_text_from(extracted_words)
  prompt = get_prompt(constructed_text)

  completion = openai.chat.completions.create(
                            model=model,
                            temperature = 0.1,
                            response_format = {'type':'json_object'},
                            messages=[
                                        {"role": "system", "content": "You are a helpful assistant"},
                                        {"role": "user", "content": json.dumps(prompt)}
                                        ],

                                        )
  return  completion

@st.cache_data()
def parse_invoice(prompt,
                  model,
                  openai_key,
                  counter=None):
    url = 'https://api.openai.com/v1/chat/completions'

    # Headers with authorization
    headers = {
        'Authorization': f'Bearer {openai_key}',
        'Content-Type': 'application/json'
    }
    payload = {
        "model": model,
        "temperature": 0.1,
        "response_format" : {'type':'json_object'},
        "messages": [

            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": json.dumps(prompt)}

        ]
    }


    return  requests.post(url, headers=headers, json=payload, timeout=60)

def convert_str_to_date(df,columns):
    for col_name in columns:
        df[col_name] = df[col_name].apply(lambda x:
                            pd.to_datetime(x,
                            infer_datetime_format=True).strftime('%Y-%m-%d')
                                if x  else None)
    return df
                
def convert_str_to_num(df0, columns):
    df = df0.reset_index(drop=True).copy()
    for col_name in columns:
        for ind, value in enumerate(df[col_name]):
            try:
              value = float(re.sub(r"[$,\(\) ]","",value))
              df.loc[ind,col_name] = value
              df[col_name] = df[col_name].astype('float')
            except:
               pass
    return df

@st.cache_data()
def get_summary_lines_from(gpt_response,
                           counter=None):
    pat = re.compile(r"item",re.I)

    res_summary = {}

    for idx, line in enumerate(gpt_response.splitlines()):
        if pat.search(line):
            break
        else:
            key_value = line.split(": ")
            if len(key_value)==2:
                key,value = key_value
                key = key.replace('"','')
                value=value.replace('"','').strip(',')
                key = key.strip('- ').strip()
                res_summary[key] = value
    invoice_summary_df = pd.DataFrame.from_dict(res_summary,
                    orient='index').T
    columns = ['Date of invoice','Due date']
    for col_name in columns:
      value = invoice_summary_df[col_name].tolist()[0]
      try:
          value = pd.to_datetime(value,
                            infer_datetime_format=True).strftime('%Y-%m-%d')
          invoice_summary_df.loc[0,col_name] = value
      except:
         pass
@st.cache_data()
def get_summary_lines_from(gpt_response,
                           counter=None):
    json_data = json.loads(gpt_response)
    invoice_summary_df = pd.DataFrame.from_dict(json_data,
                    orient='index').T
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


    # invoice_summary_df = convert_str_to_date(invoice_summary_df,columns)
    invoice_summary_df = convert_str_to_num(invoice_summary_df, ['Total amount',
                                                                 'Tax amount'])

    columns = ['Invoice number',
                'Date of invoice',
                'Due date',
                'Total amount',
                'Tax amount',
                'Invoice currency',
                'Issued by',
                'Issued to person',
                'Issued to business',
                'Issued by address',
                'Issued to address']
    
    return idx, invoice_summary_df[columns]

@st.cache_data()
def parse_line_items_in_(gpt_response,
                          counter=None):
    line_items = []
    matches = re.findall(r'\[ *\{.*?\}.*]', ''.join(gpt_response.splitlines()))
    if len(matches) >0:
    # st.write(matches)
        for match in matches:
            # st.write(match)

            try:
                extracted_dict = eval(match)  # Convert string representation of dictionary to an actual dictionary
            except:
                extracted_dict = match
                extracted_dict = json.loads(extracted_dict)
            line_items.extend(extracted_dict)
    
    if len(line_items)>0:
      #  st.write(line_items)
       line_items_df = pd.DataFrame(line_items)
       line_items_df = convert_str_to_num(line_items_df, ['Item quantity','Item unit price','Item total price'])
    return line_items_df

def parse_slow_but_thorough_response(completion,
                                     model,
                                     gpt_pricing,
                                     counter=None):
  gpt_response =completion.choices[0].message.content
  tokens_in = completion.usage.prompt_tokens
  tokens_out = completion.usage.completion_tokens
  try:
    idx, invoice_summary_df = get_summary_lines_from(gpt_response,
                                                    counter)

    invoice_summary_df['tokens_in'] = tokens_in
    invoice_summary_df['tokens_out'] = tokens_out
    token_sum = {}
    for t in ['tokens_in','tokens_out']:
        token_sum[t] = invoice_summary_df[t] * gpt_pricing[model][t]/1000
    # st.write(token_sum['tokens_in'] + token_sum['tokens_out'])
    # st.session_state.invoice_summary_df = invoice_summary_df
  except:
    st.error("Failed to retrieve invoice summary")
    invoice_summary_df = pd.DataFrame()
    token_sum = None

  try:

    line_items_df = parse_line_items_in_(gpt_response,
                            counter=counter)

    line_items_df = pd.DataFrame(line_items_df)
  except:
    line_items_df = pd.DataFrame()
    st.error("failed to retrieve line items")
  return invoice_summary_df, line_items_df, token_sum

# @st.cache_data()
# def parse_slow_but_thorough_response(gpt_response,
#                        match_to_client_toggle_on,
#                        storecodes_df,
#                        match_to_asin_toggle_on):
#   res_summary = []
#   res_items = []
#   pat = re.compile(r"item",re.I)
#   # collector=[]
#   pattern = re.compile(r'\{.*?\}')
#   res_summary = {}

#   for idx, line in enumerate(gpt_response.splitlines()):
#     try:
#       key, value = line.split(": ")
#       key = key.strip('- ').strip()
#       res_summary[key] = value
#     except:
#       pass

#     if pat.search(line):
#       break
#       # Assuming that items are placed one after another in the string
#       # Continue processing lines until an empty line or end of string is encountered
#   lines = gpt_response.splitlines()[idx+1:]
#   # lines = list(set(lines))
#   line_text = ''.join(lines)
#   # st.write(line_text)
#   matches = re.findall(r'\{.*?\}', line_text)
#   if len(matches) >0:
#   # st.write(matches)
#     for match in matches:

#       try:
#         extracted_dict = eval(match)  # Convert string representation of dictionary to an actual dictionary
#       except:
#         extracted_dict = match
#     #           # st.write(extracted_dict)
#       res_items.append(extracted_dict)
#   else:
#     name_pattern = re.compile(r"Item name:(.*)Item")
#     quantity_pattern = re.compile(r"Item quantity: (\d+)")
#     unit_price_pattern = re.compile(r"Item unit price:.*?([0-9.,]+)")
#     total_price_pattern = re.compile(r"Item total price:.*?([0-9.,]+)")
#     st.write("created patterns 209")
#     # Extract values using the patterns
#     item_name = name_pattern.search(line_text).group(1) if name_pattern.search(line_text) else None
#     item_quantity = quantity_pattern.search(line_text).group(1) if quantity_pattern.search(line_text) else None
#     item_unit_price = unit_price_pattern.search(line_text).group(1) if unit_price_pattern.search(line_text) else None
#     item_total_price = total_price_pattern.search(line_text).group(1) if total_price_pattern.search(line_text) else None
#     res_items.append({
#         'Item name': item_name,
#         'Item quantity': item_quantity,
#         'Item unit price': item_unit_price,
#         'Item total price': item_total_price
#     })
#   # st.write(res_items)
#   # st.write(res_summary)
#   if match_to_client_toggle_on:
#     # try:
#     invoice_receiver = res_summary['Issued to business']
#     (parsed_client_llc, 
#       parsed_client_code, 
#       parsed_store_name) = match_to_store_code(storecodes_df,
#                           match_to_client_toggle_on,
#                           invoice_receiver)
    
#     res_summary['LLC'] =parsed_client_llc 
#     res_summary['store_code']=parsed_client_code
#     res_summary['amazon_store_name'] = parsed_store_name
#     # except:
#     #     pass
#   # st.write(res_items)
#   res_summary_df = pd.DataFrame.from_dict(res_summary,orient='index').reset_index()

#   res_summary_df.columns = ['text','item_value']
#   res_items_df = pd.DataFrame(res_items)
#   for col_idx in [2,3,4]:
#       try:
#         res_items_df.iloc[:,col_idx] = res_items_df.iloc[:,col_idx].str.replace("[$,]","",regex=True).astype(float)
#       except:
#         pass
#   return res_summary_df, res_items_df

#++++++++++++++++++++++++++++++++++++++++FAST AND FURIOUS PARSING+++++++++++++++++++++++++++++++++++++++++++++++
@st.cache_data()
def fast_and_furious_parsing(_textract_client,
                     _image,
                     counter = None):
    # Convert PIL image to byte array
    img_byte_arr = io.BytesIO()
    _image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    return _textract_client.analyze_expense(Document={'Bytes': img_byte_arr})

@st.cache_data()
def get_summary_fields(r):

  res_summary = []
  for item in r["ExpenseDocuments"]:
      # Extract key-value pairs
      for i in item["SummaryFields"]:
          text = i["Type"]["Text"]
          try:
            label = i["LabelDetection"]["Text"]
          except:
            label=None
          value = i["ValueDetection"]["Text"]
          try:
            gr = i["GroupProperties"]["Text"]
          except:
            gr=None
          page_num = i["PageNumber"]
          res_summary.append([text, label, value, gr, page_num])
  sum_df =  pd.DataFrame(res_summary,
             columns=['text','label','value','group','page_num']).drop_duplicates()
  try:
    # [-1] because sometimes the receiver name has a person name followed by company name
    invoice_receiver = sum_df.query("text.str.lower()=='receiver_name'").value.tolist()[-1]
  except:
    invoice_receiver = None
  try:
    issued_by = list(sum_df.query("text.str.lower()=='vendor_name'").value.unique())
    issued_by =[i for i in issued_by if i != invoice_receiver]
    issued_by = issued_by[0]
  except:
    issued_by = None
  try:
    invoice_date = sum_df.query("text.str.lower()=='invoice_receipt_date'").value.tolist()[0]
  except:
    invoice_date = None
  try:
    due_date = sum_df.query("text.str.lower()=='due_date'").value.tolist()[0]
  except:
    due_date = None

  try:
    invoice_number = sum_df.query("text.str.lower()=='invoice_receipt_id'").value.tolist()[0]
  except:
    invoice_number = None
  try:
    total = sum_df.query("text.str.lower()=='total'").value.tolist()[0]
    total = re.sub('[$,]','',total)
    total = re.search("(\d+\.*\d*)",total).group(1)
    total = float(total)
  except:
    total = None
  try:
    tax = sum_df.query("text.str.lower()=='tax'").value.tolist()[0]
    tax = re.sub('[$,]','',tax)
    tax = re.search("(\d+\.*\d*)",tax).group(1)
    tax = float(tax)
  except:
    tax = None


  return (sum_df, invoice_receiver, issued_by, invoice_date, 
          due_date, invoice_number, total, tax)


def get_line_items_df(r):
  line_items = []
  for item in r['ExpenseDocuments'][0]['LineItemGroups']:
    for i in item['LineItems']:
      for j in i['LineItemExpenseFields']:
        type_text = j['Type']['Text']
        type_text_confidence = j['Type']['Confidence']
        try:
          label_text = j['LabelDetection']['Text']
          label_text_confidence = j['LabelDetection']['Confidence']
        except:
          label_text = None
          label_text_confidence = None

        value_text = j['ValueDetection']['Text']
        value_text_confidence = j['ValueDetection']['Confidence']
        page_num = j['PageNumber']
        geometry = j['ValueDetection']['Geometry']
        left = geometry['BoundingBox']['Left']
        top = geometry['BoundingBox']['Top']
        width= geometry['BoundingBox']['Width']
        height = geometry['BoundingBox']['Height']
        line_items.append((type_text,
                          label_text,
                          value_text,
                          left,
                          top,
                          width,
                          height,
                          page_num,
                          type_text_confidence,
                          label_text_confidence,
                          value_text_confidence))

  cols = ['type_text',
          'label_text',
          'value_text',
          'left',
          'top',
          'width',
          'height',
          'page_num',
          'type_text_confidence',
          'label_text_confidence',
          'value_text_confidence',
          ]
  return  pd.DataFrame(line_items, columns=cols)


def parse_line_items_df(line_items_df):
  df = line_items_df.copy()
  df['type_text'] = df['type_text'].str.lower()
  df['label_text'] = df['label_text'].str.lower()

  boundaries = df[df['type_text'] == 'expense_row'].index.tolist()
  allowed_names = ['item','other']
  # Initialize starting index
  start_index = 0

  # List to store the extracted items
  items = []

  for end_index in boundaries:
      # Extracting the values for each field based on the conditions
      try:
          item_name = df[(df['type_text'].str.lower()=='item') & 
            (start_index <= df.index) & (df.index < end_index)]['value_text'].values
      except:
        try:
            item_name = df[(df['type_text'].str.lower()=='other') & 
            (start_index <= df.index) & (df.index < end_index)]['value_text'].values
        except:
          item_name=None
      expense_row = df.loc[end_index,'value_text']
      try:
        quantity = df[(df['type_text']=='quantity') & (start_index <= df.index) & (df.index < end_index)]['value_text'].tolist()[0]
      except:
         quantity = None
      unit_price = df[(df['type_text']=='unit_price') & (start_index <= df.index) & (df.index < end_index)]['value_text'].values
      amount = df[(df['type_text']=='price') & (start_index <= df.index) & (df.index < end_index)]['value_text'].values
      # item_name0 = df.loc[end_index,'value_text'].tolist()[0].split()
      # Append the extracted values to items list
      items.append({
          'item_name': item_name[0] if item_name else None,
          'quantity': quantity,
          'unit_price': unit_price[0] if len(unit_price)>0 else None,
          'amount': amount[0] if len(amount)>0 else None
      })
      
      # Update the start_index for the next loop
      start_index = end_index + 1

  # Convert items list to DataFrame
  items_df = pd.DataFrame(items)
  for col_name in ['quantity','unit_price','amount']:
    try:
      items_df[col_name] = items_df[col_name].str.replace("[$,]","",regex=True)
    except:
       pass
  # items_df['quantity'] = items_df['quantity'].str.replace("[$,]","",regex=True).str.extract(r'(\d+)')
  # items_df['unit_price'] = items_df['unit_price'].str.replace("[$,]","",regex=True).str.extract(r"(\d+\.*\d*)")
  # items_df['amount'] = items_df['amount'].str.replace("[$,]","",regex=True).str.extract(r"(\d+\.*\d*)")
  return items_df

@st.cache_data()
def get_line_items(r):
  line_items_df = get_line_items_df(r)
  items_df = parse_line_items_df(line_items_df)
  return items_df
