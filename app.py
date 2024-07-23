import streamlit as st
import sqlite3 as sq
import openai
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt
import plotly.express as px

database = sq.connect("football.db")

openai.api_key = 'sk-proj-rTtGKFvAT9qRsrsNxYj7T3BlbkFJh1WGoPtML5496EIoanAq'


def get_table_description():
    with sq.connect('football.db') as conn:
        cursor = conn.execute('PRAGMA table_info(football);')
        description = cursor.fetchall()
        columns = [desc[1] for desc in description]
        col_types = [desc[2] for desc in description]
        table_description = "\n".join([f"{col} {col_type}" for col, col_type in zip(columns, col_types)])
    return table_description

def query_chatgpt(prompt, system_prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )
    return response.choices[0].message['content'].strip()


def translate_to_sql(natural_language_query, system_prompt):
    prompt = f"Translate the following natural language query into an SQLite query: '{natural_language_query}'"
    sql_response = query_chatgpt(prompt, system_prompt)
    sql_query = sql_response.strip()
    return sql_query

def execute_sql_query(sql_query):
    with sq.connect('football.db') as conn:
        try:
            df = pd.read_sql_query(sql_query, conn)
            return df
        except Exception as e:
            return str(e)

def plot_pie_chart(df, labels_col, values_col):
    fig, ax = plt.subplots()
    ax.pie(df[values_col], labels=df[labels_col], autopct='%1.1f%%')
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    st.pyplot(fig)

def main():
    table_description = get_table_description()
    
    system_prompt = f"""You are a SQLite database administrator. You are supposed to convert user prompts to SQL queries, and if asked for any kind of graph or chart, return the query for obtaining values from table which can be utillized to plot the graph. You are only allowed to respond to database/table-related prompts. Here's the table description - {table_description}. This database contains only this one table, and its name is football. You should only output the query without any prefix or anything extra added to the query."""
    
    st.title("Data Query and Visualization App")
    
    st.text_area("table", value=table_description, height=200, disabled=True)
    user_input = st.text_input("Enter what you might like to retrieve:")
    
    if user_input:
        sql_query = translate_to_sql(user_input, system_prompt)
        st.write(f"Generated SQL Query: `{sql_query}`")
        query_result = execute_sql_query(sql_query)
        col = query_result.columns
        rows = query_result.values.tolist()
        if isinstance(query_result, pd.DataFrame):
            st.dataframe(query_result)
            if "chart" in user_input.lower():
                columns = query_result.columns.tolist()
                x_column = st.selectbox("Select X-axis column", columns)
                y_column = st.selectbox("Select Y-axis column", columns)
                
            if "bar chart" in user_input.lower():
                    st.bar_chart(query_result.set_index(x_column)[y_column])
            elif "line chart" in user_input.lower():
                    st.line_chart(query_result.set_index(x_column)[y_column])
            elif "area chart" in user_input.lower():
                    st.area_chart(query_result.set_index(x_column)[y_column])
            elif "pie chart" in user_input.lower():
                    plot_pie_chart(query_result, x_column, y_column)
            elif "altair chart" in user_input.lower():
                chart = alt.Chart(query_result).mark_circle().encode(
                        x=x_column,
                        y=y_column,
                        size=y_column,
                        color=x_column,
                        tooltip=[x_column, y_column]
                    )
                st.altair_chart(chart, use_container_width=True)
            elif "plotly chart" in user_input.lower():
                fig = px.scatter(query_result, x=x_column, y=y_column, size=y_column, color=x_column, hover_name=x_column)
                st.plotly_chart(fig)    
        else:
            st.error(f"Error: {query_result}")

if __name__ == "__main__":
    main()
