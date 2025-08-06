import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

# 관리자 비밀번호 (간단 예시, 실제 환경에서는 보안 강화 필요)
ADMIN_PASSWORD = "admin123"

# 초기 세션 상태 설정
if 'responses' not in st.session_state:
    st.session_state['responses'] = []

if 'teams' not in st.session_state:
    st.session_state['teams'] = {}

if 'scores' not in st.session_state:
    st.session_state['scores'] = {}

# 제목
st.title("🏸 배드민턴부 점심시간 운영 시스템")

# 현재 날짜
today = datetime.now().strftime("%Y-%m-%d")
st.write(f"📅 오늘 날짜: {today}")

st.markdown("---")

##########################
# 1. 인원 확인
##########################
st.header("1️⃣ 당일 점심 참석 여부 확인")

with st.form(key='attendance_form'):
    name = st.text_input("성명을 입력하세요:", max_chars=20)
    attending = st.radio("점심시간에 올 수 있나요?", ["예", "아니오"])

    attendance_time = None
    reason = None

    if attending == "예":
        attendance_time = st.radio("언제 오나요?", ["점심 식사 전 (1:00~1:10)", "점심 식사 후 (1:30~1:40)"])
    else:
        reason = st.text_area("못 오는 사유를 입력해주세요:")

    submit = st.form_submit_button("응답 제출")

if submit and name.strip() != "":
    response = {
        'id': str(uuid.uuid4()),
        'name': name.strip(),
        'attending': attending,
        'time': attendance_time,
        'reason': reason
    }
    st.session_state.responses.append(response)
    st.success("응답이 저장되었습니다!")

st.markdown("---")

##########################
# 관리자 로그인
##########################
with st.expander("🔒 관리자 로그인"):
    admin_pw = st.text_input("관리자 비밀번호 입력", type="password")
    is_admin = (admin_pw == ADMIN_PASSWORD)
    if is_admin:
        st.success("관리자 권한이 확인되었습니다.")
    else:
        st.info("관리자 비밀번호를 입력해야 아래 기능들이 보입니다.")

##########################
# 관리자 전용: 응답 결과 보기
##########################
if is_admin:
    st.header("📋 응답 결과 보기")

    df = pd.DataFrame(st.session_state.responses)
    if not df.empty:
        st.dataframe(df[['name', 'attending', 'time', 'reason']])
    else:
        st.write("아직 제출된 응답이 없습니다.")

    # 시간별 참석자 필터링
    before_lunch = [r for r in st.session_state.responses if r['attending'] == "예" and r['time'] == "점심 식사 전 (1:00~1:10)"]
    after_lunch = [r for r in st.session_state.responses if r['attending'] == "예" and r['time'] == "점심 식사 후 (1:30~1:40)"]

    st.subheader("✅ 점심 식사 전 참석자")
    st.write(", ".join([p['name'] for p in before_lunch]) if before_lunch else "없음")

    st.subheader("✅ 점심 식사 후 참석자")
    st.write(", ".join([p['name'] for p in after_lunch]) if after_lunch else "없음")

##########################
# 2. 조 편성 (관리자만 가능)
##########################
if is_admin:
    st.header("2️⃣ 조 편성")

    if st.button("⚙️ 조 편성하기"):

        def assign_teams(players):
            teams = []
            waiting = []

            for i in range(0, len(players), 4):
                group = players[i:i+4]
                if len(group) == 4:
                    teams.append(group)
                else:
                    waiting.extend(group)
            return teams, waiting

        # 시간대별 조 편성
        for slot, players in [("before", before_lunch), ("after", after_lunch)]:
            names = [p['name'] for p in players]
            teams, waiting = assign_teams(names)
            st.session_state.teams[slot] = {
                'teams': teams,
                'waiting': waiting
            }

        st.success("조 편성이 완료되었습니다!")

    # 편성 결과 출력
    for slot_label, key in [("점심 식사 전", "before"), ("점심 식사 후", "after")]:
        st.subheader(f"🧾 {slot_label} 조 편성 결과")
        slot_teams = st.session_state.teams.get(key, {})
        for idx, team in enumerate(slot_teams.get('teams', [])):
            st.write(f"🏸 {idx+1}조 (코트 {idx%3 + 1}번): {', '.join(team)}")
        if slot_teams.get('waiting'):
            st.write(f"⏱️ 대기 인원: {', '.join(slot_teams['waiting'])}")

##########################
# 3. 경기 스코어 기록
##########################
if is_admin and st.session_state.teams:
    st.header("3️⃣ 스코어 기록")

    for slot_label, key in [("점심 식사 전", "before"), ("점심 식사 후", "after")]:
        st.subheader(f"{slot_label} 경기 결과 입력")
        slot_teams = st.session_state.teams.get(key, {})
        for idx, team in enumerate(slot_teams.get('teams', [])):
            team_id = f"{key}_team_{idx}"
            score_input = st.text_input(f"🏆 {idx+1}조 스코어 입력 (예: 21-17)", key=team_id)
            if score_input:
                st.session_state.scores[team_id] = {
                    'team': team,
                    'score': score_input
                }

    # 입력된 스코어 확인
    if st.session_state.scores:
        st.subheader("📊 기록된 스코어")
        for team_id, data in st.session_state.scores.items():
            st.write(f"{', '.join(data['team'])} → {data['score']}")
