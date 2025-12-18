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
# ★URL設定済み
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

st.set_page_config(page_title="Task Walker", page_icon="🍊", layout="wide")

# ==========================================
#  🎨 デザイン (CSS) - オレンジテーマ
# ==========================================
st.markdown("""
<style>
    /* 全体のフォントと背景 */
    .stApp {
        background-color: #FFFAF5; /* ごく薄いオレンジ白 */
    }

    /* サイドバーの背景 */
    [data-testid="stSidebar"] {
        background-color: #FFF3E0; /* 薄いオレンジ */
        border-right: 1px solid #FFCC80;
    }

    /* ヘッダーの装飾 */
    h1, h2, h3 {
        color: #E65100 !important; /* 濃いオレンジ */
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* ボタンのスタイル (オレンジ統一) */
    .stButton > button {
        background-color: white;
        color: #E65100;
        border: 2px solid #E65100;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #E65100;
        color: white;
        border-color: #E65100;
    }

    /* タブのスタイル */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 5px;
        border: 1px solid #FFCC80;
        color: #E65100;
    }
    .stTabs [aria-selected="true"] {
        background-color: #E65100 !important;
        color: white !important;
    }

    /* カードデザイン (st.container) の装飾 */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #FFE0B2 !important;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(230, 81, 0, 0.1); /* オレンジの影 */
    }

    /* 右上の処理中アニメーション */
    [data-testid="stStatusWidget"] > div > div > img { display: none; }
    [data-testid="stStatusWidget"] svg { display: none; }
    [data-testid="stStatusWidget"] > div > div {
        border: 3px solid #FFCC80;
        border-top-color: transparent;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

    /* 対応中のグルグル */
    .bearing-loader {
        display: inline-block; width: 20px; height: 20px;
        border: 2px solid #FF9800;
        border-radius: 50%;
        border-top: 2px solid transparent;
        animation: spin 1.5s linear infinite;
        margin-right: 5px; position: relative;
    }

    /* カラム間の隙間調整 */
    div[data-testid="column"] { gap: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# --- 通信関数 ---
def get_tasks_from_server():
    try:
        r = requests.get(GAS_URL)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                df = df.fillna("")
                clean_data = df.to_dict('records')
                st.session_state['tasks_cache'] = clean_data
                return clean_data
            else:
                st.session_state['tasks_cache'] = []
                return []
    except: pass
    return []

def get_unique_tasks():
    if 'tasks_cache' not in st.session_state:
        st.session_state['tasks_cache'] = get_tasks_from_server()
    tasks = st.session_state['tasks_cache']
    unique_map = {}
    for t in tasks:
        if 'id' in t and t['id']: unique_map[t['id']] = t
    return list(unique_map.values())

def safe_post(data):
    try: requests.post(GAS_URL, json=data)
    except: pass
    time.sleep(1.0)
    get_tasks_from_server()

# --- アクション ---
def update_task_local(task_id, new_status=None, new_content=None):
    if 'tasks_cache' in st.session_state:
        for t in st.session_state['tasks_cache']:
            if t['id'] == task_id:
                if new_status: t['status'] = new_status
                if new_content: t['content'] = new_content
                break
    data = {"action": "update", "id": task_id}
    if new_status: data["status"] = new_status
    if new_content: data["content"] = new_content
    safe_post(data)

def delete_task_local(task_id):
    if 'tasks_cache' in st.session_state:
        st.session_state['tasks_cache'] = [t for t in st.session_state['tasks_cache'] if t['id'] != task_id]
    safe_post({"action": "delete", "id": task_id})

def forward_task_local(current_id, new_content, new_target, my_name):
    # 完了にする
    update_task_local(current_id, new_status="完了")
    
    import datetime
    new_id = str(uuid.uuid4())
    now_str = datetime.datetime.now().strftime("%m/%d %H:%M")
    
    # 送信
    data = {
        "action": "forward", "id": current_id, "new_id": new_id,
        "new_content": new_content, "new_target": new_target,
        "from_user": my_name
    }
    safe_post(data)

def create_task_local(new_task):
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
    st.markdown("<h1 style='text-align: center; color:#E65100;'>🍊 Task Walker</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container(border=True):
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

# 状態管理変数の初期化
if "confirm_done_id" not in st.session_state: st.session_state.confirm_done_id = None
if "forwarding_id" not in st.session_state: st.session_state.forwarding_id = None

if not st.session_state["logged_in"]:
    login()
else:
    current_user = st.session_state["user_id"]
    lottie_book = load_lottieurl(LOTTIE_WALKING_BOOK)
    
    all_tasks = get_unique_tasks()
    
    my_active_tasks = [t for t in all_tasks if t.get('to_user') == current_user and t.get('status') != '完了']
    my_done_reports = [t for t in all_tasks if t.get('from_user') == current_user and t.get('status') == '完了' and t.get('to_user') != current_user]
    
    alert_msg = ""
    if len(my_active_tasks) > 0: alert_msg += f" 🔴{len(my_active_tasks)}"
    if len(my_done_reports) > 0: alert_msg += f" ✅{len(my_done_reports)}"

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
        st.info(f"📘 タスクが「{st.session_state.walking_target}」へバトンを繋いでいます！")
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
        with col2:
            st.markdown("""
            <div style="background-color:#FFF3E0; color:#E65100; padding:10px; border-radius:5px; text-align:center; border:1px solid #FFCC80;">
                <div class="bearing-loader"></div> <b>対応中</b>
            </div>""", unsafe_allow_html=True)
        with col3: st.success("✅ 完了")
        with col4: st.markdown("<div style='background-color:#E65100;color:white;padding:10px;border-radius:5px;text-align:center;'>🟣 ルーティン</div>", unsafe_allow_html=True)
        cols = {"未着手": col1, "対応中": col2, "完了": col3, "ルーティン": col4}

        for task in my_tasks:
            status = task.get('status', '未着手')
            if status not in cols: status = '未着手'
            t_id = task.get('id', '')
            content = task.get('content', '（タイトルなし）')
            logs = task.get('logs', '')
            
            with cols[status]:
                with st.container(border=True):
                    st.markdown(f"#### 📘 {content}")
                    st.caption(f"依頼: {task.get('from_user')}")
                    if logs:
                        last_log = logs.split('\n')[-1]
                        st.caption(f"🕒 {last_log}")
                    
                    # === アクションエリア ===
                    
                    # 1. 完了・バトン確認モード
                    if st.session_state.confirm_done_id == t_id:
                        st.info("このタスクをどうしますか？")
                        cc1, cc2 = st.columns(2)
                        with cc1:
                            if st.button("このまま完結 ✅", key=f"self_fin_{t_id}", use_container_width=True):
                                update_task_local(t_id, new_status="完了")
                                st.session_state.confirm_done_id = None
                                st.balloons()
                                st.rerun()
                        with cc2:
                            if st.button("バトンを渡す 🏃", key=f"to_next_{t_id}", use_container_width=True):
                                st.session_state.confirm_done_id = None
                                st.session_state.forwarding_id = t_id
                                st.rerun()
                        if st.button("キャンセル", key=f"cncl_{t_id}", use_container_width=True):
                             st.session_state.confirm_done_id = None
                             st.rerun()

                    # 2. バトンパス入力モード
                    elif st.session_state.forwarding_id == t_id:
                        st.markdown("##### 🏃 次の担当者へバトンパス")
                        with st.form(key=f"fwd_form_{t_id}"):
                            n_user = st.selectbox("誰に渡しますか？", list(USERS.keys()))
                            n_cont = st.text_input("タスク内容は？", value=content)
                            if st.form_submit_button("バトンを渡す 🚀"):
                                forward_task_local(t_id, n_cont, n_user, current_user)
                                st.session_state.forwarding_id = None
                                st.session_state.is_walking = True
                                st.session_state.walking_target = n_user
                                st.rerun()
                        if st.button("戻る", key=f"back_fwd_{t_id}"):
                            st.session_state.forwarding_id = None
                            st.rerun()

                    # 3. 通常モード
                    else:
                        if status == "未着手":
                            b_col1, b_col2 = st.columns(2)
                            with b_col1:
                                if st.button("着手 🛠", key=f"start_{t_id}", use_container_width=True):
                                    update_task_local(t_id, new_status="対応中")
                                    st.rerun()
                            with b_col2:
                                if st.button("即完了 ✅", key=f"quick_done_{t_id}", use_container_width=True):
                                    st.session_state.confirm_done_id = t_id
                                    st.rerun()

                        elif status == "対応中":
                            if st.button("完了 ✅", key=f"try_done2_{t_id}", use_container_width=True):
                                st.session_state.confirm_done_id = t_id
                                st.rerun()

                        elif status == "ルーティン":
                             if st.button("完了 ✅", key=f"try_done3_{t_id}", use_container_width=True):
                                update_task_local(t_id, new_status="完了")
                                st.balloons()
                                st.rerun()

                        elif status == "完了":
                             if st.button("↩ 戻す", key=f"back_{t_id}", use_container_width=True):
                                update_task_local(t_id, new_status="対応中")
                                st.rerun()
                        
                        if status != "完了":
                            with st.expander("⚙️ 詳細・編集"):
                                st.markdown("**📝 タイトル修正・削除**")
                                e_cont = st.text_input("修正", value=content, key=f"ec_{t_id}")
                                if st.button("保存", key=f"sv_{t_id}"):
                                    update_task_local(t_id, new_content=e_cont)
                                    st.rerun()
                                if st.button("🗑 削除", key=f"del_{t_id}"):
                                    delete_task_local(t_id)
                                    st.rerun()

    # 2. 新規依頼
    elif menu == "📝 新規タスク依頼":
        st.subheader("📤 新規タスク")
        with st.form("create"):
            content = st.text_input("タスクのタイトル")
            target = st.selectbox("依頼先", list(USERS.keys()))
            is_routine = st.checkbox("🟣 ルーティン")
            if st.form_submit_button("送信 📘💨", use_container_width=True):
                if content:
                    import datetime
                    now_str = datetime.datetime.now().strftime("%m/%d %H:%M")
                    new_task = {"id": str(uuid.uuid4()), "content": content, "from_user": current_user, "to_user": target, "status": "ルーティン" if is_routine else "未着手", "logs": "新規作成"}
                    create_task_local(new_task)
                    st.session_state.is_walking = True
                    st.session_state.walking_target = target
                    st.rerun()
                else: st.error("タイトルを入力してください")

    # 3. 通知
    elif menu == "🔔 通知センター":
        st.subheader("🔔 通知センター")
        if st.button("最新取得"): 
            get_tasks_from_server()
            st.rerun()
        
        tasks_for_me = [t for t in all_tasks if t.get('to_user') == current_user]
        tasks_done = [t for t in all_tasks if t.get('from_user') == current_user and t.get('status') == '完了' and t.get('to_user') != current_user]

        tab1, tab2 = st.tabs([f"📩 あなたへの依頼 ({len(tasks_for_me)})", f"✅ 完了報告 ({len(tasks_done)})"])
        
        with tab1:
            if tasks_for_me:
                for task in reversed(tasks_for_me):
                    with st.container(border=True):
                        st.markdown(f"**{task.get('from_user')}** ➡ あなた")
                        st.markdown(f"##### 「{task.get('content')}」")
                        st.caption(f"状態: {task.get('status')}")
                        if 'logs' in task: st.caption(f"履歴: {task['logs']}")
            else: st.info("依頼はありません")

        with tab2:
            if tasks_done:
                for task in reversed(tasks_done):
                    with st.container(border=True):
                        st.success(f"✅ {task.get('to_user')} さんが完了しました！")
                        st.markdown(f"##### 「{task.get('content')}」")
                        if 'logs' in task: st.caption(f"履歴: {task['logs']}")
            else: st.info("完了報告はありません")

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
                    cols = ['content', 'status', 'from_user', 'to_user']
                    if 'logs' in view_df.columns: cols.append('logs')
                    view_df = view_df[cols].rename(columns={'content': 'タイトル'})
                    st.dataframe(view_df, use_container_width=True, hide_index=True)
