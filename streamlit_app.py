import streamlit as st
import time
import requests
import uuid
from streamlit_lottie import st_lottie

# ==========================================
#  ⚙️ 設定エリア
# ==========================================

# 1. GAS URL (ご自身のURL)
GAS_URL = "https://script.google.com/macros/s/xxxxxxxxxxxxxxxxx/exec"

# 2. ユーザー管理（ID: パスワード）
# ※ここで担当者とパスワードを決めます
USERS = {
    "自分": "1111",
    "上司": "2222",
    "経理": "3333",
    "メンバーA": "aaaa"
}

# アニメーション
LOTTIE_WALKING_BOOK = "https://lottie.host/c6840845-b867-4323-9123-523760e2587c/8s565656.json"

# ==========================================

st.set_page_config(page_title="Task Walker", page_icon="📘", layout="wide")

# --- 関数群 ---
def get_tasks():
    try:
        r = requests.get(GAS_URL)
        return r.json() if r.status_code == 200 else []
    except:
        return []

def create_task(data):
    data["action"] = "create" # 新規作成モード
    try:
        requests.post(GAS_URL, json=data)
        return True
    except:
        return False

def update_status(task_id, new_status):
    data = {"action": "update", "id": task_id, "status": new_status}
    try:
        requests.post(GAS_URL, json=data)
        return True
    except:
        return False

def load_lottieurl(url):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# --- 認証機能 ---
def login():
    st.title("🔐 Task Walker ログイン")
    
    with st.form("login_form"):
        user_id = st.selectbox("ユーザーID（担当者）", list(USERS.keys()))
        password = st.text_input("パスワード", type="password")
        submitted = st.form_submit_button("ログイン")
        
        if submitted:
            if USERS.get(user_id) == password:
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user_id
                st.rerun()
            else:
                st.error("パスワードが違います")

# ==========================================
#  メイン処理
# ==========================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
else:
    # ログイン後の画面
    current_user = st.session_state["user_id"]
    lottie_book = load_lottieurl(LOTTIE_WALKING_BOOK)
    
    # --- サイドバー（メニュー） ---
    st.sidebar.title(f"👤 {current_user}")
    
    # 画面切り替えメニュー
    menu = st.sidebar.radio("メニュー", ["📊 タスクボード (一覧)", "📝 タスクを依頼する (新規)"])
    
    st.sidebar.divider()
    if st.sidebar.button("ログアウト"):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- アニメーション演出 ---
    if 'is_walking' not in st.session_state: st.session_state.is_walking = False
    
    if st.session_state.is_walking:
        st.info(f"📘 タスクが「{st.session_state.walking_target}」へ向かっています！")
        if lottie_book: st_lottie(lottie_book, speed=1.5, loop=True, height=200)
        time.sleep(2)
        st.session_state.is_walking = False
        st.rerun()

    # ==========================================
    #  画面1: タスクボード (4枠表示)
    # ==========================================
    if menu == "📊 タスクボード (一覧)":
        st.subheader("タスク状況")
        
        if st.button("🔄 最新データ更新"):
            st.rerun()

        # データ取得
        all_tasks = get_tasks()
        # 自分に関連するタスクのみ表示（自分が担当 or 自分が依頼）
        # ※全員分見たい場合はこのフィルタを外してください
        my_tasks = [t for t in all_tasks if t['to_user'] == current_user or t['from_user'] == current_user]
        
        # 4つの列を作成
        col1, col2, col3, col4 = st.columns(4)
        
        # 定義
        cols = {
            "未着手": col1,
            "対応中": col2,
            "完了": col3,
            "ルーティン": col4
        }
        
        # カラムのヘッダー表示
        col1.info("🛑 未着手")
        col2.warning("🏃 対応中")
        col3.success("✅ 完了")
        col4.info("🔄 ルーティン")

        # タスクを振り分け
        for task in my_tasks:
            status = task.get('status', '未着手')
            if status not in cols: status = '未着手'
            
            with cols[status]:
                # カード風表示
                with st.container(border=True):
                    # 優先度アイコン
                    prio_icon = "🔥" if task['priority'] == "🔥 至急" else "📘"
                    st.markdown(f"**{prio_icon} {task['content']}**")
                    st.caption(f"From: {task['from_user']} → To: {task['to_user']}")
                    
                    # ステータス移動ボタン
                    if status == "未着手":
                        if st.button("着手する ➡", key=f"start_{task['id']}"):
                            update_status(task['id'], "対応中")
                            st.rerun()
                    elif status == "対応中":
                        if st.button("完了する ✅", key=f"done_{task['id']}"):
                            update_status(task['id'], "完了")
                            st.rerun()
                    elif status == "完了":
                         st.caption("Great Job! 🎉")

    # ==========================================
    #  画面2: タスク依頼画面 (新規作成)
    # ==========================================
    elif menu == "📝 タスクを依頼する (新規)":
        st.subheader("📤 新しいタスクを依頼する")
        
        with st.form("create_task"):
            content = st.text_input("タスク内容")
            target = st.selectbox("誰に依頼しますか？", list(USERS.keys()))
            priority = st.radio("優先度", ["🔥 至急", "🌲 通常", "🐢 なる早"], horizontal=True, index=1)
            is_routine = st.checkbox("ルーティンタスクとして登録")
            
            submitted = st.form_submit_button("タスクを送信 📘💨")
            
            if submitted and content:
                new_id = str(uuid.uuid4()) # ユニークID生成
                status = "ルーティン" if is_routine else "未着手"
                
                new_task = {
                    "id": new_id,
                    "content": content,
                    "from_user": current_user,
                    "to_user": target,
                    "priority": priority,
                    "status": status
                }
                
                if create_task(new_task):
                    st.session_state.is_walking = True
                    st.session_state.walking_target = target
                    st.rerun()
                else:
                    st.error("送信エラー")
