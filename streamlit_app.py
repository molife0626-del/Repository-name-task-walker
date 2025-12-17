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

# --- CSS（回転アニメーション定義） ---
st.markdown("""
<style>
@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.bearing-icon {
  display: inline-block;
  font-size: 20px;
  animation: rotate 2s linear infinite; /* 2秒で1回転 */
}
.status-box-active {
  background-color: #fff3cd;
  color: #856404;
  padding: 10px;
  border-radius: 5px;
  text-align: center;
  border: 1px solid #ffeeba;
}
</style>
""", unsafe_allow_html=True)

# --- 通信・データ処理関数 ---
def get_tasks_from_server():
    """サーバーからデータを取得してキャッシュ更新"""
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

def get_unique_tasks():
    """【重要】ID重複を排除して最新のタスクだけを返す"""
    tasks = st.session_state.get('tasks_cache', [])
    if not tasks:
        tasks = get_tasks_from_server()
    
    # IDごとにデータを辞書で上書き（後ろにあるデータが優先される＝最新）
    unique_map = {}
    for t in tasks:
        if 'id' in t:
            unique_map[t['id']] = t
    
    return list(unique_map.values())

def safe_action(func, *args, **kwargs):
    """アクション実行時の共通処理"""
    with st.spinner('処理中...'):
        func(*args, **kwargs)
        time.sleep(1.5) # 待機
        get_tasks_from_server() # 最新データ取得

# --- GASへの送信関数群 ---
def _post_create(data): requests.post(GAS_URL, json=data)
def _post_update_status(task_id, new_status):
    data = {"action": "update", "id": task_id, "status": new_status}
    requests.post(GAS_URL, json=data)
def _post_update_data(task_id, status=None, content=None, priority=None):
    data = {"action": "update", "id": task_id}
    if status: data["status"] = status
    if content: data["content"] = content
    if priority: data["priority"] = priority
    requests.post(GAS_URL, json=data)
def _post_delete(task_id):
    data = {"action": "delete", "id": task_id}
    requests.post(GAS_URL, json=data)
def _post_forward(current_id, new_content, new_target, new_prio, my_name):
    new_id = str(uuid.uuid4())
    data = {
        "action": "forward", "id": current_id, "new_id": new_id,
        "new_content": new_content, "new_target": new_target,
        "new_priority": new_prio, "from_user": my_name
    }
    requests.post(GAS_URL, json=data)

# --- 爆速アクション（キャッシュ先行更新） ---
def fast_action_update_status(task_id, new_status):
    # キャッシュを即座に書き換え
    if 'tasks_cache' in st.session_state:
        for t in st.session_state['tasks_cache']:
            if t['id'] == task_id:
                t['status'] = new_status
                break
    # 裏で通信
    safe_action(_post_update_status, task_id, new_status)

def fast_action_create(new_task):
    if 'tasks_cache' in st.session_state:
        st.session_state['tasks_cache'].append(new_task)
    safe_action(_post_create, new_task)

def fast_action_forward(t_id, content, target, prio, my_name):
    # キャッシュ上で「完了」にする
    if 'tasks_cache' in st.session_state:
        for t in st.session_state['tasks_cache']:
            if t['id'] == t_id:
                t['status'] = '完了'
                break
    safe_action(_post_forward, t_id, content, target, prio, my_name)

def fast_action_delete(t_id):
    if 'tasks_cache' in st.session_state:
        st.session_state['tasks_cache'] = [t for t in st.session_state['tasks_cache'] if t['id'] != t_id]
    safe_action(_post_delete, t_id)

def fast_action_update_data(t_id, status, content):
    if 'tasks_cache' in st.session_state:
        for t in st.session_state['tasks_cache']:
            if t['id'] == t_id:
                t['status'] = status
                t['content'] = content
                break
    safe_action(_post_update_data, t_id, status, content)


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
    
    # ★重複排除したデータを取得
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

    # アニメーション
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
        if col_b.button("🔄 強制更新"): 
            get_tasks_from_server()
            st.rerun()
        
        my_tasks = [t for t in all_tasks if t.get('to_user') == current_user or t.get('from_user') == current_user]
        
        col1, col2, col3, col4 = st.columns(4)
        
        # --- カラムヘッダー（回転アニメーション適用） ---
        with col1: st.error("🛑 未着手")
        with col2:
            # HTMLで回転アイコンを表示
            st.markdown("""
            <div class="status-box-active">
                <span class="bearing-icon">⚙️</span> <b>対応中</b>
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
                    st.caption(f"依頼: {task.get('from_user')} ➡ 担当: {task.get('to_user')}")

                    # --- ワンクリック移動 ---
                    if status == "未着手":
                        if st.button("着手する ➡", key=f"go_{t_id}", use_container_width=True):
                            fast_action_update_status(t_id, "対応中")
                            st.rerun()
                            
                    elif status == "対応中":
                        if st.button("完了する ✅", key=f"done_{t_id}", use_container_width=True):
                            fast_action_update_status(t_id, "完了")
                            st.balloons()
                            st.rerun()
                            
                    elif status == "ルーティン":
                         if st.button("完了 ✅", key=f"r_done_{t_id}", use_container_width=True):
                            fast_action_update_status(t_id, "完了")
                            st.balloons()
                            st.rerun()
                            
                    elif status == "完了":
                         if st.button("↩ 戻す", key=f"back_{t_id}", use_container_width=True):
                            fast_action_update_status(t_id, "対応中")
                            st.rerun()

                    # 詳細メニュー
                    with st.expander("⚙️ 転送・編集"):
                        if status != "完了":
                            st.markdown("**🏃 バトンタッチ**")
                            n_user = st.selectbox("次へ", list(USERS.keys()), key=f"u_{t_id}")
                            n_cont = st.text_input("タイトル", value=f"確認：{content}", key=f"c_{t_id}")
                            if st.button("転送実行 🚀", key=f"fw_{t_id}"):
                                fast_action_forward(t_id, n_cont, n_user, prio, current_user)
                                st.session_state.is_walking = True
                                st.session_state.walking_target = n_user
                                st.rerun()
                            st.divider()
                        
                        st.markdown("**📝 編集**")
                        e_cont = st.text_input("タイトル修正", value=content, key=f"ec_{t_id}")
                        e_stat = st.selectbox("状態", ["未着手", "対応中", "完了", "ルーティン"], index=["未着手", "対応中", "完了", "ルーティン"].index(status), key=f"es_{t_id}")
                        
                        if st.button("保存", key=f"sv_{t_id}"):
                            fast_action_update_data(t_id, e_stat, e_cont)
                            st.rerun()
                        
                        if st.button("🗑 削除", key=f"del_{t_id}"):
                            fast_action_delete(t_id)
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
                    fast_action_create(new_task)
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
        else:
            st.info("通知なし")

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
                    view_df = view_df[['content', 'status', 'priority', 'from_user', 'to_user', 'date']].rename(columns={'content': 'タイトル'})
                    st.dataframe(view_df, use_container_width=True, hide_index=True)
