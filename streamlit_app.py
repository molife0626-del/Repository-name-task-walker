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

# 1. GAS URL (★ご自身のURL)
GAS_URL = "https://script.google.com/macros/s/AKfycbzqYGtlTBRVPiV6Ik4MdZM4wSYSQd5lDvHzx0zfwjUk1Cpb9woC3tKppCOKQ364ppDp/exec"

# 2. ユーザー管理 (ID: パスワード)
USERS = {
    "自分": "1111",
    "上司": "2222",
    "経理": "3333",
    "メンバーA": "aaaa",
    "メンバーB": "bbbb"
}

# 3. ★管理者権限を持つユーザー (全体を見れる人)
# ここに書かれたIDの人だけ、管理者メニューが表示されます
ADMIN_USERS = ["自分", "上司"]

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

# --- 認証機能 (ID入力式に変更) ---
def login():
    st.markdown("<h1 style='text-align: center;'>🔐 Task Walker ログイン</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_form"):
            st.info("IDとパスワードを入力してください")
            
            # ★ここを変更: selectbox -> text_input
            user_id = st.text_input("ユーザーID")
            password = st.text_input("パスワード", type="password")
            
            submitted = st.form_submit_button("ログイン", use_container_width=True)
            
            if submitted:
                # IDが存在し、かつパスワードが一致するか
                if user_id in USERS and USERS[user_id] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user_id
                    st.rerun()
                else:
                    st.error("IDまたはパスワードが違います")

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
    
    # ★管理者かどうか判定
    is_admin = current_user in ADMIN_USERS
    
    # --- サイドバー ---
    st.sidebar.title(f"👤 {current_user}")
    
    # メニュー作成
    menu_options = ["📊 マイタスクボード", "📝 新規タスク依頼"]
    
    # ★管理者の場合のみメニューを追加
    if is_admin:
        menu_options.append("👨‍💻 【管理者】全体タスク一覧")
        menu_options.append("📈 【管理者】チーム分析")
        
    menu = st.sidebar.radio("メニュー", menu_options)
    
    st.sidebar.divider()
    if st.sidebar.button("ログアウト"):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- アニメーション ---
    if 'is_walking' not in st.session_state: st.session_state.is_walking = False
    
    if st.session_state.is_walking:
        st.info(f"📘 タスクが「{st.session_state.walking_target}」へ向かっています！")
        if lottie_book: st_lottie(lottie_book, speed=1.5, loop=True, height=200)
        time.sleep(2)
        st.session_state.is_walking = False
        st.rerun()

    # ==========================================
    #  画面1: マイタスクボード (自分に関係あるものだけ)
    # ==========================================
    if menu == "📊 マイタスクボード":
        col_header, col_btn = st.columns([4,1])
        col_header.subheader(f"{current_user}さんのタスクボード")
        if col_btn.button("🔄 更新"): st.rerun()

        all_tasks = get_tasks()
        
        # 自分の関わるタスクのみ抽出 (From または To が自分)
        my_tasks = [t for t in all_tasks if t['to_user'] == current_user or t['from_user'] == current_user]
        
        # 4列定義
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.error("🛑 未着手")
        with col2: st.warning("🏃 対応中")
        with col3: st.success("✅ 完了")
        with col4: st.markdown("<div style='background-color: #6f42c1; color: white; padding: 5px; border-radius: 5px; text-align: center;'>🟣 ルーティン</div>", unsafe_allow_html=True)

        cols = {"未着手": col1, "対応中": col2, "完了": col3, "ルーティン": col4}

        for task in my_tasks:
            status = task.get('status', '未着手')
            if status not in cols: status = '未着手'
            
            with cols[status]:
                with st.container(border=True):
                    prio_icon = "🔥" if task['priority'] == "🔥 至急" else "📘"
                    st.markdown(f"**{prio_icon} {task['content']}**")
                    st.caption(f"{task['from_user']} ➡ {task['to_user']}")
                    
                    # 操作ボタン
                    if status == "未着手":
                        if st.button("着手 ➡", key=f"start_{task['id']}"):
                            update_status(task['id'], "対応中")
                            st.rerun()
                    elif status == "対応中":
                        if st.button("完了 ✅", key=f"done_{task['id']}"):
                            update_status(task['id'], "完了")
                            st.rerun()
                    elif status == "ルーティン":
                         if st.button("完了 ✅", key=f"r_done_{task['id']}"):
                            update_status(task['id'], "完了")
                            st.rerun()

    # ==========================================
    #  画面2: タスク依頼画面
    # ==========================================
    elif menu == "📝 新規タスク依頼":
        st.subheader("📤 タスクを依頼する")
        
        with st.form("create_task"):
            content = st.text_input("タスク内容")
            # 宛先候補から自分を除外してもいいですが、自分用メモもあるので全員表示
            target = st.selectbox("誰に依頼しますか？", list(USERS.keys()))
            priority = st.radio("優先度", ["🔥 至急", "🌲 通常", "🐢 なる早"], horizontal=True, index=1)
            is_routine = st.checkbox("🟣 ルーティンタスクとして登録")
            
            submitted = st.form_submit_button("タスクを送信 📘💨", use_container_width=True)
            
            if submitted and content:
                new_id = str(uuid.uuid4())
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

    # ==========================================
    #  画面3: 【管理者】全体タスク一覧 (権限がある人のみ表示)
    # ==========================================
    elif menu == "👨‍💻 【管理者】全体タスク一覧":
        st.subheader("👨‍💻 全体タスク監視ビュー")
        st.info("ここには組織全体の全てのタスクが表示されています。")
        
        if st.button("データ更新"): st.rerun()
        
        all_tasks = get_tasks()
        
        if not all_tasks:
            st.write("タスクがありません")
        else:
            # フィルタリング機能
            filter_user = st.selectbox("担当者で絞り込み（全員表示は空欄）", ["全員"] + list(USERS.keys()))
            
            # 表示用データの作成
            display_tasks = all_tasks
            if filter_user != "全員":
                display_tasks = [t for t in all_tasks if t['to_user'] == filter_user]

            # 4列カンバン方式で表示するか、一覧表で表示するか
            # 全体管理なら「表（データフレーム）」の方が見やすい場合が多いですが
            # 今回は要望に合わせて「全体のカンバン」を表示します
            
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.error(f"🛑 未着手 ({len([t for t in display_tasks if t['status']=='未着手'])})")
            with col2: st.warning(f"🏃 対応中 ({len([t for t in display_tasks if t['status']=='対応中'])})")
            with col3: st.success(f"✅ 完了 ({len([t for t in display_tasks if t['status']=='完了'])})")
            with col4: st.markdown(f"<div style='background-color: #6f42c1; color: white; padding: 5px; text-align: center;'>🟣 ルーティン ({len([t for t in display_tasks if t['status']=='ルーティン'])})</div>", unsafe_allow_html=True)
            
            cols = {"未着手": col1, "対応中": col2, "完了": col3, "ルーティン": col4}

            for task in display_tasks:
                status = task.get('status', '未着手')
                if status not in cols: status = '未着手'
                
                with cols[status]:
                    with st.container(border=True):
                        # 誰のタスクか分かりやすく表示
                        st.caption(f"担当: **{task['to_user']}**")
                        prio_icon = "🔥" if task['priority'] == "🔥 至急" else "📘"
                        st.markdown(f"**{prio_icon} {task['content']}**")
                        st.caption(f"依頼: {task['from_user']}")

    # ==========================================
    #  画面4: 【管理者】チーム分析
    # ==========================================
    elif menu == "📈 【管理者】チーム分析":
        st.subheader("📊 チーム全体の稼働分析")
        
        all_tasks = get_tasks()
        if all_tasks:
            df = pd.DataFrame(all_tasks)
            active_df = df[df['status'] != '完了']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 🏃 人別の抱えているタスク数")
                if not active_df.empty:
                    count_by_user = active_df['to_user'].value_counts().reset_index()
                    count_by_user.columns = ['担当者', 'タスク数']
                    fig = px.bar(count_by_user, x='担当者', y='タスク数', color='担当者')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.success("残タスクなし")
            
            with col2:
                st.markdown("##### 📋 全体のステータス割合")
                status_counts = df['status'].value_counts().reset_index()
                status_counts.columns = ['状態', '件数']
                fig2 = px.pie(status_counts, values='件数', names='状態')
                st.plotly_chart(fig2, use_container_width=True)
            
            # 生データ表示（管理者用）
            with st.expander("詳細データを見る"):
                st.dataframe(df)
