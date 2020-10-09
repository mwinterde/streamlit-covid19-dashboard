import streamlit as st
import requests
import pandas as pd
import altair as alt

@st.cache
def get_data_from_api(url):

    # Get json response
    response = requests.get(url)
    json = response.json()

    # Transform to dataframe
    data = pd.DataFrame.from_records(json)

    return data

def get_countries_from_api():

    url = 'https://api.covid19api.com/countries'

    return get_data_from_api(url)

def get_cases_from_api(country):

    url = (f'https://api.covid19api.com/total/dayone/country/{country}/status'
           f'/confirmed')

    return get_data_from_api(url)

def transform_cases_data(cases):

    # Filter relevant columns
    relevant_columns = ['Date', 'Cases']
    cases = cases[relevant_columns].copy()

    # Convert date column and make index
    cases['Date'] = cases['Date'].astype('datetime64')
    cases = cases.set_index('Date')

    # Rename cases column and create new cases column
    cases.rename(columns={'Cases': 'Total Cases'}, inplace=True)
    cases['New Cases'] = cases['Total Cases']-cases['Total Cases'].shift(1)

    return cases

def create_altair_plot(cases, country):

    # Create base chart
    base = alt.Chart(cases.reset_index()).encode(
        alt.X('Date:T', axis=alt.Axis(title='Date'))
    )

    # Create line chart for total cases
    totalcases = base.mark_line(color='#5276A7').encode(
        alt.Y('Total Cases',
              axis=alt.Axis(title='Total Cases', titleColor='#5276A7')
              )
    )

    # Create bar chart for new cases
    newcases = base.mark_bar(opacity=0.2, size=1, color='red').encode(
        alt.Y('New Cases',
              axis=alt.Axis(title='New Cases', titleColor='red')
              )
    )

    # Put both together
    layer = alt.layer(newcases, totalcases).resolve_scale(
            y='independent'
        ).properties(
        title=country
    )

    return layer


def selectbox_without_default(label, options, blocker):

    options = [''] + list(options)
    format_func = lambda x: blocker if x == '' else x
    return st.selectbox(label, options, format_func=format_func)


def main():

    # Title
    st.title("COVID 19 Dashboard")
    st.markdown("This app gets data from the [COVID19 API]("
                "https://www.covid19api.com/) and allows you to plot the "
                "number of new and total cases per country.")

    # Select a country
    st.subheader("Country Selection")
    countries = get_countries_from_api()
    country_options = countries['Country'].sort_values()
    country = selectbox_without_default("Choose country", country_options,
                                        "Choose a country")
    if not country:
        st.stop()

    # Get and transform cases data
    country_api_format = countries.loc[countries.Country==country, 'Slug'].iloc[0]
    cases = get_cases_from_api(country_api_format)
    if cases.empty:
        st.error(f"No data available for {country}")
        st.stop()
    cases = transform_cases_data(cases)


    # Make plot
    plot = create_altair_plot(cases, country)
    st.altair_chart(plot, use_container_width=True)


if __name__ == '__main__':
    main()