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

# アニメーションのURL（歩くロボット）
# 他のアニメを探す場合は https://lottiefiles.com/ からJSONのURLを取得します
LOTTIE_WALKING_BOT = "https://assets5.lottiefiles.com/packages/lf20_w51pcehl.json"
lottie_walking = load_lottieurl(LOTTIE_WALKING_BOT)


# ページ設定
st.set_page_config(page_title="Task Walker", page_icon="🚶")

# --- セッション状態の初期化 ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
# 移動中フラグ（アニメーション表示用）
if 'is_walking' not in st.session_state:
    st.session_state.is_walking = False
if 'walking_target' not in st.session_state:
    st.session_state.walking_target = ""

# --- サイドバー ---
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
#  演出強化ポイント：移動中のアニメーション表示
# =========================================
if st.session_state.is_walking:
    # 移動中のみ、画面上部に大きくアニメーションを表示
    st.info(f"🤖 タスクが「{st.session_state.walking_target}」に向かって一生懸命歩いています...")
    
    # Lottieアニメーションを表示（heightで大きさを調整）
    st_lottie(
        lottie_walking,
        speed=1.5,    # 歩くスピード（倍速）
        reverse=False,
        loop=True,    # 移動中はループ再生
        quality="medium",
        height=250,   # アニメーションの高さ
        key="walking"
    )
    # 移動が終わるまで少し待つ演出（実際は裏で時間を稼ぐ）
    time.sleep(3.5) 
    
    # 移動完了（フラグを戻す）
    st.session_state.is_walking = False
    st.session_state.walking_target = ""
    st.rerun() # 画面を更新して通常表示に戻す

# -----------------------------------------


# 1. タスク一覧の強制表示
my_tasks = [t for t in st.session_state.tasks if t['to'] == current_user and t['status'] == '未完了']

if len(my_tasks) > 0:
    st.error(f"⚠️ {len(my_tasks)}件のタスクが届いています！")
    st.markdown("""
    <div style="font-size: 50px; text-align: center; animation: shake 0.5s infinite;">
    ✊ コンコン！
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("届いたタスクを見る", expanded=True):
        for i, task in enumerate(my_tasks):
             # ... (中略: タスク表示部分は前回と同じなので省略可能です) ...
             # 念のため全文載せます
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.info(f"🤖 **From {task['from']}**: {task['content']}")
                with col2:
                    if st.button("受領・完了", key=f"btn_{i}"):
                        st.session_state.tasks.remove(task)
                        st.toast("完了しました！", icon="✅")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
else:
    # 移動中でなければ平和メッセージを表示
    if not st.session_state.is_walking:
        st.success("現在、手持ちタスクはありません。")


st.divider()

# 2. 新しいタスクを歩かせる（送信）
st.subheader("📤 新しいタスクを歩かせる")

# 移動中はフォームを無効化（disabled）して連打を防ぐ
with st.form("send_task_form", clear_on_submit=True):
    task_content = st.text_input("タスクの内容", placeholder="例：承認をお願いします")
    target_user = st.selectbox("誰に歩いて行かせますか？", ["上司", "経理担当", "自分"])
    
    # 送信ボタン
    submitted = st.form_submit_button(
        "タスク送信 🚶💨", 
        disabled=st.session_state.is_walking # 移動中は押せないようにする
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
        st.toast("いってらっしゃい！", icon="👋")
        st.rerun()

# --- 全体俯瞰 ---
with st.expander("🦅 全体の状況"):
    if st.session_state.tasks:
        st.dataframe(pd.DataFrame(st.session_state.tasks))
