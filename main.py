from asyncio.windows_events import NULL
from operator import index
import time
from turtle import up
import streamlit as st
import phonenumbers as ph
import pandas as pd
import boto3
import datetime
import re
import pymysql
from PIL import Image


header = st.container()
col1, col2 = st.columns(2)


def validate_date(date):
    year = int(date[0:4])
    month = date[5:7]
    day = date[8:10]
    if month[0] == '0':
        month = int(month[1])
    else:
        month = int(month)
    if day[0] == '0':
        day = int(day[1])
    else:
        day = int(day)
    if datetime.datetime(year, month, day).strftime("%a") != 'Fri':
        return False


def select_options(series):
    i = series[0]
    series[0] = ''
    series.loc[series.index.max()+1] = i
    return series


@st.cache(allow_output_mutation=True, hash_funcs={"_thread.RLock": lambda _: None})
def init_connection():
    return pymysql.connect(host='timesheet.c65dmnfzxks5.ap-south-1.rds.amazonaws.com',
                           user='admin',
                           passwd='timesheetAutomation9',
                           database='timesheet_db',
                           port=3306)


conn = init_connection()
cool = conn.cursor()
#  Function to take phone number and return First Name


def getNameFromPhone(phone_number):
    df = pd.read_sql_query("SELECT * from referrance;", conn)
    candidate_fname = df.loc[df.phone == str(phone_number), 'fname']
    candidate_clients = df.loc[df.phone == str(phone_number), 'clients']
    candidate_fname.reset_index(drop=True, inplace=True)
    display_candidate_fname = str(candidate_fname.values[0])
    display_candidate_client = candidate_clients.reset_index(drop=True)
    return display_candidate_fname, display_candidate_client


class upload_image:
    def __init__(self, img, key):
        self.img = img
        self.key = key
        s3 = boto3.resource(
            service_name='s3',
            region_name='ap-south-1',
            aws_access_key_id='AKIARJQTJPNVAZYJOPQZ',
            aws_secret_access_key='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')
        s3.Object('timesheet3', key).put(Body=img)

    def get_key(self):
        return str(self.key)


################################################
################# Main Program #################
################################################
wolf_logo = 'https://timesheet1.s3.ap-south-1.amazonaws.com/Adil/NeuEra/2022-02-04___Screenshot+(1).png'

with header:
    # st.image(image=wolf_logo) TO BE CONTINUEEEED//////////////////.....................\\\\\\\\\\\\\\\\\\\\\
    st.title("Timesheet Entry Portal")

# img_url = 's3://timesheet3/{}'.format(key)

# Get Phone Number
input_cell_phone = col1.text_input("Enter your Cell Number:")
try:
    if not len(input_cell_phone) >= 10:
        st.warning('Please enter your cell-number to continue...')
        st.stop()
    else:
        phone_digits = ph.parse(input_cell_phone, "US").national_number
        # Use the Phone digits and get Name from Ref file
        display_candidate_fname = getNameFromPhone(phone_digits)[0]
        display_candidate_client = getNameFromPhone(phone_digits)[1]
        st.subheader("👋 Welcome " + display_candidate_fname)
        client_name = st.selectbox(
            label="Select your End Client", options=select_options(display_candidate_client))

        if client_name != '':
            friday_date = st.date_input(label="Select Friday's Date")
            if validate_date(str(friday_date)) == False:
                st.warning("Please Enter only Friday's Date Only")
            elif validate_date(str(friday_date)) != False:
                hours_form = st.form(key="form1")
                hours_entered = hours_form.number_input(
                    "How many hours this week?", step=1, value=0, max_value=100)
                timesheet = hours_form.file_uploader(
                    label="Upload Timesheet Screenshot", type=['png', 'jpg', 'pdf'])
                submit_form_button = hours_form.form_submit_button(
                    label="Submit")

                if submit_form_button:
                    if (hours_entered) == 0.0 or 0:
                        st.warning('Please Enter hours')

                    elif timesheet == None:
                        st.warning("Please upload timesheet")

                    else:
                        st.subheader('Please Confirm the Entry')
                        confirm = st.form(key='021')
                        confirm_client = confirm.text_input(
                            'Selected Client', value=str(client_name), disabled=True)
                        confirm_hours = confirm.number_input(
                            'Entered Hours', value=hours_entered, disabled=True)
                        image = Image.open(timesheet)
                        confirm_image = confirm.image(image, 'Timesheet')
                        confirm_button = confirm.form_submit_button('Confirm')

                        if confirm_button:
                            upload_in_s3 = upload_image(timesheet, key=(display_candidate_fname+'/' +
                                                                        client_name+'/'+(re.sub('/', '-', str(friday_date)))+'{}'.format(timesheet.name[-4:])))

                            cool.execute("insert into incoming_data values('{}','{}','{}','{}','{}')".format(re.sub('/', '-', str(friday_date)), str(display_candidate_fname), str(
                                client_name), float(hours_entered), ('https://timesheet3.s3.ap-south-1.amazonaws.com/'+upload_in_s3.get_key())))

                            conn.commit()
                            st.write('Form Submitted Successfully')


except IndexError:
    st.warning("Entered Phone Number is Not registered")
