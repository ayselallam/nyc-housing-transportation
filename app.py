
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px

DATA_FILE = "nyc_housing_traffic_integrated.csv"
df = pd.read_csv(DATA_FILE)
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["affordable_units"] = pd.to_numeric(df["affordable_units"], errors="coerce")
df["avg_traffic_volume"] = pd.to_numeric(df["avg_traffic_volume"], errors="coerce")
df["traffic_sample_count"] = pd.to_numeric(df["traffic_sample_count"], errors="coerce")

boroughs = sorted(df["borough"].dropna().unique())
years = sorted(df["year"].dropna().astype(int).unique())

app = Dash(__name__)
app.title = "NYC Housing & Traffic Insights"

app.layout = html.Div([
    html.H1("NYC Housing & Transportation Insights"),
    html.P("Explore affordable housing production alongside sampled roadway traffic counts."),
    html.Div([
        html.Label("Borough"),
        dcc.Dropdown(
            id="borough-filter",
            options=[{"label": "All boroughs", "value": "ALL"}] +
                    [{"label": b, "value": b} for b in boroughs],
            value="ALL", clearable=False
        ),
        html.Label("Year"),
        dcc.Dropdown(
            id="year-filter",
            options=[{"label": "All years", "value": "ALL"}] +
                    [{"label": str(int(y)), "value": int(y)} for y in years],
            value="ALL", clearable=False
        ),
        html.Label("Search (e.g. Brooklyn 2023)"),
        dcc.Input(id="search-input", type="text", placeholder="Type borough or year",
                  style={"width": "100%", "padding": "8px"}),
        html.Button("Generate Report", id="generate-button", n_clicks=0,
                    style={"marginTop": "12px"})
    ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "10px",
              "maxWidth": "900px"}),
    html.Hr(),
    html.Div(id="summary"),
    dcc.Graph(id="scatter-chart"),
    dcc.Graph(id="bar-chart"),
    dcc.Graph(id="trend-chart"),
    html.H2("Story, interpretation and limitations"),
    html.P(
        "This dashboard compares borough-year affordable housing production with average "
        "recorded 15-minute traffic volume. Traffic counts are samples from selected roads "
        "and times, not a complete count of all borough traffic. Housing project start date "
        "is an HPD project milestone, not necessarily occupancy. Associations do not prove causation."
    )
], style={"fontFamily": "Arial, sans-serif", "padding": "24px", "maxWidth": "1200px",
          "margin": "auto"})

@app.callback(
    Output("summary", "children"),
    Output("scatter-chart", "figure"),
    Output("bar-chart", "figure"),
    Output("trend-chart", "figure"),
    Input("generate-button", "n_clicks"),
    State("borough-filter", "value"),
    State("year-filter", "value"),
    State("search-input", "value")
)
def generate_report(n_clicks, borough, year, search):
    filtered = df.copy()
    if borough != "ALL":
        filtered = filtered[filtered["borough"] == borough]
    if year != "ALL":
        filtered = filtered[filtered["year"] == float(year)]
    if search:
        s = search.strip().lower()
        matching_boroughs = [b for b in boroughs if b.lower() in s]
        matching_years = [y for y in years if str(int(y)) in s]
        if matching_boroughs:
            filtered = filtered[filtered["borough"].isin(matching_boroughs)]
        if matching_years:
            filtered = filtered[filtered["year"].isin(matching_years)]

    complete = filtered.dropna(subset=["affordable_units", "avg_traffic_volume"])
    if complete.empty:
        message = html.P("No matching borough-year records with both housing and traffic data.")
        empty = px.scatter(title="No data for the selected filters")
        return message, empty, empty, empty

    total_units = complete["affordable_units"].sum()
    avg_traffic = complete["avg_traffic_volume"].mean()
    message = html.Div([
        html.H3(f"Report generated — {len(complete)} matched borough-year records"),
        html.P(f"Affordable units represented: {total_units:,.0f}"),
        html.P(f"Mean of recorded traffic-volume averages: {avg_traffic:,.2f}")
    ])

    scatter = px.scatter(
        complete, x="affordable_units", y="avg_traffic_volume",
        color="borough", size="traffic_sample_count", hover_data=["year"],
        title="Affordable housing units vs average recorded traffic"
    )
    bar_data = complete.groupby("borough", as_index=False)["affordable_units"].sum()
    bar = px.bar(bar_data, x="borough", y="affordable_units",
                 title="Affordable housing units in filtered records")
    trend = px.line(
        complete.sort_values("year"), x="year", y="avg_traffic_volume",
        color="borough", markers=True,
        title="Average recorded traffic volume over time"
    )
    return message, scatter, bar, trend

if __name__ == "__main__":
    app.run(debug=True)
