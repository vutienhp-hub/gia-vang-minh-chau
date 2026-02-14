from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime
import plotly.express as px

app = Flask(__name__)

URL = "https://btmc.vn/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def crawl_price():
    response = requests.get(URL, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table")
    rows = table.find_all("tr")

    header_cols = rows[0].find_all(["td", "th"])
    headers_text = [col.text.strip().lower() for col in header_cols]

    buy_index = None
    sell_index = None

    for i, h in enumerate(headers_text):
        if "mua" in h:
            buy_index = i
        if "bán" in h:
            sell_index = i

    data = []

    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) > max(buy_index, sell_index):
            values = [c.text.strip() for c in cols]

            loai_vang = values[1] if len(values) > 1 else values[0]
            gia_mua = re.sub(r"[^\d]", "", values[buy_index])
            gia_ban = re.sub(r"[^\d]", "", values[sell_index])

            if gia_mua and gia_ban:
                data.append({
                    "Loại vàng": loai_vang,
                    "Giá mua vào": int(gia_mua) * 1000,
                    "Giá bán ra": int(gia_ban) * 1000,
                })

    return pd.DataFrame(data)


@app.route("/")
def index():
    df = crawl_price()

    fig = px.bar(
        df,
        x="Loại vàng",
        y="Giá bán ra",
        title="Giá Bán Ra Hiện Tại",
        text_auto=True
    )

    fig.update_layout(
        xaxis_tickangle=-30,
        height=500
    )

    graph_html = fig.to_html(full_html=False)

    html = """
    <html>
    <head>
        <meta http-equiv="refresh" content="30">
        <title>Dashboard Giá Vàng BTMC</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-dark text-light">
        <div class="container mt-4">
            <h1 class="text-warning">📈 Dashboard Giá Vàng BTMC</h1>
            <p>Cập nhật lúc: {{time}}</p>

            <div class="card bg-secondary p-3 mb-4">
                {{table | safe}}
            </div>

            <div class="card bg-light p-3">
                {{graph | safe}}
            </div>
        </div>
    </body>
    </html>
    """

    return render_template_string(
        html,
        table=df.to_html(classes="table table-dark table-striped", index=False),
        graph=graph_html,
        time=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    )


if __name__ == "__main__":
    app.run(debug=True)
