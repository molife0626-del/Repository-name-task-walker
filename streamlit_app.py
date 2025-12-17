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
GAS_URL = "https://script.google.com/macros/s/AKfycbzqYGtlTBRVPiV6Ik4MdZM4wSYSQd5lDvHzx0zfwjUk1Cpb9woC3tKppCOKQ364ppDp/exec" # ★URL書き換え

USERS = {
    "自分": "1111",
    "上司": "2222",
    "経理": "3333",
    "メンバーA": "aaaa"
}
ADMIN_USERS = ["上司", "経理"]
LOTTIE_WALKING_BOOK = "https://lottie.host/c6840845-b867-4323-9123-523760e2587c/8s565656.json"

st.set_page_config(page_title="Task Walker", page_icon="📘", layout="wide")

# --- 通信関数（高速化：キャッシュ制御） ---
def get_tasks_from_server():
    try:
        r = requests.get(GAS_URL)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                st.session_state['tasks_cache'] = data
                return data
    except:
        pass
    return []

def get_tasks():
    if 'tasks_cache' not in st.session_state:
        return get_tasks_from_server()
    return st.session_state['tasks_cache']

def create_task(data):
    data["action"] = "create"
    requests.post(GAS_URL, json=data)
    get_tasks_from_server()

def update_status(task_id, new_status):
    data = {"action": "update", "id": task_id, "status": new_status}
    requests.post(GAS_URL, json=data)
    get_tasks_from_server()

def update_task_data(task_id, status=None, content=None, priority=None):
    data = {"action": "update", "id": task_id}
    if status: data["status"] = status
    if content: data["content"] = content
    if priority: data["priority"] = priority
    requests.post(GAS_URL, json=data)
    get_tasks_from_server()

def delete_task(task_id):
    """削除機能"""
    data = {"action": "delete", "id": task_id}
    requests.post(GAS_URL, json=data)
    get_tasks_from_server()

def forward_task(current_id, new_content, new_target, new_prio, my_name):
    new_id = str(uuid.uuid4())
    data = {
        "action": "forward",
        "id": current_id,
        "new_id": new_id,
        "new_content": new_content,
        "new_target": new_target,
        "new_priority": new_prio,
        "from_user": my_name
    }
    requests.post(GAS_URL, json=data)
    get_tasks_from_server()

def load_lottieurl(url):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except:
        return None

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
                else:
                    st.error("認証失敗")

# ==========================================
#  メイン処理
# ==========================================
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
else:
    current_user = st.session_state["user_id"]
    lottie_book = load_lottieurl(LOTTIE_WALKING_BOOK)
    
    all_tasks = get_tasks()
    
    my_active_tasks = [t for t in all_tasks if t.get('to_user') == current_user and t.get('status') != '完了']
    alert_msg = f" 🔴{len(my_active_tasks)}" if my_active_tasks else ""

    st.sidebar.title(f"👤 {current_user}")
    
    menu = st.sidebar.radio(
        "メニュー", 
        [f"📊 マイタスク{alert_msg}", "📝 新規タスク依頼", "🔔 通知センター", "📈 チーム分析"]
    )
    if current_user in ADMIN_USERS:
        st.sidebar.markdown("---")
        if st.sidebar.button("🦅 管理者画面"): st.session_state["admin_mode"] = True
            
    st.sidebar.divider()
    if st.sidebar.button("ログアウト"):
        st.session_state["logged_in"] = False
        st.rerun()

    # アニメーション
    if 'is_walking' not in st.session_state: st.session_state.is_walking = False
    if st.session_state.is_walking:
        st.info(f"📘 タスクが「{st.session_state.walking_target}」へ向かっています！")
        if lottie_book: st_lottie(lottie_book, speed=1.5, loop=True, height=200)
        time.sleep(1.5)
        st.session_state.is_walking = False
        st.rerun()

    # 1. マイタスクボード
    if "マイタスク" in menu:
        col_h, col_b = st.columns([4,1])
        col_h.subheader("マイタスクボード")
        if col_b.button("🔄 更新"): 
            get_tasks_from_server()
            st.rerun()
        
        my_tasks = [t for t in all_tasks if t.get('to_user') == current_user or t.get('from_user') == current_user]
        
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
            content = task.get('content', '')
            
            with cols[status]:
                with st.container(border=True):
                    prio_icon = "🔥" if task.get('priority') == "🔥 至急" else "📘"
                    st.markdown(f"**{prio_icon} {content}**")
                    st.caption(f"{task.get('from_user')} ➡ {task.get('to_user')}")

                    # --- アクションエリア ---
                    if status in ["未着手", "対応中", "ルーティン"]:
                        with st.popover("処理を実行 ⚙️", use_container_width=True):
                            st.markdown("どう処理しますか？")
                            action_type = st.radio("アクション", ["✅ 完了にする", "🏃 バトンタッチ (転送)"], key=f"rad_{t_id}")
                            
                            if action_type == "✅ 完了にする":
                                if st.button("完了確定", key=f"fin_{t_id}"):
                                    update_status(t_id, "完了")
                                    st.toast("お疲れ様でした！")
                                    time.sleep(0.5)
                                    st.rerun()
                                    
                            elif action_type == "🏃 バトンタッチ (転送)":
                                next_user = st.selectbox("次は誰に？", list(USERS.keys()), key=f"usr_{t_id}")
                                next_content = st.text_input("内容は？", value=f"確認：{content}", key=f"cnt_{t_id}")
                                next_prio = st.radio("優先度", ["🔥 至急", "🌲 通常"], horizontal=True, key=f"pri_{t_id}")
                                
                                if st.button("転送 🚀", key=f"fwd_{t_id}"):
                                    forward_task(t_id, next_content, next_user, next_prio, current_user)
                                    st.session_state.is_walking = True
                                    st.session_state.walking_target = next_user
                                    st.rerun()
                        
                        # クイックボタン
                        if status == "未着手":
                             if st.button("着手する", key=f"qk_s_{t_id}"):
                                update_status(t_id, "対応中")
                                st.rerun()

                    # --- ★リカバリー機能（完了タスクの巻き戻し） ---
                    elif status == "完了":
                        d_done = task.get('completed_at', '')
                        if d_done: st.caption(f"🏁 {d_done}")
                        
                        # 間違えた時のためのボタン
                        if st.button("↩ 対応中に戻す", key=f"undo_{t_id}"):
                            update_status(t_id, "対応中") # ステータスを戻す
                            st.toast("ステータスを戻しました")
                            time.sleep(0.5)
                            st.rerun()

                    # --- 編集・削除機能 ---
                    with st.expander("📝 編集・削除"):
                        with st.form(key=f"edit_{t_id}"):
                            new_content = st.text_input("内容", value=content)
                            new_status = st.selectbox("状態", ["未着手", "対応中", "完了", "ルーティン"], index=["未着手", "対応中", "完了", "ルーティン"].index(status))
                            
                            col_upd, col_del = st.columns(2)
                            with col_upd:
                                if st.form_submit_button("更新保存"):
                                    update_task_data(t_id, status=new_status, content=new_content)
                                    st.rerun()
                            with col_del:
                                # ★削除ボタン（赤字で注意喚起）
                                if st.form_submit_button("🗑 削除する", type="primary"):
                                    delete_task(t_id)
                                    st.toast("タスクを削除しました")
                                    time.sleep(0.5)
                                    st.rerun()

    # 2. 通知センター
    elif menu == "🔔 通知センター":
        st.subheader("🔔 通知センター")
        if st.button("最新情報を取得"): 
            get_tasks_from_server()
            st.rerun()
        my_related = [t for t in all_tasks if t.get('to_user') == current_user]
        if my_related:
            for task in reversed(my_related):
                with st.container(border=True):
                    st.markdown(f"**{task.get('from_user')}** ➡ あなた: 「{task.get('content')}」")
                    st.caption(f"状態: {task.get('status')} | {task.get('date')}")
        else:
            st.info("通知はありません")

    # 3. 新規依頼
    elif menu == "📝 新規タスク依頼":
        st.subheader("📤 タスクを依頼する")
        with st.form("create"):
            content = st.text_input("タスク内容")
            col_u, col_p = st.columns(2)
            target = col_u.selectbox("依頼先", list(USERS.keys()))
            priority = col_p.radio("優先度", ["🔥 至急", "🌲 通常", "🐢 なる早"], horizontal=True, index=1)
            is_routine = st.checkbox("🟣 ルーティンタスク")
            
            if st.form_submit_button("送信 📘💨", use_container_width=True):
                if content:
                    new_id = str(uuid.uuid4())
                    status = "ルーティン" if is_routine else "未着手"
                    new_task = {"id": new_id, "content": content, "from_user": current_user, "to_user": target, "priority": priority, "status": status}
                    create_task(new_task)
                    st.session_state.is_walking = True
                    st.session_state.walking_target = target
                    st.rerun()
                else:
                    st.error("内容を入力してください")

    # 4. 分析
    elif "チーム分析" in menu:
        st.subheader("📊 チーム分析")
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
                    else: st.info("残タスクなし")
                with col2:
                    st.markdown("##### 📋 全体割合")
                    c = df['status'].value_counts().reset_index()
                    c.columns=['状態','件数']
                    st.plotly_chart(px.pie(c, values='件数', names='状態'), use_container_width=True)
                
                st.divider()
                st.markdown("##### 🔍 詳細リスト")
                selected_user = st.selectbox("担当者", ["全員"] + list(USERS.keys()))
                view_df = df[df['to_user'] == selected_user] if selected_user != "全員" else df
                if not view_df.empty:
                    display_cols = ['content', 'status', 'priority', 'from_user', 'to_user', 'date']
                    view_df = view_df[[c for c in display_cols if c in view_df.columns]]
                    st.dataframe(view_df, use_container_width=True, hide_index=True)
