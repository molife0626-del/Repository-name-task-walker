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

# --- CSS: ベアリング統一 & 処理中アイコン ---
st.markdown("""
<style>
/* 1. 標準のRunningアイコン(人)などを消す */
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
/* 中の玉（点線）を追加 */
[data-testid="stStatusWidget"] > div > div::after {
    content: "";
    position: absolute;
    top: 3px; left: 3px; right: 3px; bottom: 3px;
    border: 2px dotted #888; /* ボール */
    border-radius: 50%;
}

/* 3. 対応中アイコン（カラム用） */
.bearing-loader {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid #666;
  border-radius: 50%;
  border-top: 2px solid transparent;
  animation: spin 1.5s linear infinite;
  margin-right: 5px;
  position: relative;
}
.bearing-loader::after {
    content: "";
    position: absolute;
    top: 2px; left: 2px; right: 2px; bottom: 2px;
    border: 2px dotted #888;
    border-radius: 50%;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* カードデザイン */
.task-card {
    padding: 10px;
    border-radius: 10px;
    background-color: #ffffff;
    border: 1px solid #ddd;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# --- 通信・データ処理関数 ---
def get_tasks_from_server():
    try:
        r = requests.get(GAS_URL)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                st.session_state['tasks_cache'] = data
                return data
    except: pass
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
    try: requests.post(GAS_URL, json=data)
    except: pass

# --- アクション（即時反映） ---
def update_task_local(task_id, new_status=None, new_content=None, new_prio=None):
    if 'tasks_cache' in st.session_state:
        for t in st.session_state['tasks_cache']:
            if t['id'] == task_id:
                if new_status: t['status'] = new_status
                if new_content: t['content'] = new_content
                if new_prio: t['priority'] = new_prio
                break
    data = {"action": "update", "id": task_id}
    if new_status: data["status"] = new_status
    if new_content: data["content"] = new_content
    if new_prio: data["priority"] = new_prio
    safe_post(data)

def delete_task_local(task_id):
    if 'tasks_cache' in st.session_state:
        st.session_state['tasks_cache'] = [t for t in st.session_state['tasks_cache'] if t['id'] != task_id]
    safe_post({"action": "delete", "id": task_id})

def forward_task_local(current_id, new_content, new_target, new_prio, my_name):
    # 1. 自分のタスクを完了に
    update_task_local(current_id, new_status="完了")
    
    # 2. 相手用の新タスク作成
    import datetime
    new_id = str(uuid.uuid4())
    now_str = datetime.datetime.now().strftime("%m/%d %H:%M")
    
    new_task = {
        "id": new_id, "content": new_content, "from_user": my_name, 
        "to_user": new_target, "priority": new_prio, "status": "未着手",
        "date": now_str, "completed_at": ""
    }
    # 相手のタスクなので自分のキャッシュには追加しない（リストに残ってしまうため）
    # ただし「チーム分析」など全体データには必要なため、サーバー同期を待つ運用にするか、
    # ここではあえて追加せず、次回更新時に取得させる
    
    # 3. 裏で送信
    data = {
        "action": "forward", "id": current_id, "new_id": new_id,
        "new_content": new_content, "new_target": new_target,
        "new_priority": new_prio, "from_user": my_name
    }
    safe_post(data)

def create_task_local(new_task):
    # 自分宛てならキャッシュに追加して即表示
    if new_task['to_user'] == st.session_state.get('user_id'):
        if 'tasks_cache' in st.session_state:
            st.session_state['tasks_cache'].append(new_task)
    
    new_task["action"] = "create"
    safe_post(new_task)

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
        
        # ★修正：自分宛て(to_user)のタスクのみ表示（依頼したタスクは表示しない）
        my_tasks = [t for t in all_tasks if t.get('to_user') == current_user]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.error("🛑 未着手")
        with col2:
            st.markdown("""
            <div style="background-color:#fff3cd; color:#856404; padding:10px; border-radius:5px; text-align:center; border:1px solid #ffeeba;">
                <div class="bearing-loader"></div> <b>対応中</b>
            </div>
            """, unsafe_allow_html=True)
        with col3: st.success("✅ 完了")
        with col4: st.markdown("<div style='background-color:#6f42c1;color:white;padding:10px;border-radius:5px;text-align:center;'>🟣 ルーティン</div>", unsafe_allow_html=True)
        
        cols = {"未着手": col1, "対応中": col2, "完了": col3, "ルーティン": col4}

        for task in my_tasks:
            status = task.get('status', '未着手')
            if status not in cols: status = '未着手'
            t_id = task.get('id', '')
            content = task.get('content', '（タイトルなし）')
            prio = task.get('priority', '🌲 通常')
            
            with cols[status]:
                with st.container(border=True):
                    prio_icon = "🔥" if prio == "🔥 至急" else "📘"
                    st.markdown(f"#### {prio_icon} {content}")
                    # 依頼元を表示
                    st.caption(f"依頼: {task.get('from_user')}")

                    if status == "完了" and task.get('completed_at'):
                        st.caption(f"🏁 {task.get('completed_at')}")

                    # --- ワンクリック移動 ---
                    if status == "未着手":
                        if st.button("対応開始 ➡", key=f"go_{t_id}", use_container_width=True):
                            update_task_local(t_id, new_status="対応中")
                            st.rerun()
                            
                    elif status == "対応中":
                        if st.button("完了する ✅", key=f"done_{t_id}", use_container_width=True):
                            update_task_local(t_id, new_status="完了")
                            st.balloons()
                            st.rerun()
                            
                    elif status == "ルーティン":
                         if st.button("完了 ✅", key=f"r_done_{t_id}", use_container_width=True):
                            update_task_local(t_id, new_status="完了")
                            st.balloons()
                            st.rerun()
                            
                    elif status == "完了":
                         if st.button("↩ 戻す", key=f"back_{t_id}", use_container_width=True):
                            update_task_local(t_id, new_status="対応中")
                            st.rerun()

                    with st.expander("⚙️ 転送・編集"):
                        if status != "完了":
                            st.markdown("**🏃 バトンタッチ**")
                            n_user = st.selectbox("次へ", list(USERS.keys()), key=f"u_{t_id}")
                            n_cont = st.text_input("タイトル", value=f"確認：{content}", key=f"c_{t_id}")
                            if st.button("転送実行 🚀", key=f"fw_{t_id}"):
                                forward_task_local(t_id, n_cont, n_user, prio, current_user)
                                st.session_state.is_walking = True
                                st.session_state.walking_target = n_user
                                st.rerun()
                            st.divider()
                        
                        st.markdown("**📝 編集**")
                        e_cont = st.text_input("タイトル修正", value=content, key=f"ec_{t_id}")
                        e_stat = st.selectbox("状態", ["未着手", "対応中", "完了", "ルーティン"], index=["未着手", "対応中", "完了", "ルーティン"].index(status), key=f"es_{t_id}")
                        
                        if st.button("保存", key=f"sv_{t_id}"):
                            update_task_local(t_id, new_status=e_stat, new_content=e_cont)
                            st.rerun()
                        
                        if st.button("🗑 削除", key=f"del_{t_id}"):
                            delete_task_local(t_id)
                            st.rerun()

    # 2. 新規依頼
    elif menu == "📝 新規タスク依頼":
        st.subheader("📤 新規タスク")
        with st.form("create"):
            content = st.text_input("タスクのタイトル (件名)")
            col_u, col_p = st.columns(2)
            target = col_u.selectbox("依頼先", list(USERS.keys()))
            priority = col_p.radio("優先度", ["🔥 至急", "🌲 通常", "🐢 なる早"], horizontal=True, index=1)
            is_routine = st.checkbox("🟣 ルーティン")
            if st.form_submit_button("送信 📘💨", use_container_width=True):
                if content:
                    new_id = str(uuid.uuid4())
                    status = "ルーティン" if is_routine else "未着手"
                    import datetime
                    now_str = datetime.datetime.now().strftime("%m/%d %H:%M")
                    new_task = {"id": new_id, "content": content, "from_user": current_user, "to_user": target, "priority": priority, "status": status, "date": now_str}
                    
                    create_task_local(new_task)
                    
                    st.session_state.is_walking = True
                    st.session_state.walking_target = target
                    st.rerun()

    # 3. 通知センター
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
                    view_df = view_df
