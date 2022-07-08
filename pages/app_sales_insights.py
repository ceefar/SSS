# app_sales_insights.py

# ---- imports ----

# for web app 
import streamlit as st
import streamlit.components.v1 as stc
# for charts, dataframes, data manipulation
import altair as alt
import pandas as pd
# for date time objects
import datetime
# for db integration
import db_integration as db 


# ---- db connection ----

# connection now started and passed around from db_integration once using singleton
conn = db.init_connection()

# perform get/fetch query - uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=600)
def run_query(query):
    """ self referencing """
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


# ---- main web app ----

with st.sidebar:
    devmode = st.checkbox("Portfolio Mode")

def run():

    # BASE QUERIES queries
    currentdate = run_query("SELECT DATE(GETDATE())")
    yesterdate = run_query("SELECT DATE(DATEADD(day,-1,GETDATE()))")
    firstdate = run_query("SELECT current_day FROM redshift_bizinsights ORDER BY current_day ASC LIMIT 1")
    currentdate = currentdate[0][0]
    yesterdate = yesterdate[0][0]
    firstdate = firstdate[0][0]

    # ALTAIR CHART item type sold by hour of day
    with st.container():
        st.write(f"### :bulb: Insight - Sales vs Time of Day") 
        st.write("##### AKA Popularity")
        st.write("Includes everything except the 3 most popular items") # because they are all favoured so really theres 15 not 3
        st.write("##")

        stores_list = ['Chesterfield', 'Uppingham', 'Longridge',  'London Camden', 'London Soho']
        altairChartSelectCol1, altairChartSelectCol2 = st.columns(2)
        with altairChartSelectCol1:
            current_day = st.date_input("What Date Would You Like Info On?", datetime.date(2022, 7, 5), max_value=yesterdate, min_value=firstdate)  
        with altairChartSelectCol2:
            store_selector = st.selectbox("Choose The Store", options=stores_list, index=0) 

        # PORTFOLIO 
        # ADD FUCKING COMMENTS && EXPANDER && PORTFOLIO MODE CHECKBOX TO SIDEBAR 
        if devmode:
            with st.expander("Complex 'Join/Group By' SQL Query (converted from original complex MySQL Query)"):       
                with st.echo():
                    # note - data hosted on redshift, moved to s3 bucket, then transferred to snowflake warehouse
                    # inner join data and items tables on matching transaction ids, for each store, at set dates for each item
                    cups_by_hour_query = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                                        i.item_name FROM redshift_customeritems i inner join redshift_customerdata d on (i.transaction_id = d.transaction_id)\
                                        WHERE store = '{store_selector}' AND DATE(d.timestamp) = '{current_day}' GROUP BY d.timestamp, i.item_name"
                    hour_cups_data = run_query(cups_by_hour_query)
        else:
            cups_by_hour_query = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                                i.item_name FROM redshift_customeritems i inner join redshift_customerdata d on (i.transaction_id = d.transaction_id)\
                                WHERE store = '{store_selector}' AND DATE(d.timestamp) = '{current_day}' GROUP BY d.timestamp, i.item_name"
            hour_cups_data = run_query(cups_by_hour_query)

        st.write("##")
        
        just_names_list = []
        just_hour_list = []
        just_cupcount_list = []
        for cups_data in hour_cups_data:
            just_cupcount_list.append(cups_data[0])
            just_hour_list.append(cups_data[1])
            just_names_list.append(cups_data[2])
        
        source4 = pd.DataFrame({
        "DrinkName": just_names_list,
        "CupsSold":  just_cupcount_list,
        "HourOfDay": just_hour_list
        })

        bar_chart4 = alt.Chart(source4).mark_bar().encode(
            color="DrinkName:N", # x="month(Date):O",
            x="sum(CupsSold):Q",
            y="HourOfDay:N"
        ).properties(height=300)

        text4 = alt.Chart(source4).mark_text(dx=-10, dy=3, color='white', fontSize=12, fontWeight=600).encode(
            x=alt.X('sum(CupsSold):Q', stack='zero'),
            y=alt.Y('HourOfDay:N'),
            detail='DrinkName:N',
            text=alt.Text('sum(CupsSold):Q', format='.0f')
        )

        # ---- end altair table creation ----
        # note hasn't been initialised yet tho


        # ---- start new insights calculation ----

        # BIG N0TE!
        #   - 100 need try except incase hour data is missing or all data is missing btw
 
        # sum_9 = sum(source4['HourOfDay'] == 9)
        # details = source4.apply(lambda x : True if x['HourOfDay'] == 9 else False, axis = 1)
        # temptemp = len(details[details == True].index)
        # print(source4.iloc[[18]])

        # FIXME 
        # TODO 
        # PORTFOLIO - PUT THIS SHIT IN ECHO, MANS IS A GOATPANDA NOW... jesus i need to sleep XD
        # get sum of cupsSold column based on condition (HourOfDay == x)
        sum9cups = source4.loc[source4['HourOfDay'] == 9, 'CupsSold'].sum()
        sum10cups = source4.loc[source4['HourOfDay'] == 10, 'CupsSold'].sum()
        sum11cups = source4.loc[source4['HourOfDay'] == 11, 'CupsSold'].sum()
        sum12cups = source4.loc[source4['HourOfDay'] == 12, 'CupsSold'].sum()

        # get unique values in HourOfDay column to loop (returns array object so convert to list)
        # note returned list is not sorted (doesn't really make a difference but meh)
        # uniqueCols = source4['HourOfDay'].unique()
        # print(type(uniqueCols)) # -> numpy.ndarray
        # uniqueCols = list(uniqueCols)
        
        uniqueCols = sorted(list(source4['HourOfDay'].unique()))

        print(f"{sum9cups = }")
        print(f"{sum10cups = }")
        print(f"{sum11cups = }")
        print(f"{sum12cups = }")
        print(f"{uniqueCols = }")

        randolist = []
        results_dict = {}
        for value in uniqueCols:
            cupForHour = source4.loc[source4['HourOfDay'] == value, 'CupsSold'].sum()
            results_dict[value] = cupForHour

        dont_print_2 = [randolist.append(f"{value} = {source4.loc[source4['HourOfDay'] == value, 'CupsSold'].sum()}") for value in uniqueCols]
        print(f"{randolist = }")

        print(f"{results_dict = }")

        sort_by_value = dict(sorted(results_dict.items(), key=lambda x: x[1])) 
        print(f"{sort_by_value = }")       

        sort_by_value_list = list(map(lambda x: (f"{x[1]} items sold at {x[0]}pm") if x[0] > 11 else (f"{x[1]} items sold at {x[0]}am"), sort_by_value.items()))

        worst_performer = sort_by_value_list[0]
        best_performer = sort_by_value_list[-1]

        print(sort_by_value_list)
        print(f"{worst_performer = }") 
        print(f"{best_performer = }") 


        print("- - - ")

        # end insights calc

        
        METRIC_ERROR = """
            Wild MISSINGNO Appeared!\n
            No Data for {} on {}\n
            ({})
            """

        INSIGHT_TIP_1 = f"""
            SAVING INSIGHT!\n
            Try to reduce overhead (staff hours) during prolonged quieter periods for huge savings\n
            Consider cutting back on products with less sales and smaller margins\n
            Worst Performer = {worst_performer} - Consider offers at this time + less staff\n
            Best Performer = {best_performer} - Ensure staff numbers with strong workers at this time to maximise sales
            """

        # if no data returned for store and day then show missingno (missing number) error
        if hour_cups_data:
            st.altair_chart(bar_chart4 + text4, use_container_width=True)
            with st.expander("Gain Insight"):
                insightCol1, insightCol2 = st.columns([1,5])
                insightCol2.success(INSIGHT_TIP_1)
                insightCol1.image("imgs/insight.png", width=140)
                #print(store_selector)
                # if london then join
                #insightCol1.image(f"imgs/coffee-shop-light-{}.png", width=140)
        else:
            altairChartCol1, altairChartCol2 = st.columns([2,2])
            try:
                altairChartCol2.image("imgs/Missingno.png")
            except FileNotFoundError:
                pass
            altairChartCol1.error(METRIC_ERROR.format(store_selector, current_day, "no selected or previous day available"))
            st.write("##")
            st.sidebar.info("Cause... Missing Numbers... Get it...")

        st.write("##")
        st.write("##")
        st.write("---")











    # ---- NEW ----

        
    # ALTAIR CHART product sold by hour of day (COMPARE 2?!) - INDIVIDUAL ITEM VERSION OF ABOVE
    with st.container():
        st.write(f"### :bulb: Insight - Compare Two Items") 

        # new store selector
        store_selector_2 = st.selectbox(label="Choose The Store", key="store_select_2", options=stores_list, index=0) 
        
        # new date selector
        current_day_2 = st.date_input("What Date Would You Like Info On?", datetime.date(2022, 7, 5), max_value=yesterdate, min_value=firstdate, key="day_select_2")  

        # get only main item name
        get_main_item = run_query(f"SELECT DISTINCT i.item_name FROM redshift_customeritems i INNER JOIN redshift_customerdata d on (i.transaction_id = d.transaction_id) WHERE d.store = '{store_selector_2}'")
        final_main_item_list = []
        for item in get_main_item:
            final_main_item_list.append(item[0])
    
        # select any item from the store for comparison
        item1Col, _, item2Col = st.columns([3,1,3])
        with item1Col:
            item_selector_1 = st.selectbox(label=f"Choose An Item From Store {store_selector_2}", key="item_selector_1", options=final_main_item_list, index=0) 
        with item2Col:
            item_selector_2 = st.selectbox(label=f"Choose An Item From Store {store_selector_2}", key="item_selector_2", options=final_main_item_list, index=1)

        # MAKE FUNCTION AND REUSE THE QUERY FFS
        cups_by_hour_query_2 = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                            i.item_name FROM redshift_customeritems i inner join redshift_customerdata d on (i.transaction_id = d.transaction_id)\
                            WHERE store = '{store_selector_2}' AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_1}' GROUP BY d.timestamp, i.item_name"
        hour_cups_data_2 = run_query(cups_by_hour_query_2)

        cups_by_hour_query_3 = f"SELECT COUNT(i.item_name) AS cupsSold, EXTRACT(HOUR FROM TO_TIMESTAMP(d.timestamp)) AS theHour,\
                            i.item_name FROM redshift_customeritems i inner join redshift_customerdata d on (i.transaction_id = d.transaction_id)\
                            WHERE store = '{store_selector_2}' AND DATE(d.timestamp) = '{current_day_2}' AND i.item_name = '{item_selector_2}' GROUP BY d.timestamp, i.item_name"
        hour_cups_data_3 = run_query(cups_by_hour_query_3)

        #print(hour_cups_data_2)
        #print(hour_cups_data_3)

        # WHAT WE WANT HERE IS ADVANCED MODE FOR SELECTING EVEN MORE DETAIL
        # AND PROPER COMPARISON OF 2 ITEMS

        st.write("##")

        # CREATE AND PRINT THE ALTAIR CHART

        # MAKE WHOLE THING A FUNCTION (FUNCTION OF FUNCTIONS TBF - BREAK UP AT RELEVANT POINTS) AND CAN REUSE IT TOO! 

        just_names_list_2 = []
        just_hour_list_2 = []
        just_cupcount_list_2 = []
        for cups_data in hour_cups_data_2:
            just_cupcount_list_2.append(cups_data[0])
            just_hour_list_2.append(cups_data[1])
            just_names_list_2.append(cups_data[2])
        
        just_names_list_3 = []
        just_hour_list_3 = []
        just_cupcount_list_3 = []
        for cups_data in hour_cups_data_3:
            just_cupcount_list_3.append(cups_data[0])
            just_hour_list_3.append(cups_data[1])
            just_names_list_3.append(cups_data[2])

        just_names_list_2.extend(just_names_list_3)
        just_hour_list_2.extend(just_hour_list_3)
        just_cupcount_list_2.extend(just_cupcount_list_3)

        source2 = pd.DataFrame({
        "DrinkName": just_names_list_2,
        "CupsSold":  just_cupcount_list_2,
        "HourOfDay": just_hour_list_2
        })

        source3 = pd.DataFrame({
        "DrinkName": just_names_list_3,
        "CupsSold":  just_cupcount_list_3,
        "HourOfDay": just_hour_list_3
        })

        bar_chart2 = alt.Chart(source2).mark_bar().encode(
            color="DrinkName:N", # x="month(Date):O",
            x="sum(CupsSold):Q",
            y="HourOfDay:N"
        ).properties(height=300)

        text2 = alt.Chart(source2).mark_text(dx=-10, dy=3, color='white', fontSize=12, fontWeight=600).encode(
            x=alt.X('sum(CupsSold):Q', stack='zero'),
            y=alt.Y('HourOfDay:N'),
            detail='DrinkName:N',
            text=alt.Text('sum(CupsSold):Q', format='.0f')
        )

        st.altair_chart(bar_chart2 + text2, use_container_width=True)



        # PIE CHART - OBVS MOVE BUT DO KEEP THIS CODE AS LIKELY DO A PIE CHART SOON ENOUGH
        #pie_chart1 = alt.Chart(source2).mark_arc(innerRadius=50).encode(
        #    #color="DrinkName:N", # x="month(Date):O",
        #    theta="sum(CupsSold):Q",
        #    color="HourOfDay:N"
        #).properties(height=300)
        #
        #st.altair_chart(pie_chart1, use_container_width=True)



        st.write("##")
        st.write("##")
        st.write("---")





############# FOR MENU PRINT ################
    
    # new store selector
    store_selector_4 = st.selectbox(label="Choose The Store", key="store_select_4", options=stores_list, index=0) 
    
    # get every valid unique combination of item, size and flavour, returned as tuple for the selected store only
    get_menu = run_query(f"SELECT DISTINCT i.item_name, i.item_size, i.item_flavour FROM redshift_customeritems i INNER JOIN redshift_customerdata d on (i.transaction_id = d.transaction_id) WHERE d.store = '{store_selector_4}'")
    # query for all below
    # get_menu = run_query("SELECT DISTINCT item_name, item_size, item_flavour AS unique_items FROM redshift_customeritems")
    final_menu = []
    for item in get_menu:
        final_item = []
        # remove any None types from the tuple returned from the query
        dont_print = [final_item.append(subitem) for subitem in item if subitem is not None]
        # join each element of iterable in to one string with spaces between
        menu_item = (" ".join(final_item))
        # format and append all items to a list for user selection
        menu_item = menu_item.title().strip()
        final_menu.append(menu_item)

    # select any item from the store for comparison
    item_selector_1 = st.selectbox(label=f"Choose An Item From Store {store_selector_4}", key="item_selector_1", options=final_menu, index=0) 

    st.write("##")
    st.write("---")


###############################################











    
    ## ADD TO CONTAINER BELOW


    breakfast_sales = db.get_cups_sold_by_time_of_day(1)
    earlylunch_sales = db.get_cups_sold_by_time_of_day(2)
    latelunch_sales = db.get_cups_sold_by_time_of_day(3)
    afternoon_sales = db.get_cups_sold_by_time_of_day(4)

    ChaiLatte_Breaky = breakfast_sales[0]
    Cortado_Breaky = breakfast_sales[1]
    Espresso_Breaky = breakfast_sales[2]
    FlatWhite_Breaky = breakfast_sales[3]
    FlavouredHotChocolate_Breaky = breakfast_sales[4]
    FlavouredIcedLatte_Breaky = breakfast_sales[5] #####
    FlavouredLatte_Breaky = breakfast_sales[6]
    Frappes_Breaky = breakfast_sales[7]
    GlassOfMilk_Breaky = breakfast_sales[8]
    HotChocolate_Breaky = breakfast_sales[9]
    IcedLatte_Breaky = breakfast_sales[10]
    Latte_Breaky = breakfast_sales[11]
    LuxuryHotChocolate_Breaky = breakfast_sales[12]
    Mocha_Breaky = breakfast_sales[13]
    RedLabelTea_Breaky = breakfast_sales[14]
    Smoothies_Breaky = breakfast_sales[15] 
    SpecialityTea_Breaky = breakfast_sales[16] #####

    ChaiLatte_Lunch = earlylunch_sales[0]
    Cortado_Lunch = earlylunch_sales[1]
    Espresso_Lunch = earlylunch_sales[2]
    FlatWhite_Lunch = earlylunch_sales[3]
    FlavouredHotChocolate_Lunch = earlylunch_sales[4]
    FlavouredIcedLatte_Lunch = earlylunch_sales[5]
    FlavouredLatte_Lunch = earlylunch_sales[6]
    Frappes_Lunch = earlylunch_sales[7]
    GlassOfMilk_Lunch = earlylunch_sales[8]
    HotChocolate_Lunch = earlylunch_sales[9]
    IcedLatte_Lunch = earlylunch_sales[10]
    Latte_Lunch = earlylunch_sales[11]
    LuxuryHotChocolate_Lunch = earlylunch_sales[12]
    Mocha_Lunch = earlylunch_sales[13]
    RedLabelTea_Lunch = earlylunch_sales[14]
    Smoothies_Lunch = earlylunch_sales[15]
    SpecialityTea_Lunch = earlylunch_sales[16] #####

    ChaiLatte_LateLunch = latelunch_sales[0]
    Cortado_LateLunch = latelunch_sales[1]
    Espresso_LateLunch = latelunch_sales[2]
    FlatWhite_LateLunch = latelunch_sales[3]
    FlavouredHotChocolate_LateLunch = latelunch_sales[4]
    FlavouredIcedLatte_LateLunch = latelunch_sales[5] #####
    FlavouredLatte_LateLunch = latelunch_sales[6]
    Frappes_LateLunch = latelunch_sales[7]
    GlassOfMilk_LateLunch = latelunch_sales[8]
    HotChocolate_LateLunch = latelunch_sales[9]
    IcedLatte_LateLunch = latelunch_sales[10]
    Latte_LateLunch = latelunch_sales[11]
    LuxuryHotChocolate_LateLunch = latelunch_sales[12]
    Mocha_LateLunch = latelunch_sales[13]
    RedLabelTea_LateLunch = latelunch_sales[14]
    Smoothies_LateLunch = latelunch_sales[15]
    SpecialityTea_LateLunch = latelunch_sales[16] #####

    ChaiLatte_Afternoon = afternoon_sales[0]
    Cortado_Afternoon = afternoon_sales[1]
    Espresso_Afternoon = afternoon_sales[2]
    FlatWhite_Afternoon = afternoon_sales[3]
    FlavouredHotChocolate_Afternoon = afternoon_sales[4]
    FlavouredIcedLatte_Afternoon = afternoon_sales[5] #####
    FlavouredLatte_Afternoon = afternoon_sales[6]
    Frappes_Afternoon = afternoon_sales[7]
    GlassOfMilk_Afternoon = afternoon_sales[8]
    HotChocolate_Afternoon = afternoon_sales[9]
    IcedLatte_Afternoon = afternoon_sales[10]
    Latte_Afternoon = afternoon_sales[11]
    LuxuryHotChocolate_Afternoon = afternoon_sales[12]
    Mocha_Afternoon = afternoon_sales[13]
    RedLabelTea_Afternoon = afternoon_sales[14]
    Smoothies_Afternoon = afternoon_sales[15]
    SpecialityTea_Afternoon = afternoon_sales[16] #####

    # CHART name container
    with st.container():

        # DO LIKE LEAST POP, MOST POP - OBVS FLAV ONES HAVE FLAVS SO THIS IS WHY THEY WANNA BE SECTIONED AGAIN THEMSELVES BUT MEH ANOTHER TIME
        st.write("#### Less Popular - All Days - All Stores - Volume Sold (Popularity)") # time of day popularity or sumnt?
        st.write("Consider removing the least popular products (lowest volume) for new ones, particularly if profit margins are small")
        st.write("##")

        source6 = pd.DataFrame({
        "CoffeeType": [FlatWhite_Breaky[1], FlatWhite_Lunch[1],FlatWhite_LateLunch[1],FlatWhite_Afternoon[1],
                        Latte_Breaky[1], Latte_Lunch[1],Latte_LateLunch[1],Latte_Afternoon[1],
                        FlavouredLatte_Breaky[1], FlavouredLatte_Lunch[1],FlavouredLatte_LateLunch[1],FlavouredLatte_Afternoon[1],
                        ChaiLatte_Breaky[1], ChaiLatte_Lunch[1], ChaiLatte_LateLunch[1],ChaiLatte_Afternoon[1],
                        FlavouredHotChocolate_Breaky[1], FlavouredHotChocolate_Lunch[1], FlavouredHotChocolate_LateLunch[1], FlavouredHotChocolate_Afternoon[1],
                        HotChocolate_Breaky[1], HotChocolate_Lunch[1], HotChocolate_LateLunch[1],HotChocolate_Afternoon[1],
                        LuxuryHotChocolate_Breaky[1], LuxuryHotChocolate_Lunch[1], LuxuryHotChocolate_LateLunch[1], LuxuryHotChocolate_Afternoon[1],
                        IcedLatte_Breaky[1], IcedLatte_Lunch[1], IcedLatte_LateLunch[1],IcedLatte_Afternoon[1],
                        Espresso_Breaky[1], Espresso_Lunch[1], Espresso_LateLunch[1],Espresso_Afternoon[1],
                        Frappes_Breaky[1], Frappes_Lunch[1], Frappes_LateLunch[1],Frappes_Afternoon[1],
                        Mocha_Breaky[1], Mocha_Lunch[1], Mocha_LateLunch[1],Mocha_Afternoon[1],
                        Smoothies_Breaky[1], Smoothies_Lunch[1], Smoothies_LateLunch[1], Smoothies_Afternoon[1],
                        GlassOfMilk_Breaky[1], GlassOfMilk_Lunch[1], GlassOfMilk_LateLunch[1], GlassOfMilk_Afternoon[1],
                        Cortado_Breaky[1], Cortado_Lunch[1], Cortado_LateLunch[1], Cortado_Afternoon[1],
                        RedLabelTea_Breaky[1], RedLabelTea_Lunch[1], RedLabelTea_LateLunch[1], RedLabelTea_Afternoon[1]], 

        "CupsSold":  [FlatWhite_Breaky[0],FlatWhite_Lunch[0],FlatWhite_LateLunch[0],FlatWhite_Afternoon[0],
                        Latte_Breaky[0],Latte_Lunch[0],Latte_LateLunch[0],Latte_Afternoon[0],
                        FlavouredLatte_Breaky[0],FlavouredLatte_Lunch[0],FlavouredLatte_LateLunch[0],FlavouredLatte_Afternoon[0],
                        ChaiLatte_Breaky[0],ChaiLatte_Lunch[0], ChaiLatte_LateLunch[0], ChaiLatte_Afternoon[0],
                        FlavouredHotChocolate_Breaky[0],FlavouredHotChocolate_Lunch[0], FlavouredHotChocolate_LateLunch[0], FlavouredHotChocolate_Afternoon[0],
                        HotChocolate_Breaky[0], HotChocolate_Lunch[0], HotChocolate_LateLunch[0],HotChocolate_Afternoon[0],
                        LuxuryHotChocolate_Breaky[0],LuxuryHotChocolate_Lunch[0], LuxuryHotChocolate_LateLunch[0], LuxuryHotChocolate_Afternoon[0],
                        IcedLatte_Breaky[0],IcedLatte_Lunch[0], IcedLatte_LateLunch[0],IcedLatte_Afternoon[0],
                        Espresso_Breaky[0],Espresso_Lunch[0], Espresso_LateLunch[0],Espresso_Afternoon[0],
                        Frappes_Breaky[0],Frappes_Lunch[0], Frappes_LateLunch[0],Frappes_Afternoon[0],
                        Mocha_Breaky[0],Mocha_Lunch[0], Mocha_LateLunch[0],Mocha_Afternoon[0],
                        Smoothies_Breaky[0],Smoothies_Lunch[0], Smoothies_LateLunch[0], Smoothies_Afternoon[0],
                        GlassOfMilk_Breaky[0],GlassOfMilk_Lunch[0], GlassOfMilk_LateLunch[0], GlassOfMilk_Afternoon[0],
                        Cortado_Breaky[0],Cortado_Lunch[0], Cortado_LateLunch[0], Cortado_Afternoon[0],
                        RedLabelTea_Breaky[0],RedLabelTea_Lunch[0], RedLabelTea_LateLunch[0], RedLabelTea_Afternoon[0]], 

        "TimeOfDay": [FlatWhite_Breaky[2],FlatWhite_Lunch[2],FlatWhite_LateLunch[2],FlatWhite_Afternoon[2],
                        Latte_Breaky[2],Latte_Lunch[2],Latte_LateLunch[2],Latte_Afternoon[2],
                        FlavouredLatte_Breaky[2],FlavouredLatte_Lunch[2],FlavouredLatte_LateLunch[2],FlavouredLatte_Afternoon[2],
                        ChaiLatte_Breaky[2],ChaiLatte_Lunch[2], ChaiLatte_LateLunch[2],ChaiLatte_Afternoon[2],
                        FlavouredHotChocolate_Breaky[2],FlavouredHotChocolate_Lunch[2], FlavouredHotChocolate_LateLunch[2],FlavouredHotChocolate_Afternoon[2],
                        HotChocolate_Breaky[2],HotChocolate_Lunch[2], HotChocolate_LateLunch[2],HotChocolate_Afternoon[2],
                        LuxuryHotChocolate_Breaky[2],LuxuryHotChocolate_Lunch[2], LuxuryHotChocolate_LateLunch[2], LuxuryHotChocolate_Afternoon[2],
                        IcedLatte_Breaky[2],IcedLatte_Lunch[2], IcedLatte_LateLunch[2],IcedLatte_Afternoon[2],
                        Espresso_Breaky[2],Espresso_Lunch[2], Espresso_LateLunch[2],Espresso_Afternoon[2],
                        Frappes_Breaky[2],Frappes_Lunch[2], Frappes_LateLunch[2],Frappes_Afternoon[2],
                        Mocha_Breaky[2],Mocha_Lunch[2], Mocha_LateLunch[2],Mocha_Afternoon[2],
                        Smoothies_Breaky[2],Smoothies_Lunch[2], Smoothies_LateLunch[2], Smoothies_Afternoon[2],
                        GlassOfMilk_Breaky[2],GlassOfMilk_Lunch[2], GlassOfMilk_LateLunch[2],GlassOfMilk_Afternoon[2],
                        Cortado_Breaky[2],Cortado_Lunch[2], Cortado_LateLunch[2],Cortado_Afternoon[2],
                        RedLabelTea_Breaky[2],RedLabelTea_Lunch[2],RedLabelTea_LateLunch[2], RedLabelTea_Afternoon[2]]
                    })

        bar_chart6 = alt.Chart(source6).mark_bar().encode(
            color="TimeOfDay:N", # x="month(Date):O",
            x="CupsSold:Q",
            y="CoffeeType:N"
        ).properties(height=600, width=1000)

        text6 = alt.Chart(source6).mark_text(dx=-10, dy=3, color='white', fontSize=12, fontWeight=600).encode(
            x=alt.X('CupsSold:Q', stack='zero'),
            y=alt.Y('CoffeeType:N'),
            detail='TimeOfDay:N',
            text=alt.Text('CupsSold:Q', format='.0f')
        )

        st.altair_chart(bar_chart6 + text6, use_container_width=True)




run()


