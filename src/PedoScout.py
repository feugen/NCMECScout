# ###################################################### #
# ######      Software: PedoScout                 ###### #
# ######      License: GPLv3                      ###### #
# ######      Author: Eugen Fischer               ###### #
# ######      Email: suppenphysik@gmail.com       ###### #
# ###################################################### #


import requests
import sqlite3
from bs4 import BeautifulSoup
from openpyxl import load_workbook
from matplotlib import pyplot as plt
from scipy import stats
import plotly.plotly as py
import pandas as pd


# ######################## Control Center for turning on and off the functions ########################## #
get_raw_data = False
format_raw_data = False
create_sqlite_db = False
import_childs_sqlite_db = False
import_states_sqlite_db = False
import_counties_sqlite_db = False
counties_fix_db = False
stat_analysis = True
# ####################################################################################################### #




# Create a file and get the date from the web page
if get_raw_data:

    # Create a new file called raw_data in write modus
    with open("./raw_data", "w+") as file:

        # Define the state shortcuts
        state_shortcut = ["AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "IA", "ID", "IL",
                          "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE",
                          "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT",
                          "VA", "VT", "WA", "WI", "WV", "WY"]

        # Get the raw data from http://www.missingkids.com/. Table 3 in HTML contains the data.

        for i in state_shortcut:
            url = 'http://www.missingkids.com/missingkids/servlet/PubCaseSearchServlet?act=usMapSearch&missState=' \
                  + str(i)
            print("Get data for: ", i)
            source_code = requests.get(url)
            plain_text = source_code.text.encode('utf-8')
            soup_all = BeautifulSoup(plain_text, "lxml")

            all_tables = soup_all.findAll('table')
            select_table_3 = all_tables[2].table
            select_table_3_text = select_table_3.text.encode('utf-8')

            soup_table_3 = BeautifulSoup(select_table_3_text, 'lxml')

            for result in soup_table_3:
                print(result)
                print(result, file=file)
            # Add 4 empty lines for optimal format, or it will break between the states
            file.write('\n\n\n\n')


    file.close()



# Now format the raw data file and store it in a new file
if format_raw_data:
    # In file2 handle we will store formated data
    with open("./formated_data", "w+") as file2:

        # Open an existing file called raw_data
        with open("./raw_data", "r+") as file:

            rows = file.readlines()

            # Ensure, you are at the top of the file
            file.seek(0)

            # Now remove the strings from the lines
            rem_html_body_p = "<html><body><p>"
            rem_p_body_html = "</p></body></html>"
            rem_view_poster = "  (View Poster)"
            rem_dash = "-"
            rem_tab = '\t'

            n = 0

            for line_string in rows:
                # Set '\n' counter to 0
                if line_string != '\n':
                    n = 0
                if rem_html_body_p in line_string:
                    line_string = line_string.replace(rem_html_body_p, '')
                if rem_p_body_html in line_string:
                    line_string = line_string.replace(rem_p_body_html, '')
                if rem_view_poster in line_string:
                    line_string = line_string.replace(rem_view_poster, '')
                if rem_dash in line_string:
                    line_string = line_string.replace(rem_dash, '')
                if rem_tab in line_string:
                    line_string = line_string.replace(rem_tab, '')
                while '   ' in line_string:
                    line_string = line_string.replace('   ', '')
                while '  ' in line_string:
                    line_string = line_string.replace('  ', '')
                if line_string == '\n':
                    n += 1
                if n <= 6:
                    # Write to file not more than 6 '\n'
                    file2.write(line_string)

        file.close()

    file2.close



# Now we will create sqlite databese

if create_sqlite_db:

    # Establish connection and create handle
    sqlite_file = "./childs.db"
    db_conn = sqlite3.connect(sqlite_file)
    db_handle = db_conn.cursor()

    #now create Table
    db_handle.execute('create table us_childs (db_id integer primary key, name, web_id, info_short, birthday,'
                      ' missing_date, race, county, state, county_id)')
    db_handle.execute('create table us_states (state, population integer, state_long)')
    db_handle.execute('create table us_counties (county_id integer, county, state, population integer)')

    db_conn.commit()
    db_conn.close


# This function formatting the date in a appropriate way for SQlite3 (YYYY-MM-DD)
def fix_date(date, type):

    # Get the months string
    month_str = date[:3]
    # create list for comparison
    month_list = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

    if month_str in month_list:
        # Count the chars
        char_number = len(date)

        if str(type) == 'birthday':
            if char_number == 13:
                date = date[:4] + '0' + date[4:]
        if str(type) == 'missing_day':
            if char_number == 12:
                date = date[:4] + '0' + date[4:]
        date = date[:12]
        # create dictionary...
        month = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9,
                 "Oct": 10, "Nov": 11, "Dec": 12}

        date = str(month[month_str]) + date[3:]
        if len(date) == 10:
            date = '0' + date
        date = date[7:11] + '-' + date[:2] + '-' + date[3:5]
    else:
        date = None

    return date



# Now we will store the formatted data in created sqlite databese

if import_childs_sqlite_db:
    sqlite_file = "./childs.db"
    db_conn = sqlite3.connect(sqlite_file)
    db_handle = db_conn.cursor()

    with open("./formated_data", "r+") as file3:

        string = file3.readlines()
        file3.seek(0)

        n = 0
        m = 0
        while n < len(string):
            if 'DOE' in string[n]:
                Race = string[n + 17]
                if Race == '\n':
                    n += 29
                else:
                    n += 30
            else:
                m += 1
                ID = m
                Name = string[n].rstrip(' ')
                if Name == '\n':
                    # Try next row, between some states are 7 rows :-/
                    n += 1
                    Name = string[n].rstrip(' ')
                    if Name == '\n':
                        # If still nothing, then we reached the end?
                        # Last entry reached, break here or you get out of index on n+2 etc.
                        break
                Web_Id = string[n + 2].rstrip(' ')
                Info_Short = string[n + 5].rstrip(' ')
                # date for birthday and missing day will be fixed in fix_date function
                Birthday = fix_date(string[n + 9].rstrip(' '), 'birthday')
                Missing_day = fix_date(string[n + 16], 'missing_day')
                Race = string[n + 19][:5]
                if Race == '\n':
                    # sometimes the race is missing, then we jump to far, subtract 1 to fix it
                    n -= 1
                County = string[n + 22].split(',')[0]
                State = string[n + 23][:2]
                n += 32
                db_handle.execute('insert into us_childs (db_id, name, web_id, info_short, birthday,'
                                  ' missing_date, race, county, state) values (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                  (ID, Name, Web_Id, Info_Short, Birthday, Missing_day, Race, County, State))

    db_conn.commit()
    db_conn.close

# ######################################################################################################### #
# # Attention! You have still to perform some manual tasks. For the task list look at the end of this file. #
# ######################################################################################################### #

# Now we want to get the states data and create the sqlite table

if import_states_sqlite_db:

    sqlite_file = "./childs.db"
    db_conn = sqlite3.connect(sqlite_file)
    db_handle = db_conn.cursor()

    # open a file for BeautifulSoup
    with open("./raw_state_data", 'w+') as f:

        url = "http://www.infoplease.com/us/states/population-by-rank.html"
        source_code = requests.get(url)

        plain_text = source_code.text.encode('utf-8')
        soup_all = BeautifulSoup(plain_text, "lxml")
        soup_result = soup_all.findAll('table', {'class': 'sgmltable'})

        # create a new soup object with limited data
        soup_all = BeautifulSoup(str(soup_result), "lxml")

        # search for state names
        soup_result = soup_all.findAll('a')

        states_list = []

        for i in soup_result:
            states_list.append(i.string)

        # now get population numbers
        soup_result = soup_all.findAll('td')

        i = 0
        states_population = []

        # -1 prevents the last number being printed since its a sum of all states
        while i < len(soup_result) - 1:
            # only uneven numbers are valid numbers
            if i % 2 != 0:
                states_population.append(soup_result[i].string)
            i += 1

        # Now write the data to a file
        i = 0
        while i < len(states_list):
            f.write(states_list[i] + '\t' + states_population[i] + '\n')
            i += 1
        f.close()

        # But more important safe the date strait to database

        # create a list with us states short codes ordered by population as stated in
        # http://www.infoplease.com/us/states/population-by-rank.html
        # then pass the list to database together with states_population and states_list

        states_shortcuts = ['CA', 'TX', 'FL', 'NY', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI', 'NJ', 'VA', 'WA', 'AZ', 'MA',
                            'IN', 'TN', 'MO', 'MD', 'WI', 'MN', 'CO', 'SC', 'AL', 'LA', 'KY', 'OR', 'OK', 'CT', 'IA',
                            'UT', 'MS', 'AR', 'KS', 'NV', 'NM', 'NE', 'WV', 'ID', 'HI', 'NH', 'ME', 'RI', 'MT', 'DE',
                            'SD', 'ND', 'AK', 'DC', 'VT', 'WY']

        i = 0
        while i < len(states_list):
            db_handle.execute('insert into us_states (state, population, state_long) values (?, ?, ?)',
                              (states_shortcuts[i], states_population[i], states_list[i]))
            i += 1

    db_conn.commit()
    db_conn.close



if import_counties_sqlite_db:

    sqlite_file = "./childs.db"
    db_conn = sqlite3.connect(sqlite_file)
    db_handle = db_conn.cursor()

    wb = load_workbook("./PopulationEstimates.xlsx", read_only=True)

    sheet_ranges = wb['Population Estimates 2010-2015']

    column_county_id = 0
    column_county_state = 1
    column_county_name = 2
    column_county_population = 13
    values = []

    for row in list(sheet_ranges.rows)[4:]:
        for cell in row:
            values.append(cell.value)
        if int(values[column_county_id])%1000 != 0:
            print('County ID:' + str(values[column_county_id]))
            print('Country State:' + str(values[column_county_state]))
            print('Country Name:' + str(values[column_county_name]))
            print('Country Population:' + str(values[column_county_population]))
            print('==================================')

            # Now lets write it to the database

            db_handle.execute('insert into us_counties (county_id, county, state, population) values (?, ?, ?, ?)',
                              (values[column_county_id], values[column_county_name], values[column_county_state],
                               values[column_county_population]))
            db_conn.commit()
        values.clear()

    db_conn.close


# Sadly the counties in us_childs dont match the county names in us_couties, since not all entries are counties,
# but cities or villages. So we have to connect the counties IDs from us_counties to us_childs entries

if counties_fix_db:

    sqlite_file = './childs.db'
    db_conn = sqlite3.connect(sqlite_file)
    db_handle = db_conn.cursor()

    # first get the list of county names and state names and check if they exist in us_counties, if they do, then
    # write the id from us_county to us_child. The missing ids have to be corrected manually.

    db_handle.execute('select db_id, county, state from us_childs')
    result = db_handle.fetchall()

    for i in result:
        db_handle.execute("select county_id from us_counties where county like ? and state = ? order by "
                          "population asc", ('%'+i[1]+'%',i[2],))
        result2 = db_handle.fetchall()
        for k in result2:
            db_handle.execute('update us_childs set county_id = ? where db_id = ? ', (k[0], i[0],))
            print(k[0])
            db_conn.commit()

    db_conn.close()

    # Around 2660 entries are still missing, 1260 of them are unique. Araound 1000 were added by the code above.
    # Probalby its the best way to get a list of all names with states and make a dictionary... Right now go for
    # state analysis and VA counties for the first evidence. After that add other counties.



# Attention!!!!!!!!!
# We have to fix the population numbers in us_states table by removing "," in all numbers





# ############################################################################################################# #
# ############################################################################################################# #
#                                               Statistical analysis
# ############################################################################################################# #
# ############################################################################################################# #


if stat_analysis:

    # Create Sqlite connection
    db_file = './childs.db'
    db_conn = sqlite3.connect(db_file)
    db_handle = db_conn.cursor()

    # now get the data from DB: count number of victims by state

    state_shortcut = ["AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "IA", "ID", "IL",
                      "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE",
                      "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT",
                      "VA", "VT", "WA", "WI", "WV", "WY"]


    # USA population 1984-2016, last number is an estimate
    population_historic = (235825, 237924, 240133, 242289, 244499, 246819, 249623, 252981, 256514, 259919, 263126,
                           266278, 269394, 272657, 275854, 279040, 282162, 284969, 287625, 290107, 292805, 295516,
                           298378, 301231, 304094, 306771, 309347, 311719, 314103, 316427, 318907, 321418, 323929)

    # factor based on 1984
    population_historic_factor = []

    # Now calculate the factors for each year
    i = 0
    while(i < len(population_historic)):
        population_historic_factor.append(population_historic[i]/population_historic[0])
        i += 1


    # ############################
    # Chapter 4.1
    # ############################

    # ######################################################################################################### #
    # Simple results by year, from 1984 - 2016
    # ######################################################################################################### #

    year_start = 1984
    year_end = 2017
    result_by_year_x_axis = []
    result_by_year_y_axis = []

    while(year_start < year_end):
        db_handle.execute("select count (*) from us_childs where missing_date > ? and missing_date < ? ",
                          (str(year_start), str(year_start+1), ))
        result = db_handle.fetchone()[0]

        result_by_year_x_axis.append(year_start)
        result_by_year_y_axis.append(result)
        year_start += 1

    # For debuging
    #print(result_by_year_x_axis, result_by_year_y_axis)

    # The results suggest to dismiss the year 2014-2016 since to many fake results
    #print(len(result_by_year_x_axis), len(result_by_year_y_axis))

    plt.bar(result_by_year_x_axis,result_by_year_y_axis, label='USA_by_year_simple')
    plt.xlabel('Year')
    plt.ylabel('Missing children')
    plt.title('Number of missing children by year (1984-2016)')
    plt.xlim(1983,2018)

    #plt.show()

    plt.close()

    # ######################################################################################################### #
    # Results normalized to 1984, from 1984 - 2016
    # ######################################################################################################### #

    result_by_year_y_axis_fixed = []

    i=0
    while i < len(population_historic):
        result_by_year_y_axis_fixed.append(result_by_year_y_axis[i]/population_historic_factor[i])
        i += 1

    plt.bar(result_by_year_x_axis, result_by_year_y_axis_fixed, label='USA_by_year_normalized')
    plt.xlabel('Year')
    plt.ylabel('Missing children normalized to 1984')
    plt.title('Number of missing children normalized to 1984')
    plt.xlim(1983, 2018)

    #plt.show()

    plt.close()

    # ######################################################################################################### #
    # Results normalized to 1984, from 1984 - 2016
    # ######################################################################################################### #


    i = 20
    while(i <= len(result_by_year_y_axis_fixed)):
        test = stats.normaltest(result_by_year_y_axis_fixed[:i])
        # For debugging
        #print(test, result_by_year_x_axis[i-1])
        i += 1
    #print(result_by_year_y_axis_fixed)

    # ######################################################################################################### #
    # Results simple and normalized to 1984, from 1984 - 2013
    # ######################################################################################################### #


    plt.bar(result_by_year_x_axis[:-3], result_by_year_y_axis[:-3],
             label='Real number of victims',color='blue')
    plt.bar(result_by_year_x_axis[:-3], result_by_year_y_axis_fixed[:-3],
             label='Normalized number of victims', color='green')
    plt.xlabel('Year')
    plt.ylabel('Missing children 1984 - 2013')
    plt.title('Number of missing children 1984 - 2013 comparison')
    plt.xlim(1983, 2015)
    plt.legend()

    #plt.show()

    plt.close()

    # ######################################################################################################### #
    # Test for normal distribution
    # ######################################################################################################### #





    # ######################################################################################################### #
    # Results by state per capita within a certain year range
    # ######################################################################################################### #

    year_start = 1984
    year_end = 2014

    for i in state_shortcut:

        db_handle.execute("select count (*) from us_childs where state = ? and missing_date > ? "
                          "and missing_date < ? ", (i, year_start, year_end))
        result_child_by_state = db_handle.fetchone()

        db_handle.execute("select population from us_states where state = ? ", (i,))
        result_population_by_state = db_handle.fetchone()

        result_population_by_state_fixed = float(str(result_population_by_state[0]).replace(',', ''))
        childs_per_capita = []

        childs_per_capita.append(i)
        childs_per_capita.append(int(result_child_by_state[0]) / result_population_by_state_fixed)
        childs_per_capita.append(int(result_child_by_state[0]))

        print(childs_per_capita)

    db_conn.close()

    # select county, county_id, state, count(county) AS Value_occurance from us_childs where missing_date > '2000'
    #  and missing_date < '2007' group by county order by Value_occurance desc
    # VA from 2000-2006 one of the most safest states? MD near Washington was on top? 2010-2014 VA is on top



    #select us_childs.county, us_childs.county_id, us_childs.state, count(us_childs.county_id) as occurance, us_counties.population
    #from us_childs
    #left join us_counties on us_childs.county_id = us_counties.county_id
    #where missing_date > '2000' and missing_date < '2014' and us_childs.state = 'MD'
    #group by us_counties.population order by occurance desc



    #select us_childs.county, us_childs.county_id, us_childs.state, count(
    #    us_childs.county_id) as occurance, us_counties.population, cast(
    #    count(us_childs.county_id) as float) / us_counties.population as Density
    #from us_childs

    #left join us_counties on us_childs.county_id = us_counties.county_id
    #where missing_date > '2006' and missing_date < '2014' - - and us_childs.state = 'MD'
    #and us_counties.population > 500000
    #group by us_counties.population order by Density desc



    #select us_childs.state as State, us_states.state_long as State_Name, count(
    #    us_childs.state) as Occurance, us_states.population as Population, cast(count(us_childs.state) as float) / cast(
    #    us_states.population as float) as Density
    #from us_childs
    #left join us_states on us_childs.state = us_states.state
    #where missing_date > '2005' and missing_date < '2014'
    #-- and (us_childs.missing_date - us_childs.birthday) < 12
    #-- and us_childs.race = 'White'
    #and us_states.population > 2000000
    #group by us_states.population order by state asc



# Addtionaly in formated_data correct the data:
# 36710: removed, cant get data
# 41063: remove 3 blank lines
# 53965: remove 5 blank lines
# 56786 remove unknown, keep 6 lines between individuals
# 60131 remove FALLS ROAD UNIDENTIFIED
# 64885 remove 5 blank lines
# 66892 remove E from the name to avoid false DOE trigger
# 73931 remove noname child
# 76814 remove 5 blank lines
# 77151 remove 3 lines and several following doe's
# 81486 add unknown status
# 81513 add unknown as above
# 81765 remove 3 blank lines
# 94500 remove 3 blank lines
# 109075 added 2 vlank lines
# 109107 added 2 vlank lines
# 109803 added unknown status
# For all VA children add 2 blank lines after age, if the age is missing, Its for better parsing
# Write a script for this task or ot will take half an hour!!!
# 110694 added unknown status
# 112105 added unknown status
# 112400 remove 6 DOEs
# 116260 added unknown status
# 121700 remove doe
