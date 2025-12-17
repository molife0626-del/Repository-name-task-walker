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
GAS_URL = "https://script.google.com/macros/s/AKfycbzqYGtlTBRVPiV6Ik4MdZM4wSYSQd5lDvHzx0zfwjUk1Cpb9woC3tKppCOKQ364ppDp/exec" # ★ご自身のURL

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

# --- 通信関数 ---
def get_tasks():
    try:
        r = requests.get(GAS_URL)
        if r.status_code == 200:
            data = r.json()
            # データがリスト形式か確認
            if isinstance(data, list):
                return data
    except:
        pass
    return []

def create_task(data):
    data["action"] = "create"
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

# --- 認証 ---
def login():
    st.markdown("<h1 style='text-align: center;'>🔐 Task Walker ログイン</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login"):
            uid = st.text_input("ユーザーID")
            pwd = st.text_input("パスワード", type="password")
            if st.form_submit_button("ログイン", use_container_width=True):
                if uid in USERS and USERS[uid] == pwd:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = uid
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
    
    # データを取得
    all_tasks = get_tasks()
    
    # ★修正ポイント： .get() を使って安全に取得する
    my_active_tasks = [t for t in all_tasks if t.get('to_user') == current_user and t.get('status') != '完了']
    
    alert_msg = ""
    if len(my_active_tasks) > 0:
        alert_msg = f" 🔴 {len(my_active_tasks)}"

    # --- サイドバー ---
    st.sidebar.title(f"👤 {current_user}")
    
    menu = st.sidebar.radio(
        "メニュー", 
        [f"📊 マイタスク{alert_msg}", "📝 新規タスク依頼", "🔔 通知センター", "📈 チーム分析"]
    )
    if current_user in ADMIN_USERS:
        st.sidebar.markdown("---")
        if st.sidebar.button("🦅 管理者画面へ"):
            st.session_state["admin_mode"] = True
        else:
            st.session_state["admin_mode"] = False
            
    st.sidebar.divider()
    if st.sidebar.button("ログアウト"):
        st.session_state["logged_in"] = False
        st.rerun()

    # アニメーション
    if 'is_walking' not in st.session_state: st.session_state.is_walking = False
    if st.session_state.is_walking:
        st.info(f"📘 タスクが「{st.session_state.walking_target}」へ向かっています！")
        if lottie_book: st_lottie(lottie_book, speed=1.5, loop=True, height=200)
        time.sleep(2)
        st.session_state.is_walking = False
        st.rerun()

    # 1. マイタスクボード
    if "マイタスク" in menu:
        col_h, col_b = st.columns([4,1])
        col_h.subheader("マイタスクボード")
        if col_b.button("🔄 更新"): st.rerun()
        
        if len(my_active_tasks) > 0:
            st.error(f"⚠️ あなた宛てのタスクが {len(my_active_tasks)} 件残っています！")

        # 自分の関わるタスク全体（安全に取得）
        my_tasks = [t for t in all_tasks if t.get('to_user') == current_user or t.get('from_user') == current_user]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.error("🛑 未着手")
        with col2: st.warning("🏃 対応中")
        with col3: st.success("✅ 完了")
        with col4: st.markdown("<div style='background-color:#6f42c1;color:white;padding:10px;border-radius:5px;text-align:center;'>🟣 ルーティン</div>", unsafe_allow_html=True)

        cols = {"未着手": col1, "対応中": col2, "完了": col3, "ルーティン": col4}

        for task in my_tasks:
            # 安全に値を取得
            status = task.get('status', '未着手')
            if status not in cols: status = '未着手'
            t_id = task.get('id', str(uuid.uuid4()))
            content = task.get('content', '内容なし')
            priority = task.get('priority', '🌲 通常')
            from_u = task.get('from_user', '?')
            to_u = task.get('to_user', '?')
            
            with cols[status]:
                with st.container(border=True):
                    prio_icon = "🔥" if priority == "🔥 至急" else "📘"
                    st.markdown(f"**{prio_icon} {content}**")
                    
                    d_add = task.get('date', '')
                    d_done = task.get('completed_at', '')
                    
                    st.caption(f"{from_u} ➡ {to_u}")
                    if d_add: st.caption(f"📅 追加: {d_add}")
                    if status == "完了" and d_done: st.markdown(f"<small style='color:green'>🏁 完了: {d_done}</small>", unsafe_allow_html=True)

                    if status == "未着手":
                        if st.button("着手 ➡", key=f"s_{t_id}"):
                            update_status(t_id, "対応中")
                            st.rerun()
                    elif status == "対応中":
                        if st.button("完了 ✅", key=f"d_{t_id}"):
                            update_status(t_id, "完了")
                            st.rerun()
                    elif status == "ルーティン":
                         if st.button("完了 ✅", key=f"rd_{t_id}"):
                            update_status(t_id, "完了")
                            st.rerun()

    # 2. 通知センター
    elif menu == "🔔 通知センター":
        st.subheader("🔔 通知センター")
        if st.button("最新情報を取得"): st.rerun()
        
        # 安全に取得
        my_related = [t for t in all_tasks if t.get('to_user') == current_user]
        
        if my_related:
            for task in reversed(my_related):
                with st.container(border=True):
                    col_icon, col_text = st.columns([1, 8])
                    stat = task.get('status', '')
                    prio = task.get('priority', '')
                    
                    with col_icon:
                        if stat == '完了': st.markdown("✅")
                        elif prio == '🔥 至急': st.markdown("🔥")
                        else: st.markdown("📩")
                    
                    with col_text:
                        st.markdown(f"**{task.get('from_user')}** からの依頼: 「{task.get('content')}」")
                        st.caption(f"状態: {stat} | 追加日: {task.get('date','--')} | 完了日: {task.get('completed_at','--')}")
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
                    if create_task(new_task):
                        st.session_state.is_walking = True
                        st.session_state.walking_target = target
                        st.rerun()
                    else:
                        st.error("送信エラー")

    # 4. 分析
    elif "チーム分析" in menu:
        st.subheader("📊 チーム分析")
        if all_tasks:
            df = pd.DataFrame(all_tasks)
            # 安全にフィルタリング
            if 'status' in df.columns and 'to_user' in df.columns:
                active_df = df[df['status'] != '完了']
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("##### 🏃 残タスク")
                    if not active_df.empty:
                        c = active_df['to_user'].value_counts().reset_index()
                        c.columns=['担当','件数']
                        st.plotly_chart(px.bar(c, x='担当', y='件数', color='担当'), use_container_width=True)
                    else: st.write("タスクなし")
                with col2:
                    st.markdown("##### 📋 全体割合")
                    c = df['status'].value_counts().reset_index()
                    c.columns=['状態','件数']
                    st.plotly_chart(px.pie(c, values='件数', names='状態'), use_container_width=True)
            else:
                st.write("データが不足しています（列が見つかりません）")
