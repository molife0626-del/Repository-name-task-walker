import streamlit as st
import time
import requests
import uuid
import pandas as pd
from streamlit_lottie import st_lottie
import plotly.express as px
import base64
import random

# ==========================================
#  ⚙️ 設定エリア
# ==========================================
# ★URL設定済み
GAS_URL = "https://script.google.com/macros/s/AKfycbyH0Mw-GnshnEnClFzMUYNrPxtAHoXrSpiXFBnlYU61EA9vWz32LHBBl6B9MmJJyKV5/exec"

# ユーザー管理
USERS = {
    "自分": "1111",
    "上司": "2222",
    "経理": "3333",
    "メンバーA": "aaaa"
}
ADMIN_USERS = ["上司", "経理"]

st.set_page_config(page_title="MBS Task Walker", page_icon="Ⓜ️", layout="wide")

# ==========================================
#  🎨 デザイン (CSS)
# ==========================================
st.markdown("""
<style>
    /* 1. 全体の余白調整 */
    .block-container {
        padding-top: 5rem !important;
        padding-bottom: 3rem !important;
    }
    
    /* 2. 背景色 */
    .stApp { background-color: #FFFAF5; }

    /* 3. サイドバー */
    [data-testid="stSidebar"] { background-color: #FFF3E0; border-right: 1px solid #FFCC80; }

    /* 4. テキスト・見出し */
    h1, h2, h3 { color: #E65100 !important; font-family: 'Helvetica Neue', sans-serif; }
    
    /* 5. ボタン (MBSオレンジ) */
    .stButton > button {
        background-color: white; color: #E65100; border: 2px solid #E65100;
        border-radius: 8px; font-weight: bold; transition: all 0.3s;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #E65100; color: white; border-color: #E65100;
    }

    /* 6. カードデザイン */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #FFE0B2 !important; background-color: white;
        border-radius: 10px; box-shadow: 0 2px 4px rgba(230, 81, 0, 0.1);
    }

    /* 7. スマホ対応 (レスポンシブ) */
    @media (max-width: 768px) {
        [data-testid="column"] {
            width: 100% !important; flex: 1 1 auto !important; min-width: 100% !important;
        }
        h1 { font-size: 1.8em !important; }
    }

    /* 8. アニメーション定義 */
    @keyframes runIn {
        0% { left: -20%; transform: rotate(0deg); }
        20% { transform: rotate(-5deg); }
        40% { transform: rotate(5deg); }
        100% { left: 45%; transform: rotate(0deg); }
    }
    @keyframes receive {
        0% { opacity: 0; transform: scale(0.8); }
        100% { opacity: 1; transform: scale(1); }
    }
    @keyframes textFade {
        0% { opacity: 0; top: 60%; }
        100% { opacity: 1; top: 55%; }
    }
    
    .anim-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(255, 250, 245, 0.95); z-index: 99999;
        display: flex; align-items: center; justify-content: center;
        overflow: hidden; pointer-events: none;
    }
    
    .runner-book {
        position: absolute; font-size: 6rem; top: 40%;
        animation: runIn 1.2s ease-out forwards;
    }
    .receiver-book {
        position: absolute; font-size: 6rem; top: 40%; right: 40%;
        opacity: 0; animation: receive 0.5s 1.2s forwards;
    }
    .pass-message {
        position: absolute; width: 100%; text-align: center;
        font-size: 2rem; color: #E65100; font-weight: bold;
        font-family: sans-serif; opacity: 0; animation: textFade 0.5s 1.5s forwards;
    }
    
    /* 9. 右上の処理中アイコンを丸いローダーに戻す */
    [data-testid="stStatusWidget"] > div > div > img { display: none; }
    [data-testid="stStatusWidget"] svg { display: none; }
    [data-testid="stStatusWidget"] > div > div {
        border: 3px solid #FFCC80; border-top-color: transparent;
        border-radius: 50%; animation: spin 1s linear infinite;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    
    .bearing-loader {
        display: inline-block; width: 20px; height: 20px;
        border: 2px solid #FF9800; border-radius: 50%;
        border-top: 2px solid transparent;
        animation: spin 1.5s linear infinite; margin-right: 5px; position: relative;
    }

</style>
""", unsafe_allow_html=True)

# --- バトンパスアニメーション ---
def show_baton_pass_animation():
    anim_html = """
    <div class="anim-overlay">
        <div class="runner-book">📘💨</div>
        <div class="receiver-book">📙✨</div>
        <div class="pass-message">Nice Pass! バトンを繋ぎました</div>
    </div>
    """
    placeholder = st.empty()
    placeholder.markdown(anim_html, unsafe_allow_html=True)
    time.sleep(3.0)
    placeholder.empty()

# --- 動画表示関数 ---
def render_video_html(video_path, width="100%"):
    try:
        with open(video_path, "rb") as f:
            video_content = f.read()
        video_b64 = base64.b64encode(video_content).decode()
        video_tag = f"""
            <video width="{width}" autoplay loop muted playsinline style="border-radius: 15px; box-shadow: 0 8px 16px rgba(230, 81, 0, 0.2); max-width: 100%;">
                <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
            </video>
        """
        st.markdown(video_tag, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"⚠️ 動画ファイル '{video_path}' が見つかりません。")

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
    update_task_local(current_id, new_status="完了")
    import datetime
    new_id = str(uuid.uuid4())
    now_str = datetime.datetime.now().strftime("%m/%d %H:%M")
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

# --- 認証 ---
def login():
    VIDEO_FILENAME = "TaskWalkerアプリの動画生成.mp4"

    CATCHPHRASES = [
        {"main": "停滞を、前進へ。<br>タスクが歩き出す。", "sub": "Task Walker gives footsteps to your workflow."},
        {"main": "そのバトンには、<br>熱がある。", "sub": "Pass the passion, not just the task."},
        {"main": "いい仕事は、<br>「いいパス」から。", "sub": "Great work starts with a great pass."},
        {"main": "その一歩が、<br>チームのリズムになる。", "sub": "Your step creates the team's rhythm."},
        {"main": "「任せた」と<br>「任された」の繰り返し。", "sub": "Trust given, trust received. The cycle of teamwork."},
        {"main": "ページをめくろう。<br>次は仲間の番だ。", "sub": "Turn the page. It's their turn now."}
    ]
    phrase = random.choice(CATCHPHRASES)

    col_left, col_right = st.columns([1.5, 1], gap="medium")

    with col_left:
        st.markdown("<br>", unsafe_allow_html=True)
        render_video_html(VIDEO_FILENAME)
        st.markdown(f"""
        <div style="margin-top: 20px;">
            <h1 style="color:#E65100; font-size: 2.5em; margin-bottom: 0; line-height: 1.2;">{phrase['main']}</h1>
            <p style="color:#FB8C00; font-family: 'Helvetica Neue', sans-serif; font-weight: 500; font-size: 1.0em; margin-top: 10px; letter-spacing: 0.5px;">{phrase['sub']}</p>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### 🔐 MBS メンバーログイン")
            with st.form("login"):
                uid = st.text_input("ユーザーID")
                pwd = st.text_input("パスワード", type="password")
                submit = st.form_submit_button("バトンを受け取る 👟", use_container_width=True)
                if submit:
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
if "confirm_done_id" not in st.session_state: st.session_state.confirm_done_id = None
if "forwarding_id" not in st.session_state: st.session_state.forwarding_id = None
if "show_anim" not in st.session_state: st.session_state.show_anim = False
if "new_task_content" not in st.session_state: st.session_state.new_task_content = ""

if not st.session_state["logged_in"]:
    login()
else:
    if st.session_state.show_anim:
        show_baton_pass_animation()
        st.session_state.show_anim = False
        st.rerun()

    current_user = st.session_state["user_id"]
    is_admin = current_user in ADMIN_USERS
    
    all_tasks = get_unique_tasks()
    
    my_active_tasks = [t for t in all_tasks if t.get('to_user') == current_user and t.get('status') != '完了']
    my_done_reports = [t for t in all_tasks if t.get('from_user') == current_user and t.get('status') == '完了' and t.get('to_user') != current_user]
    
    alert_msg = ""
    if len(my_active_tasks) > 0: alert_msg += f" 🔴{len(my_active_tasks)}"
    if len(my_done_reports) > 0: alert_msg += f" ✅{len(my_done_reports)}"

    user_label = f"Ⓜ️ {current_user}"
    if is_admin: user_label += " 🛡️"
    
    st.sidebar.title(user_label)
    menu = st.sidebar.radio("メニュー", [f"📊 マイタスク{alert_msg}", "📝 新規タスク依頼", "🔔 通知センター", "📈 チーム分析"])
    
    st.sidebar.divider()
    if st.sidebar.button("ログアウト"):
        st.session_state["logged_in"] = False
        st.rerun()

    # 1. マイタスクボード
    if "マイタスク" in menu:
        # --- ヘッダーエリア（タイトル・同期・履歴スイッチ） ---
        col_h, col_b, col_t = st.columns([3, 1, 1])
        col_h.subheader("📊 マイタスクボード")
        if col_b.button("🔄 同期", use_container_width=True): 
            get_tasks_from_server()
            st.rerun()
        
        # 履歴表示用トグルスイッチ
        show_history = col_t.toggle("🗄️ 完了履歴", value=False)

        # --- レイアウト切り替えロジック ---
        if show_history:
             # ONの場合: 3(メイン) : 1(履歴)
            main_area, right_sidebar = st.columns([3, 1], gap="large")
        else:
             # OFFの場合: メインのみ
            main_area = st.container()
            right_sidebar = None

        # === メインエリア ===
        with main_area:
            my_tasks = [t for t in all_tasks if t.get('to_user') == current_user]
            
            # メイン3カラム
            col1, col2, col3 = st.columns(3)
            with col1: st.error("🛑 未着手")
            with col2:
                st.markdown("""
                <div style="background-color:#FFF3E0; color:#E65100; padding:10px; border-radius:5px; text-align:center; border:1px solid #FFCC80;">
                    <div class="bearing-loader"></div> <b>対応中</b>
                </div>""", unsafe_allow_html=True)
            with col3: st.markdown("<div style='background-color:#E65100;color:white;padding:10px;border-radius:5px;text-align:center;'>🟣 ルーティン</div>", unsafe_allow_html=True)
            
            cols = {"未着手": col1, "対応中": col2, "ルーティン": col3}
            done_tasks = []

            for task in my_tasks:
                status = task.get('status', '未着手')
                if status == "完了":
                    done_tasks.append(task)
                    continue
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
                        
                        if st.session_state.confirm_done_id == t_id:
                            st.info("どうしますか？")
                            cc1, cc2 = st.columns(2)
                            with cc1:
                                if st.button("完結 ✅", key=f"fin_{t_id}", use_container_width=True):
                                    update_task_local(t_id, new_status="完了")
                                    st.session_state.confirm_done_id = None
                                    st.balloons()
                                    st.rerun()
                            with cc2:
                                if st.button("渡す 🏃", key=f"next_{t_id}", use_container_width=True):
                                    st.session_state.confirm_done_id = None
                                    st.session_state.forwarding_id = t_id
                                    st.rerun()
                            if st.button("キャンセル", key=f"cncl_{t_id}", use_container_width=True):
                                st.session_state.confirm_done_id = None
                                st.rerun()
                        elif st.session_state.forwarding_id == t_id:
                            st.markdown("##### 🏃 バトンパス")
                            with st.form(key=f"fwd_form_{t_id}"):
                                n_user = st.selectbox("誰に？", list(USERS.keys()))
                                n_cont = st.text_input("内容は？", value=content)
                                if st.form_submit_button("バトンを渡す 🚀"):
                                    forward_task_local(t_id, n_cont, n_user, current_user)
                                    st.session_state.forwarding_id = None
                                    st.session_state.show_anim = True
                                    st.rerun()
                            if st.button("戻る", key=f"back_fwd_{t_id}"):
                                st.session_state.forwarding_id = None
                                st.rerun()
                        else:
                            if status == "未着手":
                                b1, b2 = st.columns(2)
                                with b1:
                                    if st.button("着手 🛠", key=f"st_{t_id}", use_container_width=True):
                                        update_task_local(t_id, new_status="対応中")
                                        st.rerun()
                                with b2:
                                    if st.button("即完 ✅", key=f"q_{t_id}", use_container_width=True):
                                        st.session_state.confirm_done_id = t_id
                                        st.rerun()
                            elif status == "対応中":
                                if st.button("完了 ✅", key=f"dn_{t_id}", use_container_width=True):
                                    st.session_state.confirm_done_id = t_id
                                    st.rerun()
                            elif status == "ルーティン":
                                if st.button("完了 ✅", key=f"rdn_{t_id}", use_container_width=True):
                                    update_task_local(t_id, new_status="完了")
                                    st.balloons()
                                    st.rerun()
                            with st.expander("⚙️ 編集"):
                                e_cont = st.text_input("修正", value=content, key=f"ec_{t_id}")
                                if st.button("保存", key=f"sv_{t_id}"):
                                    update_task_local(t_id, new_content=e_cont)
                                    st.rerun()
                                if st.button("🗑 削除", key=f"del_{t_id}"):
                                    delete_task_local(t_id)
                                    st.rerun()

        # === 履歴エリア (スイッチONの時だけ表示) ===
        if show_history and right_sidebar:
            with right_sidebar:
                st.markdown("#### ✅ 完了済み履歴")
                with st.container(border=True):
                    if done_tasks:
                        for t in done_tasks:
                            st.markdown(f"**{t.get('content')}**")
                            st.caption(f"{t.get('date', '')}")
                            if st.button("戻す", key=f"re_{t.get('id')}", use_container_width=True):
                                update_task_local(t.get('id'), new_status="対応中")
                                st.rerun()
                            st.divider()
                    else:
                        st.caption("完了タスクなし")

    # 2. 新規依頼
    elif menu == "📝 新規タスク依頼":
        st.subheader("📤 新規タスク")
        with st.container(border=True):
            content = st.text_input("タスクのタイトル", key="new_task_input")
            target = st.selectbox("依頼先", list(USERS.keys()))
            is_routine = st.checkbox("🟣 ルーティン")
            
            if st.button("送信 📘💨", use_container_width=True):
                if content:
                    import datetime
                    new_task = {"id": str(uuid.uuid4()), "content": content, "from_user": current_user, "to_user": target, "status": "ルーティン" if is_routine else "未着手", "logs": "新規作成"}
                    create_task_local(new_task)
                    st.session_state.show_anim = True
                    st.rerun()
                else:
                    st.error("タイトルを入力してください")

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
            else: st.info("依頼はありません")
        with tab2:
            if tasks_done:
                for task in reversed(tasks_done):
                    with st.container(border=True):
                        st.success(f"✅ {task.get('to_user')} さんが完了しました！")
                        st.markdown(f"##### 「{task.get('content')}」")
            else: st.info("完了報告はありません")

    # 4. 分析
    elif "チーム分析" in menu:
        st.subheader("📊 チーム分析・レポート")
        if st.button("データ更新"): 
            get_tasks_from_server()
            st.rerun()

        if all_tasks:
            df = pd.DataFrame(all_tasks)
            view_df = pd.DataFrame()
            
            if is_admin:
                st.markdown(f"#### 🛡️ 管理者メニュー: {current_user}")
                view_mode = st.radio("表示対象", ["全員のデータ", "メンバー個別"], horizontal=True)
                if view_mode == "全員のデータ":
                    view_df = df
                else:
                    target_member = st.selectbox("メンバーを選択", list(USERS.keys()))
                    view_df = df[(df['to_user'] == target_member) | (df['from_user'] == target_member)]
            else:
                view_df = df[(df['to_user'] == current_user) | (df['from_user'] == current_user)]

            if not view_df.empty and 'status' in view_df.columns:
                active_df = view_df[view_df['status'] != '完了']
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("##### 🏃 残タスク状況")
                    if not active_df.empty:
                        c = active_df['to_user'].value_counts().reset_index()
                        c.columns=['担当','件数']
                        st.plotly_chart(px.bar(c, x='担当', y='件数', color='担当'), use_container_width=True)
                    else: st.caption("残タスクはありません")
                with col2:
                    st.markdown("##### 📋 タスク状態の内訳")
                    c = view_df['status'].value_counts().reset_index()
                    c.columns=['状態','件数']
                    st.plotly_chart(px.pie(c, values='件数', names='状態'), use_container_width=True)
                
                st.divider()
                st.markdown("##### 🔍 タスク詳細リスト")
                cols_to_show = ['content', 'status', 'from_user', 'to_user']
                st.dataframe(view_df[cols_to_show].rename(columns={'content':'タイトル', 'status':'状態', 'from_user':'依頼者', 'to_user':'担当'}), use_container_width=True, hide_index=True)
            else: st.info("表示できるデータがありません")
