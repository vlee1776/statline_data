import pandas as pd 
from sqlalchemy import create_engine
from google.cloud import secretmanager
import os 

def query_states_daily():
    states_url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv'
    statesdf = pd.read_csv(states_url)
    statesdf['date'] = pd.to_datetime(statesdf['date'])
    # shift the date 
    statesdf['shift_date'] = statesdf['date'] + pd.DateOffset(days=1)
    # grab only if the cases & deaths greater than 0
    subquery1df = statesdf[statesdf.cases + statesdf.deaths > 0][['state','fips','cases','shift_date']]
    # merge the two on shift_date and regular date 
    merged = statesdf.merge(subquery1df,left_on=['date','fips'],right_on=['shift_date','fips'],how='inner')
    merged = merged.sort_values(by='date',ascending=True)
    merged['new_cases'] = merged['cases_x'] - merged['cases_y']
    result = merged[['date','state_x','new_cases']].sort_values(by=['state_x','date'],ascending=[True,True])
    d = {'date': 'date', 'state_x': 'state', 'new_cases':'new_cases'}
    result = result.rename(columns=d)
    return result

def insertDF(df):
    client = secretmanager.SecretManagerServiceClient()
    project_name = ""
    db_user = client.access_secret_version(f"projects/{project_name}/secrets/db_user/versions/latest")
    db_password = client.access_secret_version(f"projects/{project_name}/secrets/db_password/versions/latest")
    connection_name = client.access_secret_version(f"projects/{project_name}/secrets/connection_name/versions/latest")
    db_name = 'nytimes'
    print('Create Engine')
    engine = create_engine(f"mysql+mysqldb://{db_user}@/{db_name}?unix_socket=/cloudsql/{connection_name}")
    print('Created Engine')
    df.to_sql('temp_table', engine, if_exists='replace')
    
def main(request):
    df = query_states_daily()
    insertDF(df)