import io
import pandas as pd
import streamlit as st
import re
import fitz
from PIL import Image
import json
import re
import pdfplumber



def wrap_into_json(key, value):
    return json.dumps({key: value})

# per 1K tokens
gpt_pricing = {'gpt-3.5-turbo-1106': {'tokens_in' : 0.001,
                                 'tokens_out': 0.002},
               'gpt-3.5-turbo-instruct' : {'tokens_in':0.0015,
                                        'tokens_out':0.002},
               'gpt-4-1106-preview': {'tokens_in':0.01,
                                        'tokens_out':0.03},
               'gpt-4-1106-vision-preview': {'tokens_in':0.01,
                                        'tokens_out':0.03},
               'gpt-4-vision-preview':{'tokens_in':0.01,
                                        'tokens_out':0.03}
               }




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

# @st.cache_data()
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


    




# @st.cache_data()
def extract_words_from_pdf(uploaded_file,
                           max_words_per_page=1700,
                           counter=None):


    all_extracted_words = []
    pages_used_for_extraction = []
    with pdfplumber.open(uploaded_file) as pdf:
        # Initialize the height offset as 0
        height_offset = 0
        for page_number, pdf_page in enumerate(pdf.pages):
            try:
                # Extract words from the current page
                extracted_words = pdf_page.extract_words()
                if len(extracted_words)>max_words_per_page:
                   pass
                else:

                  # If this is not the first page, adjust the vertical coordinates
                  if page_number > 0:
                      for word in extracted_words:
                          word['top'] += height_offset
                          word['bottom'] += height_offset

                  # Append adjusted words to the main list
                  all_extracted_words.extend(extracted_words)
                  pages_used_for_extraction.append(page_number)

                  # Update the height offset by adding the height of the current page
                  height_offset += pdf_page.height

            except Exception as e:
                
                pass

    return normalize_extracted_words(all_extracted_words), pages_used_for_extraction

def get_line_items_df(gpt_response):
    if isinstance(gpt_response, str):
        json_response = json.loads(gpt_response)
    line_items = gpt_response['Line items']
    return pd.DataFrame.from_dict(gpt_response['Line items'],
                       orient='columns')


def get_summary_df(gpt_response):
    # gpt_response = completion['choices'][0]['message']['content']
    if isinstance(gpt_response, str):
        gpt_response = json.loads(gpt_response)
    summary = gpt_response['Summary']
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


def pdf_to_images(pdf_file):
    # Load the PDF file
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        images = []
        # pdf_pages = []
        for page_number in range(len(doc)):
            # Get the page
            page = doc.load_page(page_number)
            # st.write("loaded page")
            # page_document = fitz.open()
            # page_document.insert_page(page_number, page)
            # st.write("inserted page")
            # Render page to an image
            pix = page.get_pixmap()
            # Store the image as PIL.Image
            images.append(Image.open(io.BytesIO(pix.tobytes("png"))))
            # pdf_pages.append(page_document)
        # pdf_file.seek[0]
        doc.close()
        return images
    except:
        st.error("Error: Invalid file format")




