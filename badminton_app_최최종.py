import streamlit as st
from datetime import datetime
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pathlib import Path

# Google API 스코프 정의
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# JSON 키 파일 경로 설정 (너의 경로에 맞게 수정)
json_path = Path.home() / "OneDrive" / "ドキュメント" / "개인폴더" / "파이썬" / "streamlit-badminton-311bd4396ecf.json"

# 인증 객체 생성
creds = ServiceAccountCredentials.from_json_keyfile_name(str(json_path), scope)

# gspread 클라이언트 생성
client = gspread.authorize(creds)

# Google Sheet 연결
sheet_participants = client.open("배드민턴참가자명단").sheet1
sheet_absent = client.open("불참자명단").sheet1
sheet_attendance = client.open("출석현황").sheet1

# 상태 초기화
if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False
if 'submitted' not in st.session_state:
    st.session_state['submitted'] = False
if 'participants' not in st.session_state:
    data = sheet_participants.get_all_records()
    st.session_state['participants'] = [{'name': row['name'], 'time': row['time'].split(', ')} for row in data]
if 'unavailable' not in st.session_state:
    data = sheet_absent.get_all_records()
    st.session_state['unavailable'] = [{'name': row['name'], 'reason': row['reason']} for row in data]
if 'attendance' not in st.session_state:
    data = sheet_attendance.get_all_records()
    st.session_state['attendance'] = data
if 'assignments' not in st.session_state:
    st.session_state['assignments'] = {}
if 'scores' not in st.session_state:
    st.session_state['scores'] = {}
if 'partners' not in st.session_state:
    st.session_state['partners'] = {}

# --- 관리자 사이드바 ---
with st.sidebar:
    st.markdown("## 🛠️ 관리자 메뉴")
    if not st.session_state['is_admin']:
        password = st.text_input("비밀번호", type="password")
        if password == "04281202":
            st.session_state['is_admin'] = True
            st.success("✅ 관리자 인증 완료")
            st.rerun()
    else:
        st.success("✅ 관리자 모드입니다.")
        if st.button("비관리자 모드로 전환"):
            st.session_state['is_admin'] = False
            st.rerun()

        if st.button("조 편성"):
            total = st.session_state['participants']
            front = [p for p in total if '전' in p['time']]
            back = [p for p in total if '후' in p['time']]

            def assign_teams(group):
                teams = {}
                for i in range(0, len(group) - len(group) % 4, 4):
                    members = group[i:i+4]
                    teams[f"코트 {(i//4)+1}"] = {
                        '1팀': [members[0]['name'], members[1]['name']],
                        '2팀': [members[2]['name'], members[3]['name']]
                    }
                waitlist = group[len(group) - len(group) % 4:] if len(group) % 4 != 0 else []
                return teams, waitlist

            st.session_state['assignments'] = {}
            st.session_state['assignments']['전'], front_wait = assign_teams(front)
            st.session_state['assignments']['후'], back_wait = assign_teams(back)
            st.session_state['assignments']['대기'] = front_wait + back_wait

        if st.button("초기화"):
            for key in ['submitted', 'participants', 'unavailable', 'assignments', 'scores', 'partners', 'attendance']:
                st.session_state[key] = [] if isinstance(st.session_state.get(key), list) else {}
            st.rerun()

        if st.button("불참자 확인하기"):
            st.markdown("### ❌ 불참자 명단")
            for u in st.session_state['unavailable']:
                st.write(f"- {u['name']}: {u['reason']}")

        if st.button("출석 현황 다운로드"):
            df = pd.DataFrame(st.session_state['attendance'])
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 출석 CSV 다운로드",
                data=csv,
                file_name='출석현황.csv',
                mime='text/csv'
            )

# --- 사용자 입력 영역 ---
if not st.session_state['is_admin']:
    if not st.session_state['submitted']:
        name = st.text_input("성함을 입력해주세요:")
        response = st.radio("점심시간에 올 수 있나요?", ["예", "아니오"])

        times = []
        if response == "예":
            st.write("언제 오실 수 있나요?")
            col1, col2 = st.columns(2)
            with col1:
                check1 = st.checkbox("점심시간 전 (1:00~1:10)")
            with col2:
                check2 = st.checkbox("점심시간 후 (1:30~1:40)")
            if check1: times.append("전")
            if check2: times.append("후")
        else:
            reason = st.text_area("불참 사유를 입력해주세요")

        if st.button("응답 제출"):
            st.session_state['submitted'] = True
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if response == "예" and name:
                st.session_state['participants'].append({'name': name, 'time': times})
                sheet_participants.append_row([name, ", ".join(times), now])
                st.success("✅ 응답 제출 완료")
            elif response == "아니오" and name:
                st.session_state['unavailable'].append({'name': name, 'reason': reason})
                sheet_absent.append_row([name, reason, now])
                st.success("❌ 응답 제출 완료")
            else:
                st.warning("이름을 입력해주세요")
    else:
        st.info("응답을 제출하였습니다.")

# --- 조 편성 결과 및 출석 확인 ---
if not st.session_state['is_admin'] and '전' in st.session_state['assignments']:
    st.markdown("## ✅ 조 편성 현황")

    for time in ['전', '후']:
        if time in st.session_state['assignments']:
            st.markdown(f"### 점심시간 {time}")
            teams = st.session_state['assignments'][time]
            for court, t in teams.items():
                st.markdown(f"**{court}**")
                for team_label, members in t.items():
                    cols = st.columns(len(members))
                    for idx, name in enumerate(members):
                        with cols[idx]:
                            if name not in [a['name'] for a in st.session_state['attendance']]:
                                if st.button(f"출석 ({name})", key=f"attend_{court}_{team_label}_{name}"):
                                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    st.session_state['attendance'].append({
                                        'name': name,
                                        'court': court,
                                        'team': team_label,
                                        'time_slot': time,
                                        'timestamp': timestamp
                                    })
                                    sheet_attendance.append_row([name, court, team_label, time, timestamp])
                                    st.success(f"✅ {name} 출석 완료")
                            else:
                                st.write(f"✅ {name} 출석 완료")

                col1, col2 = st.columns(2)
                with col1:
                    team1 = st.multiselect(f"1팀 ({court})", t['1팀'], key=f"t1_{court}_{time}")
                    st.session_state['partners'][f"{court}_{time}_1팀"] = team1
                with col2:
                    team2 = st.multiselect(f"2팀 ({court})", t['2팀'], key=f"t2_{court}_{time}")
                    st.session_state['partners'][f"{court}_{time}_2팀"] = team2

                st.markdown("#### 스코어 입력")
                score = st.text_input(f"{court} 스코어 입력 (예: 21-15)", key=f"score_{court}_{time}")
                if st.button(f"스코어 제출 ({court})", key=f"btn_{court}_{time}"):
                    st.session_state['scores'][f"{court}_{time}"] = score
                    st.success("🏁 경기 종료: 스코어 제출 완료")

    if st.session_state['assignments'].get('대기'):
        st.markdown("### ⏳ 대기 인원")
        for person in st.session_state['assignments']['대기']:
            st.write(f"- {person['name']}")

# --- 조 편성 전 참가자만 보여주기 ---
if not st.session_state['is_admin'] and not st.session_state['assignments']:
    st.markdown("## 👥 참가자 현황")
    front = [p['name'] for p in st.session_state['participants'] if '전' in p['time']]
    back = [p['name'] for p in st.session_state['participants'] if '후' in p['time']]
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 점심시간 전")
        for name in front:
            st.write(f"- {name}")
    with col2:
        st.markdown("### 점심시간 후")
        for name in back:
            st.write(f"- {name}")
