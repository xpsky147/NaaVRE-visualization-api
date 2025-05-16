import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
import json

# Set Streamlit page config
st.set_page_config(page_title="Data Visualization", layout="wide")

# Receive query parameters (e.g., visualization id)
query_params = st.experimental_get_query_params()
viz_id = query_params.get('id', [None])[0]

# API endpoint configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "http://visualization-api")

def load_visualization_data(viz_id):
    """Load visualization data from the backend API by ID."""
    try:
        st.info(f"Loading data from API: {API_BASE_URL}/api/visualization/data/{viz_id}")
        response = requests.get(f"{API_BASE_URL}/api/visualization/data/{viz_id}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to load data: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def create_chart(chart_type, data, layout):
    """
    Create common charts: line, bar, scatter, area.
    Data should be either a list of dicts or {x:[], y:[]}.
    """
    try:
        if "data" in data and isinstance(data["data"], list):
            df = pd.DataFrame(data["data"])
            # 自动识别"特征均值分组柱状图"
            if set(["feature", "species", "mean"]).issubset(df.columns):
                fig = px.bar(
                    df,
                    x="feature",
                    y="mean",
                    color="species",
                    barmode="group",
                    title=layout.get("title", "")
                )
                # Axis label设置
                if layout:
                    if "xaxis_title" in layout:
                        fig.update_xaxes(title_text=layout["xaxis_title"])
                    if "yaxis_title" in layout:
                        fig.update_yaxes(title_text=layout["yaxis_title"])
                return fig
            # 否则，继续兼容通用list-of-dict情况
            # 比如data为{"data":[{"x":1,"y":2},...]}
            elif set(["x", "y"]).issubset(df.columns):
                pass  # 走到后面chart_type分支
            else:
                st.error("Unrecognized list-of-dict data structure")
                st.json(data)
                return None

        elif "x" in data and "y" in data:
            df = pd.DataFrame({
                "x": data["x"],
                "y": data["y"]
            })
        else:
            st.error("Unrecognized data format")
            st.json(data)
            return None

        if df.empty:
            st.error("Data is empty")
            return None

        # chart_type通用分支
        if chart_type == "line":
            fig = px.line(df, x="x", y="y", title=layout.get("title", ""))
        elif chart_type == "bar":
            fig = px.bar(df, x="x", y="y", title=layout.get("title", ""))
        elif chart_type == "scatter":
            fig = px.scatter(df, x="x", y="y", title=layout.get("title", ""))
        elif chart_type == "area":
            fig = px.area(df, x="x", y="y", title=layout.get("title", ""))
        else:
            st.warning(f"Unsupported chart type: {chart_type}")
            return None

        # Axis label设置
        if layout:
            if "xaxis_title" in layout:
                fig.update_xaxes(title_text=layout["xaxis_title"])
            elif "x_label" in data:
                fig.update_xaxes(title_text=data["x_label"])
            if "yaxis_title" in layout:
                fig.update_yaxes(title_text=layout["yaxis_title"])
            elif "y_label" in data:
                fig.update_yaxes(title_text=data["y_label"])

        return fig

    except Exception as e:
        st.error(f"Error creating chart: {str(e)}")
        st.write("Data content:")
        st.json(data)
        return None

def create_scientific_chart(chart_type, data, layout):
    """
    Create scientific charts: boxplot, violin, correlation.
    """
    try:
        # Accepts both list-of-dicts and {x,y} data
        if "data" in data and isinstance(data["data"], list):
            df = pd.DataFrame(data["data"])
        elif "x" in data and "y" in data:
            df = pd.DataFrame({
                "x": data["x"],
                "y": data["y"]
            })
        else:
            st.error("Unrecognized data format")
            st.json(data)
            return None

        if chart_type == "boxplot":
            # Boxplot for categorical data if available
            if "category" in df.columns and "value" in df.columns:
                fig = px.box(df, x="category", y="value", title=layout.get("title", ""))
            else:
                fig = px.box(df, title=layout.get("title", ""))
        elif chart_type == "violin":
            if "category" in df.columns and "value" in df.columns:
                fig = px.violin(df, x="category", y="value", title=layout.get("title", ""))
            else:
                fig = px.violin(df, title=layout.get("title", ""))
        elif chart_type == "correlation":
            # Show correlation matrix if at least two numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) >= 2:
                corr = df[numeric_cols].corr()
                fig = px.imshow(corr,
                                title=layout.get("title", "Correlation Matrix"),
                                color_continuous_scale='RdBu_r',
                                zmin=-1, zmax=1)
            else:
                st.error("Correlation matrix needs at least two numeric columns")
                return None
        else:
            st.warning(f"Unsupported scientific chart type: {chart_type}")
            return None

        # Apply layout settings
        if layout:
            if "xaxis_title" in layout:
                fig.update_xaxes(title_text=layout["xaxis_title"])
            elif "x_label" in data:
                fig.update_xaxes(title_text=data["x_label"])
            if "yaxis_title" in layout:
                fig.update_yaxes(title_text=layout["yaxis_title"])
            elif "y_label" in data:
                fig.update_yaxes(title_text=data["y_label"])

        return fig
    except Exception as e:
        st.error(f"Error creating scientific chart: {str(e)}")
        st.exception(e)
        return None

def render_dashboard(dashboard_data):
    """
    Render a dashboard with multiple charts.
    Charts are defined in dashboard_data["charts"].
    """
    st.subheader("Dashboard")

    layout = dashboard_data.get("layout", {"rows": 2, "cols": 2})
    charts = dashboard_data.get("charts", [])

    if not charts:
        st.warning("No chart configuration in dashboard")
        return

    rows = layout.get("rows", 2)
    cols = layout.get("cols", 2)

    for r in range(rows):
        columns = st.columns(cols)
        for c in range(cols):
            chart_index = r * cols + c
            if chart_index < len(charts):
                chart = charts[chart_index]
                with columns[c]:
                    st.subheader(chart.get("title", f"Chart {chart_index+1}"))
                    chart_type = chart.get("type", "line")
                    chart_data = chart.get("data", {})
                    chart_layout = chart.get("layout", {})

                    # Render chart based on type
                    if chart_type in ["line", "bar", "scatter", "area"]:
                        fig = create_chart(chart_type, chart_data, chart_layout)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.error(f"Failed to create {chart_type} chart")
                    elif chart_type in ["boxplot", "violin", "correlation"]:
                        fig = create_scientific_chart(chart_type, chart_data, chart_layout)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.error(f"Failed to create {chart_type} chart")
                    else:
                        st.warning(f"Unsupported chart type: {chart_type}")

# Main app logic
if viz_id:
    # Load visualization data from API
    viz_data = load_visualization_data(viz_id)

    if viz_data:
        st.title(viz_data.get('title', 'Data Visualization'))

        chart_type = viz_data.get('chart_type')
        data = viz_data.get('data', {})
        layout = viz_data.get('layout', {})
        options = viz_data.get('options', {})

        # Show metadata if available
        if "metadata" in viz_data and viz_data["metadata"]:
            with st.expander("Visualization Metadata"):
                st.json(viz_data["metadata"])

        # Render based on chart type
        if chart_type == "dashboard":
            render_dashboard(data)
        elif chart_type in ["boxplot", "violin", "correlation"]:
            fig = create_scientific_chart(chart_type, data, layout)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            fig = create_chart(chart_type, data, layout)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

        # Show raw data for transparency
        with st.expander("Show Raw Data"):
            if 'data' in data and isinstance(data['data'], list):
                st.dataframe(pd.DataFrame(data['data']))
            elif 'x' in data and 'y' in data:
                df = pd.DataFrame({
                    "x": data['x'],
                    "y": data['y']
                })
                st.dataframe(df)
            else:
                st.json(data)
    else:
        st.error(f"Failed to load visualization data for ID {viz_id}")
else:
    st.title("Data Visualization Demo")
    st.info("Please create a visualization using the API and access it via the returned URL.")

    # Demo chart
    st.subheader("Sample Visualization")
    data = pd.DataFrame({
        "x": [1, 2, 3, 4, 5],
        "y": [10, 20, 30, 20, 10]
    })
    st.line_chart(data)