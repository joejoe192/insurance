import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
df = pd.read_csv('insurance.csv')
#df.groupby('TRANSACTIONTYPE')['PREMIUMAMOUNT'].sum()
df['EXPIRYDATE']=pd.to_datetime(df['EXPIRYDATE'])
df['EFFECTIVEDATE']=pd.to_datetime(df['EFFECTIVEDATE'])
df['TRANSACTIONDATE'] = pd.to_datetime(df['TRANSACTIONDATE'].astype(str), format='%Y%m%d')
def parse_oracle_timestamp(ts):
    # Replace the first two '.' in time with ':' and remove the '.' before nanoseconds
    ts = ts.replace('.', ':', 2)
    ts = ts.replace('.', '', 1)
    return pd.to_datetime(ts, format='%d-%b-%y %I:%M:%S%f %p')
df['TIME_parsed'] = df['TIME'].apply(parse_oracle_timestamp)
df['TIME_parsed'] = pd.to_datetime(df['TIME_parsed'], format='%H:%M:%S')
df['TIME'] = df['TIME_parsed'].dt.time
df_sale= df.groupby('PROD_NM')['PREMIUMAMOUNT'].sum().sort_values()
df_nb = df[df['TRANSACTIONTYPE'] == 'NB']
unique_nb_policies = df_nb['PLCY_NO'].nunique()
df['TransactionMonth']=df['TRANSACTIONDATE'].dt.month_name()
st.set_page_config(page_title='Insurance Dashboard',page_icon=':bar_chart:')
st.sidebar.header('Please filter here')
our_premium = round(df['PREMIUMAMOUNT'].sum(),2)
# Step 1: Group by agent & month and aggregate
agent_summary = df.groupby(['AGENT_NAME', 'TransactionMonth']).agg({
    'PREMIUMAMOUNT': 'sum',
    'PLCY_NO': 'count',
    'Commission': 'sum'
}).rename(columns={'PLCY_NO': 'NumberOfPolicies'})

# Step 2: Calculate commission percentage per group
agent_summary['CommissionPct'] = round(agent_summary['Commission'] / agent_summary['PREMIUMAMOUNT'] * 100, 2)
agent_summary['CommissionPct'] = agent_summary['CommissionPct'].apply(lambda x: f"{x:.2f}%")
agent_summary['Commission'] = agent_summary['Commission'].apply(lambda x: f"{float(x):.2f}")
agent_summary['PREMIUMAMOUNT'] = agent_summary['PREMIUMAMOUNT'].apply(lambda x: f"{float(x):.2f}")

# Step 3: Reset index to get AGENT_NAME and TransactionMonth as columns
agent_summary = agent_summary.reset_index()

# Step 4: Sort by PREMIUMAMOUNT descending and get top 8
top_agents = agent_summary.sort_values(by='PREMIUMAMOUNT', ascending=False)
user_plan = st.sidebar.multiselect(
 'Select PlanName',
    options = df['PLANNAME'].unique(),
    default = df['PLANNAME'].unique()[:5]
)
user_month = st.sidebar.multiselect(
  'Select Month',
    options = df['TransactionMonth'].unique(),
    default = df['TransactionMonth'].unique()[:5]
)
#user_transtyp = st.sidebar.selectbox(
  #'Select Transaction Type',
   # options = df['TRANSACTIONTYPE'].unique()
#)
st.title(':moneybag: Insurance Analysis')
no_of_plan=df['PLANNAME'].nunique()
left_col,right_col = st.columns([2, 1])
color_map = {
    'NB': '#636EFA',
    'ReDoCover': '#EF553B',
    'ENDROSEMENT': '#00CC96',
     'Reinstatement of the coverage': '#AB63FA',
    'RENEW': '#FFA15A',
    'Automation Renew':'#A52A2A'
}

with left_col:
    st.subheader('Total Premium')
    st.subheader(f'Us ${our_premium}')
with right_col:
    st.subheader('Polices Sold(NB)')
    st.subheader(f'{unique_nb_policies}')

user_select = df.query('PLANNAME==@user_plan')
user_month_select = df.query('TransactionMonth==@user_month')
premium_by_plan=user_select.groupby('PLANNAME')['PREMIUMAMOUNT'].sum().sort_values()
premium_by_product=user_month_select.groupby('TransactionMonth')['PREMIUMAMOUNT'].sum().sort_values()
fig_premium_by_plan = px.bar(premium_by_plan, x=premium_by_plan.index, y=premium_by_plan.values,title='Total Premium by Plan')
fig_premium_by_product = px.bar(premium_by_product, x=premium_by_product.index, y=premium_by_product.values,title='Total Premium For each month')
premium_by_transtyp=df.groupby('PYMT_FREQ')['PREMIUMAMOUNT'].sum().sort_values()
fig_premium_by_transtyp = px.pie(premium_by_transtyp, values=premium_by_transtyp.values,names=premium_by_transtyp.index,hole=0.0,title='Total Premium by Payment Type')
#px.pie(sale_by_city,values=sale_by_city.values,names=sale_by_city.index,title='Sales by City')
fig_premium_by_transtyp.update_traces(textinfo='percent+label')
total_tx_by_month = df.groupby('TransactionMonth').size()
fig_total_tx_by_month = px.line(x=total_tx_by_month.index, y=total_tx_by_month.values, labels={'x': 'Month', 'y': 'Total Transactions'}, title='Total Transactions by Month')
renewals_by_month = df[df['TRANSACTIONTYPE'].isin(['RENEW', 'Automation Renew'])].groupby('TransactionMonth').size()
no_renewals_by_month = df[~df['TRANSACTIONTYPE'].isin(['RENEW', 'Automation Renew'])].groupby('TransactionMonth').size()
renewal_rate_by_month = (renewals_by_month / total_tx_by_month) * 100
no_renewal_rate_by_month = (no_renewals_by_month / total_tx_by_month) * 100
months = renewal_rate_by_month.index.tolist()
selected_month = st.selectbox("Select Renewal Distribution Month", months)
renewed = renewal_rate_by_month.get(selected_month, 0)
not_renewed = no_renewal_rate_by_month.get(selected_month, 0)
labels = ['Renewed', 'Not Renewed']
values = [renewed,not_renewed]
fig_renewal_rate_by_month=px.pie(values=values, names=labels,color=labels, color_discrete_map={
        'Renewed': 'green',
        'Not Renewed': '#FF6666'
    }, title=f'Renewal Distribution for {selected_month}')
filtered_transtyp = df[df['TRANSACTIONTYPE'].isin(['NB','ReDoCover','ENDROSEMENT','Reinstatement of the coverage','RENEW','Automation Renew'])]
premium_by_transtyp = filtered_transtyp.groupby('TRANSACTIONTYPE')['PREMIUMAMOUNT'].sum().reset_index()
premium_by_transtyp.columns = ['TransactionType', 'Premium']
fig = px.pie(
        premium_by_transtyp,
        names='TransactionType',  # category names
        values='Premium',         # numerical values
        hole=0.4,
        title='Premium by Transaction Type',
        color='TransactionType',
        color_discrete_map=color_map
    )
fig.update_traces(textinfo='percent+label',textposition='inside')
fig_agent_info = go.Figure(data=[go.Table(
    header=dict(values=list(top_agents.columns),
                fill_color='paleturquoise',
                align='left',
               height=30),
    cells=dict(values=[top_agents[col] for col in top_agents.columns],
               fill_color='lavender',
               align='left',
              height=30))
])
    #st.plotly_chart(fig, use_container_width=True)
fig_agent_info.update_layout(width=1000,title='Top Agents Summary By Month',margin=dict(l=10, r=10, t=50, b=10))
a,b,c=st.columns(3)
a.plotly_chart(fig_premium_by_plan,use_container_width = True)
b.plotly_chart(fig_total_tx_by_month,use_container_width = True)
c.plotly_chart(fig_renewal_rate_by_month,user_container_width=True)
#c.plotly_chart(fig_premium_by_product,use_container_width = True)
d,e = st.columns(2)
d.plotly_chart(fig_premium_by_product,use_container_width = True)
#fig.update_layout(width=600, height=600)
e.plotly_chart(fig,use_container_width = True)
#col1, col2, col3 = st.columns([1, 2, 1])
#with col1:
st.plotly_chart(fig_agent_info,use_container_width = False)
# --- Download Button for CSV ---
csv = top_agents.to_csv(index=False).encode('utf-8')
st.download_button(
    label="⬇️ Download Agent Summary",
    data=csv,
    file_name='top_agents.csv',
    mime='text/csv'
)
