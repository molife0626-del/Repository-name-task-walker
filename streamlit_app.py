import streamlit as st
import time
import requests
import uuid
import pandas as pd
from streamlit_lottie import st_lottie
import plotly.express as px

# ==========================================
#  ⚙️ 設定エリア
# ==========================================
# ★ご自身のURLに書き換えてください
GAS_URL = "https://script.google.com/macros/s/AKfycbzqYGtlTBRVPiV6Ik4MdZM4wSYSQd5lDvHzx0zfwjUk1Cpb9woC3tKppCOKQ364ppDp/exec" 

# ユーザー管理
USERS = {
    "自分": "1111",
    "上司": "2222",
    "経理": "3333",
    "メンバーA": "aaaa"
}
ADMIN_USERS = ["上司", "経理"]
LOTTIE_WALKING_BOOK = "https://lottie.host/c6840845-b867-4323-9123-523760e2587c/8s565656.json"

st.set_page_config(page_title="Task Walker", page_icon="📘", layout="wide")

# --- CSS: 右上のベアリング復活 ---
st.markdown("""
<style>
/* 1. 標準のRunningアイコンなどを消す */
[data-testid="stStatusWidget"] > div > div > img { display: none; }
[data-testid="stStatusWidget"] svg { display: none; }

/* 2. 右上の処理中アイコンを「ベアリング」にする */
[data-testid="stStatusWidget"] > div > div {
    width: 30px;
    height: 30px;
    border: 3px solid #666; /* 外輪 */
    border-radius: 50%;
    border-top-color: transparent; /* 回転感 */
    position: relative;
    animation: spin 1s linear infinite;
    margin-top: 5px;
}
/* 中の玉（点線） */
[data-testid="stStatusWidget"] > div > div::after {
    content: "";
    position: absolute;
    top: 3px; left: 3px; right: 3px; bottom: 3px;
    border: 2px dotted #888; /* ボール */
    border-radius: 50%;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* カードのデザイン */
.task-card {
    padding: 15px;
    border-radius: 8px;
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    margin-bottom: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# --- 通信関数 ---
def get_tasks_from_server():
    """サーバーからデータを取得"""
    try:
        r = requests.get(GAS_URL)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                st.session_state['tasks_cache'] = data
                return data
    except Exception as e:
        pass
    return []

def get_unique_tasks():
    if 'tasks_cache' not in st.session_state:
        st.session_state['tasks_cache'] = get_tasks_from_server()
    tasks = st.session_state['tasks_cache']
    unique_map = {}
    for t in tasks:
        if 'id' in t: unique_map[t['id']] = t
    return list(unique_map.values())

def safe_post(data):
    """送信処理（完了後にリロード）"""
    with st.spinner('通信中...'):
        try:
            r = requests.post(GAS_URL, json=data)
            if r.status_code != 200:
                st.error(f"送信エラー: {r.status_code}")
                return False
        except Exception as e:
            st.error(f"通信エラー: {e}")
            return False
            
        time.sleep(1.0) # 確実に反映させるための待機
        get_tasks_from_server() # 最新データを取得
        return True

# --- アクション ---
def update_status(task_id, new_status):
    safe_post({"action": "update", "id": task_id, "status": new_status})
    st.rerun()

def update_content(task_id, new_content):
    safe_post({"action": "update", "id": task_id, "content": new_content})
    st.rerun()

def delete_task(task_id):
    safe_post({"action": "delete", "id": task_id})
    st.rerun()

def forward_task(current_id, new_content, new_target, my_name):
    data = {
        "action": "forward", 
        "id": current_id, 
        "new_id": str(uuid.uuid4()),
        "new_content": new_content, 
        "new_target": new_target, 
        "from_user": my_name
    }
    if safe_post(data):
        st.session_state.is_walking = True
        st.session_state.walking_target = new_target
        st.rerun()

def create_task(content, target, my_name, is_routine):
    status = "ルーティン" if is_routine else "未着手"
    data = {
        "action": "create",
        "id": str(uuid.uuid4()),
        "content": content,
        "from_user": my_name,
        "to_user": target,
        "status": status
    }
    if safe_post(data):
        st.session_state.is_walking = True
        st.session_state.walking_target = target
        st.rerun()

def load_lottieurl(url):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- 認証 ---
def login():
    st.markdown("<h1 style='text-align: center;'>🔐 Task Walker</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login"):
            uid = st.text_input("ユーザーID")
            pwd = st.text_input("パスワード", type="password")
            if st.form_submit_button("ログイン", use_container_width=True):
                if uid in USERS and USERS[uid] == pwd:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = uid
                    get_tasks_from_server()
                    st.rerun()
                else: st.error("認証失敗")

# ==========================================
#  メイン処理
# ==========================================
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
else:
    current_user = st.session_state["user_id"]
    lottie_book = load_lottieurl(LOTTIE_WALKING_BOOK)
    
    all_tasks = get_unique_tasks()
    my_active_tasks = [t for t in all_tasks if t.get('to_user') == current_user and t.get('status') != '完了']
    alert_msg = f" 🔴{len(my_active_tasks)}" if my_active_tasks else ""

    st.sidebar.title(f"👤 {current_user}")
    menu = st.sidebar.radio("メニュー", [f"📊 マイタスク{alert_msg}", "📝 新規タスク依頼", "🔔 通知センター", "📈 チーム分析"])
    
    if current_user in ADMIN_USERS:
        st.sidebar.markdown("---")
        if st.sidebar.button("🦅 管理者画面"): st.session_state["admin_mode"] = True
    
    st.sidebar.divider()
    if st.sidebar.button("ログアウト"):
        st.session_state["logged_in"] = False
        st.rerun()

    if 'is_walking' not in st.session_state: st.session_state.is_walking = False
    if st.session_state.is_walking:
        st.info(f"📘 タスクが「{st.session_state.walking_target}」へ向かっています！")
        if lottie_book: st_lottie(lottie_book, speed=1.5, loop=True, height=200)
        time.sleep(0.8)
        st.session_state.is_walking = False
        st.rerun()

    # 1. マイタスクボード
    if "マイタスク" in menu:
        col_h, col_b = st.columns([4,1])
        col_h.subheader("マイタスクボード")
        if col_b.button("🔄 同期"): 
            get_tasks_from_server()
            st.rerun()
        
        my_tasks = [t for t in all_tasks if t.get('to_user') == current_user]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.error("🛑 未着手")
        with col2: st.warning("🏃 対応中")
        with col3: st.success("✅ 完了")
        with col4: st.markdown("<div style='background-color:#6f42c1;color:white;padding:10px;border-radius:5px;text-align:center;'>🟣 ルーティン</div>", unsafe_allow_html=True)
        cols = {"未着手": col1, "対応中": col2, "完了": col3, "ルーティン": col4}

        for task in my_tasks:
            status = task.get('status', '未着手')
            if status not in cols: status = '未着手'
            t_id = task.get('id', '')
            content = task.get('content', '（タイトルなし）')
            
            with cols[status]:
                with st.container(border=True):
                    st.markdown(f"#### {content}")
                    st.caption(f"依頼: {task.get('from_user')}")

                    if status == "完了" and task.get('completed_at'):
                        st.caption(f"🏁 {task.get('completed_at')}")

                    # --- アクション ---
                    if status == "未着手":
                        if st.button("対応開始 ➡", key=f"go_{t_id}", use_container_width=True):
                            update_status(t_id, "対応中")
                            
                    elif status == "対応中":
                        if st.button("完了する ✅", key=f"done_{t_id}", use_container_width=True):
                            update_status(t_id, "完了")
                            
                    elif status == "ルーティン":
                         if st.button("完了 ✅", key=f"r_done_{t_id}", use_container_width=True):
                            update_status(t_id, "完了")
                            
                    elif status == "完了":
                         if st.button("↩ 戻す", key=f"back_{t_id}", use_container_width=True):
                            update_status(t_id, "対応中")

                    # 詳細メニュー
                    with st.expander("⚙️ 転送・編集"):
                        if status != "完了":
                            st.markdown("**🏃 バトンタッチ**")
                            n_user = st.selectbox("次へ", list(USERS.keys()), key=f"u_{t_id}")
                            n_cont = st.text_input("内容", value=f"確認：{content}", key=f"c_{t_id}")
                            if st.button("転送実行 🚀", key=f"fw_{t_id}"):
                                forward_task(t_id, n_cont, n_user, current_user)
                            st.divider()
                        
                        st.markdown("**📝 編集**")
                        e_cont = st.text_input("タイトル修正", value=content, key=f"ec_{t_id}")
                        if st.button("変更保存", key=f"sv_{t_id}"):
                            update_content(t_id, e_cont)
                        
                        if st.button("🗑 削除", key=f"del_{t_id}"):
                            delete_task(t_id)

    # 2. 新規依頼
    elif menu == "📝 新規タスク依頼":
        st.subheader("📤 新規タスク")
        with st.form("create"):
            content = st.text_input("タスクのタイトル")
            target = st.selectbox("依頼先", list(USERS.keys()))
            is_routine = st.checkbox("🟣 ルーティン")
            if st.form_submit_button("送信 📘💨", use_container_width=True):
                if content:
                    create_task(content, target, current_user, is_routine)
                else:
                    st.error("タイトルを入力してください")

    # 3. 通知
    elif menu == "🔔 通知センター":
        st.subheader("🔔 通知センター")
        if st.button("最新取得"): 
            get_tasks_from_server()
            st.rerun()
        my_related = [t for t in all_tasks if t.get('to_user') == current_user]
        if my_related:
            for task in reversed(my_related):
                with st.container(border=True):
                    st.markdown(f"**{task.get('from_user')}** ➡ あなた")
                    st.markdown(f"##### 「{task.get('content')}」")
                    st.caption(f"状態: {task.get('status')} | {task.get('date')}")
        else: st.info("通知なし")

    # 4. 分析
    elif "チーム分析" in menu:
        st.subheader("📊 分析")
        if st.button("データ更新"): 
            get_tasks_from_server()
            st.rerun()
        if all_tasks:
            df = pd.DataFrame(all_tasks)
            if 'status' in df.columns:
                active_df = df[df['status'] != '完了']
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("##### 🏃 残タスク")
                    if not active_df.empty:
                        c = active_df['to_user'].value_counts().reset_index()
                        c.columns=['担当','件数']
                        st.plotly_chart(px.bar(c, x='担当', y='件数', color='担当'), use_container_width=True)
                with col2:
                    st.markdown("##### 📋 割合")
                    c = df['status'].value_counts().reset_index()
                    c.columns=['状態','件数']
                    st.plotly_chart(px.pie(c, values='件数', names='状態'), use_container_width=True)
                st.divider()
                st.markdown("##### 🔍 詳細リスト")
                selected_user = st.selectbox("担当者", ["全員"] + list(USERS.keys()))
                view_df = df[df['to_user'] == selected_user] if selected_user != "全員" else df
                if not view_df.empty:
                    view_df = view_df[['content', 'status', 'from_user', 'to_user', 'date']].rename(columns={'content': 'タイトル'})
                    st.dataframe(view_df, use_container_width=True, hide_index=True)
