import pydeck as pdk 
import pandas as pd
from datetime import datetime as dt, timedelta 
from datetime import date, time
import re 
import streamlit as st 

st.set_page_config(layout='wide')

'''
# The Dunkin' Donut Data Viewer

Hello! I am the Dunkin' Donut Data Viewer. If you're looking for a place to stop for a Donut you're in the right place!

I am an app built to show how quick and lightweight geospatial data tools can be set up with Streamlit and PyDeck.
'''

# read in data and drop any rows without location coordinates as they cannot be mapped
df = pd.read_csv('dunkin_stores.csv')
df.dropna(subset=['loc_lat', 'loc_long'], inplace=True)

# set up options
with st.sidebar:
    '''
    ### Filter options
    '''
    FILTER_OPEN = st.selectbox('Show open only: ', (True, False))
    FILTER_CARD = st.selectbox('Dunkin\' Card accepted only ', (False, True))
    FILTER_DRIVETHRU = st.selectbox('Drive Thru only: ', (False, True))
    FILTER_BASKIN = st.selectbox('Baskin Robbins only: ', (False, True))
    FILTER_MOBILE = st.selectbox('Mobile ordering only: ', (False, True))


STATE_SELECT = st.multiselect('If there is a Dunkin\' Donuts in your state you can search for it below:', set(df['state']))

df.fillna('', inplace=True)

# time cols for filtering whether a store is open
time_cols = {'Monday': 'mon_hrs', 
    'Tuesday': 'tue_hrs', 
    'Wednesday': 'wed_hrs', 
    'Thursday': 'thu_hrs', 
    'Friday': 'fri_hrs', 
    'Saturday': 'sat_hrs', 
    'Sunday': 'sun_hrs'}

# find the current date to compare
now = dt.now()

# get the current day but at midnight 
midnight_today = date.today()

# day to compare to 
col_to_use = time_cols.get(now.strftime('%A'))

# find whether a DD is open 
def is_open(time_frame):
    
    if time_frame == 'Open 24 Hours':
        return True

    if time_frame == 'Closed':
        return False

    if time_frame is None:
        return False

    # strip the opening times out of that col 
    opens_at = re.search('^[0-9]{1,2}:[0-9]{2} [A-z]{2}', time_frame).group()
    closes_at = re.search('- [0-9]{1,2}:[0-9]{2} [A-z]{2}', time_frame).group()
    
    # strip out the time data 
    opens_at_time = dt.strptime(opens_at, "%I:%M %p").time()
    closes_at_time = dt.strptime(closes_at, "- %I:%M %p").time()

    # combine the hour and day 
    opens_at_dt = dt.combine(midnight_today, opens_at_time)
    closes_at_dt = dt.combine(midnight_today, closes_at_time)

    # check if it's after opening and before closing time 
    if now > opens_at_dt and now < closes_at_dt:
        return True 
    else:
        return False


# build the is_open column 
df['is_open'] = df[col_to_use].apply(is_open)

# build lists of cols for filtering
geospatial_cols = ['loc_long', 'loc_lat']
named_geospatial_cols = ['city', 'state']
feature_cols = ['drive-thru', 'has-baskin-robbins', 'dunkin-card', 'mobile-order']


# filter logic 
if FILTER_OPEN:
    df = df[df['is_open'] == True]

if FILTER_DRIVETHRU:
    df = df[df['drive-thru'] == True]

if FILTER_MOBILE:
    df = df[df['mobile-order'] == True]

if FILTER_BASKIN:
    df = df[df['has-baskin-robbins'] == True]

if FILTER_CARD:
    df = df[df['dunkin-card'] == True]

if STATE_SELECT:
    df = df[df['state'].isin(STATE_SELECT)]


if len(df) == 0:
    st.info('There are no Dunkin\' Donuts that meet the current selection, please try a looser set of search terms.')

else:
    # set path to donut image 
    DONUT = "https://upload.wikimedia.org/wikipedia/commons/7/72/Farm-Fresh_donut.png"

    # define the view (if fewer than 10 locations focus on one corner)
    if len(df) >= 10:
        view = pdk.data_utils.compute_view(df[["loc_long", "loc_lat"]], 0.9)
    else: 
        view = pdk.ViewState(longitude=max(df['loc_long']),
        latitude=max(df['loc_lat']), zoom=4)

    icon_data = {
        # Icon from Wikimedia
        "url": DONUT,
        "width": 20,
        "height": 20,
        "anchorY": 20,
    }

    # populate with image data 
    df['icon_data'] = None
    for i in df.index:
        df['icon_data'][i] = icon_data

    # build the icon layer 
    icon_layer = pdk.Layer(
        type="IconLayer",
        data=df,
        get_icon="icon_data",
        get_size=4,
        size_scale=15,
        get_position=["loc_long", "loc_lat"],
        pickable=True
    )

    # set up the tool tip
    tooltip = {
   "html": "<b>{address_line_1},</b> <br/> {address_line_2}, <br/> {city}, <br/> {zip}",
   "style": {
        "backgroundColor": "#e11383",
        "color": "#f5821f"
   }
}

    # compile the map 
    r = pdk.Deck(layers=[icon_layer], initial_view_state=view, tooltip={"text": "One"})

    # set up the chart 
    st.pydeck_chart(r)
