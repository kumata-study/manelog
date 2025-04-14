import streamlit as st
from logic import init_session_data, save_data, load_data, migrate_to_nested_structure
from layout import show_header, show_project_input


# ▼ セッションステートの初期化（これを追加！）
if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = "dashboard"  # 初期値は用途に応じて変えてOK

if "selected_project" not in st.session_state:
    st.session_state.selected_project = None

if "selected_file" not in st.session_state:
    st.session_state.selected_file = None

if "editing_mode" not in st.session_state:
    st.session_state.editing_mode = False

if "undo_stack" not in st.session_state:
    st.session_state.undo_stack = []

if "task_input" not in st.session_state:
    st.session_state.task_input = ""

if "log_input" not in st.session_state:
    st.session_state.log_input = ""

if "memo_input" not in st.session_state:
    st.session_state.memo_input = ""


# --- ページ設定 ---
st.set_page_config(page_title="マネログ", layout="wide")

# --- サイドバーにロゴボタン（中央寄せ + CSS） ---
with st.sidebar:
    st.markdown("# 📘 マネログ")  # ← 太く大きめに表示する（見出し風）

    if st.button("ホームに戻る"):
        st.session_state.selected_genre = None
        st.session_state.selected_mode = None
        st.session_state.selected_project = None
        st.session_state.selected_file = None
        st.rerun()

    # 💬 ChatGPTを開くリンク
    chatgpt_url = "https://chatgpt.com/g/g-p-67f96e613a108191b008bb24adc94357-manesimentoahuri"
    st.markdown(f"<a href='{chatgpt_url}' target='_blank'>💬 ChatGPTを開く</a>", unsafe_allow_html=True)



# --- セッション初期化とデータ読み込み ---
init_session_data()
if "undo_history" not in st.session_state:
    st.session_state.undo_history = []
load_data()
migrate_to_nested_structure()
save_data()

# --- サイドバー：ロゴ風タイトル ---
with st.sidebar:
    st.markdown("""
        <style>
        div.stButton > button {
            all: unset;
            font-size: 16px;
            color: #333;
            padding: 6px 0px;
            text-align: left;
            cursor: pointer;
            width: 100%;
        }
        div.stButton > button:hover {
            background-color: #f5f5f5;
            border-radius: 4px;
        }
        </style>
    """, unsafe_allow_html=True)


with st.sidebar:
    st.title("カテゴリ管理")

    # --- 初期化 ---
    if "selected_genre" not in st.session_state:
        st.session_state.selected_genre = None
    if "show_genre_input" not in st.session_state:
        st.session_state.show_genre_input = False
    if "show_genre_delete" not in st.session_state:
        st.session_state.show_genre_delete = False

    # --- テーマ一覧表示 ---
    st.markdown("### 📂 テーマ一覧")
    for genre in list(st.session_state.data.keys()):
        cols = st.columns([6, 1])
        with cols[0]:
            # ✅ ジャンル選択時のセッション初期化
            if st.button(f"{genre}", key=f"select_{genre}"):
                st.session_state.selected_genre = genre
                st.session_state.selected_mode = None
                st.session_state.selected_project = None
                st.session_state.selected_file = None
                st.rerun()
    #----------------------------------------
    st.markdown("---")
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # --- 新しいテーマ作成 ---
    if st.button("➕ 新規作成"):
        st.session_state.show_genre_input = not st.session_state.show_genre_input

    if st.session_state.show_genre_input:
        new_genre = st.text_input(
            "新しいテーマ名:", 
            key="new_genre_input_box", 
            placeholder="新しいテーマ名"
        )
        if st.button("✅ 登録"):
            if new_genre:
                if new_genre in st.session_state.data:
                    st.warning(f"テーマ「{new_genre}」は既に存在します")
                else:
                    st.session_state.data[new_genre] = {}
                    st.session_state.selected_genre = new_genre
                    save_data()
                    st.success(f"テーマ「{new_genre}」を作成しました")
                    st.session_state.show_genre_input = False
                    st.rerun()  # ← 🔧 ここを追加！
            else:
                st.warning("テーマ名を入力してください")
        
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)


    # --- 削除モードトグル ---
    if st.button("🗑️ 削除"):
        st.session_state.show_genre_delete = not st.session_state.show_genre_delete

    if st.session_state.show_genre_delete:
        delete_target = st.selectbox("削除するテーマを選択", list(st.session_state.data.keys()), key="delete_target_genre")
        if st.button("✅ 削除", key="confirm_delete_genre"):
            # 🔽 履歴を追加（複数対応）
            st.session_state.undo_history.append({
                "type": "genre",
                "path": [delete_target],
                "data": st.session_state.data[delete_target]
            })
            del st.session_state.data[delete_target]
            if st.session_state.selected_genre == delete_target:
                st.session_state.selected_genre = None
            save_data()
            st.success(f"テーマ「{delete_target}」を削除しました")
            st.rerun()
    if st.session_state.undo_history:
        last = st.session_state.undo_history[-1]
        label = " > ".join(last["path"])
        if st.button(f"↩ やり直す（{label} を復元）"):
            last = st.session_state.undo_history.pop()
            t, path, data = last["type"], last["path"], last["data"]

            if t == "genre":
                st.session_state.data[path[0]] = data

            elif t == "project":
                st.session_state.data[path[0]][path[1]] = data

            elif t == "task":
                genre, project, file, task_id = path
                # 復元先を検索して挿入（末尾でOK）
                st.session_state.data[genre][project][file]["tasks"].append(data)

            save_data()
            st.success(f"{t}「{' > '.join(path)}」を復元しました")
            st.rerun()



# --- メイン画面：ファイル or 通常表示 ---
selected_genre = st.session_state.selected_genre

if selected_genre is None:
    from layout import show_home
    show_home()
elif st.session_state.get("selected_mode") == "file":
    from layout import show_file_page
    show_file_page(
        selected_genre=selected_genre,
        project=st.session_state.selected_project,
        file=st.session_state.selected_file
    )
else:
    show_header(selected_genre)
    show_project_input(selected_genre)


