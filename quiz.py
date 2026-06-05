import streamlit as st
import pandas as pd
from datetime import datetime
import io
import time
from streamlit_autorefresh import st_autorefresh

# ==============================
# تنظیمات صفحه
# ==============================
st.set_page_config(
    page_title="تحلیلگر پاسخ‌برگ آزمون v2.1",
    layout="wide",
    initial_sidebar_state="expanded"
)

# فعال سازی رفرش خودکار هر ۱ ثانیه برای آپدیت تایمر
# این باعث می‌شود تایمر بدون نیاز به کلیک کاربر، حرکت کند
st_autorefresh(interval=1000, key="timer_refresh")

# ==============================
# CSS
# ==============================
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1f4e79;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        color: #666;
        margin-bottom: 1.5rem;
    }
    .q-num {
        font-size: 1.15rem;
        font-weight: 700;
        color: #444;
        margin-bottom: 0.35rem;
    }
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 44px;
        font-weight: 700;
        border: 1px solid #d9d9d9;
        background: #ffffff;
        color: #222;
        transition: all 0.15s ease-in-out;
    }
    div.stButton > button:hover {
        border-color: #8ab4f8;
        box-shadow: 0 0 0 2px rgba(138, 180, 248, 0.18);
    }
    .timer-box {
        background: linear-gradient(135deg, #fff8e1, #fff3cd);
        border: 1px solid #ffe082;
        border-radius: 14px;
        padding: 14px 18px;
        text-align: center;
        font-size: 1.5rem;
        font-weight: 800;
        color: #8a5a00;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# Session State (بسیار مهم برای پایداری)
# ==============================
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "key_answers" not in st.session_state:
    st.session_state.key_answers = {}
if "exam_started" not in st.session_state:
    st.session_state.exam_started = False
if "exam_finished" not in st.session_state:
    st.session_state.exam_finished = False
if "exam_submitted" not in st.session_state:
    st.session_state.exam_submitted = False
if "total_questions" not in st.session_state:
    st.session_state.total_questions = 20
if "timer_minutes" not in st.session_state:
    st.session_state.timer_minutes = 10
if "start_time" not in st.session_state:
    st.session_state.start_time = None

# ==============================
# توابع منطقی
# ==============================
def select_option(q_num, option):
    """مدیریت انتخاب گزینه با حفظ وضعیت در session_state"""
    if not st.session_state.exam_finished:
        current = st.session_state.answers.get(q_num)
        if current == option:
            st.session_state.answers[q_num] = None  # اگر دوباره زد، لغو شود
        else:
            st.session_state.answers[q_num] = option

def start_exam():
    st.session_state.exam_started = True
    st.session_state.exam_finished = False
    st.session_state.exam_submitted = False
    st.session_state.answers = {}
    st.session_state.start_time = time.time()

def finish_exam():
    st.session_state.exam_finished = True
    st.session_state.exam_submitted = True

def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def get_remaining_seconds():
    if not st.session_state.start_time:
        return st.session_state.timer_minutes * 60
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = (st.session_state.timer_minutes * 60) - elapsed
    return max(0, remaining)

def format_time(seconds):
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"

def build_report():
    correct = 0
    wrong = 0
    unanswered = 0
    report_list = []

    for i in range(1, st.session_state.total_questions + 1):
        user_ans = st.session_state.answers.get(i)
        correct_ans = st.session_state.key_answers.get(i)

        if user_ans is None:
            unanswered += 1
            status = "⚪ بی‌پاسخ"
        elif user_ans == correct_ans:
            correct += 1
            status = "✅ درست"
        else:
            wrong += 1
            status = "❌ غلط"

        report_list.append({
            "سوال": i,
            "پاسخ شما": user_ans if user_ans is not None else "-",
            "پاسخ صحیح": correct_ans if correct_ans is not None else "-",
            "وضعیت": status
        })

    total_possible = st.session_state.total_questions * 3
    final_score = (correct * 3) - wrong
    percentage = (final_score / total_possible) * 100 if total_possible else 0

    return correct, wrong, unanswered, percentage, pd.DataFrame(report_list)

# ==============================
# Sidebar
# ==============================
with st.sidebar:
    st.markdown("## ⚙️ تنظیمات آزمون")
    st.session_state.total_questions = st.number_input("تعداد سوالات", 1, 200, st.session_state.total_questions)
    st.session_state.timer_minutes = st.number_input("زمان (دقیقه)", 1, 300, st.session_state.timer_minutes)
    
    st.divider()
    st.markdown("### 🔑 کلید پاسخ‌ها")
    for i in range(1, st.session_state.total_questions + 1):
        st.session_state.key_answers[i] = st.selectbox(
            f"سوال {i}", [None, 1, 2, 3, 4], 
            format_func=lambda x: "-" if x is None else str(x),
            key=f"key_{i}"
        )
    st.divider()
    if st.button("🧹 ریست کل سیستم", use_container_width=True):
        reset_all()

# ==============================
# Main Interface
# ==============================
st.markdown('<div class="main-title">📝 تحلیلگر پاسخ‌برگ آزمون v2.1</div>', unsafe_allow_html=True)

# بخش تایمر
top_left, top_right = st.columns([2, 1])
with top_left:
    if not st.session_state.exam_started:
        if st.button("🚀 شروع آزمون", use_container_width=True):
            start_exam()
            st.rerun()

with top_right:
    if st.session_state.exam_started:
        remaining = get_remaining_seconds()
        if remaining <= 0:
            st.session_state.exam_finished = True
            st.session_state.exam_submitted = True
            st.markdown('<div class="timer-box">⏰ زمان تمام شد!</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="timer-box">⏳ {format_time(remaining)}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="timer-box">⏳ --:--</div>', unsafe_allow_html=True)

st.divider()

# نمایش سوالات
if st.session_state.exam_started:
    cols = st.columns(2)
    q_per_col = (st.session_state.total_questions + 1) // 2

    for col_idx in range(2):
        with cols[col_idx]:
            start_q = col_idx * q_per_col + 1
            end_q = min(start_q + q_per_col, st.session_state.total_questions + 1)

            for i in range(start_q, end_q):
                if i > st.session_state.total_questions: break
                
                st.markdown(f'<div class="q-num">سوال {i}</div>', unsafe_allow_html=True)
                btn_cols = st.columns(4)
                
                for opt in range(1, 5):
                    is_selected = st.session_state.answers.get(i) == opt
                    # تغییر اصلی طبق درخواست شما: نمایش 🟢 داخل دکمه
                    btn_label = f"🟢 {opt}" if is_selected else str(opt)
                    
                    btn_cols[opt-1].button(
                        btn_label,
                        key=f"btn_{i}_{opt}",
                        on_click=select_option,
                        args=(i, opt),
                        disabled=st.session_state.exam_finished,
                        use_container_width=True
                    )
                st.write("") # فاصله بین سوالات

    st.divider()

    # دکمه‌های عملیاتی
    act1, act2 = st.columns(2)
    with act1:
        if st.button("✅ پایان آزمون و تحلیل", use_container_width=True, disabled=st.session_state.exam_finished):
            finish_exam()
            st.rerun()
    with act2:
        if st.button("📊 مشاهده نتیجه", use_container_width=True):
            st.session_state.exam_submitted = True

    # نمایش نتایج
    if st.session_state.exam_submitted:
        correct, wrong, unanswered, percentage, df = build_report()
        st.markdown("## 📈 تحلیل نهایی")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("درصد", f"{percentage:.1f}%")
        m2.metric("درست", correct)
        m3.metric("غلط", wrong)
        m4.metric("بی‌پاسخ", unanswered)

        st.dataframe(df, use_container_width=True)

        output = io.StringIO()
        output.write(f"گزارش آزمون - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        output.write(f"درصد نهایی: {percentage:.2f}%\n")
        df.to_csv(output, index=False)
        st.download_button("📥 دانلود گزارش CSV", output.getvalue().encode("utf-8-sig"), "report.csv", "text/csv")

else:
    st.info("لطفاً برای شروع، دکمه «🚀 شروع آزمون» را بزنید.")
