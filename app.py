from flask import Flask, request, render_template_string, redirect
import sqlite3
import csv
import io
import os

app = Flask(__name__)
DB_NAME = "scores.db"

# データベース初期化
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            composer TEXT,
            genre TEXT,
            instrument TEXT,
            shelf TEXT,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ホーム画面・検索
@app.route("/", methods=["GET"])
def index():
    query = request.args.get("q", "")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if query:
        c.execute("SELECT * FROM books WHERE title LIKE ? OR composer LIKE ? OR instrument LIKE ? ORDER BY title",
                  (f"%{query}%", f"%{query}%", f"%{query}%"))
    else:
        c.execute("SELECT * FROM books ORDER BY title")
    books = c.fetchall()
    conn.close()
    
html = """
<!DOCTYPE html>
<html>
<head>
    <title>楽譜データベース</title>
    <style>
        body {
            background-color: #87cefa;  /* ここで好きな色に変更 */
            font-family: Arial, sans-serif;
        }
        table {
            border-collapse: collapse;
        }
        th, td {
            padding: 5px 10px;
        }
    </style>
</head>
<body>
    <h1>楽譜データベース</h1>
    <form method="get">
        <input type="text" name="q" placeholder="タイトル/作曲者/楽器で検索" value="{{ request.args.get('q','') }}">
        <input type="submit" value="検索">
    </form>
    <a href="/add">新しい楽譜を追加</a> | 
    <a href="/upload">CSV一括登録</a>
    <table border="1" style="margin-top:10px;">
        <tr><th>ID</th><th>タイトル</th><th>作曲者</th><th>ジャンル</th><th>楽器</th><th>棚</th><th>備考</th></tr>
        {% for b in books %}
        <tr>
            <td>{{ b[0] }}</td><td>{{ b[1] }}</td><td>{{ b[2] }}</td>
            <td>{{ b[3] }}</td><td>{{ b[4] }}</td><td>{{ b[5] }}</td><td>{{ b[6] }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""
return render_template_string(html, books=books, request=request)

# 個別追加画面
@app.route("/add", methods=["GET", "POST"])
def add():
    instruments_list = [
        "フルート","ピッコロ","クラリネット","バスクラリネット","オーボエ","ファゴット",
        "ソプラノサックス","アルトサックス","テナーサックス","バリトンサックス","トランペット",
        "ホルン","ユーフォニアム","チューバ","トロンボーン","ティンパニ","スネア","バスドラム",
        "ドラム","シンバル","グロッケン","ビブラフォン","シロフォン","マリンバ","チャイム",
        "コントラバス","ピアノ","エレクトリックベース"
    ]

    if request.method == "POST":
        title = request.form["title"]
        composer = request.form["composer"]
        genre = request.form["genre"]
        instruments = request.form.getlist("instrument")
        instrument_str = ",".join(instruments)
        shelf = request.form["shelf"]
        notes = request.form["notes"]

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO books (title, composer, genre, instrument, shelf, notes) VALUES (?, ?, ?, ?, ?, ?)",
                  (title, composer, genre, instrument_str, shelf, notes))
        conn.commit()
        conn.close()
        return redirect("/")

    html = """
    <h1>楽譜を追加</h1>
    <form method="post">
      タイトル: <input type="text" name="title"><br>
      作曲者: <input type="text" name="composer"><br>
      ジャンル: <input type="text" name="genre"><br>
      楽器:<br>
      {% for inst in instruments_list %}
      <input type="checkbox" name="instrument" value="{{ inst }}"> {{ inst }}<br>
      {% endfor %}
      棚の場所: <input type="text" name="shelf"><br>
      備考: <input type="text" name="notes"><br>
      <input type="submit" value="追加">
    </form>
    <a href="/">戻る</a>
    """
    return render_template_string(html, instruments_list=instruments_list)

# CSV一括登録
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["file"]
        if not file:
            return "ファイルが選択されていません"
        
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        for row in reader:
            c.execute("INSERT INTO books (title, composer, genre, instrument, shelf, notes) VALUES (?, ?, ?, ?, ?, ?)",
                      (row["タイトル"], row["作曲者"], row["ジャンル"], row["楽器"], row["棚"], row["備考"]))
        conn.commit()
        conn.close()
        return redirect("/")
    
    html = """
    <h1>CSV一括登録</h1>
    <form method="post" enctype="multipart/form-data">
      CSVファイルを選択: <input type="file" name="file"><br>
      <input type="submit" value="アップロード">
    </form>
    <a href="/">戻る</a>
    """
    return render_template_string(html)

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
