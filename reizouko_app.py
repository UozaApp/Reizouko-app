import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta

# セッション内で画面幅を記録
st.markdown("""
<script>
const width = window.innerWidth;
window.parent.postMessage({type: 'streamlit:width', width}, '*');
</script>
""", unsafe_allow_html=True)

# カスタムJSから画面幅を受信
st.components.v1.html(
    """
    <script>
    const sendWidth = () => {
        const width = window.innerWidth;
        const streamlitEvent = new Event("streamlit:render");
        window.dispatchEvent(streamlitEvent);
        window.parent.postMessage({type: "streamlit:width", width: width}, "*");
    };
    sendWidth();
    window.addEventListener("resize", sendWidth);
    </script>
    """,
    height=0,
)

if "screen_width" not in st.session_state:
    st.session_state["screen_width"] = 1200  # デフォルト

# WebSocketイベントで幅を受信
st.markdown("""
<script>
window.addEventListener("message", (event) => {
    if (event.data.type === "streamlit:width") {
        const width = event.data.width;
        fetch("/_stcore/update_session_state", {
            method: "POST",
            body: JSON.stringify({screen_width: width}),
            headers: {
                "Content-Type": "application/json"
            }
        });
    }
});
</script>
""", unsafe_allow_html=True)


# ----------------------------
# データ保存用CSVファイル名
DATA_FILE = "reizouko_list.csv"

# ----------------------------
# 初回起動時にファイルがなければ作成
def init_data_file():
    try:
        pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        df_init = pd.DataFrame(columns=["食材", "購入日", "賞味期限", "ジャンル", "個数"])
        df_init.to_csv(DATA_FILE, index=False)

# ----------------------------
# データを読み込み／保存
def load_data():
    return pd.read_csv(DATA_FILE)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def add_items(items, buy_date, expiry_date, genre, quantity):
    df = load_data()
    new_entries = pd.DataFrame({
        "食材": items,
        "購入日": [buy_date] * len(items),
        "賞味期限": [expiry_date] * len(items),
        "ジャンル": [genre] * len(items),
        "個数": [quantity] * len(items)
    })
    df = pd.concat([df, new_entries], ignore_index=True)
    save_data(df)

# ----------------------------
# アプリ開始処理
init_data_file()

# ----------------------------
# UI設定
st.set_page_config(page_title="わがやの冷蔵庫", layout="wide")

st.markdown("""
<style>
/* レスポンシブ対応 */
@media (max-width: 768px) {
    .food-card {
        width: 100% !important;
        margin: 10px 0 !important;
    }
    .section-card {
        margin: 10px !important;
        padding: 10px !important;
    }
    .css-1v0mbdj {  /* Streamlit のカラムを縦に積む */
        flex-direction: column !important;
    }
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"] * {
    font-family: 'Kiwi Maru', sans-serif !important;
}
[data-testid="stSidebar"] {
    background-color: #F6F4EF;
}
.section-card {
    background-color: #ffffff;
    padding: 20px;
    margin: 20px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
.food-card {
    padding: 10px 12px;
    border-radius: 10px;
    font-size: 13px;
    line-height: 1.3em;
    color: #333;
    margin: 10px auto;
    height: 120px;
    width: 100%;
    max-width: 200px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    overflow: hidden;
}
.food-card strong {
    font-size: 20px;
    margin-bottom: 2px;
    line-height: 1.4em;
}
</style>
""", unsafe_allow_html=True)

import streamlit as st

# ----------------------------
# フォント＋余白調整CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic&display=swap');

/* 全体フォント */
html, body, [class^="css"], [data-testid="stAppViewContainer"] * {
    font-family: 'Zen Maru Gothic', sans-serif !important;
}

/* メイン領域の余白削除 */
[data-testid="stAppViewContainer"] > .main {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* 最初のセクションの余白も削除 */
section.main > div:first-child {
    padding-top: 0 !important;
    margin-top: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# HTMLで直接タイトル表示（余白ゼロにする）
st.markdown("""
<div style="margin-top:0; padding-top:0">
    <h1 style='font-family: "Kiwi Maru", sans-serif; margin-top:0;'>うおざ家の冷蔵庫</h1>
</div>
""", unsafe_allow_html=True)

# 本文
st.markdown("食材を登録して、賞味期限も一緒に管理しましょう。")


# ----------------------------
# サイドバー：食材登録
st.sidebar.header("食材登録")
def food_registration():
    default_items = ["にんじん", "玉ねぎ", "ピーマン", "じゃがいも", "牛乳", "卵", "納豆", "キャベツ", "鶏もも肉"]
    selected_items = st.sidebar.multiselect("よく使う食材", default_items)
    new_item = st.sidebar.text_input("新しい食材（カンマ区切り）", placeholder="例: パプリカ, 豆腐")
    genre = st.sidebar.selectbox("ジャンル", ["野菜", "肉・魚", "冷凍肉・魚", "卵", "加工食品", "その他冷凍食品", "その他"])
    buy_date = st.sidebar.date_input("購入日", value=datetime.today())

    genre_expiry_days = {
        "野菜": 7, "肉・魚": 3, "冷凍肉・魚": 20, "その他冷凍食品": 20,
        "卵": None, "加工食品": None, "その他": None
    }
    if genre == "その他":
        expiry_date = st.sidebar.date_input("賞味期限（手入力）", value=datetime.today() + timedelta(days=3))
    else:
        expiry_date = buy_date + timedelta(days=genre_expiry_days[genre])
        st.sidebar.markdown(f"自動設定された賞味期限: **{expiry_date.strftime('%Y-%m-%d')}**")

    quantity = st.sidebar.number_input("個数", min_value=1, value=1)

    if st.sidebar.button("登録"):
        all_items = selected_items.copy()
        if new_item:
            all_items += [item.strip() for item in new_item.split(",") if item.strip()]
        if all_items:
            add_items(all_items, buy_date.strftime("%Y-%m-%d"), expiry_date.strftime("%Y-%m-%d"), genre, quantity)
            st.sidebar.success(f"{', '.join(all_items)} を登録しました！")
        else:
            st.sidebar.warning("食材を選ぶか入力してください。")

food_registration()

# ----------------------------
# 食材一覧表示（メイン）
st.subheader("冷蔵庫の中身")
df_current = load_data()
df_current["賞味期限"] = pd.to_datetime(df_current["賞味期限"], errors="coerce")
df_current = df_current.sort_values("賞味期限")
today = pd.Timestamp.today().normalize()

if df_current.empty:
    st.info("現在、食材は登録されていません。")
else:
    grouped = df_current.groupby("ジャンル")
for genre, group in grouped:
    st.markdown(f"#### ジャンル: {genre}")
    num_items = len(group)

    # ▼ スマホとPCで列数を自動切替
    screen_width = st.session_state.get("screen_width", 1200)
    if screen_width < 768:
        num_columns = 2
    elif screen_width < 1080:
        num_columns = 2
    else:
        num_columns = 3
    num_columns = min(num_items, num_columns)

    rows = math.ceil(num_items / num_columns)
    for row in range(rows):
        cols = st.columns(num_columns)
        for i in range(num_columns):
            idx = row * num_columns + i
            if idx < num_items:
                r = group.iloc[idx]
                food = r["食材"]
                expiry = r["賞味期限"]
                buy_date = r["購入日"]
                quantity = r["個数"]
                days_left = (expiry - today).days if pd.notna(expiry) else None

                if days_left is None:
                    color = "#aaa"; status = "賞味期限不明"
                elif days_left < 0:
                    color = "#f2b5b5"; status = f"期限切れ（{abs(days_left)}日前）"
                elif days_left == 0:
                    color = "#ffcccc"; status = "本日まで"
                elif days_left <= 2:
                    color = "#ffe5b4"; status = f"あと{days_left}日"
                elif days_left <= 5:
                    color = "#f5f0c9"; status = f"あと{days_left}日"
                else:
                    color = "#d5f5e3"; status = f"あと{days_left}日"

                with cols[i]:
                    st.markdown(
                        f"<div class='food-card' style='background-color:{color};'>"
                        f"<strong>{food}</strong>"
                        f"購入日: {buy_date}<br>賞味期限: {expiry.date()}<br>個数: {quantity}<br>{status}"
                        f"</div>",
                        unsafe_allow_html=True
                    )


# ----------------------------
# 食材使用セクション
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("食材を使ったら更新")
if not df_current.empty:
    df_current["表示用"] = df_current.apply(lambda row: f"{row['食材']}（{row['購入日']}｜残り{row['個数']}個）", axis=1)
    selected_label = st.selectbox("使った食材を選んでください", df_current["表示用"])
    selected_row = df_current[df_current["表示用"] == selected_label].iloc[0]
    current_qty = selected_row["個数"]
    idx = selected_row.name
    max_reduction = min(current_qty, 10)
    reduction_choices = [i * 0.5 for i in range(1, int(max_reduction * 2) + 1)]
    reduce_amount = st.selectbox("使った量", reduction_choices)

    col_update, col_empty = st.columns([1, 1])
    with col_update:
        if st.button("更新"):
            new_qty = current_qty - reduce_amount
            if new_qty > 0:
                df_current.at[idx, "個数"] = round(new_qty, 2)
                st.success(f"{selected_row['食材']} を {reduce_amount} 使用（残り: {new_qty}個）")
            else:
                df_current = df_current.drop(idx)
                st.success(f"{selected_row['食材']} を使い切りました。")
            df_current = df_current.drop(columns=["表示用"])
            save_data(df_current.reset_index(drop=True))
            st.rerun()

# ----------------------------
# レシピ提案プロンプト
st.subheader("レシピ提案")
ingredients_list = df_current["食材"].tolist()
ingredients_text = ", ".join(ingredients_list)
if st.button("レシピを提案"):
    if not ingredients_list:
        st.warning("冷蔵庫に食材が登録されていません。")
    else:
        prompt = f"""
以下の条件に合うレシピを1つ提案してください：
- 使用可能な食材: {ingredients_text}
- 減塩・低コレステロール
- 夕飯の主菜と副菜
- 足りない材料があってもOK（その場合は足りない材料を明記）
- 調味料は材料として考慮しなくてOKだが、レシピの分量は記載要
- 出力形式:
  ### レシピ名
  - 材料 分量
  - 作り方
  - 不足している材料があれば最後に列挙
"""
        st.code(prompt, language="markdown")

# ChatGPTへのリンクボタン
st.markdown("""
<div style='text-align: center; margin-top: 30px;'>
    <a href='https://chat.openai.com' target='_blank' style='text-decoration: none;'>
        <button style='background-color: #6C757D; color: white; padding: 10px 20px; border: none; border-radius: 8px; font-size: 14px;'>
            ChatGPTリンク
        </button>
    </a>
</div>
""", unsafe_allow_html=True)
