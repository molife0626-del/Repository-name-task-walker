import streamlit as st
import time
import pandas as pd
import requests
from streamlit_lottie import st_lottie

# --- Lottieアニメーションを読み込む関数 ---
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# アニメーションURL設定
# 書類（タスク）のキャラクターが走っているアニメーション
LOTTIE_RUNNING_TASK = "https://lottie.host/20278684-5751-4180-9681-600004093955/oG4X6R8s2a.json"
lottie_running = load_lottieurl(LOTTIE_RUNNING_TASK)

# ページ設定
st.set_page_config(page_title="Task Walker", page_icon="🏃‍♂️")

# --- セッション状態の初期化（簡易データベース） ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
    
# 移動中フラグ（アニメーション表示用）
if 'is_walking' not in st.session_state:
    st.session_state.is_walking = False
if 'walking_target' not in st.session_state:
    st.session_state.walking_target = ""

# --- サイドバー：ユーザー切り替え ---
st.sidebar.header("👤 ログイン設定")
current_user = st.sidebar.selectbox(
    "あなたは誰ですか？",
    ["自分", "上司", "経理担当"],
    index=0
)
st.sidebar.info(f"現在「{current_user}」として操作中")

# --- メイン画面 ---
st.title(f"Task Walker: {current_user}のデスク 🏠")

# =========================================
#  演出パート：移動中のアニメーション表示
# =========================================
if st.session_state.is_walking:
    # 移動中のみ、画面上部に大きくアニメーションを表示
    st.info(f"🏃‍♂️ タスクが「{st.session_state.walking_target}」に向かって全力で走っています！")
    
    # 走るアニメーションを表示
    if lottie_running:
        st_lottie(
            lottie_running,
            speed=1.5,    # 走るスピード（少し速く）
            reverse=False,
            loop=True,
            quality="medium",
            height=300,   # アニメーションのサイズ
            key="running"
        )
    else:
        st.write("🏃‍♂️💨 走っています...（アニメーション読込エラー）")

    # 移動時間の演出（3.5秒待つ）
    time.sleep(3.5) 
    
    # 移動完了処理
    st.session_state.is_walking = False
    st.session_state.walking_target = ""
    st.rerun() # 画面を更新して通常表示に戻す

# -----------------------------------------

# 1. タスク一覧（インボックス）
# 自分宛てのタスクを抽出
my_tasks = [t for t in st.session_state.tasks if t['to'] == current_user and t['status'] == '未完了']

if len(my_tasks) > 0:
    # タスクがある場合：警告表示とノック
    st.error(f"⚠️ {len(my_tasks)}件のタスクが到着しています！")
    
    # 視覚的な「ノック」演出
    st.markdown("""
    <div style="font-size: 50px; text-align: center; animation: shake 0.5s infinite;">
    ✊ コンコン！
    </div>
    <style>
    @keyframes shake {
      0% { transform: translate(1px, 1px) rotate(0deg); }
      10% { transform: translate(-1px, -2px) rotate(-1deg); }
      20% { transform: translate(-3px, 0px) rotate(1deg); }
      30% { transform: translate(3px, 2px) rotate(0deg); }
      40% { transform: translate(1px, -1px) rotate(1deg); }
      50% { transform: translate(-1px, 2px) rotate(-1deg); }
      60% { transform: translate(-3px, 1px) rotate(0deg); }
      70% { transform: translate(3px, 1px) rotate(-1deg); }
      80% { transform: translate(-1px, -1px) rotate(1deg); }
      90% { transform: translate(1px, 2px) rotate(0deg); }
      100% { transform: translate(1px, -2px) rotate(-1deg); }
    }
    </style>
    """, unsafe_allow_html=True)

    # タスクカードの表示
    with st.container():
        for i, task in enumerate(my_tasks):
            st.info(f"📄 **From {task['from']}**: {task['content']}")
            if st.button("受領・完了", key=f"btn_{i}"):
                # タスクを完了状態にする（リストから削除）
                st.session_state.tasks.remove(task)
                st.toast("お疲れ様です！タスクを完了しました。", icon="✅")
                st.balloons()
                time.sleep(1)
                st.rerun() # 画面更新
else:
    # 移動中でなければ平和メッセージを表示
    if not st.session_state.is_walking:
        st.success("現在、手持ちタスクはありません。平和です ☕")


st.divider()

# 2. 新しいタスクを走らせる（送信フォーム）
st.subheader("📤 新しいタスクを走らせる")

# 移動中はフォームを操作できないようにする
with st.form("send_task_form", clear_on_submit=True):
    task_content = st.text_input("タスクの内容", placeholder="例：企画書の確認をお願いします")
    target_user = st.selectbox("誰のところへ走らせますか？", ["上司", "経理担当", "自分"])
    
    # 送信ボタン
    submitted = st.form_submit_button(
        "タスク送信 🏃💨", 
        disabled=st.session_state.is_walking
    )

    if submitted and task_content:
        # データを保存
        new_task = {
            "content": task_content,
            "from": current_user,
            "to": target_user,
            "status": "未完了"
        }
        st.session_state.tasks.append(new_task)
        
        # 移動フラグを立てて画面更新（アニメーションを開始させる）
        st.session_state.is_walking = True
        st.session_state.walking_target = target_user
        st.toast("いってらっしゃい！全力疾走中です！", icon="👋")
        st.rerun()

# --- 全体俯瞰（管理者用） ---
with st.expander("🦅 全体のタスク状況（管理者ビュー）"):
    if st.session_state.tasks:
        st.dataframe(pd.DataFrame(st.session_state.tasks))
    else:
        st.write("現在、タスクは1つもありません。")
